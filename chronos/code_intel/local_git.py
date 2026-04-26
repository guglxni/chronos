"""
Local git operations via ``subprocess`` — no network, no extra services.

Replaces the ``gitnexus_get_commits`` stub. Returns commits whose paths or
diffs reference an entity name, plus ``git show`` metadata used for
root-cause attribution downstream.

Design rules:
    * Never raise on a non-git directory or unknown entity — return ``[]``.
    * All shell args are passed as a list (no ``shell=True``) and the entity
      name is validated against a strict charset before being interpolated
      into a regex pattern. This blocks shell-meta injection from webhook
      payloads (the entity FQN is attacker-controlled).
    * Times out after ``GIT_TIMEOUT_SECONDS`` to keep step 4 within the
      pipeline budget.
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("chronos.code_intel.local_git")

GIT_TIMEOUT_SECONDS = 15

# Entity FQNs look like ``service.database.schema.table.column``. Allow only
# alphanumerics, underscore, dot, hyphen — covers every realistic data asset
# while blocking shell metacharacters and regex backtracking attacks.
_SAFE_ENTITY_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,256}$")

_GIT_AVAILABLE: bool | None = None


def _git_available() -> bool:
    """Return True iff the ``git`` binary is on PATH. Cached for the process."""
    global _GIT_AVAILABLE
    if _GIT_AVAILABLE is None:
        _GIT_AVAILABLE = shutil.which("git") is not None
    return _GIT_AVAILABLE


def _is_git_repo(repo_path: Path) -> bool:
    """Return True iff ``repo_path`` is inside a git working tree."""
    if not _git_available() or not repo_path.exists():
        return False
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "-C", str(repo_path), "rev-parse", "--is-inside-work-tree"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _safe_entity(entity_name: str) -> str | None:
    """Return the entity name iff it matches the safe charset, else None."""
    if not entity_name or not _SAFE_ENTITY_RE.match(entity_name):
        return None
    return entity_name


def _run_git(args: list[str], repo_path: Path) -> str:
    """Run ``git`` with the given args inside ``repo_path``.

    Returns the captured stdout on success. Returns empty string on any
    failure — git errors should never bubble up and abort the investigation.
    """
    if not _git_available():
        return ""
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "-C", str(repo_path), *args],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.debug("git %s failed: %s", " ".join(args), exc)
        return ""
    if result.returncode != 0:
        logger.debug(
            "git %s exit=%d stderr=%s",
            " ".join(args),
            result.returncode,
            result.stderr.strip()[:200],
        )
        return ""
    return result.stdout


def _parse_commit_log(raw: str) -> list[dict[str, Any]]:
    """Parse the ``%H%x1f%an%x1f%aI%x1f%s`` pretty format into commit dicts.

    The unit-separator (0x1f) is used between fields and a record-separator
    (0x1e) terminates each commit so that messages containing newlines or
    pipes do not corrupt parsing.
    """
    commits: list[dict[str, Any]] = []
    for record in raw.split("\x1e"):
        record = record.strip("\n\r ")
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 4:
            continue
        sha, author, iso_date, message = parts[0], parts[1], parts[2], "\x1f".join(parts[3:])
        commits.append(
            {
                "sha": sha,
                "author": author,
                "date": iso_date,
                "message": message.strip()[:500],
                "files_changed": [],  # filled in by ``_attach_changed_files`` if requested
            }
        )
    return commits


def _attach_changed_files(commits: list[dict[str, Any]], repo_path: Path) -> None:
    """Populate ``files_changed`` for each commit via a single ``git show``."""
    for commit in commits:
        sha = commit.get("sha", "")
        if not sha:
            continue
        out = _run_git(
            ["show", "--no-patch", "--name-only", "--pretty=format:", sha],
            repo_path,
        )
        files = [line.strip() for line in out.splitlines() if line.strip()]
        commit["files_changed"] = files[:50]  # cap to keep payloads sane


def get_commits_for_entity(
    entity_name: str,
    repo_path: Path,
    limit: int = 10,
    since_days: int | None = None,
) -> list[dict[str, Any]]:
    """Find recent commits whose diff or message mentions the entity.

    Args:
        entity_name: Data entity name (table, column, dbt model). Validated
            against ``_SAFE_ENTITY_RE`` to block injection.
        repo_path: Path to a git working tree. If not a repo, returns ``[]``.
        limit: Cap on the number of commits returned.
        since_days: Optional ``--since`` filter, e.g. ``7`` → last week.

    Returns:
        List of commit dicts: ``{sha, author, date, message, files_changed}``.
    """
    safe = _safe_entity(entity_name)
    if safe is None or not _is_git_repo(repo_path):
        return []

    args = [
        "log",
        f"-n{int(max(1, min(limit, 200)))}",
        "--pretty=format:%H%x1f%an%x1f%aI%x1f%s%x1e",
        # ``-G`` matches added/removed lines that contain the regex —
        # captures both content changes and rename moves involving the entity.
        f"-G{re.escape(safe)}",
    ]
    if since_days is not None and since_days > 0:
        args.append(f"--since={int(since_days)}.days.ago")

    raw = _run_git(args, repo_path)
    commits = _parse_commit_log(raw)
    _attach_changed_files(commits, repo_path)
    return commits


def get_file_history(
    file_path: str,
    repo_path: Path,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return the most recent commits that touched ``file_path``.

    Used by Step 4 once we already know which files reference an entity —
    surfaces the actual change history per file for the LLM synthesis step.
    """
    if not _is_git_repo(repo_path):
        return []
    # Defend against absolute paths or path traversal — git ``--`` separator
    # protects against ambiguous arg parsing but we still normalise.
    rel_path = file_path.lstrip("/")
    if ".." in Path(rel_path).parts:
        return []

    raw = _run_git(
        [
            "log",
            f"-n{int(max(1, min(limit, 50)))}",
            "--pretty=format:%H%x1f%an%x1f%aI%x1f%s%x1e",
            "--",
            rel_path,
        ],
        repo_path,
    )
    return _parse_commit_log(raw)


async def aget_commits_for_entity(
    entity_name: str,
    repo_path: Path,
    limit: int = 10,
    since_days: int | None = None,
) -> list[dict[str, Any]]:
    """Async wrapper — runs the blocking subprocess call in a thread pool."""
    return await asyncio.to_thread(
        get_commits_for_entity, entity_name, repo_path, limit, since_days
    )


async def aget_file_history(
    file_path: str,
    repo_path: Path,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Async wrapper for ``get_file_history``."""
    return await asyncio.to_thread(get_file_history, file_path, repo_path, limit)

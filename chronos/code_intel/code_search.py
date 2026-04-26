"""
Codebase scanner that finds files referencing a data entity.

Replaces the ``gitnexus_search_files`` and ``gitnexus_get_file_references``
stubs.  Strategy:

1. Try ``ripgrep`` (``rg``) for sub-second scan over large repos. ripgrep
   honours ``.gitignore`` by default which keeps results sane.
2. Fall back to a pure-Python ``pathlib`` walk that opens each file and
   substring-matches. Slow on huge repos but always available.

Both backends return the same ``[{path, line, snippet, language}]`` shape so
the rest of the pipeline does not care which one ran.

Security: the entity name is validated against a strict charset before being
passed to ripgrep (``--fixed-strings`` avoids regex parsing entirely).
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("chronos.code_intel.code_search")

RG_TIMEOUT_SECONDS = 10
PY_WALK_FILE_LIMIT = 5000  # cap for fallback walker — protects against huge trees
PY_WALK_BYTES_LIMIT = 2_000_000  # 2 MB cap per file — skip big binaries / fixtures

# Entity FQNs use the same charset as ``local_git`` — alphanumerics + ``._-``.
_SAFE_QUERY_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,256}$")

# File extensions worth scanning for data-entity references. Tuned for a
# typical data platform: SQL/dbt/Python/YAML/Airflow/dbt configs.
_RELEVANT_EXTENSIONS = frozenset(
    {
        ".py", ".sql", ".yml", ".yaml", ".json", ".jinja", ".jinja2",
        ".j2", ".ipynb", ".dbtignore", ".csv", ".tsv", ".toml", ".ini",
        ".sh", ".scala", ".java", ".kt", ".rs", ".go", ".ts", ".tsx",
    }
)

_LANGUAGE_HINTS = {
    ".py": "python", ".sql": "sql", ".yml": "yaml", ".yaml": "yaml",
    ".json": "json", ".ipynb": "jupyter", ".sh": "shell",
    ".ts": "typescript", ".tsx": "typescript", ".scala": "scala",
    ".java": "java", ".kt": "kotlin", ".rs": "rust", ".go": "go",
    ".jinja": "jinja", ".jinja2": "jinja", ".j2": "jinja",
}

_RG_AVAILABLE: bool | None = None


def _rg_available() -> bool:
    """Return True iff the ripgrep binary is on PATH. Cached for the process."""
    global _RG_AVAILABLE
    if _RG_AVAILABLE is None:
        _RG_AVAILABLE = shutil.which("rg") is not None
    return _RG_AVAILABLE


def _safe_query(query: str) -> str | None:
    """Return the query iff it matches the safe charset, else None."""
    if not query or not _SAFE_QUERY_RE.match(query):
        return None
    return query


def _ext_to_language(ext: str) -> str:
    """Map a file extension to a coarse language label for the LLM prompt."""
    return _LANGUAGE_HINTS.get(ext.lower(), "text")


def _search_with_ripgrep(
    query: str,
    repo_path: Path,
    limit: int,
) -> list[dict[str, Any]]:
    """Run ripgrep and return ``[{path, line, snippet, language}]``."""
    args = [
        "rg",
        "--fixed-strings",          # treat query as a literal, no regex parsing
        "--no-heading",
        "--with-filename",
        "--line-number",
        "--max-count", "3",        # at most 3 matches per file — we just need refs
        "--max-filesize", "2M",
        "--ignore-case",
        # Limit file types to the relevant set — avoids matching node_modules etc.
        "--type-add", "data:*.{sql,yml,yaml,json,jinja,jinja2,j2,csv,tsv}",
        "--type-add", "code:*.{py,ts,tsx,scala,java,kt,rs,go,sh}",
        "-tdata", "-tcode",
        "--",
        query,
        str(repo_path),
    ]
    try:
        result = subprocess.run(  # noqa: S603
            args,
            capture_output=True,
            text=True,
            timeout=RG_TIMEOUT_SECONDS,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.debug("ripgrep failed: %s", exc)
        return []

    # rg exits 0 on matches, 1 on no matches (not an error), 2 on error.
    if result.returncode > 1:
        logger.debug("rg exit=%d stderr=%s", result.returncode, result.stderr[:200])
        return []

    hits: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for line in result.stdout.splitlines():
        # Format: ``path:lineno:snippet`` (paths never contain a colon outside
        # of Windows drive letters which we don't target).
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path_str, lineno_str, snippet = parts
        try:
            lineno = int(lineno_str)
        except ValueError:
            continue
        # Make path relative to repo root for stable display in the UI.
        try:
            rel_path = str(Path(path_str).resolve().relative_to(repo_path.resolve()))
        except ValueError:
            rel_path = path_str
        ext = Path(path_str).suffix.lower()
        hits.append(
            {
                "path": rel_path,
                "line": lineno,
                "snippet": snippet.strip()[:200],
                "language": _ext_to_language(ext),
            }
        )
        seen_paths.add(rel_path)
        if len(seen_paths) >= limit:
            break
    return hits


def _search_with_pywalk(
    query: str,
    repo_path: Path,
    limit: int,
) -> list[dict[str, Any]]:
    """Pure-Python fallback scanner. Slow but works without ripgrep."""
    query_bytes = query.lower().encode("utf-8", errors="ignore")
    hits: list[dict[str, Any]] = []
    files_scanned = 0
    for path in repo_path.rglob("*"):
        if files_scanned >= PY_WALK_FILE_LIMIT or len(hits) >= limit:
            break
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in _RELEVANT_EXTENSIONS:
            continue
        # Skip hidden directories and common cache dirs cheaply.
        if any(part.startswith(".") and part not in {".github"} for part in path.parts):
            continue
        if any(part in {"node_modules", "__pycache__", "target", "dist", "build"}
               for part in path.parts):
            continue
        try:
            if path.stat().st_size > PY_WALK_BYTES_LIMIT:
                continue
            content = path.read_bytes()
        except OSError:
            continue
        files_scanned += 1
        lower = content.lower()
        if query_bytes not in lower:
            continue
        # Find the first match's line number for citation.
        idx = lower.index(query_bytes)
        line_no = lower.count(b"\n", 0, idx) + 1
        # Extract a one-line snippet around the match.
        line_start = lower.rfind(b"\n", 0, idx) + 1
        line_end = lower.find(b"\n", idx)
        if line_end == -1:
            line_end = min(len(content), idx + 200)
        snippet = content[line_start:line_end].decode("utf-8", errors="replace").strip()[:200]
        try:
            rel_path = str(path.relative_to(repo_path))
        except ValueError:
            rel_path = str(path)
        hits.append(
            {
                "path": rel_path,
                "line": line_no,
                "snippet": snippet,
                "language": _ext_to_language(ext),
            }
        )
    return hits


def search_entity_references(
    query: str,
    repo_path: Path,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Find files in ``repo_path`` whose contents reference ``query``.

    Tries ripgrep first (fast, gitignore-aware) and falls back to a pure
    Python walker. Returns at most ``limit`` distinct files.
    """
    safe = _safe_query(query)
    if safe is None or not repo_path.exists():
        return []
    if _rg_available():
        results = _search_with_ripgrep(safe, repo_path, limit)
        if results:
            return results
        # Fall through to pywalk only if rg returned nothing — covers the
        # case where rg respected ``.gitignore`` and excluded a real match.
    return _search_with_pywalk(safe, repo_path, limit)


async def asearch_entity_references(
    query: str,
    repo_path: Path,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Async wrapper — runs the blocking scanner in a thread pool."""
    return await asyncio.to_thread(search_entity_references, query, repo_path, limit)

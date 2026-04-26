"""
Step 4 — Code Blast Radius

Identifies the code surface impacted by the failing entity. This step now
runs three backends in parallel and merges their results:

1. **dbt manifest** (``dbt_get_node`` / ``dbt_walk_upstream`` /
   ``dbt_walk_downstream``) — exact dbt DAG when a manifest is configured.
2. **GitNexus-compatible local backends** (``gitnexus_search_files``,
   ``gitnexus_get_commits``) — text/AST scan of the data-platform repo
   plus ``git log -G`` for recent commits.
3. **Graphify graph adapter** (``graphify_get_neighbors``) — code-structure
   neighbours for the entity, used for cross-module call traces.

Results are written to richer state slots so Step 7 (synthesis) and the
final IncidentReport can present an architectural blast radius alongside
the file-level changes.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import (
    dbt_walk_downstream,
    dbt_walk_upstream,
    gitnexus_get_commits,
    gitnexus_search_files,
    graphify_get_neighbors,
)

logger = logging.getLogger("chronos.agent.code_blast_radius")


def _normalise_table_candidates(entity_fqn: str) -> list[str]:
    """Return a ranked list of search terms for a data-entity FQN.

    Most data warehouses present entities as ``service.db.schema.table`` and
    callers commonly reference the trailing ``schema.table`` or just the
    bare table name. We try the most specific form first so search results
    are tightly relevant.
    """
    parts = [p for p in entity_fqn.split(".") if p]
    if not parts:
        return []
    candidates: list[str] = []
    if len(parts) >= 2:
        candidates.append(".".join(parts[-2:]))  # schema.table
    candidates.append(parts[-1])  # table
    seen: set[str] = set()
    deduped: list[str] = []
    for cand in candidates:
        if cand and cand not in seen:
            seen.add(cand)
            deduped.append(cand)
    return deduped


async def _gather_file_references(
    entity_fqn: str,
    target_count: int = 20,
) -> list[dict[str, Any]]:
    """Run gitnexus search across all candidate names, de-duplicated by path."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for candidate in _normalise_table_candidates(entity_fqn):
        try:
            files = await gitnexus_search_files(candidate)
        except Exception as exc:
            logger.warning("gitnexus_search_files(%s) failed: %s", candidate, exc)
            continue
        for entry in files:
            path = str(entry.get("path", ""))
            if not path or path in seen:
                continue
            seen.add(path)
            out.append(entry)
            if len(out) >= target_count:
                return out
    return out


async def code_blast_radius_node(state: InvestigationState) -> InvestigationState:
    """Search code + dbt + graphify for everything that touches the entity."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.now(tz=UTC)

    related_code_files: list[dict[str, Any]] = []
    recent_commits: list[dict[str, Any]] = []
    dbt_upstream: list[dict[str, Any]] = []
    dbt_downstream: list[dict[str, Any]] = []
    code_graph_neighbors: list[dict[str, Any]] = []

    if entity_fqn:
        # The most specific candidate (schema.table or just table) is the
        # one we use for git log and graphify lookups; the broader search
        # already explores all candidates.
        candidates = _normalise_table_candidates(entity_fqn)
        primary = candidates[0] if candidates else entity_fqn

        results = await asyncio.gather(
            _gather_file_references(entity_fqn, target_count=20),
            gitnexus_get_commits(primary, limit=10),
            dbt_walk_upstream(entity_fqn, depth=3),
            dbt_walk_downstream(entity_fqn, depth=3),
            graphify_get_neighbors(primary, limit=15),
            return_exceptions=True,
        )

        # Defensive unpack — any backend may legitimately return [].
        if isinstance(results[0], list):
            related_code_files = results[0][:20]
        if isinstance(results[1], list):
            recent_commits = results[1]
        if isinstance(results[2], list):
            dbt_upstream = results[2]
        if isinstance(results[3], list):
            dbt_downstream = results[3]
        if isinstance(results[4], list):
            code_graph_neighbors = results[4]

        # Surface backend failures in the logs but keep the pipeline running.
        for idx, label in enumerate(
            (
                "search_files",
                "get_commits",
                "dbt_walk_upstream",
                "dbt_walk_downstream",
                "graphify_get_neighbors",
            )
        ):
            if isinstance(results[idx], Exception):
                logger.warning("code_blast_radius backend %s failed: %s", label, results[idx])

    code_dependencies = [f.get("path", "") for f in related_code_files if f.get("path")]

    summary = (
        f"Found {len(related_code_files)} related code files, "
        f"{len(recent_commits)} recent commits, "
        f"{len(dbt_upstream)} dbt upstream / {len(dbt_downstream)} downstream, "
        f"{len(code_graph_neighbors)} graph neighbours for '{entity_fqn}'"
    )

    step_result = {
        "step": 4,
        "name": "code_blast_radius",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": summary,
    }

    return {
        **state,
        "related_code_files": related_code_files,
        "recent_commits": recent_commits,
        "code_dependencies": code_dependencies,
        "dbt_upstream_models": dbt_upstream,
        "dbt_downstream_models": dbt_downstream,
        "code_graph_neighbors": code_graph_neighbors,
        "step_results": [*state.get("step_results", []), step_result],
    }

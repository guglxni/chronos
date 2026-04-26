"""
High-level MCP tool helper functions.

Each function wraps a specific MCP tool call with a clean, typed interface so that
agent nodes never need to know about JSON-RPC details or server routing.

For ``gitnexus_*`` tools the wrapper applies a "local-first" fallback:

* When ``settings.code_intel_prefer_local`` is True (the default), the
  in-process ``chronos.code_intel`` backend handles the call directly —
  no MCP roundtrip, no external binary required.
* When it is False, the wrapper calls the real GitNexus MCP server first
  and falls back to the local backend on any error. This preserves the
  contract for callers that have wired a real GitNexus CLI.

The ``graphify_*`` tools always use the in-process adapter (live
``graph.json`` queries via NetworkX). A future remote ``graphify --mcp``
deployment can be plugged in by extending ``_call_graphify_remote``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chronos.graphiti_client as graphiti_client
from chronos.code_intel import (
    code_search as _local_code_search,
)
from chronos.code_intel import (
    dbt_manifest as _dbt_manifest,
)
from chronos.code_intel import (
    graphify_adapter as _graphify_adapter,
)
from chronos.code_intel import (
    local_git as _local_git,
)
from chronos.config.settings import settings
from chronos.mcp.client import mcp_client
from chronos.mcp.config import MCPServerType

logger = logging.getLogger("chronos.mcp.tools")


def _resolve_repo_path() -> Path:
    """Return the configured repo path as a ``Path``."""
    return Path(settings.code_repo_path).expanduser().resolve()


def _resolve_graph_path() -> Path | None:
    """Return the configured graphify graph path or ``None`` if blank."""
    raw = settings.graphify_graph_path
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    return candidate


def _resolve_manifest_path() -> Path | None:
    """Return the configured dbt manifest path or ``None`` if blank."""
    raw = settings.dbt_manifest_path
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    return candidate


def _normalize_list_result(result: Any, *candidate_keys: str) -> list[dict[str, Any]]:
    """Return a list of dictionaries from heterogeneous MCP response shapes."""
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]

    if isinstance(result, dict):
        for key in candidate_keys:
            value = result.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


# ─── OpenMetadata tools ────────────────────────────────────────────────────────

async def om_get_entity(fqn: str) -> dict[str, Any]:
    """Fetch a single entity by its fully qualified name."""
    return await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "get_entity",
        {"fullyQualifiedName": fqn},
    )


async def om_get_lineage(
    fqn: str,
    direction: str = "both",
    depth: int = 5,
) -> dict[str, Any]:
    """
    Fetch lineage graph for an entity.

    Args:
        fqn: Fully qualified name of the entity.
        direction: 'upstream', 'downstream', or 'both'.
        depth: Number of hops to traverse.
    """
    return await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "get_lineage",
        {"fullyQualifiedName": fqn, "direction": direction, "depth": depth},
    )


async def om_get_test_results(fqn: str, limit: int = 10) -> list[dict[str, Any]]:
    """Fetch recent test case results for an entity."""
    result = await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "get_test_cases",
        {"entityFQN": fqn, "limit": limit},
    )
    return _normalize_list_result(result, "data", "testCases")


async def om_get_version_history(fqn: str) -> list[dict[str, Any]]:
    """Fetch the entity version history (schema/metadata changes over time)."""
    result = await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "get_entity_versions",
        {"fullyQualifiedName": fqn},
    )
    return _normalize_list_result(result, "versions", "data")


async def om_get_audit_logs(
    fqn: str,
    start_ts: int,
    end_ts: int,
) -> list[dict[str, Any]]:
    """
    Fetch audit log events for an entity within a time window.

    Args:
        fqn: Entity fully qualified name.
        start_ts: Start timestamp in milliseconds.
        end_ts: End timestamp in milliseconds.
    """
    result = await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "get_audit_logs",
        {"entityFQN": fqn, "startTs": start_ts, "endTs": end_ts},
    )
    return _normalize_list_result(result, "data", "logs")


async def om_search_entities(
    query: str,
    entity_type: str = "",
) -> list[dict[str, Any]]:
    """Full-text search across OpenMetadata entities."""
    params: dict[str, Any] = {"query": query}
    if entity_type:
        params["entityType"] = entity_type
    result = await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "search_entities",
        params,
    )
    return _normalize_list_result(result, "hits", "data")


# ─── Graphiti tools ────────────────────────────────────────────────────────────

async def graphiti_add_episode(
    group_id: str,
    name: str,
    content: str,
    source_type: str = "text",
) -> dict[str, Any]:
    """Add an episode to a Graphiti group via the in-process graphiti-core client."""
    return await graphiti_client.add_episode(
        group_id=group_id,
        name=name,
        content=content,
        source_type=source_type,
    )


async def graphiti_search_facts(
    query: str,
    group_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for facts (edges) in a Graphiti group using semantic + graph search."""
    return await graphiti_client.search_facts(
        query=query,
        group_id=group_id,
        limit=limit,
    )


async def graphiti_search_nodes(
    query: str,
    group_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for nodes in a Graphiti group."""
    return await graphiti_client.search_nodes(
        query=query,
        group_id=group_id,
        limit=limit,
    )


async def graphiti_get_episodes(
    group_id: str,
    last_n: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve the most recent episodes in a Graphiti group."""
    return await graphiti_client.get_episodes(
        group_id=group_id,
        limit=last_n,
    )


# ─── GitNexus tools (local-first with optional MCP delegation) ─────────────────
#
# The historical GitNexus stub was wired as ``gitnexus serve --stdio`` but the
# upstream project is browser-only and non-commercial. These wrappers default
# to the in-process ``chronos.code_intel`` backend (real subprocess git,
# ripgrep / Python walker, sqlglot / regex) and only delegate to the MCP
# server when ``settings.code_intel_prefer_local`` is False.


async def _try_remote_gitnexus(
    tool: str,
    args: dict[str, Any],
    *list_keys: str,
) -> list[dict[str, Any]] | None:
    """Try the GitNexus MCP server. Return None if it errors or is missing."""
    try:
        result = await mcp_client.call_tool(MCPServerType.GITNEXUS, tool, args)
    except Exception as exc:
        logger.debug("gitnexus.%s remote failed: %s", tool, exc)
        return None
    return _normalize_list_result(result, *list_keys)


async def gitnexus_search_files(query: str) -> list[dict[str, Any]]:
    """Search code files referencing ``query`` (table name, dbt model, column).

    Local-first: scans ``settings.code_repo_path`` with ripgrep when available,
    otherwise a pure-Python walker. Returns ``[{path, line, snippet, language}]``.
    """
    if not settings.code_intel_prefer_local:
        remote = await _try_remote_gitnexus(
            "search_files", {"query": query}, "files", "results"
        )
        if remote is not None:
            return remote
    return await _local_code_search.asearch_entity_references(
        query, _resolve_repo_path()
    )


async def gitnexus_get_file_references(entity_name: str) -> list[dict[str, Any]]:
    """Return all files that reference ``entity_name``.

    Combines the dbt manifest backend (exact lineage when a manifest exists)
    with the local code scanner. Results are de-duplicated by ``path``.
    """
    if not settings.code_intel_prefer_local:
        remote = await _try_remote_gitnexus(
            "get_file_references", {"entity_name": entity_name},
            "references", "files",
        )
        if remote is not None:
            return remote

    manifest_files = _dbt_manifest.get_node_files(
        entity_name, _resolve_manifest_path()
    )
    scan_files = await _local_code_search.asearch_entity_references(
        entity_name, _resolve_repo_path()
    )
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for entry in (*manifest_files, *scan_files):
        path = str(entry.get("path", ""))
        if not path or path in seen:
            continue
        seen.add(path)
        merged.append(entry)
    return merged


async def gitnexus_get_commits(
    entity_name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return recent git commits that touch code referencing ``entity_name``.

    Each commit dict contains: ``sha``, ``message``, ``author``, ``date``,
    ``files_changed``. Local-first via subprocess ``git log -G`` against
    ``settings.code_repo_path``.
    """
    if not settings.code_intel_prefer_local:
        remote = await _try_remote_gitnexus(
            "get_commits", {"entity_name": entity_name, "limit": limit},
            "commits", "results",
        )
        if remote is not None:
            return remote
    return await _local_git.aget_commits_for_entity(
        entity_name, _resolve_repo_path(), limit=limit
    )


# ─── Graphify tools (live in-process graph queries) ───────────────────────────


async def graphify_query(
    question: str,
    depth: int = 2,
    limit: int = 30,
) -> dict[str, Any]:
    """Return a context bundle (nodes + edges) seeded by terms in ``question``.

    Replaces the prior naive markdown grep — runs a real BFS over the live
    graph and returns JSON-serialisable structure ready for an LLM prompt.
    """
    return _graphify_adapter.query_graph(
        question, depth=depth, limit=limit, graph_path=_resolve_graph_path()
    )


async def graphify_get_node(query: str) -> dict[str, Any]:
    """Look up a node by id or label. Returns ``{}`` when missing."""
    return _graphify_adapter.get_node(query, graph_path=_resolve_graph_path())


async def graphify_get_neighbors(
    query: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Return directly-connected nodes with edge metadata."""
    return _graphify_adapter.get_neighbors(
        query, limit=limit, graph_path=_resolve_graph_path()
    )


async def graphify_get_community(
    query: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Return all nodes in the same louvain community as ``query``."""
    return _graphify_adapter.get_community(
        query, limit=limit, graph_path=_resolve_graph_path()
    )


async def graphify_shortest_path(
    source: str,
    target: str,
) -> list[dict[str, Any]]:
    """Find the shortest code-level path between two nodes."""
    return _graphify_adapter.shortest_path(
        source, target, graph_path=_resolve_graph_path()
    )


async def graphify_god_nodes(limit: int = 10) -> list[dict[str, Any]]:
    """Return the most-connected nodes in the graph (architectural risk)."""
    return _graphify_adapter.god_nodes(
        limit=limit, graph_path=_resolve_graph_path()
    )


async def graphify_health() -> dict[str, Any]:
    """Compact graph status for ``/healthz`` endpoints."""
    return _graphify_adapter.graph_stats(graph_path=_resolve_graph_path())


# ─── dbt manifest tools (exact lineage when a dbt project is configured) ──────


async def dbt_get_node(entity_name: str) -> dict[str, Any]:
    """Locate the dbt node for an entity FQN — empty dict when not found."""
    return _dbt_manifest.get_node_by_entity(
        entity_name, _resolve_manifest_path()
    )


async def dbt_get_parents(entity_name: str) -> list[dict[str, Any]]:
    """Return the direct upstream dbt nodes."""
    return _dbt_manifest.get_parents(entity_name, _resolve_manifest_path())


async def dbt_get_children(entity_name: str) -> list[dict[str, Any]]:
    """Return the direct downstream dbt nodes."""
    return _dbt_manifest.get_children(entity_name, _resolve_manifest_path())


async def dbt_walk_upstream(
    entity_name: str,
    depth: int = 3,
) -> list[dict[str, Any]]:
    """BFS upstream through the dbt DAG."""
    return _dbt_manifest.walk_upstream(
        entity_name, depth, _resolve_manifest_path()
    )


async def dbt_walk_downstream(
    entity_name: str,
    depth: int = 3,
) -> list[dict[str, Any]]:
    """BFS downstream through the dbt DAG."""
    return _dbt_manifest.walk_downstream(
        entity_name, depth, _resolve_manifest_path()
    )


async def dbt_health() -> dict[str, Any]:
    """Compact dbt manifest status for ``/healthz`` endpoints."""
    return _dbt_manifest.manifest_stats(_resolve_manifest_path())

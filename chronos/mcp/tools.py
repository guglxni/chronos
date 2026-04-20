"""
High-level MCP tool helper functions.

Each function wraps a specific MCP tool call with a clean, typed interface so that
agent nodes never need to know about JSON-RPC details or server routing.
"""

from __future__ import annotations

import logging
from typing import Any

from chronos.mcp.client import mcp_client
from chronos.mcp.config import MCPServerType

logger = logging.getLogger("chronos.mcp.tools")


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
    # Normalize to list
    if isinstance(result, list):
        return result
    return result.get("data", result.get("testCases", []))


async def om_get_version_history(fqn: str) -> list[dict[str, Any]]:
    """Fetch the entity version history (schema/metadata changes over time)."""
    result = await mcp_client.call_tool(
        MCPServerType.OPENMETADATA,
        "get_entity_versions",
        {"fullyQualifiedName": fqn},
    )
    if isinstance(result, list):
        return result
    return result.get("versions", result.get("data", []))


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
    if isinstance(result, list):
        return result
    return result.get("data", result.get("logs", []))


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
    if isinstance(result, list):
        return result
    return result.get("hits", result.get("data", []))


# ─── Graphiti tools ────────────────────────────────────────────────────────────

async def graphiti_add_episode(
    group_id: str,
    name: str,
    content: str,
    source_type: str = "text",
) -> dict[str, Any]:
    """
    Add an episode to a Graphiti group.

    Episodes are the primary ingest unit — they are split into facts/nodes
    by the Graphiti server.
    """
    return await mcp_client.call_tool(
        MCPServerType.GRAPHITI,
        "add_episode",
        {
            "group_id": group_id,
            "name": name,
            "episode_body": content,
            "source": source_type,
        },
    )


async def graphiti_search_facts(
    query: str,
    group_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for facts (edges) in a Graphiti group using semantic + graph search."""
    result = await mcp_client.call_tool(
        MCPServerType.GRAPHITI,
        "search_facts",
        {"query": query, "group_id": group_id, "max_facts": limit},
    )
    if isinstance(result, list):
        return result
    return result.get("facts", result.get("edges", []))


async def graphiti_search_nodes(
    query: str,
    group_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for nodes in a Graphiti group."""
    result = await mcp_client.call_tool(
        MCPServerType.GRAPHITI,
        "search_nodes",
        {"query": query, "group_id": group_id, "max_nodes": limit},
    )
    if isinstance(result, list):
        return result
    return result.get("nodes", [])


async def graphiti_get_episodes(
    group_id: str,
    last_n: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve the most recent episodes in a Graphiti group."""
    result = await mcp_client.call_tool(
        MCPServerType.GRAPHITI,
        "get_episodes",
        {"group_id": group_id, "last_n": last_n},
    )
    if isinstance(result, list):
        return result
    return result.get("episodes", [])


# ─── GitNexus tools ────────────────────────────────────────────────────────────

async def gitnexus_search_files(query: str) -> list[dict[str, Any]]:
    """
    Search code files referencing a given query string (table name, model name, etc.).
    """
    result = await mcp_client.call_tool(
        MCPServerType.GITNEXUS,
        "search_files",
        {"query": query},
    )
    if isinstance(result, list):
        return result
    return result.get("files", result.get("results", []))


async def gitnexus_get_file_references(entity_name: str) -> list[dict[str, Any]]:
    """
    Return all code files that reference a given entity (table, column, model).
    """
    result = await mcp_client.call_tool(
        MCPServerType.GITNEXUS,
        "get_file_references",
        {"entity_name": entity_name},
    )
    if isinstance(result, list):
        return result
    return result.get("references", result.get("files", []))

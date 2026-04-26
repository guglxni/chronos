"""
Graphify context enrichment.

Builds the ``graphify_context`` string embedded in the IncidentReport. The
prior implementation was a naive markdown grep over ``GRAPH_REPORT.md``;
this version routes through ``chronos.code_intel.graphify_adapter`` so the
caller gets:

* the entity's louvain community (members + cohesion),
* its top neighbours (call / import / semantically_similar_to relations),
* god-node context (most-connected modules in the graph).

The result is rendered as a compact markdown block so the LiteLLM RCA
synthesis prompt can consume it directly. When the graph artifact is
missing, the function returns an empty string — consistent with the
historical contract.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from chronos.code_intel import graphify_adapter

logger = logging.getLogger("chronos.enrichment.graphify_context")

# Display caps — tight by design so the RCA prompt stays under budget.
_MAX_CHARS = 2000
_MAX_NEIGHBORS = 8
_MAX_COMMUNITY_MEMBERS = 10
_MAX_GOD_NODES = 5

# Default location of the graph artifact. Mirrors
# ``settings.graphify_graph_path`` so tests can monkey-patch this constant
# without spinning up the full settings stack.
GRAPH_PATH = Path("graphify-out/graph.json")


def _render_block(payload: dict[str, Any]) -> str:
    """Render the adapter payload into a compact markdown block."""
    if not payload:
        return ""
    lines: list[str] = []

    # Architectural community
    community = payload.get("community") or {}
    if community.get("members"):
        cid = community.get("community_id", "n/a")
        lines.append(f"### Architectural community {cid} ({community.get('size', 0)} members)")
        for member in community["members"][:_MAX_COMMUNITY_MEMBERS]:
            label = str(member.get("label", member.get("id", "")))[:120]
            file_type = member.get("file_type", "")
            lines.append(f"- {label} ({file_type})")
        lines.append("")

    # Top neighbours
    neighbours = payload.get("neighbors") or []
    if neighbours:
        lines.append("### Direct code dependencies")
        for nb in neighbours[:_MAX_NEIGHBORS]:
            node = nb.get("node") or {}
            lines.append(
                f"- {str(node.get('label', node.get('id', '')))[:120]}"
                f" — relation `{nb.get('relation', '')}`"
                f" [{nb.get('confidence', '')}"
                f", {nb.get('confidence_score', 0):.2f}]"
            )
        lines.append("")

    # God nodes
    gods = payload.get("god_nodes") or []
    if gods:
        lines.append("### Top architectural risk surface (god nodes)")
        for g in gods[:_MAX_GOD_NODES]:
            lines.append(
                f"- {str(g.get('label', g.get('id', '')))[:120]}"
                f" (degree={g.get('degree', 0)})"
            )
        lines.append("")

    rendered = "\n".join(lines).strip()
    return rendered[:_MAX_CHARS]


def get_graphify_context(entity_name: str = "") -> str:
    """Return rendered graphify context for the failing entity.

    Args:
        entity_name: Entity FQN. Empty string returns the global god-node
            summary, useful when no specific entity is in scope.

    Returns:
        Markdown-formatted context block, capped at ``_MAX_CHARS``.
        Empty string when the graph is unavailable.
    """
    if not graphify_adapter.is_available(GRAPH_PATH):
        return ""

    payload: dict[str, Any] = {}
    if entity_name:
        # Try the most specific term first, then the trailing segment.
        candidates: list[str] = [entity_name]
        last_segment = entity_name.rsplit(".", 1)[-1]
        if last_segment and last_segment != entity_name:
            candidates.append(last_segment)

        for candidate in candidates:
            community = graphify_adapter.get_community(
                candidate, limit=_MAX_COMMUNITY_MEMBERS, graph_path=GRAPH_PATH
            )
            neighbours = graphify_adapter.get_neighbors(
                candidate, limit=_MAX_NEIGHBORS, graph_path=GRAPH_PATH
            )
            if community or neighbours:
                payload["community"] = community
                payload["neighbors"] = neighbours
                break

    payload["god_nodes"] = graphify_adapter.god_nodes(
        limit=_MAX_GOD_NODES, graph_path=GRAPH_PATH
    )
    return _render_block(payload)

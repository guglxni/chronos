"""
Step 3 — Lineage Walk

Walks upstream lineage from the failing entity to discover whether any upstream
tables/pipelines also have failures, which would indicate UPSTREAM_FAILURE root cause.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from chronos.agent.state import InvestigationState
from chronos.config.settings import settings
from chronos.mcp.tools import om_get_lineage, om_get_test_results


async def lineage_walk_node(state: InvestigationState) -> InvestigationState:
    """Walk upstream lineage and check each node for test failures."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.now(tz=UTC)

    lineage = await om_get_lineage(
        fqn=entity_fqn,
        direction="upstream",
        depth=settings.lineage_upstream_depth,
    )

    upstream_nodes: list[dict[str, Any]] = lineage.get("nodes", [])
    upstream_failures: list[dict[str, Any]] = []
    upstream_changes: list[dict[str, Any]] = []

    # Check up to 10 upstream entities for their own test failures
    for node in upstream_nodes[:10]:
        node_fqn = (
            node.get("fullyQualifiedName")
            or node.get("fqn")
            or node.get("name", "")
        )
        if not node_fqn or node_fqn == entity_fqn:
            continue

        node_results = await om_get_test_results(node_fqn, limit=5)
        for result in node_results:
            tc_status = (
                result.get("testCaseResult", {}).get("testCaseStatus")
                or result.get("testCaseStatus", "")
            )
            if tc_status == "Failed":
                upstream_failures.append(
                    {"entity_fqn": node_fqn, "test": result}
                )
                break  # One failure per node is enough to flag it

    step_result = {
        "step": 3,
        "name": "lineage_walk",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": (
            f"Walked {len(upstream_nodes)} upstream nodes; "
            f"found {len(upstream_failures)} upstream failures"
        ),
    }

    return {
        **state,
        "upstream_lineage": upstream_nodes,
        "upstream_failures": upstream_failures,
        "upstream_changes": upstream_changes,
        "step_results": [*state.get("step_results", []), step_result],
    }

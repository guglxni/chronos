"""
Integration tests for investigation nodes that consume the new code_intel
backends (``code_blast_radius``, ``scope_failure``, ``downstream_impact``).
All MCP tool calls are patched — no live infrastructure required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest


def _base_state(**overrides) -> dict:
    base = {
        "incident_id": "test-001",
        "triggered_at": datetime.now(tz=UTC),
        "entity_fqn": "service.db.analytics.orders",
        "test_name": "column_not_null",
        "failure_message": "1 null found",
        "step_results": [],
        "investigation_start": datetime.now(tz=UTC),
    }
    base.update(overrides)
    return base


# ─── code_blast_radius_node ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_code_blast_radius_merges_all_backends() -> None:
    """All four backends are called and their results land in state."""
    from chronos.agent.nodes.code_blast_radius import code_blast_radius_node

    files_mock = AsyncMock(
        side_effect=[
            [{"path": "etl.py", "line": 1, "snippet": "orders", "language": "python"}],
            # The second candidate produces a duplicate path that should be deduped.
            [
                {"path": "etl.py", "line": 1, "snippet": "orders", "language": "python"},
                {"path": "model.sql", "line": 1, "snippet": "orders", "language": "sql"},
            ],
        ]
    )
    commits_mock = AsyncMock(
        return_value=[
            {
                "sha": "abc",
                "author": "alice",
                "date": "2026-04-26T00:00:00Z",
                "message": "fix orders",
                "files_changed": ["etl.py"],
            },
        ]
    )
    dbt_up_mock = AsyncMock(
        return_value=[
            {
                "node_id": "source.shop.raw.orders",
                "name": "orders",
                "resource_type": "source",
                "depth": 1,
            },
        ]
    )
    dbt_down_mock = AsyncMock(
        return_value=[
            {
                "node_id": "model.shop.dim_orders",
                "name": "dim_orders",
                "resource_type": "model",
                "depth": 1,
            },
        ]
    )
    graph_neighbors_mock = AsyncMock(
        return_value=[
            {
                "node": {"id": "n1", "label": "load_orders()"},
                "relation": "calls",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "source_file": "",
                "source_location": "",
            },
        ]
    )

    with (
        patch("chronos.agent.nodes.code_blast_radius.gitnexus_search_files", new=files_mock),
        patch("chronos.agent.nodes.code_blast_radius.gitnexus_get_commits", new=commits_mock),
        patch("chronos.agent.nodes.code_blast_radius.dbt_walk_upstream", new=dbt_up_mock),
        patch("chronos.agent.nodes.code_blast_radius.dbt_walk_downstream", new=dbt_down_mock),
        patch(
            "chronos.agent.nodes.code_blast_radius.graphify_get_neighbors", new=graph_neighbors_mock
        ),
    ):
        result = await code_blast_radius_node(_base_state())

    assert {f["path"] for f in result["related_code_files"]} == {"etl.py", "model.sql"}
    assert result["recent_commits"][0]["sha"] == "abc"
    assert result["dbt_upstream_models"][0]["name"] == "orders"
    assert result["dbt_downstream_models"][0]["name"] == "dim_orders"
    assert result["code_graph_neighbors"][0]["relation"] == "calls"
    # search_files is called once per candidate (schema.table + table)
    assert files_mock.await_count == 2


@pytest.mark.asyncio
async def test_code_blast_radius_tolerates_backend_failures() -> None:
    """A single backend exception does not break the step."""
    from chronos.agent.nodes.code_blast_radius import code_blast_radius_node

    with (
        patch(
            "chronos.agent.nodes.code_blast_radius.gitnexus_search_files",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.gitnexus_get_commits",
            new=AsyncMock(side_effect=RuntimeError("git not available")),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.dbt_walk_upstream",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.dbt_walk_downstream",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.graphify_get_neighbors",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await code_blast_radius_node(_base_state())

    assert result["recent_commits"] == []
    assert result["related_code_files"] == []
    assert len(result["step_results"]) == 1


@pytest.mark.asyncio
async def test_code_blast_radius_skips_when_entity_blank() -> None:
    """No entity FQN means no backend calls and an empty result."""
    from chronos.agent.nodes.code_blast_radius import code_blast_radius_node

    files_mock = AsyncMock(return_value=[])
    with (
        patch("chronos.agent.nodes.code_blast_radius.gitnexus_search_files", new=files_mock),
        patch(
            "chronos.agent.nodes.code_blast_radius.gitnexus_get_commits",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.dbt_walk_upstream",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.dbt_walk_downstream",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.graphify_get_neighbors",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await code_blast_radius_node(_base_state(entity_fqn=""))

    files_mock.assert_not_awaited()
    assert result["related_code_files"] == []
    assert result["dbt_upstream_models"] == []


# ─── scope_failure_node ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scope_failure_records_architectural_community() -> None:
    """When graphify returns a community, it lands in state."""
    from chronos.agent.nodes.scope_failure import scope_failure_node

    community = {
        "community_id": 5,
        "size": 12,
        "node_id": "orders_node",
        "members": [
            {
                "id": "n1",
                "label": "load_orders()",
                "file_type": "code",
                "source_file": "etl.py",
                "degree": 4,
            }
        ],
    }

    with (
        patch(
            "chronos.agent.nodes.scope_failure.om_get_entity",
            new=AsyncMock(return_value={"id": "e1"}),
        ),
        patch(
            "chronos.agent.nodes.scope_failure.om_get_test_results", new=AsyncMock(return_value=[])
        ),
        patch(
            "chronos.agent.nodes.scope_failure.graphify_get_community",
            new=AsyncMock(return_value=community),
        ),
    ):
        result = await scope_failure_node(_base_state())

    assert result["architectural_community"] == community
    assert "community=5" in result["step_results"][0]["summary"]


@pytest.mark.asyncio
async def test_scope_failure_handles_graphify_miss() -> None:
    """An empty graphify response leaves the state field as ``{}``."""
    from chronos.agent.nodes.scope_failure import scope_failure_node

    with (
        patch(
            "chronos.agent.nodes.scope_failure.om_get_entity",
            new=AsyncMock(return_value={"id": "e1"}),
        ),
        patch(
            "chronos.agent.nodes.scope_failure.om_get_test_results", new=AsyncMock(return_value=[])
        ),
        patch(
            "chronos.agent.nodes.scope_failure.graphify_get_community",
            new=AsyncMock(return_value={}),
        ),
    ):
        result = await scope_failure_node(_base_state())

    assert result["architectural_community"] == {}


# ─── downstream_impact_node ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_downstream_impact_records_blast_paths_for_tier1() -> None:
    """Tier-1 downstream assets get a graphify-based code path."""
    from chronos.agent.nodes.downstream_impact import downstream_impact_node

    lineage = {
        "nodes": [
            {
                "fullyQualifiedName": "db.schema.fact_revenue",
                "displayName": "fact_revenue",
                "tags": [{"tagFQN": "Tier.Tier1"}],
                "owners": [],
            },
        ],
    }
    path_mock = AsyncMock(
        return_value=[
            {
                "id": "n1",
                "label": "scope_failure_node",
                "source_file": "",
                "edge_to_next": {"relation": "calls", "confidence": "EXTRACTED"},
            },
            {"id": "n2", "label": "fact_revenue_loader", "source_file": "", "edge_to_next": {}},
        ]
    )

    with (
        patch(
            "chronos.agent.nodes.downstream_impact.om_get_lineage",
            new=AsyncMock(return_value=lineage),
        ),
        patch("chronos.agent.nodes.downstream_impact.graphify_shortest_path", new=path_mock),
    ):
        result = await downstream_impact_node(_base_state())

    assert result["business_impact_score"] == "critical"
    assert len(result["architectural_blast_radius"]) == 1
    assert result["architectural_blast_radius"][0]["to"] == "db.schema.fact_revenue"
    assert len(result["architectural_blast_radius"][0]["hops"]) == 2
    path_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_downstream_impact_no_blast_paths_for_low_tier() -> None:
    """Low-tier downstream means we don't bother with graphify lookups."""
    from chronos.agent.nodes.downstream_impact import downstream_impact_node

    lineage = {
        "nodes": [
            {
                "fullyQualifiedName": "db.schema.warehouse_stage",
                "displayName": "warehouse_stage",
                "tags": [],
                "owners": [],
            },
        ],
    }
    path_mock = AsyncMock(return_value=[])

    with (
        patch(
            "chronos.agent.nodes.downstream_impact.om_get_lineage",
            new=AsyncMock(return_value=lineage),
        ),
        patch("chronos.agent.nodes.downstream_impact.graphify_shortest_path", new=path_mock),
    ):
        result = await downstream_impact_node(_base_state())

    assert result["business_impact_score"] == "medium"
    assert result["architectural_blast_radius"] == []
    path_mock.assert_not_awaited()

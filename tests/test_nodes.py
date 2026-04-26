"""
Unit tests for CHRONOS LangGraph investigation nodes.

MCP tool calls are patched so these tests run without live infrastructure.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

# ── helpers ────────────────────────────────────────────────────────────────────


def _base_state(**overrides) -> dict:
    base = {
        "incident_id": "test-001",
        "triggered_at": datetime.now(tz=UTC),
        "entity_fqn": "db.schema.table",
        "test_name": "column_not_null",
        "failure_message": "1 null found",
        "step_results": [],
        "investigation_start": datetime.now(tz=UTC),
    }
    base.update(overrides)
    return base


# ── scope_failure_node ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scope_failure_node_populates_failed_test():
    """Failed test is extracted from test results; step_result appended."""
    from chronos.agent.nodes.scope_failure import scope_failure_node

    mock_entity = {"id": "e1", "name": "table"}
    mock_results = [
        {
            "name": "column_not_null",
            "testCaseResult": {"testCaseStatus": "Failed"},
            "entityLink": "<#E::table::db.schema.table::columns::order_id>",
        }
    ]

    with (
        patch(
            "chronos.agent.nodes.scope_failure.om_get_entity",
            new=AsyncMock(return_value=mock_entity),
        ),
        patch(
            "chronos.agent.nodes.scope_failure.om_get_test_results",
            new=AsyncMock(return_value=mock_results),
        ),
    ):
        result = await scope_failure_node(_base_state())

    assert result["failed_test"] == mock_results[0]
    assert result["affected_entity"] == mock_entity
    assert result["affected_columns"] == ["order_id"]
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["step"] == 1
    assert result["step_results"][0]["name"] == "scope_failure"


@pytest.mark.asyncio
async def test_scope_failure_node_no_results():
    """Empty test results produce an empty failed_test without raising."""
    from chronos.agent.nodes.scope_failure import scope_failure_node

    with (
        patch("chronos.agent.nodes.scope_failure.om_get_entity", new=AsyncMock(return_value={})),
        patch(
            "chronos.agent.nodes.scope_failure.om_get_test_results", new=AsyncMock(return_value=[])
        ),
    ):
        result = await scope_failure_node(_base_state())

    assert result["failed_test"] == {}
    assert result["affected_columns"] == []


# ── downstream_impact_node ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_downstream_impact_node_populates_assets():
    from chronos.agent.nodes.downstream_impact import downstream_impact_node

    # om_get_lineage returns {"nodes": [...]} — each node has OM field names
    mock_lineage = {
        "nodes": [
            {
                "fullyQualifiedName": "db.schema.fact_orders",
                "displayName": "Fact Orders",
                "tags": [{"tagFQN": "Tier.Tier1"}],
                "owners": [{"displayName": "alice"}],
            },
            {
                "fullyQualifiedName": "db.schema.report",
                "displayName": "Report",
                "tags": [{"tagFQN": "Tier.Tier2"}],
                "owners": [],
            },
        ]
    }

    with patch(
        "chronos.agent.nodes.downstream_impact.om_get_lineage",
        new=AsyncMock(return_value=mock_lineage),
    ):
        result = await downstream_impact_node(
            _base_state(affected_entity={"id": "e1"}, affected_columns=["order_id"])
        )

    assets = result.get("downstream_assets", [])
    assert len(assets) == 2
    assert assets[0]["fqn"] == "db.schema.fact_orders"
    # Tier1 downstream → critical
    assert result["business_impact_score"] == "critical"
    assert len(result["step_results"]) == 1


@pytest.mark.asyncio
async def test_downstream_impact_node_empty_lineage():
    from chronos.agent.nodes.downstream_impact import downstream_impact_node

    with patch(
        "chronos.agent.nodes.downstream_impact.om_get_lineage",
        new=AsyncMock(return_value={"nodes": []}),
    ):
        result = await downstream_impact_node(_base_state())

    assert result["downstream_assets"] == []
    assert result["business_impact_score"] == "low"


# ── audit_correlation_node ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_correlation_node_filters_suspicious():
    from chronos.agent.nodes.audit_correlation import audit_correlation_node

    # om_get_audit_logs returns a list directly
    mock_audit = [
        {"eventType": "ENTITY_UPDATED", "userName": "admin", "timestamp": 1700000000000},
        {"eventType": "READ", "userName": "reader", "timestamp": 1700000001000},
        {"eventType": "COLUMN_DELETED", "userName": "admin", "timestamp": 1700000002000},
    ]

    with (
        patch(
            "chronos.agent.nodes.audit_correlation.om_get_audit_logs",
            new=AsyncMock(return_value=mock_audit),
        ),
        patch(
            "chronos.agent.nodes.audit_correlation.graphiti_search_facts",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await audit_correlation_node(
            _base_state(
                affected_entity={"id": "e1"},
                affected_columns=["order_id"],
                temporal_changes=[],
                schema_changes=[],
            )
        )

    audit_events = result.get("audit_events", [])
    assert len(audit_events) == 3

    suspicious = result.get("suspicious_actions", [])
    suspicious_types = {a.get("eventType") for a in suspicious}
    assert "COLUMN_DELETED" in suspicious_types
    assert "ENTITY_UPDATED" in suspicious_types
    assert "READ" not in suspicious_types
    assert len(result["step_results"]) == 1


@pytest.mark.asyncio
async def test_audit_correlation_node_no_audit_events():
    from chronos.agent.nodes.audit_correlation import audit_correlation_node

    with (
        patch(
            "chronos.agent.nodes.audit_correlation.om_get_audit_logs",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.audit_correlation.graphiti_search_facts",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await audit_correlation_node(_base_state())

    assert result["audit_events"] == []
    assert result["suspicious_actions"] == []

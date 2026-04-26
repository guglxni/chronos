"""
Unit tests for the 7 CHRONOS LangGraph nodes not covered in test_nodes.py.

All MCP and LLM calls are patched — tests exercise node business logic only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ── shared state factory ───────────────────────────────────────────────────────


def _base_state(**overrides) -> dict:
    base = {
        "incident_id": "test-001",
        "triggered_at": datetime.now(tz=UTC),
        "entity_fqn": "db.schema.orders",
        "test_name": "column_not_null",
        "failure_message": "1 null found",
        "step_results": [],
        "investigation_start": datetime.now(tz=UTC),
    }
    base.update(overrides)
    return base


_MINIMAL_REPORT: dict = {
    "incident_id": "test-001",
    "detected_at": "2026-04-23T10:00:00+00:00",
    "affected_entity_fqn": "db.schema.orders",
    "test_name": "column_not_null",
    "failure_message": "1 null found",
    "probable_root_cause": "Column order_id was renamed upstream.",
    "root_cause_category": "SCHEMA_CHANGE",
    "confidence": 0.85,
    "business_impact": "high",
    "evidence_chain": [],
    "affected_downstream": [],
    "recommended_actions": [],
}


# ── lineage_walk_node ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_lineage_walk_finds_upstream_failures():
    from chronos.agent.nodes.lineage_walk import lineage_walk_node

    mock_lineage = {
        "nodes": [
            {"fullyQualifiedName": "db.schema.order_items"},
            {"fullyQualifiedName": "db.schema.dim_products"},
        ]
    }
    # First upstream node has a failed test; second has none
    mock_results_failed = [{"name": "null_check", "testCaseResult": {"testCaseStatus": "Failed"}}]
    mock_results_ok: list = []

    with (
        patch(
            "chronos.agent.nodes.lineage_walk.om_get_lineage",
            new=AsyncMock(return_value=mock_lineage),
        ),
        patch(
            "chronos.agent.nodes.lineage_walk.om_get_test_results",
            new=AsyncMock(side_effect=[mock_results_failed, mock_results_ok]),
        ),
    ):
        result = await lineage_walk_node(_base_state())

    assert len(result["upstream_lineage"]) == 2
    assert len(result["upstream_failures"]) == 1
    assert result["upstream_failures"][0]["entity_fqn"] == "db.schema.order_items"
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["name"] == "lineage_walk"


@pytest.mark.asyncio
async def test_lineage_walk_empty_upstream():
    from chronos.agent.nodes.lineage_walk import lineage_walk_node

    with (
        patch(
            "chronos.agent.nodes.lineage_walk.om_get_lineage",
            new=AsyncMock(return_value={"nodes": []}),
        ),
        patch(
            "chronos.agent.nodes.lineage_walk.om_get_test_results",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await lineage_walk_node(_base_state())

    assert result["upstream_lineage"] == []
    assert result["upstream_failures"] == []


# ── temporal_diff_node ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_temporal_diff_extracts_schema_changes():
    from chronos.agent.nodes.temporal_diff import temporal_diff_node

    mock_temporal = [{"fact": "Column order_id renamed at 2026-04-22T09:00"}]
    mock_versions = [
        {
            "version": "1.2",
            "changeDescription": {"fieldsAdded": [], "fieldsUpdated": [{"name": "columns"}]},
        },
        {
            "version": "1.1",
            "changeDescription": {"fieldsAdded": [{"name": "description"}]},
        },
    ]

    with (
        patch(
            "chronos.agent.nodes.temporal_diff.graphiti_search_facts",
            new=AsyncMock(return_value=mock_temporal),
        ),
        patch(
            "chronos.agent.nodes.temporal_diff.om_get_version_history",
            new=AsyncMock(return_value=mock_versions),
        ),
    ):
        result = await temporal_diff_node(_base_state())

    assert len(result["temporal_changes"]) == 1
    assert len(result["schema_changes"]) == 1  # only v1.2 mentions "columns"
    assert result["entity_version_diff"] == mock_versions[0]
    assert len(result["step_results"]) == 1


@pytest.mark.asyncio
async def test_temporal_diff_empty_history():
    from chronos.agent.nodes.temporal_diff import temporal_diff_node

    with (
        patch(
            "chronos.agent.nodes.temporal_diff.graphiti_search_facts",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.temporal_diff.om_get_version_history",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await temporal_diff_node(_base_state())

    assert result["temporal_changes"] == []
    assert result["schema_changes"] == []
    assert result["entity_version_diff"] == {}


# ── prior_investigations_node ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_prior_investigations_combines_facts_and_nodes():
    from chronos.agent.nodes.prior_investigations import prior_investigations_node

    mock_facts = [{"fact": "past incident on db.schema.orders"}]
    mock_nodes = [{"name": "orders_incident_node"}]

    with (
        patch(
            "chronos.agent.nodes.prior_investigations.graphiti_search_facts",
            new=AsyncMock(return_value=mock_facts),
        ),
        patch(
            "chronos.agent.nodes.prior_investigations.graphiti_search_nodes",
            new=AsyncMock(return_value=mock_nodes),
        ),
    ):
        result = await prior_investigations_node(_base_state())

    assert len(result["prior_investigations"]) == 2
    assert result["step_results"][0]["name"] == "prior_investigations"


@pytest.mark.asyncio
async def test_prior_investigations_empty():
    from chronos.agent.nodes.prior_investigations import prior_investigations_node

    with (
        patch(
            "chronos.agent.nodes.prior_investigations.graphiti_search_facts",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "chronos.agent.nodes.prior_investigations.graphiti_search_nodes",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await prior_investigations_node(_base_state())

    assert result["prior_investigations"] == []


# ── code_blast_radius_node ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_code_blast_radius_populates_files_and_commits():
    from chronos.agent.nodes.code_blast_radius import code_blast_radius_node

    mock_files = [
        {"path": "dbt/models/orders.sql"},
        {"path": "airflow/dags/orders_dag.py"},
    ]
    mock_commits = [{"sha": "abc123", "message": "Rename order_id column", "author": "alice"}]

    with (
        patch(
            "chronos.agent.nodes.code_blast_radius.gitnexus_search_files",
            new=AsyncMock(return_value=mock_files),
        ),
        patch(
            "chronos.agent.nodes.code_blast_radius.gitnexus_get_commits",
            new=AsyncMock(return_value=mock_commits),
        ),
    ):
        result = await code_blast_radius_node(_base_state())

    assert len(result["related_code_files"]) == 2
    assert len(result["recent_commits"]) == 1
    assert result["recent_commits"][0]["sha"] == "abc123"
    assert "dbt/models/orders.sql" in result["code_dependencies"]
    assert result["step_results"][0]["name"] == "code_blast_radius"


@pytest.mark.asyncio
async def test_code_blast_radius_empty_entity_skips_search():
    from chronos.agent.nodes.code_blast_radius import code_blast_radius_node

    result = await code_blast_radius_node(_base_state(entity_fqn=""))

    assert result["related_code_files"] == []
    assert result["recent_commits"] == []
    assert result["code_dependencies"] == []


# ── persist_trace_node ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persist_trace_node_success():
    from chronos.agent.nodes.persist_trace import persist_trace_node

    state = _base_state(
        incident_report=_MINIMAL_REPORT,
        step_results=[
            {
                "step": 1,
                "name": "scope_failure",
                "started_at": "2026-04-23T10:00:00+00:00",
                "completed_at": "2026-04-23T10:00:01+00:00",
                "summary": "scoped",
            }
        ],
    )
    episode_calls: list = []

    async def _mock_add_episode(**kwargs):
        episode_calls.append(kwargs)
        return {}

    with patch(
        "chronos.agent.nodes.persist_trace.graphiti_add_episode",
        new=AsyncMock(side_effect=_mock_add_episode),
    ):
        result = await persist_trace_node(state)

    assert result["trace_persisted"] is True
    # Main trace + 1 step telemetry = 2 calls
    assert len(episode_calls) == 2
    assert result["step_results"][-1]["name"] == "persist_trace"


@pytest.mark.asyncio
async def test_persist_trace_node_graphiti_error_is_nonfatal():
    """A Graphiti failure must NOT raise — trace persistence is best-effort."""
    from chronos.agent.nodes.persist_trace import persist_trace_node

    state = _base_state(incident_report=_MINIMAL_REPORT)

    with patch(
        "chronos.agent.nodes.persist_trace.graphiti_add_episode",
        new=AsyncMock(side_effect=httpx.HTTPError("connection refused")),
    ):
        result = await persist_trace_node(state)

    # Should complete without raising, trace_persisted still True
    assert result["trace_persisted"] is True


# ── notify_node ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_node_sends_when_report_present():
    from chronos.agent.nodes.notify import notify_node

    state = _base_state(incident_report=_MINIMAL_REPORT)

    with patch(
        "chronos.agent.nodes.notify.send_incident_notification",
        new=AsyncMock(return_value=True),
    ):
        result = await notify_node(state)

    assert result["notification_status"] == "sent"
    assert result["step_results"][-1]["name"] == "notify"


@pytest.mark.asyncio
async def test_notify_node_skipped_when_no_report():
    from chronos.agent.nodes.notify import notify_node

    result = await notify_node(_base_state())

    assert result["notification_status"] == "skipped"


@pytest.mark.asyncio
async def test_notify_node_failed_when_slack_returns_false():
    from chronos.agent.nodes.notify import notify_node

    state = _base_state(incident_report=_MINIMAL_REPORT)

    with patch(
        "chronos.agent.nodes.notify.send_incident_notification",
        new=AsyncMock(return_value=False),
    ):
        result = await notify_node(state)

    assert "failed" in result["notification_status"]


# ── rca_synthesis_node ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rca_synthesis_node_builds_incident_report():
    from chronos.agent.nodes.rca_synthesis import rca_synthesis_node

    mock_llm_output = {
        "root_cause_category": "SCHEMA_CHANGE",
        "confidence": 0.88,
        "probable_root_cause": "Column order_id was renamed upstream.",
        "business_impact": "high",
        "evidence_chain": [
            {"source": "openmetadata", "description": "Schema diff detected", "confidence": 0.9}
        ],
        "recommended_actions": [
            {"description": "Restore column name", "priority": "immediate", "owner": "data-team"}
        ],
    }

    state = _base_state(
        downstream_assets=[
            {
                "fqn": "db.schema.revenue",
                "display_name": "Revenue",
                "tier": "Tier1",
                "owners": ["alice"],
                "domain": "",
            },
        ],
        upstream_lineage=[],
        prior_investigations=[],
        business_impact_score="high",
    )

    with (
        patch(
            "chronos.agent.nodes.rca_synthesis.synthesize_rca",
            new=AsyncMock(return_value=mock_llm_output),
        ),
        patch(
            "chronos.agent.nodes.rca_synthesis.get_graphify_context",
            return_value="",
        ),
    ):
        result = await rca_synthesis_node(state)

    report = result["incident_report"]
    assert report is not None
    assert report["root_cause_category"] == "SCHEMA_CHANGE"
    assert abs(report["confidence"] - 0.88) < 0.01
    assert len(report["evidence_chain"]) == 1
    assert len(report["recommended_actions"]) == 1
    assert len(report["affected_downstream"]) == 1
    assert result["step_results"][-1]["name"] == "rca_synthesis"


@pytest.mark.asyncio
async def test_rca_synthesis_node_graphify_context_included():
    from chronos.agent.nodes.rca_synthesis import rca_synthesis_node

    mock_llm_output = {
        "root_cause_category": "UNKNOWN",
        "confidence": 0.3,
        "probable_root_cause": "Unknown cause",
        "business_impact": "low",
    }

    with (
        patch(
            "chronos.agent.nodes.rca_synthesis.synthesize_rca",
            new=AsyncMock(return_value=mock_llm_output),
        ),
        patch(
            "chronos.agent.nodes.rca_synthesis.get_graphify_context",
            return_value="Entity orders has 3 upstream dependencies.",
        ),
    ):
        result = await rca_synthesis_node(_base_state())

    report = result["incident_report"]
    assert report["graphify_context"] == "Entity orders has 3 upstream dependencies."

"""
Integration tests for CHRONOS FastAPI routes.

Uses Starlette TestClient (sync) so we can test the full request/response
cycle including response_model validation, error handling, and HTTP status
codes — without spawning a real server or touching any external services.
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from chronos.core import incident_store
from chronos.main import app
from chronos.models.incident import IncidentReport, IncidentStatus, RootCauseCategory

client = TestClient(app, raise_server_exceptions=True)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_store():
    incident_store._incidents.clear()
    yield
    incident_store._incidents.clear()


def _make_report(incident_id: str = "inc-001", **kwargs) -> IncidentReport:
    defaults = dict(
        incident_id=incident_id,
        detected_at=datetime.now(tz=UTC),
        affected_entity_fqn="db.schema.orders",
        test_name="column_not_null",
        failure_message="1 null found",
        probable_root_cause="Schema change upstream.",
        root_cause_category=RootCauseCategory.SCHEMA_CHANGE,
        confidence=0.85,
        status=IncidentStatus.OPEN,
    )
    defaults.update(kwargs)
    return IncidentReport(**defaults)


# ── /api/v1/incidents — list ──────────────────────────────────────────────────

def test_list_incidents_empty():
    resp = client.get("/api/v1/incidents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["incidents"] == []


def test_list_incidents_returns_stored():
    incident_store.store(_make_report("inc-A"))
    incident_store.store(_make_report("inc-B"))
    resp = client.get("/api/v1/incidents")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_incidents_filter_by_status():
    incident_store.store(_make_report("inc-open", status=IncidentStatus.OPEN))
    incident_store.store(_make_report("inc-ack", status=IncidentStatus.ACKNOWLEDGED))
    resp = client.get("/api/v1/incidents?status=open")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["incidents"][0]["incident_id"] == "inc-open"


def test_list_incidents_filter_by_root_cause():
    incident_store.store(_make_report("inc-sc", root_cause_category=RootCauseCategory.SCHEMA_CHANGE))
    incident_store.store(_make_report("inc-pf", root_cause_category=RootCauseCategory.PIPELINE_FAILURE))
    resp = client.get("/api/v1/incidents?root_cause=SCHEMA_CHANGE")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_list_incidents_invalid_status_returns_400():
    resp = client.get("/api/v1/incidents?status=not_a_status")
    assert resp.status_code == 400
    assert "Invalid status" in resp.json()["detail"]


def test_list_incidents_invalid_root_cause_returns_400():
    resp = client.get("/api/v1/incidents?root_cause=BANANA")
    assert resp.status_code == 400


def test_list_incidents_pagination():
    for i in range(5):
        incident_store.store(_make_report(f"inc-{i}"))
    resp = client.get("/api/v1/incidents?limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["incidents"]) == 2


# ── /api/v1/incidents/{id} — get single ──────────────────────────────────────

def test_get_incident_found():
    incident_store.store(_make_report("inc-X"))
    resp = client.get("/api/v1/incidents/inc-X")
    assert resp.status_code == 200
    assert resp.json()["incident_id"] == "inc-X"


def test_get_incident_not_found():
    resp = client.get("/api/v1/incidents/ghost-id")
    assert resp.status_code == 404
    assert "ghost-id" in resp.json()["detail"]


# ── /api/v1/incidents/{id}/acknowledge ───────────────────────────────────────

def test_acknowledge_incident():
    incident_store.store(_make_report("inc-ack"))
    resp = client.post("/api/v1/incidents/inc-ack/acknowledge?user=alice")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_by"] == "alice"
    # Verify persisted
    stored = incident_store.get("inc-ack")
    assert stored is not None
    assert stored.status == IncidentStatus.ACKNOWLEDGED


def test_acknowledge_not_found_returns_404():
    resp = client.post("/api/v1/incidents/no-such/acknowledge")
    assert resp.status_code == 404


# ── /api/v1/incidents/{id}/resolve ───────────────────────────────────────────

def test_resolve_incident():
    incident_store.store(_make_report("inc-res"))
    resp = client.post("/api/v1/incidents/inc-res/resolve?user=bob")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolved"
    assert body["resolved_by"] == "bob"
    stored = incident_store.get("inc-res")
    assert stored is not None
    assert stored.status == IncidentStatus.RESOLVED


def test_resolve_not_found_returns_404():
    resp = client.post("/api/v1/incidents/no-such/resolve")
    assert resp.status_code == 404


# ── /api/v1/stats ─────────────────────────────────────────────────────────────

def test_stats_empty_store():
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_incidents"] == 0
    assert body["open_count"] == 0
    assert body["critical_count"] == 0


def test_stats_counts_correctly():
    incident_store.store(_make_report("s1", status=IncidentStatus.OPEN, confidence=0.95))
    incident_store.store(_make_report("s2", status=IncidentStatus.OPEN, confidence=0.5))
    incident_store.store(_make_report("s3", status=IncidentStatus.RESOLVED, confidence=0.7))
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_incidents"] == 3
    assert body["open_count"] == 2
    assert body["avg_confidence"] == pytest.approx((0.95 + 0.5 + 0.7) / 3, abs=0.01)


# ── /api/v1/stats/patterns ────────────────────────────────────────────────────

def test_patterns_returns_list():
    # Patterns only appear for entities with > 1 incident
    incident_store.store(_make_report("p1", root_cause_category=RootCauseCategory.SCHEMA_CHANGE))
    incident_store.store(_make_report("p2", root_cause_category=RootCauseCategory.SCHEMA_CHANGE))
    resp = client.get("/api/v1/stats/patterns")
    assert resp.status_code == 200
    body = resp.json()
    assert "patterns" in body
    assert body["total_recurring_entities"] == 1  # one entity with 2 incidents
    assert body["patterns"][0]["entity_fqn"] == "db.schema.orders"
    assert body["patterns"][0]["incident_count"] == 2


def test_patterns_empty_when_no_recurring():
    # Single incident — no recurring pattern
    incident_store.store(_make_report("p1"))
    resp = client.get("/api/v1/stats/patterns")
    assert resp.status_code == 200
    assert resp.json()["patterns"] == []


# ── /api/v1/health ────────────────────────────────────────────────────────────

def test_health_check():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ("ok", "healthy")


# ── /.well-known/agent-card.json ─────────────────────────────────────────────

def test_agent_card_contains_name():
    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    body = resp.json()
    assert "name" in body
    assert "CHRONOS" in body["name"]


# ── /api/v1/investigate — trigger ────────────────────────────────────────────

def test_trigger_investigation_returns_incident_id():
    with patch(
        "chronos.api.routes.investigations.run_investigation",
        new=AsyncMock(return_value=None),
    ):
        resp = client.post(
            "/api/v1/investigate",
            json={"entity_fqn": "db.schema.orders", "test_name": "null_check"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "incident_id" in body
    assert "stream_url" in body
    assert "stream_token" in body
    assert "db.schema.orders" in body["entity_fqn"]


def test_trigger_investigation_missing_entity_fqn_returns_422():
    # entity_fqn has no default — omitting it must yield 422
    resp = client.post("/api/v1/investigate", json={"test_name": "null_check"})
    assert resp.status_code == 422


def test_stream_requires_valid_token():
    """SSE stream endpoint must reject requests without a valid stream_token (A2)."""
    with patch(
        "chronos.api.routes.investigations.run_investigation",
        new=AsyncMock(return_value=None),
    ):
        trigger_resp = client.post(
            "/api/v1/investigate",
            json={"entity_fqn": "db.schema.orders", "test_name": "null_check"},
        )
    assert trigger_resp.status_code == 200
    incident_id = trigger_resp.json()["incident_id"]

    # No token → 422 (missing required query param)
    no_token_resp = client.get(f"/api/v1/investigations/{incident_id}/stream")
    assert no_token_resp.status_code == 422

    # Wrong token → 401
    wrong_token_resp = client.get(
        f"/api/v1/investigations/{incident_id}/stream",
        params={"stream_token": "wrong-token"},
    )
    assert wrong_token_resp.status_code == 401

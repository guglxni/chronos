"""
Unit tests for chronos.core.incident_store.

Exercises store / get / update_field / list_all / eviction — all in-process,
no I/O.  Each test gets a clean store via the clear_store fixture.
"""

from __future__ import annotations

import pytest

from chronos.core import incident_store
from chronos.models.incident import IncidentReport, IncidentStatus, RootCauseCategory

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_store():
    """Reset the in-memory store before and after each test."""
    incident_store._incidents.clear()
    yield
    incident_store._incidents.clear()


def _make_report(incident_id: str = "inc-001", **kwargs) -> IncidentReport:
    from datetime import UTC, datetime

    defaults = dict(
        incident_id=incident_id,
        detected_at=datetime.now(tz=UTC),
        affected_entity_fqn="db.schema.orders",
        test_name="column_not_null",
        failure_message="1 null found",
        probable_root_cause="Column order_id renamed upstream.",
        root_cause_category=RootCauseCategory.SCHEMA_CHANGE,
        confidence=0.85,
        status=IncidentStatus.OPEN,
    )
    defaults.update(kwargs)
    return IncidentReport(**defaults)


# ── store + get roundtrip ─────────────────────────────────────────────────────


def test_store_and_get_roundtrip():
    report = _make_report("inc-A")
    incident_store.store(report)
    retrieved = incident_store.get("inc-A")
    assert retrieved is not None
    assert retrieved.incident_id == "inc-A"


def test_get_returns_none_for_missing():
    assert incident_store.get("no-such-id") is None


def test_get_or_raise_raises_key_error():
    with pytest.raises(KeyError, match="no-such-id"):
        incident_store.get_or_raise("no-such-id")


def test_store_accepts_dict():
    from datetime import UTC, datetime

    raw = {
        "incident_id": "inc-dict",
        "detected_at": datetime.now(tz=UTC).isoformat(),
        "affected_entity_fqn": "db.s.t",
        "test_name": "null_check",
        "failure_message": "fail",
        "probable_root_cause": "unknown",
        "root_cause_category": "UNKNOWN",
        "confidence": 0.5,
    }
    incident_store.store(raw)
    assert incident_store.get("inc-dict") is not None


def test_store_invalid_dict_raises():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        incident_store.store({"incident_id": "x"})  # missing required fields


# ── list_all ──────────────────────────────────────────────────────────────────


def test_list_all_empty():
    assert incident_store.list_all() == []


def test_list_all_returns_all_incidents():
    incident_store.store(_make_report("inc-1"))
    incident_store.store(_make_report("inc-2"))
    incident_store.store(_make_report("inc-3"))
    result = incident_store.list_all()
    assert len(result) == 3
    ids = {r.incident_id for r in result}
    assert ids == {"inc-1", "inc-2", "inc-3"}


# ── update_field ──────────────────────────────────────────────────────────────


def test_update_field_changes_status():
    incident_store.store(_make_report("inc-upd"))
    updated = incident_store.update_field("inc-upd", status=IncidentStatus.ACKNOWLEDGED)
    assert updated.status == IncidentStatus.ACKNOWLEDGED
    # Verify persisted
    stored = incident_store.get("inc-upd")
    assert stored is not None
    assert stored.status == IncidentStatus.ACKNOWLEDGED


def test_update_field_missing_raises_key_error():
    with pytest.raises(KeyError):
        incident_store.update_field("ghost-id", status=IncidentStatus.RESOLVED)


def test_update_field_preserves_other_fields():
    r = _make_report("inc-pres")
    incident_store.store(r)
    updated = incident_store.update_field("inc-pres", status=IncidentStatus.RESOLVED)
    assert updated.affected_entity_fqn == "db.schema.orders"
    assert updated.confidence == 0.85


# ── eviction at cap ───────────────────────────────────────────────────────────


def test_eviction_removes_oldest_when_over_cap():
    cap = incident_store._MAX_STORE_SIZE
    for i in range(cap + 1):
        incident_store.store(_make_report(f"inc-{i:04d}"))

    assert len(incident_store._incidents) == cap
    # The very first entry should have been evicted
    assert incident_store.get("inc-0000") is None
    # The most recently added should still be present
    assert incident_store.get(f"inc-{cap:04d}") is not None

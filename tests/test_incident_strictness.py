from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronos.core import incident_store
from chronos.models.incident import IncidentReport


@pytest.fixture(autouse=True)
def _clear_store():
    incident_store._incidents.clear()
    yield
    incident_store._incidents.clear()


def _valid_report_dict() -> dict:
    return {
        "incident_id": "incident-dict-1",
        "affected_entity_fqn": "sample_db.default.orders",
        "test_name": "column_values_to_be_not_null",
        "probable_root_cause": "Schema changed",
        "root_cause_category": "SCHEMA_CHANGE",
        "confidence": 0.91,
    }


def test_incident_report_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        IncidentReport.model_validate({"incident_id": "x"})


def test_store_accepts_dict_and_model():
    incident_store.store(_valid_report_dict())

    report_model = IncidentReport(
        incident_id="incident-model-1",
        affected_entity_fqn="sample_db.default.customers",
        test_name="duplicate_count",
        probable_root_cause="Upstream data drift",
        root_cause_category="DATA_DRIFT",
        confidence=0.88,
    )
    incident_store.store(report_model)

    reports = incident_store.list_all()
    assert len(reports) == 2
    assert all(isinstance(report, IncidentReport) for report in reports)

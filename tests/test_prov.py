"""
Unit tests for the W3C PROV-O provenance generator.

These tests verify that generate_provenance produces a valid ProvDocument with
the expected agents, activities, entities, and relationships — without requiring
the prov library to be installed in a live stack.
"""

from __future__ import annotations

import pytest

try:
    from prov.model import ProvDocument
except ImportError:
    pytest.skip("prov library not installed", allow_module_level=True)

from chronos.compliance.prov_generator import generate_provenance, safe_generate_provenance


def _minimal_report(**overrides) -> dict:
    base = {
        "incident_id": "abc-123",
        "affected_entity_fqn": "db.schema.orders",
        "test_name": "not_null_order_id",
        "detected_at": "2026-04-22T10:00:00+00:00",
        "investigation_completed_at": "2026-04-22T10:02:00+00:00",
        "root_cause_category": "SCHEMA_CHANGE",
        "confidence": 0.85,
        "business_impact": "high",
        "probable_root_cause": "Column order_id was renamed upstream.",
        "evidence_chain": [],
        "affected_downstream": [],
    }
    base.update(overrides)
    return base


def test_returns_prov_document():
    doc = generate_provenance(_minimal_report())
    assert isinstance(doc, ProvDocument)


def test_document_has_agent():
    doc = generate_provenance(_minimal_report())
    serialised = str(doc.serialize(format="json"))
    assert "agent_chronos" in serialised


def test_document_serialises_to_jsonld():
    doc = generate_provenance(_minimal_report())
    data = doc.serialize(format="json")
    assert len(data) > 10


def test_document_contains_incident_id():
    doc = generate_provenance(_minimal_report())
    serialised = str(doc.serialize(format="json"))
    assert "abc-123" in serialised


def test_document_version_from_settings():
    """PROV-O agent_version must come from settings.version, not hardcoded."""
    from chronos.config.settings import settings

    doc = generate_provenance(_minimal_report())
    serialised = str(doc.serialize(format="json"))
    assert settings.version in serialised


def test_evidence_chain_entities():
    report = _minimal_report(
        evidence_chain=[
            {"source": "openmetadata", "description": "Schema diff detected", "confidence": 0.9},
            {"source": "graphiti", "description": "Related past incident found", "confidence": 0.7},
        ]
    )
    doc = generate_provenance(report)
    serialised = str(doc.serialize(format="json"))
    assert "Schema diff detected" in serialised or "evidence_" in serialised


def test_downstream_entities():
    report = _minimal_report(
        affected_downstream=[
            {"fqn": "db.schema.fact_sales", "tier": "Tier1"},
        ]
    )
    doc = generate_provenance(report)
    serialised = str(doc.serialize(format="json"))
    assert "downstream_" in serialised


def test_handles_missing_timestamps_gracefully():
    report = _minimal_report(detected_at=None, investigation_completed_at=None)
    doc = generate_provenance(report)
    assert isinstance(doc, ProvDocument)


def test_entity_fqn_with_special_chars():
    """Dots and colons in FQN must not break PROV identifiers."""
    report = _minimal_report(affected_entity_fqn="catalog:db.schema.orders")
    doc = generate_provenance(report)
    assert isinstance(doc, ProvDocument)
    doc.serialize(format="json")  # Must not raise


# ── safe_generate_provenance fallback (B4) ────────────────────────────────────


def test_safe_generate_provenance_succeeds_normally():
    doc = safe_generate_provenance(_minimal_report())
    assert isinstance(doc, ProvDocument)


def test_safe_generate_provenance_returns_stub_on_failure():
    """When generate_provenance raises, safe_generate_provenance returns a stub."""
    import unittest.mock as mock

    with mock.patch(
        "chronos.compliance.prov_generator.generate_provenance",
        side_effect=RuntimeError("simulated prov failure"),
    ):
        doc = safe_generate_provenance(_minimal_report())

    assert isinstance(doc, ProvDocument)
    serialised = str(doc.serialize(format="json"))
    assert "abc-123" in serialised  # incident_id in stub


def test_safe_generate_provenance_stub_is_valid_prov():
    """The fallback stub must serialise to all three formats without raising."""
    import unittest.mock as mock

    with mock.patch(
        "chronos.compliance.prov_generator.generate_provenance",
        side_effect=ValueError("bad data"),
    ):
        doc = safe_generate_provenance(_minimal_report())

    doc.serialize(format="json")
    doc.serialize(format="rdf", rdf_format="turtle")
    doc.serialize(format="provn")

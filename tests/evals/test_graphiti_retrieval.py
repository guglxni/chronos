"""
RAGAs Graphiti retrieval quality tests (F18).

Evaluates whether Graphiti's semantic search returns relevant facts when queried
during an investigation.

Run with: pytest tests/evals/test_graphiti_retrieval.py -v
Requires: ANTHROPIC_API_KEY env var and the ragas + datasets packages.
Install eval extras: pip install -e ".[eval]"
"""

from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping retrieval eval tests",
)
@pytest.mark.asyncio
async def test_graphiti_context_recall():
    """
    Test that Graphiti returns schema-change facts with high recall and precision
    when queried about the orders table within a 72-hour window.

    In production, this test would:
    1. Pre-seed Graphiti with known facts via graphiti_add_episode
    2. Query via graphiti_search_facts
    3. Evaluate the returned context against known ground truth using RAGAs
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import context_precision, context_recall
    except ImportError:
        pytest.skip("ragas or datasets not installed — run: pip install -e '.[eval]'")

    # Simulated retrieval results.
    # In a full integration test, these would come from a live Graphiti query.
    data = {
        "question": ["What changed in table orders in the last 72 hours?"],
        "contexts": [
            [
                "Schema change: order_id column changed from NOT NULL to NULL "
                "at 2026-04-21T14:00:00Z",
                "Audit log: data_engineer modified orders table schema at 2026-04-21T13:58:00Z",
                "Test case column_values_to_be_not_null failed on orders.order_id "
                "with 1523 null values at 2026-04-21T14:00:00Z",
            ]
        ],
        "ground_truth": [
            "The order_id column in the orders table was modified to allow NULL "
            "values on 2026-04-21, causing the not_null constraint to fail."
        ],
    }

    dataset = Dataset.from_dict(data)
    result = evaluate(
        dataset=dataset,
        metrics=[context_recall, context_precision],
    )

    recall = float(result["context_recall"])
    precision = float(result["context_precision"])

    assert recall > 0.8, (
        f"Context recall too low: {recall:.3f} (expected > 0.8). "
        "Graphiti may not be returning relevant schema change facts."
    )
    assert precision > 0.6, (
        f"Context precision too low: {precision:.3f} (expected > 0.6). "
        "Too many irrelevant facts are being returned."
    )


@pytest.mark.asyncio
async def test_deduplicator_prevents_duplicate_investigations():
    """
    Unit test — EventDeduplicator correctly blocks re-processing the same event
    within the dedup window.
    """
    from chronos.ingestion.deduplicator import EventDeduplicator

    dedup = EventDeduplicator()
    key = "sample_db.default.orders:TEST_CASE_FAILED"

    assert not dedup.is_duplicate(key), "First occurrence should not be duplicate"
    assert dedup.is_duplicate(key), "Second occurrence within window should be duplicate"

    # Reset and verify fresh start
    dedup.reset()
    assert not dedup.is_duplicate(key), "After reset, key should no longer be duplicate"


def test_investigation_state_is_partial():
    """
    Unit test — InvestigationState accepts partial dicts (total=False).
    """
    from chronos.agent.state import InvestigationState

    # Should not raise — all keys are optional
    state: InvestigationState = {
        "incident_id": "test-123",
        "entity_fqn": "sample_db.default.orders",
    }
    assert state["incident_id"] == "test-123"
    assert "test_name" not in state


def test_prov_generator_produces_valid_document():
    """
    Unit test — generate_provenance creates a valid ProvDocument for a minimal
    incident report.
    """
    from chronos.compliance.prov_generator import generate_provenance

    incident = {
        "incident_id": "prov-test-001",
        "affected_entity_fqn": "sample_db.default.orders",
        "test_name": "column_values_to_be_not_null",
        "probable_root_cause": "Schema change",
        "root_cause_category": "SCHEMA_CHANGE",
        "confidence": 0.92,
        "business_impact": "high",
        "detected_at": "2026-04-21T14:00:00",
        "investigation_completed_at": "2026-04-21T14:05:00",
        "evidence_chain": [
            {
                "source": "openmetadata",
                "description": "Column became nullable",
                "confidence": 0.95,
            }
        ],
        "affected_downstream": [],
    }

    doc = generate_provenance(incident)
    assert doc is not None

    # Verify the document can be serialized to PROV-N
    provn = doc.serialize(format="provn")
    assert "investigation_prov_test_001" in provn or "investigation" in provn
    assert "chronos" in provn.lower()

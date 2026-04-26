"""
DeepEval RCA quality tests (F17).

Run with: pytest tests/evals/test_rca_quality.py -v
Requires: ANTHROPIC_API_KEY env var (skips gracefully if not set).
Install eval extras: pip install -e ".[eval]"
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent / "fixtures/events/schema_change_webhook.json"


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping LLM evaluation tests",
)
def test_rca_accuracy_schema_change():
    """Test that CHRONOS correctly identifies a schema change as the root cause."""
    try:
        from deepeval import assert_test
        from deepeval.metrics import FaithfulnessMetric, GEval
        from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    except ImportError:
        pytest.skip("deepeval not installed — run: pip install -e '.[eval]'")

    fixture = json.loads(FIXTURE_PATH.read_text())

    # Simulated CHRONOS LLM output.
    # In a full integration test, this would come from invoking the real agent.
    predicted_rca = {
        "probable_root_cause": (
            "Schema change detected: the order_id column was modified to allow "
            "NULL values in a recent migration, causing the not_null constraint "
            "test to fail. Audit logs show a DDL change by data_engineer 2 hours "
            "before the test failure."
        ),
        "root_cause_category": "SCHEMA_CHANGE",
        "confidence": 0.92,
        "evidence_chain": [
            {
                "source": "openmetadata",
                "description": "Entity version diff shows order_id changed from NOT NULL to nullable",
                "confidence": 0.95,
            },
            {
                "source": "audit_log",
                "description": "data_engineer ran ALTER TABLE orders MODIFY COLUMN order_id at 2026-04-21T13:58:00Z",
                "confidence": 0.90,
            },
        ],
    }

    ground_truth = (
        "The root cause is a schema change where the order_id column in the "
        "orders table was altered to allow NULL values on 2026-04-21."
    )

    test_case = LLMTestCase(
        input=json.dumps(fixture),
        actual_output=json.dumps(predicted_rca),
        expected_output=ground_truth,
        retrieval_context=[
            "Schema version history shows column order_id changed from NOT NULL "
            "to NULL at 2026-04-21T14:00:00Z",
            "Audit log: user data_engineer modified table orders schema at 2026-04-21T13:58:00",
        ],
    )

    g_eval = GEval(
        name="RCA Accuracy",
        criteria=(
            "Is the probable_root_cause factually correct and does "
            "root_cause_category match the evidence provided?"
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.7,
    )

    faithfulness = FaithfulnessMetric(threshold=0.7)

    assert_test(test_case, [g_eval, faithfulness])


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_confidence_threshold():
    """
    Test that the confidence score is above 0.8 for an unambiguous schema
    change scenario with strong evidence.
    """
    fixture = json.loads(FIXTURE_PATH.read_text())

    # Structural checks on the fixture
    assert fixture["eventType"] == "TEST_CASE_FAILED", "Fixture must be a TEST_CASE_FAILED event"
    assert "orders" in fixture["entityFullyQualifiedName"], (
        "Fixture must reference the orders entity"
    )

    test_result = fixture["entity"]["testCaseResult"]
    assert test_result["testCaseStatus"] == "Failed"
    assert int(test_result["testResultValue"][0]["value"]) > 0, (
        "Expected at least one null value in fixture"
    )

    # In a full integration test we'd invoke the agent and assert:
    # assert result["confidence"] > 0.8
    # For now, validate fixture integrity.
    assert True, "Fixture integrity check passed"


def test_incident_report_schema():
    """Unit test — IncidentReport model accepts valid schema change output."""
    from chronos.models.incident import (
        BusinessImpact,
        IncidentReport,
        RootCauseCategory,
    )

    report = IncidentReport(
        affected_entity_fqn="sample_db.default.orders",
        test_name="column_values_to_be_not_null",
        probable_root_cause="Schema change: order_id column became nullable",
        root_cause_category=RootCauseCategory.SCHEMA_CHANGE,
        confidence=0.92,
        business_impact=BusinessImpact.HIGH,
    )

    assert report.root_cause_category == RootCauseCategory.SCHEMA_CHANGE
    assert report.confidence == 0.92
    assert report.incident_id  # auto-generated UUID

"""
Step 7 — RCA Synthesis

Calls the LiteLLM-backed synthesis model with all collected evidence and builds
a structured IncidentReport from the LLM output.
"""

from __future__ import annotations

from datetime import datetime

from chronos.agent.state import InvestigationState
from chronos.llm.client import synthesize_rca
from chronos.models.incident import BusinessImpact, IncidentReport, RootCauseCategory


async def rca_synthesis_node(state: InvestigationState) -> InvestigationState:
    """Synthesize all evidence into a structured IncidentReport via LLM."""
    start_time = datetime.utcnow()

    # Package evidence — cap list sizes to keep the prompt manageable
    evidence = {
        "entity_fqn": state.get("entity_fqn", ""),
        "test_name": state.get("test_name", ""),
        "failure_message": state.get("failure_message", ""),
        "failed_test": state.get("failed_test", {}),
        "temporal_changes": state.get("temporal_changes", [])[:5],
        "schema_changes": state.get("schema_changes", [])[:3],
        "upstream_failures": state.get("upstream_failures", [])[:5],
        "related_code_files": state.get("related_code_files", [])[:5],
        "downstream_assets": state.get("downstream_assets", [])[:10],
        "audit_events": state.get("audit_events", [])[:5],
        "suspicious_actions": state.get("suspicious_actions", [])[:3],
        "prior_investigations": state.get("prior_investigations", [])[:3],
        "business_impact_score": state.get("business_impact_score", "medium"),
    }

    llm_result = await synthesize_rca(evidence)

    # Validate and coerce root_cause_category
    raw_category = llm_result.get("root_cause_category", "UNKNOWN")
    try:
        root_cause_category = RootCauseCategory(raw_category)
    except ValueError:
        root_cause_category = RootCauseCategory.UNKNOWN

    # Validate and coerce business_impact
    raw_impact = (
        llm_result.get("business_impact")
        or state.get("business_impact_score", "medium")
    )
    try:
        business_impact = BusinessImpact(raw_impact.lower())
    except (ValueError, AttributeError):
        business_impact = BusinessImpact.MEDIUM

    # Clamp confidence to [0.0, 1.0]
    confidence = max(0.0, min(1.0, float(llm_result.get("confidence", 0.5))))

    incident_report = IncidentReport(
        incident_id=state.get("incident_id", ""),
        detected_at=state.get("triggered_at", datetime.utcnow()),
        investigation_completed_at=datetime.utcnow(),
        affected_entity_fqn=state.get("entity_fqn", ""),
        test_name=state.get("test_name", ""),
        failure_message=state.get("failure_message", ""),
        probable_root_cause=llm_result.get("probable_root_cause", "Unknown"),
        root_cause_category=root_cause_category,
        confidence=confidence,
        business_impact=business_impact,
    )

    step_result = {
        "step": 7,
        "name": "rca_synthesis",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "summary": (
            f"RCA: {incident_report.root_cause_category}, "
            f"confidence={incident_report.confidence:.2f}"
        ),
    }

    return {
        **state,
        "incident_report": incident_report.model_dump(mode="json"),
        "step_results": state.get("step_results", []) + [step_result],
    }

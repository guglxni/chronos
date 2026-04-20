"""
Step 9 — Persist Trace

Persists the completed investigation and per-step telemetry to Graphiti so that
future investigations on the same entity can benefit from historical context.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import graphiti_add_episode

logger = logging.getLogger("chronos.agent.persist_trace")

TRACE_GROUP = "chronos-investigation-traces"
TELEMETRY_GROUP = "chronos-step-telemetry"


async def persist_trace_node(state: InvestigationState) -> InvestigationState:
    """Persist full investigation trace and per-step telemetry to Graphiti."""
    start_time = datetime.utcnow()
    incident_report = state.get("incident_report") or {}
    incident_id = state.get("incident_id", "")

    # ── Main investigation trace ───────────────────────────────────────────────
    trace_content = json.dumps(
        {
            "incident_id": incident_id,
            "entity_fqn": state.get("entity_fqn"),
            "test_name": state.get("test_name"),
            "root_cause_category": incident_report.get("root_cause_category"),
            "confidence": incident_report.get("confidence"),
            "probable_root_cause": incident_report.get("probable_root_cause"),
            "business_impact": incident_report.get("business_impact"),
            "detected_at": str(incident_report.get("detected_at", "")),
            "investigation_completed_at": str(
                incident_report.get("investigation_completed_at", "")
            ),
        },
        default=str,
    )

    try:
        await graphiti_add_episode(
            group_id=TRACE_GROUP,
            name=f"investigation:{incident_id}",
            content=trace_content,
            source_type="json",
        )
        logger.info(f"Persisted investigation trace for incident {incident_id}")
    except Exception as exc:
        logger.error(f"Failed to persist trace for incident {incident_id}: {exc}")

    # ── Per-step telemetry ─────────────────────────────────────────────────────
    for step_result in state.get("step_results", []):
        try:
            telemetry_content = json.dumps(step_result, default=str)
            step_num = step_result.get("step", "?")
            await graphiti_add_episode(
                group_id=TELEMETRY_GROUP,
                name=f"step:{incident_id}:{step_num}",
                content=telemetry_content,
                source_type="json",
            )
        except Exception as exc:
            logger.warning(
                f"Failed to persist step telemetry "
                f"step={step_result.get('step')} for {incident_id}: {exc}"
            )

    final_step_result = {
        "step": 9,
        "name": "persist_trace",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "summary": f"Persisted investigation trace + telemetry for incident {incident_id}",
    }

    return {
        **state,
        "trace_persisted": True,
        "step_results": state.get("step_results", []) + [final_step_result],
    }

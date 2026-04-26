"""
Step 9 — Persist Trace

Persists the completed investigation and per-step telemetry to Graphiti so that
future investigations on the same entity can benefit from historical context.

Fix #4: broad ``except Exception`` replaced with httpx.HTTPError and
        json.JSONDecodeError / ValueError — each catchable error type that
        ``graphiti_add_episode`` can reasonably raise is listed explicitly.
        A programming bug (AttributeError, TypeError) will correctly bubble up
        rather than being swallowed.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

import httpx

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import graphiti_add_episode

logger = logging.getLogger("chronos.agent.persist_trace")

TRACE_GROUP = "chronos-investigation-traces"
TELEMETRY_GROUP = "chronos-step-telemetry"

# Exception types that graphiti_add_episode may raise legitimately.
# Kept in one place so they're easy to update when the MCP client evolves.
_GRAPHITI_ERRORS = (httpx.HTTPError, json.JSONDecodeError, ValueError, OSError)


async def persist_trace_node(state: InvestigationState) -> InvestigationState:
    """Persist full investigation trace and per-step telemetry to Graphiti."""
    start_time = datetime.now(tz=UTC)
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
        logger.info("Persisted investigation trace for incident %s", incident_id)
    except _GRAPHITI_ERRORS as exc:
        logger.error(
            "Failed to persist trace for incident %s (%s): %s",
            incident_id,
            type(exc).__name__,
            exc,
        )

    # ── Per-step telemetry ─────────────────────────────────────────────────────
    for step_result in state.get("step_results", []):
        step_num = step_result.get("step", "?")
        try:
            telemetry_content = json.dumps(step_result, default=str)
            await graphiti_add_episode(
                group_id=TELEMETRY_GROUP,
                name=f"step:{incident_id}:{step_num}",
                content=telemetry_content,
                source_type="json",
            )
        except _GRAPHITI_ERRORS as exc:
            logger.warning(
                "Failed to persist step telemetry step=%s for %s (%s): %s",
                step_num,
                incident_id,
                type(exc).__name__,
                exc,
            )

    final_step_result = {
        "step": 9,
        "name": "persist_trace",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": f"Persisted investigation trace + telemetry for incident {incident_id}",
    }

    return {
        **state,
        "trace_persisted": True,
        "step_results": [*state.get("step_results", []), final_step_result],
    }

"""
Step 8 — Notify

Sends a Slack Block Kit notification with the investigation results.
Failure is non-fatal — a notification error does not abort the pipeline.

Fix #3: passes a typed IncidentReport to send_incident_notification instead
        of a raw dict — all field access inside slack.py is attribute-based.
Fix #4: broad ``except Exception`` in the notification call is unnecessary now
        that slack.py handles its own errors; the only outer guard is for
        IncidentReport.model_validate failures (structural, not network).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from pydantic import ValidationError

from chronos.agent.state import InvestigationState
from chronos.models.incident import IncidentReport
from chronos.notifications.slack import send_incident_notification

logger = logging.getLogger("chronos.agent.notify")


async def notify_node(state: InvestigationState) -> InvestigationState:
    """Send Slack notification for the completed investigation."""
    start_time = datetime.now(tz=UTC)
    incident_report_raw = state.get("incident_report") or {}

    notification_status = "skipped"

    if incident_report_raw:
        try:
            # Validate and convert the raw dict to a typed model so slack.py
            # can use attribute access instead of dict.get() on required fields.
            incident_report = IncidentReport.model_validate(incident_report_raw)
            success = await send_incident_notification(incident_report)
            notification_status = "sent" if success else "failed: webhook returned non-200"
            logger.info("Slack notification status: %s", notification_status)
        except ValidationError as exc:
            # Structural mismatch between the agent output and IncidentReport schema.
            # Log details and skip — the incident_report field in state is malformed.
            notification_status = f"failed: invalid incident_report schema ({exc})"
            logger.error("Cannot send Slack notification — incident_report schema invalid: %s", exc)
    else:
        logger.debug("No incident report in state — skipping notification")

    step_result = {
        "step": 8,
        "name": "notify",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": f"Notification status: {notification_status}",
    }

    return {
        **state,
        "notification_status": notification_status,
        "step_results": [*state.get("step_results", []), step_result],
    }

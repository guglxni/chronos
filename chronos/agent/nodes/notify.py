"""
Step 8 — Notify

Sends a Slack Block Kit notification with the investigation results.
Failure is non-fatal — a notification error does not abort the pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime

from chronos.agent.state import InvestigationState
from chronos.notifications.slack import send_incident_notification

logger = logging.getLogger("chronos.agent.notify")


async def notify_node(state: InvestigationState) -> InvestigationState:
    """Send Slack notification for the completed investigation."""
    start_time = datetime.utcnow()
    incident_report = state.get("incident_report") or {}

    notification_status = "skipped"

    if incident_report:
        try:
            success = await send_incident_notification(incident_report)
            notification_status = "sent" if success else "failed: webhook returned non-200"
            logger.info(f"Slack notification status: {notification_status}")
        except Exception as exc:
            notification_status = f"failed: {exc}"
            logger.warning(
                f"Slack notification failed for incident "
                f"{incident_report.get('incident_id', '?')}: {exc}"
            )
    else:
        logger.debug("No incident report in state — skipping notification")

    step_result = {
        "step": 8,
        "name": "notify",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "summary": f"Notification status: {notification_status}",
    }

    return {
        **state,
        "notification_status": notification_status,
        "step_results": state.get("step_results", []) + [step_result],
    }

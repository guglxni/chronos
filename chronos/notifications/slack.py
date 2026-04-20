"""
Slack Block Kit notification sender for CHRONOS incident reports.

Sends a rich, interactive Block Kit message to the configured webhook URL.
"""

from __future__ import annotations

import logging

import httpx

from chronos.config.settings import settings

logger = logging.getLogger("chronos.notifications.slack")

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

ROOT_CAUSE_EMOJI = {
    "SCHEMA_CHANGE": "🏗️",
    "CODE_CHANGE": "💻",
    "DATA_DRIFT": "📊",
    "PIPELINE_FAILURE": "⚙️",
    "PERMISSION_CHANGE": "🔐",
    "UPSTREAM_FAILURE": "🔗",
    "CONFIGURATION_CHANGE": "⚙️",
    "UNKNOWN": "❓",
}


async def send_incident_notification(incident_report: dict) -> bool:
    """
    Send a rich Block Kit Slack notification for a completed investigation.

    Returns True if the webhook returned HTTP 200, False otherwise.
    If no webhook URL is configured, returns False immediately (no error raised).
    """
    if not settings.slack_webhook_url:
        logger.debug("SLACK_WEBHOOK_URL not configured — notification skipped")
        return False

    severity = incident_report.get("business_impact", "medium")
    root_cause = incident_report.get("root_cause_category", "UNKNOWN")
    confidence = float(incident_report.get("confidence", 0.0))
    entity = incident_report.get("affected_entity_fqn", "unknown")
    incident_id = incident_report.get("incident_id", "")
    probable_cause = incident_report.get("probable_root_cause", "No analysis available.")
    test_name = incident_report.get("test_name", "")

    # Build owner mention string from affected downstream assets
    downstream = incident_report.get("affected_downstream", [])
    owner_names: list[str] = []
    for asset in downstream[:3]:
        for owner in asset.get("owners", []):
            if owner and f"@{owner}" not in owner_names:
                owner_names.append(f"@{owner}")
    owners_text = " ".join(owner_names) if owner_names else "No owners tagged"

    severity_icon = SEVERITY_EMOJI.get(severity, "🔴")
    rc_icon = ROOT_CAUSE_EMOJI.get(root_cause, "❓")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_icon} Data Quality Incident Detected",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Entity:*\n`{entity}`"},
                {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                {
                    "type": "mrkdwn",
                    "text": f"*Root Cause:*\n{rc_icon} {root_cause}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Confidence:*\n{confidence * 100:.0f}%",
                },
            ],
        },
    ]

    if test_name:
        blocks.append(
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Failing Test:*\n`{test_name}`"},
                ],
            }
        )

    blocks += [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Analysis:*\n{probable_cause}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Owners:* {owners_text}"},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Investigation", "emoji": True},
                    "url": f"http://localhost:3000/incidents/{incident_id}",
                    "style": "primary",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Acknowledge", "emoji": True},
                    "url": f"http://localhost:8100/api/v1/incidents/{incident_id}/acknowledge",
                },
            ],
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Incident ID: `{incident_id}` | CHRONOS v2.0",
                }
            ],
        },
    ]

    payload = {"blocks": blocks, "channel": settings.slack_channel}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.slack_webhook_url, json=payload)
            if response.status_code != 200:
                logger.warning(
                    f"Slack webhook returned {response.status_code}: {response.text[:200]}"
                )
                return False
            logger.info(f"Slack notification sent for incident {incident_id}")
            return True
    except Exception as exc:
        logger.error(f"Slack notification error for incident {incident_id}: {exc}")
        return False

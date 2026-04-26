"""
Slack Block Kit notification sender for CHRONOS incident reports.

Sends a rich, interactive Block Kit message to the configured webhook URL.

Fix #1: reads slack_webhook_url as SecretStr and unwraps via secret_or_none().
Fix #3: accepts a typed IncidentReport — all field access is attribute-based.
Fix #4: broad except replaced with specific httpx error types.
Owner mapping: OpenMetadata owner names are resolved to Slack IDs via
config/slack_users.yaml at module load time; unmapped names fall back to "@name".
"""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import quote

import httpx

from chronos.config.settings import secret_or_none, settings
from chronos.models.incident import IncidentReport

logger = logging.getLogger("chronos.notifications.slack")

_SLACK_USER_MAP_PATH = Path(__file__).resolve().parents[2] / "config" / "slack_users.yaml"


def _load_slack_user_map() -> dict[str, str]:
    """Parse config/slack_users.yaml once at import time.

    We parse manually (``key: value`` lines only) rather than pulling in PyYAML
    — the file format is deliberately flat and we already minimise dependencies.
    """
    mapping: dict[str, str] = {}
    if not _SLACK_USER_MAP_PATH.exists():
        return mapping
    try:
        for raw in _SLACK_USER_MAP_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            mapping[key.strip()] = value.strip()
    except OSError as exc:
        logger.warning("Could not read %s: %s", _SLACK_USER_MAP_PATH, exc)
    return mapping


_SLACK_USER_MAP = _load_slack_user_map()


def _render_owner_mention(owner: str) -> str:
    """Render an owner name as a Slack mention using the YAML map."""
    slack_id = _SLACK_USER_MAP.get(owner, "").strip()
    if slack_id.startswith("U"):
        return f"<@{slack_id}>"
    if slack_id.startswith("S"):
        # Usergroup mention — fall back to the original name as display text
        # so Slack shows something meaningful if the subteam can't be resolved.
        return f"<!subteam^{slack_id}|{owner}>"
    if slack_id:
        return slack_id
    return f"@{owner}"

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


async def send_incident_notification(incident_report: IncidentReport) -> bool:
    """
    Send a rich Block Kit Slack notification for a completed investigation.

    Returns True if the webhook returned HTTP 200, False otherwise.
    If no webhook URL is configured, returns False immediately (no error raised).

    Args:
        incident_report: A validated IncidentReport.  Typed model so all field
            access is guaranteed safe — no silent dict.get() fallbacks.
    """
    webhook_url = secret_or_none(settings.slack_webhook_url)
    if not webhook_url:
        logger.debug("SLACK_WEBHOOK_URL not configured — notification skipped")
        return False

    # Typed attribute access — never returns None for required fields
    severity = incident_report.business_impact.value
    root_cause = incident_report.root_cause_category.value
    confidence = incident_report.confidence
    entity = incident_report.affected_entity_fqn
    incident_id = incident_report.incident_id
    probable_cause = incident_report.probable_root_cause or "No analysis available."
    test_name = incident_report.test_name

    # Build owner mention string from affected downstream assets.
    # Owner names are resolved through the YAML map to Slack IDs; unmapped
    # names fall back to "@name" so messages still carry owner context.
    owner_names: list[str] = []
    seen: set[str] = set()
    for asset in incident_report.affected_downstream[:3]:
        for owner in asset.owners:  # list[str] — no .get() needed
            if owner and owner not in seen:
                seen.add(owner)
                owner_names.append(_render_owner_mention(owner))
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
                    "text": {
                        "type": "plain_text",
                        "text": "View Investigation",
                        "emoji": True,
                    },
                    "url": f"{settings.frontend_url}/incidents/{quote(incident_id, safe='')}",
                    "style": "primary",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View in OpenMetadata",
                        "emoji": True,
                    },
                    "url": (
                        f"{settings.openmetadata_host.rstrip('/')}"
                        f"/explore/tables/{quote(entity, safe='')}"
                    ),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Acknowledge", "emoji": True},
                    "url": (
                        f"{settings.api_url}/api/v1/incidents/"
                        f"{quote(incident_id, safe='')}/acknowledge"
                    ),
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
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.warning(
                    "Slack webhook returned %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return False
            logger.info("Slack notification sent for incident %s", incident_id)
            return True
    except httpx.RequestError as exc:
        # Network-level failure (DNS, TCP, timeout before response)
        logger.error(
            "Slack notification network error for incident %s: %r", incident_id, exc
        )
        return False
    except httpx.HTTPStatusError as exc:
        # 4xx/5xx from the Slack API (after response arrived)
        logger.error(
            "Slack API error %d for incident %s: %s",
            exc.response.status_code,
            incident_id,
            exc.response.text[:200],
        )
        return False

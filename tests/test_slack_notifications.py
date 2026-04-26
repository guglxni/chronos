"""
Unit tests for chronos.notifications.slack.

Cover the owner → Slack ID mapping (new feature) and the webhook-URL fallback
behaviour.  HTTP transport is mocked via respx so no real network calls fire.
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from chronos.models.incident import (
    AffectedAsset,
    IncidentReport,
    IncidentStatus,
    RootCauseCategory,
)
from chronos.notifications import slack as slack_module


def _make_report(owners: list[str]) -> IncidentReport:
    return IncidentReport(
        incident_id="test-inc-001",
        detected_at=datetime.now(tz=UTC),
        affected_entity_fqn="db.schema.orders",
        test_name="column_not_null",
        failure_message="nulls found",
        probable_root_cause="Schema change upstream.",
        root_cause_category=RootCauseCategory.SCHEMA_CHANGE,
        confidence=0.85,
        status=IncidentStatus.OPEN,
        affected_downstream=[
            AffectedAsset(fqn="db.x.y", owners=owners),
        ],
    )


def test_render_owner_mention_direct_user():
    with patch.dict(slack_module._SLACK_USER_MAP, {"alice": "U0ALICE"}, clear=False):
        assert slack_module._render_owner_mention("alice") == "<@U0ALICE>"


def test_render_owner_mention_usergroup():
    with patch.dict(
        slack_module._SLACK_USER_MAP,
        {"data-team": "S0DATATEAM"},
        clear=False,
    ):
        result = slack_module._render_owner_mention("data-team")
        assert result.startswith("<!subteam^S0DATATEAM|")
        assert "data-team" in result


def test_render_owner_mention_fallback_for_unmapped():
    # "unknown-person" is not in the YAML map → fallback to literal "@name"
    assert slack_module._render_owner_mention("unknown-person") == "@unknown-person"


@pytest.mark.asyncio
async def test_send_notification_returns_false_without_webhook():
    # Defaults: slack_webhook_url is None → notification silently skipped
    report = _make_report(["alice"])
    result = await slack_module.send_incident_notification(report)
    assert result is False


def test_slack_user_map_file_is_optional():
    """Loader must not crash when the YAML file is absent."""
    with patch.object(slack_module, "_SLACK_USER_MAP_PATH", slack_module.Path("/nonexistent/path.yaml")):
        mapping = slack_module._load_slack_user_map()
        assert mapping == {}

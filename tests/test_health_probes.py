"""Tests for chronos.health probes — covering success, failure, timeout, not_configured."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from chronos.health.aggregator import aggregate_overall_state
from chronos.health.probes import (
    probe_falkordb,
    probe_litellm,
    probe_openmetadata,
    probe_slack,
)
from chronos.health.types import ComponentState, ComponentStatus


# ── OpenMetadata probe ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_openmetadata_not_configured_when_localhost():
    """Default localhost host means production is not configured."""
    with patch("chronos.health.probes.settings") as fake_settings:
        fake_settings.openmetadata_host = "http://localhost:8585"
        fake_settings.openmetadata_jwt_token = None
        result = await probe_openmetadata()
    assert result.state == ComponentState.NOT_CONFIGURED


@pytest.mark.asyncio
async def test_openmetadata_healthy_on_200():
    with patch("chronos.health.probes.settings") as fake_settings, \
         patch("httpx.AsyncClient") as fake_client_cls:
        fake_settings.openmetadata_host = "https://example.collate.io"
        fake_settings.openmetadata_jwt_token = None
        ctx = AsyncMock()
        ctx.get.return_value = httpx.Response(200, json={"version": "1.5.0"})
        fake_client_cls.return_value.__aenter__.return_value = ctx
        result = await probe_openmetadata()
    assert result.state == ComponentState.HEALTHY
    assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_openmetadata_degraded_on_401():
    with patch("chronos.health.probes.settings") as fake_settings, \
         patch("httpx.AsyncClient") as fake_client_cls:
        fake_settings.openmetadata_host = "https://example.collate.io"
        fake_settings.openmetadata_jwt_token = None
        ctx = AsyncMock()
        ctx.get.return_value = httpx.Response(401)
        fake_client_cls.return_value.__aenter__.return_value = ctx
        result = await probe_openmetadata()
    assert result.state == ComponentState.DEGRADED
    assert "auth rejected" in (result.detail or "")


@pytest.mark.asyncio
async def test_openmetadata_down_on_network_error():
    with patch("chronos.health.probes.settings") as fake_settings, \
         patch("httpx.AsyncClient") as fake_client_cls:
        fake_settings.openmetadata_host = "https://nonexistent-host.invalid"
        fake_settings.openmetadata_jwt_token = None
        ctx = AsyncMock()
        ctx.get.side_effect = httpx.ConnectError("name not resolved")
        fake_client_cls.return_value.__aenter__.return_value = ctx
        result = await probe_openmetadata()
    assert result.state == ComponentState.DOWN


# ── FalkorDB probe ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_falkordb_not_configured_localhost_no_password():
    with patch("chronos.health.probes.settings") as fake_settings:
        fake_settings.falkordb_host = "localhost"
        fake_settings.falkordb_port = 6379
        fake_settings.falkordb_password = None
        result = await probe_falkordb()
    assert result.state == ComponentState.NOT_CONFIGURED


@pytest.mark.asyncio
async def test_falkordb_healthy_on_pong():
    with patch("chronos.health.probes.settings") as fake_settings, \
         patch("redis.asyncio.Redis") as fake_redis_cls:
        fake_settings.falkordb_host = "r-1234.falkor.cloud.falkordb.io"
        fake_settings.falkordb_port = 12345
        fake_settings.falkordb_password = None
        client = AsyncMock()
        client.ping.return_value = True
        client.aclose = AsyncMock()
        fake_redis_cls.return_value = client
        result = await probe_falkordb()
    assert result.state == ComponentState.HEALTHY
    assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_falkordb_down_on_exception():
    with patch("chronos.health.probes.settings") as fake_settings, \
         patch("redis.asyncio.Redis") as fake_redis_cls:
        fake_settings.falkordb_host = "r-1234.falkor.cloud.falkordb.io"
        fake_settings.falkordb_port = 12345
        fake_settings.falkordb_password = None
        client = AsyncMock()
        client.ping.side_effect = ConnectionRefusedError("connection refused")
        client.aclose = AsyncMock()
        fake_redis_cls.return_value = client
        result = await probe_falkordb()
    assert result.state == ComponentState.DOWN


# ── LiteLLM probe ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_litellm_healthy_when_provider_key_configured_in_direct_mode():
    """No proxy URL but provider key set → direct mode is healthy."""
    from pydantic import SecretStr
    with patch("chronos.health.probes.settings") as fake_settings:
        fake_settings.litellm_proxy_url = "http://localhost:4000"  # default = "not configured"
        fake_settings.anthropic_api_key = None
        fake_settings.openai_api_key = None
        fake_settings.groq_api_key = SecretStr("gsk_fake_test")
        result = await probe_litellm()
    assert result.state == ComponentState.HEALTHY
    assert "direct mode" in (result.detail or "")


@pytest.mark.asyncio
async def test_litellm_not_configured_when_proxy_local_and_no_key():
    with patch("chronos.health.probes.settings") as fake_settings:
        fake_settings.litellm_proxy_url = "http://localhost:4000"
        fake_settings.anthropic_api_key = None
        fake_settings.openai_api_key = None
        fake_settings.groq_api_key = None
        result = await probe_litellm()
    assert result.state == ComponentState.NOT_CONFIGURED


# ── Slack probe ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_slack_not_configured_when_unset():
    with patch("chronos.health.probes.settings") as fake_settings:
        fake_settings.slack_webhook_url = None
        result = await probe_slack()
    assert result.state == ComponentState.NOT_CONFIGURED
    assert result.required is False  # slack is optional


@pytest.mark.asyncio
async def test_slack_healthy_when_webhook_configured():
    from pydantic import SecretStr
    with patch("chronos.health.probes.settings") as fake_settings:
        fake_settings.slack_webhook_url = SecretStr("https://hooks.slack.com/services/T/B/X")
        result = await probe_slack()
    assert result.state == ComponentState.HEALTHY
    assert result.required is False


# ── Aggregator overall-state rollup ───────────────────────────────────────────


def _status(name: str, state: ComponentState, *, required: bool = True) -> ComponentStatus:
    from datetime import UTC, datetime
    return ComponentStatus(
        name=name, state=state, latency_ms=10.0, detail="test",
        last_checked=datetime.now(UTC), required=required,
    )


def test_overall_healthy_when_all_required_healthy():
    components = [
        _status("openmetadata", ComponentState.HEALTHY),
        _status("falkordb", ComponentState.HEALTHY),
        _status("litellm", ComponentState.HEALTHY),
        _status("slack", ComponentState.NOT_CONFIGURED, required=False),
    ]
    assert aggregate_overall_state(components) == "healthy"


def test_overall_down_when_any_required_down():
    components = [
        _status("openmetadata", ComponentState.HEALTHY),
        _status("falkordb", ComponentState.DOWN),
        _status("litellm", ComponentState.HEALTHY),
        _status("slack", ComponentState.HEALTHY, required=False),
    ]
    assert aggregate_overall_state(components) == "down"


def test_overall_degraded_when_required_degraded():
    components = [
        _status("openmetadata", ComponentState.DEGRADED),
        _status("falkordb", ComponentState.HEALTHY),
        _status("litellm", ComponentState.HEALTHY),
        _status("slack", ComponentState.HEALTHY, required=False),
    ]
    assert aggregate_overall_state(components) == "degraded"


def test_overall_degraded_when_optional_down():
    components = [
        _status("openmetadata", ComponentState.HEALTHY),
        _status("falkordb", ComponentState.HEALTHY),
        _status("litellm", ComponentState.HEALTHY),
        _status("slack", ComponentState.DOWN, required=False),
    ]
    assert aggregate_overall_state(components) == "degraded"


def test_not_configured_treated_as_benign():
    components = [
        _status("openmetadata", ComponentState.NOT_CONFIGURED),
        _status("falkordb", ComponentState.HEALTHY),
        _status("litellm", ComponentState.HEALTHY),
        _status("slack", ComponentState.NOT_CONFIGURED, required=False),
    ]
    # NOT_CONFIGURED is intentional config — does not flag overall down/degraded
    assert aggregate_overall_state(components) == "healthy"

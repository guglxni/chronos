"""
Async probes for each backing service CHRONOS depends on.

Every probe MUST:
- return within ``_PROBE_TIMEOUT_SECONDS`` (no hung dyno workers)
- catch every exception and translate to a sanitized ``ComponentStatus``
- never include credentials, full URLs, or stack traces in ``detail``
- treat missing config as ``NOT_CONFIGURED`` (intentional, not a failure)
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime

import httpx
import redis.asyncio as aioredis

from chronos.config.settings import secret_or_none, settings
from chronos.health.types import ComponentState, ComponentStatus

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT_SECONDS = 2.0


def _now() -> datetime:
    return datetime.now(UTC)


def _sanitize(message: str, max_length: int = 120) -> str:
    """Trim long error messages and strip likely-sensitive substrings."""
    msg = message.strip().replace("\n", " ")
    # Remove anything that looks like a token (long hex/base64 runs).
    sanitized = []
    for word in msg.split():
        if len(word) > 40:  # plausibly a token
            sanitized.append(word[:8] + "...")
        else:
            sanitized.append(word)
    out = " ".join(sanitized)
    return out[:max_length] + ("..." if len(out) > max_length else "")


async def probe_openmetadata() -> ComponentStatus:
    """Hit /api/v1/system/version on the configured OM host."""
    name = "openmetadata"
    host = (settings.openmetadata_host or "").rstrip("/")
    token = secret_or_none(settings.openmetadata_jwt_token)

    # localhost defaults mean nothing was configured for production.
    if not host or "localhost" in host:
        return ComponentStatus(
            name=name,
            state=ComponentState.NOT_CONFIGURED,
            detail="OPENMETADATA_HOST not configured for production",
            last_checked=_now(),
        )

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{host}/api/v1/system/version"

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if resp.status_code == 200:
            return ComponentStatus(
                name=name,
                state=ComponentState.HEALTHY,
                latency_ms=round(elapsed_ms, 1),
                detail=f"version endpoint reachable ({resp.status_code})",
                last_checked=_now(),
            )
        if resp.status_code in (401, 403):
            return ComponentStatus(
                name=name,
                state=ComponentState.DEGRADED,
                latency_ms=round(elapsed_ms, 1),
                detail=f"auth rejected ({resp.status_code}) — check JWT token",
                last_checked=_now(),
            )
        return ComponentStatus(
            name=name,
            state=ComponentState.DEGRADED,
            latency_ms=round(elapsed_ms, 1),
            detail=f"unexpected status {resp.status_code}",
            last_checked=_now(),
        )
    except (httpx.TimeoutException, asyncio.TimeoutError):
        return ComponentStatus(
            name=name,
            state=ComponentState.DOWN,
            detail=f"timeout after {_PROBE_TIMEOUT_SECONDS}s",
            last_checked=_now(),
        )
    except httpx.HTTPError as exc:
        return ComponentStatus(
            name=name,
            state=ComponentState.DOWN,
            detail=_sanitize(str(exc)),
            last_checked=_now(),
        )
    except Exception as exc:
        logger.exception("openmetadata probe failed unexpectedly")
        return ComponentStatus(
            name=name,
            state=ComponentState.DOWN,
            detail=_sanitize(f"{type(exc).__name__}: {exc}"),
            last_checked=_now(),
        )


async def probe_falkordb() -> ComponentStatus:
    """PING the FalkorDB instance over the Redis wire protocol."""
    name = "falkordb"
    host = settings.falkordb_host or ""
    port = settings.falkordb_port
    password = secret_or_none(settings.falkordb_password)

    # Localhost default with no password = unconfigured for production.
    # FalkorDB Cloud always requires a password.
    if not host or (host in ("localhost", "127.0.0.1") and not password):
        return ComponentStatus(
            name=name,
            state=ComponentState.NOT_CONFIGURED,
            detail="FALKORDB_HOST/FALKORDB_PASSWORD not configured for production",
            last_checked=_now(),
        )

    started = time.perf_counter()
    client: aioredis.Redis | None = None
    try:
        kwargs: dict = {
            "host": host,
            "port": port,
            "password": password,
            "socket_connect_timeout": _PROBE_TIMEOUT_SECONDS,
            "socket_timeout": _PROBE_TIMEOUT_SECONDS,
            "decode_responses": True,
        }
        if settings.falkordb_username:
            kwargs["username"] = settings.falkordb_username
        if settings.falkordb_tls:
            kwargs["ssl"] = True
            kwargs["ssl_cert_reqs"] = None  # cloud uses wildcard cert
        client = aioredis.Redis(**kwargs)
        pong = await asyncio.wait_for(client.ping(), timeout=_PROBE_TIMEOUT_SECONDS)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if pong:
            return ComponentStatus(
                name=name,
                state=ComponentState.HEALTHY,
                latency_ms=round(elapsed_ms, 1),
                detail=f"PING {host}:{port} ok",
                last_checked=_now(),
            )
        return ComponentStatus(
            name=name,
            state=ComponentState.DEGRADED,
            latency_ms=round(elapsed_ms, 1),
            detail="PING returned falsy response",
            last_checked=_now(),
        )
    except (asyncio.TimeoutError, TimeoutError):
        return ComponentStatus(
            name=name,
            state=ComponentState.DOWN,
            detail=f"timeout after {_PROBE_TIMEOUT_SECONDS}s",
            last_checked=_now(),
        )
    except Exception as exc:
        return ComponentStatus(
            name=name,
            state=ComponentState.DOWN,
            detail=_sanitize(f"{type(exc).__name__}: {exc}"),
            last_checked=_now(),
        )
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


async def probe_litellm() -> ComponentStatus:
    """Probe LiteLLM proxy /health (or /v1/models for direct provider URLs)."""
    name = "litellm"
    base = (settings.litellm_proxy_url or "").rstrip("/")
    has_provider_key = any([
        settings.anthropic_api_key,
        settings.openai_api_key,
        settings.groq_api_key,
    ])

    if not base or "localhost" in base:
        if has_provider_key:
            # Direct provider mode (Groq etc.) — we can't probe a generic /health,
            # but having the key configured means LLM calls will work.
            return ComponentStatus(
                name=name,
                state=ComponentState.HEALTHY,
                detail="provider API key configured — direct mode (no proxy)",
                last_checked=_now(),
            )
        return ComponentStatus(
            name=name,
            state=ComponentState.NOT_CONFIGURED,
            detail="LITELLM_PROXY_URL and provider keys both unset",
            last_checked=_now(),
        )

    # Try /health first, then fall back to /v1/models (Groq-style).
    candidates = [f"{base}/health", f"{base}/v1/models"]
    started = time.perf_counter()
    last_status: int | None = None
    last_error: str | None = None

    for url in candidates:
        try:
            async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_SECONDS) as client:
                # Some endpoints (Groq /v1/models) require auth; include if present.
                headers = {}
                key = secret_or_none(settings.groq_api_key) or secret_or_none(settings.openai_api_key)
                if key:
                    headers["Authorization"] = f"Bearer {key}"
                resp = await client.get(url, headers=headers)
            elapsed_ms = (time.perf_counter() - started) * 1000
            if resp.status_code == 200:
                return ComponentStatus(
                    name=name,
                    state=ComponentState.HEALTHY,
                    latency_ms=round(elapsed_ms, 1),
                    detail=f"reachable via {url.rsplit('/', 1)[-1]} endpoint",
                    last_checked=_now(),
                )
            last_status = resp.status_code
        except (httpx.TimeoutException, asyncio.TimeoutError):
            last_error = "timeout"
        except httpx.HTTPError as exc:
            last_error = _sanitize(str(exc))
        except Exception as exc:
            last_error = _sanitize(f"{type(exc).__name__}: {exc}")

    return ComponentStatus(
        name=name,
        state=ComponentState.DOWN,
        detail=f"all probe endpoints failed (last status={last_status}, err={last_error})",
        last_checked=_now(),
    )


async def probe_slack() -> ComponentStatus:
    """
    Slack incoming-webhook URLs cannot be probed without sending a real message,
    so we report HEALTHY when configured and NOT_CONFIGURED otherwise. The actual
    delivery success is observable via the slack notifier's own logs.
    """
    name = "slack"
    webhook = secret_or_none(settings.slack_webhook_url)
    if not webhook:
        return ComponentStatus(
            name=name,
            state=ComponentState.NOT_CONFIGURED,
            detail="SLACK_WEBHOOK_URL not set",
            last_checked=_now(),
            required=False,
        )
    return ComponentStatus(
        name=name,
        state=ComponentState.HEALTHY,
        detail="webhook URL configured (delivery not actively probed)",
        last_checked=_now(),
        required=False,
    )


async def run_all_probes() -> list[ComponentStatus]:
    """Run every probe in parallel; return the results in stable order."""
    results = await asyncio.gather(
        probe_openmetadata(),
        probe_falkordb(),
        probe_litellm(),
        probe_slack(),
        return_exceptions=False,
    )
    return list(results)

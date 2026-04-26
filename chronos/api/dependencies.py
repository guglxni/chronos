"""
FastAPI dependencies for CHRONOS API security.

Provides HMAC-SHA256 signature validation for webhook endpoints (Fix #2).
When WEBHOOK_SIGNATURE_REQUIRED=true (production), unsigned or incorrectly
signed requests are rejected with HTTP 401.  In development (the default) the
check is bypassed so local testing works without configuring a shared secret.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Literal

from fastapi import Header, HTTPException, Request, status

from chronos.config.settings import secret_or_none, settings

logger = logging.getLogger("chronos.api.auth")

SignatureHeader = Literal["X-OM-Signature", "X-OpenLineage-Signature"]

_REPLAY_WINDOW_SECONDS = 300  # ±5 minutes matches Slack/GitHub convention


def _compute_hmac(body: bytes, secret: str, timestamp: str | None = None) -> str:
    """
    Return a 'sha256=<hex>' HMAC digest.

    When ``timestamp`` is provided the signed payload is ``f"{timestamp}.{body}"``,
    matching the Slack/GitHub replay-protection pattern.  Without a timestamp the
    raw body is signed (backward-compatible with callers that don't send the header).
    """
    payload = (f"{timestamp}.".encode() + body) if timestamp else body
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def _verify_signature(
    request: Request,
    provided: str | None,
    header_name: SignatureHeader,
    timestamp: str | None = None,
) -> None:
    """
    Validate the HMAC-SHA256 signature header against the raw request body.

    When the caller includes ``X-OM-Timestamp`` (Unix seconds), replay protection
    is enforced: requests older than ±300 s are rejected, and the HMAC is verified
    over ``f"{timestamp}.{body}"`` rather than the raw body alone.  Callers that
    omit the timestamp fall back to the legacy body-only HMAC so that existing
    integrations continue to work.

    Short-circuits when signature checking is disabled (development mode).
    Fails *closed* — not open — if the feature is enabled but misconfigured.
    """
    if not settings.effective_webhook_signature_required:
        return  # Dev mode — signature optional

    secret = secret_or_none(settings.webhook_hmac_secret)
    if secret is None:
        logger.error(
            "WEBHOOK_SIGNATURE_REQUIRED=true but WEBHOOK_HMAC_SECRET is unset — "
            "rejecting request to avoid accepting unsigned payloads"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook signing misconfigured — contact server administrator",
        )

    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing required header: {header_name}",
        )

    # Replay protection: when a timestamp header is present, enforce freshness
    if timestamp is not None:
        try:
            ts = int(timestamp)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-OM-Timestamp must be a Unix epoch integer",
            ) from None
        age = abs(time.time() - ts)
        if age > _REPLAY_WINDOW_SECONDS:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                "Webhook replay detected on %s from %s (age=%.0fs)",
                request.url.path,
                client_ip,
                age,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook timestamp too old — possible replay attack",
            )

    body = await request.body()
    expected = _compute_hmac(body, secret, timestamp)

    # Constant-time comparison prevents timing-based side-channel attacks
    if not hmac.compare_digest(expected, provided):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            "Webhook signature mismatch on %s from %s",
            request.url.path,
            client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


async def verify_openmetadata_signature(
    request: Request,
    x_om_signature: str | None = Header(default=None, alias="X-OM-Signature"),
    x_om_timestamp: str | None = Header(default=None, alias="X-OM-Timestamp"),
) -> None:
    """Dependency: validate OpenMetadata webhook HMAC signature (with optional replay guard)."""
    await _verify_signature(request, x_om_signature, "X-OM-Signature", x_om_timestamp)


async def verify_openlineage_signature(
    request: Request,
    x_openlineage_signature: str | None = Header(
        default=None, alias="X-OpenLineage-Signature"
    ),
    x_openlineage_timestamp: str | None = Header(
        default=None, alias="X-OpenLineage-Timestamp"
    ),
) -> None:
    """Dependency: validate OpenLineage webhook HMAC signature (with optional replay guard)."""
    await _verify_signature(
        request, x_openlineage_signature, "X-OpenLineage-Signature", x_openlineage_timestamp
    )

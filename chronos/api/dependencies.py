"""
FastAPI dependencies for CHRONOS API security.

Three independent auth mechanisms — each follows the same pattern:
  dev mode  → check skipped (local testing with no secrets configured)
  prod mode → fail closed if the relevant secret is unset

  1. verify_openmetadata_signature / verify_openlineage_signature
       HMAC-SHA256 on webhook bodies.  In production X-OM-Timestamp is
       REQUIRED (not merely optional) so replay attacks are impossible.

  2. verify_bearer_token
       Static shared-secret bearer auth for mutation endpoints
       (acknowledge, resolve).  Configured via API_BEARER_TOKEN env var.
       In production the token MUST be set; in dev the check is skipped so
       curl tests work without configuration.
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


# ── Bearer token auth ─────────────────────────────────────────────────────────

async def verify_bearer_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    """Require a valid Bearer token on mutation endpoints (acknowledge, resolve).

    In development (no API_BEARER_TOKEN set): always passes — safe for local
    curl and test usage.  In production: the token MUST be configured and the
    caller MUST supply ``Authorization: Bearer <token>``.  Fails closed if the
    env var is absent in production to prevent an unauthenticated default.
    """
    is_prod = settings.environment == "production"
    configured_token = secret_or_none(settings.api_bearer_token)

    if configured_token is None:
        if is_prod:
            # Fail closed: no bearer token configured in prod → block all mutations.
            logger.error(
                "API_BEARER_TOKEN is unset in production — "
                "blocking mutation request to avoid unauthenticated writes"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Mutation auth misconfigured — contact administrator",
            )
        # Dev mode with no token: skip check entirely.
        return

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header (expected: Bearer <token>)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format (expected: Bearer <token>)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── HMAC webhook signature ────────────────────────────────────────────────────

def _compute_hmac(body: bytes, secret: str, timestamp: str | None = None) -> str:
    """Return a 'sha256=<hex>' HMAC digest.

    When ``timestamp`` is provided the signed payload is ``f"{timestamp}.{body}"``,
    matching the Slack/GitHub replay-protection pattern.
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
    """Validate the HMAC-SHA256 signature header against the raw request body.

    In production X-OM-Timestamp is REQUIRED — omitting it is rejected with 401
    so a captured signature cannot be replayed indefinitely.  In development the
    timestamp is optional (body-only HMAC accepted) for convenient local testing.

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

    # In production the timestamp header is REQUIRED to prevent replay attacks.
    # A signed payload without a timestamp can be replayed indefinitely; with a
    # timestamp the replay window is bounded to ±_REPLAY_WINDOW_SECONDS.
    if timestamp is None and settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-OM-Timestamp header is required in production (replay protection)",
        )

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
    """Dependency: validate OpenMetadata webhook HMAC signature."""
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
    """Dependency: validate OpenLineage webhook HMAC signature."""
    await _verify_signature(
        request, x_openlineage_signature, "X-OpenLineage-Signature", x_openlineage_timestamp
    )

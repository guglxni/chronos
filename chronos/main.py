"""
CHRONOS FastAPI application entry point.

Mounts all route groups, registers middleware, and wires up the lifespan handler
for startup/shutdown work (OpenLLMetry init).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import Response

from chronos.api.middleware import error_handler, logging_middleware
from chronos.api.rate_limit import limiter
from chronos.api.routes import demo, incidents, investigations, stats, webhooks, well_known
from chronos.api.schemas import HealthResponse
from chronos.config.settings import settings
from chronos.mcp.client import mcp_client
from chronos.observability.otel_setup import setup_openllmetry

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)-30s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("chronos")


_MAX_REQUEST_BODY_BYTES = 1_000_000  # 1 MB


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — runs setup before first request, teardown on shutdown."""
    logger.info(
        "CHRONOS v%s starting (env=%s, debug=%s)",
        settings.version,
        settings.environment,
        settings.debug,
    )
    setup_openllmetry()
    yield
    await mcp_client.close()
    logger.info("CHRONOS shutting down cleanly")


_is_prod = settings.environment == "production"

app = FastAPI(
    title="CHRONOS",
    description=(
        "Autonomous Data Incident Root Cause Analysis Agent. "
        "Investigates data quality failures across OpenMetadata, Graphiti, and GitNexus."
    ),
    version=settings.version,
    lifespan=lifespan,
    # Disable interactive docs in production — they expose the full API surface
    # and accept live requests without any auth gate on the /docs UI itself.
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-OM-Signature", "X-OpenLineage-Signature"],
)

# ── Body-size guard ───────────────────────────────────────────────────────────
@app.middleware("http")
async def enforce_body_size(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Reject oversize request bodies.

    Two-stage enforcement because the Content-Length header is attacker-controlled
    (and absent for ``Transfer-Encoding: chunked`` requests):
      1. Fast path: if the client honestly advertises a length over the cap, 413
         immediately and avoid buffering the body at all.
      2. Slow path: stream the body in chunks, count bytes, and 413 the moment we
         cross the cap.  Replace ``request._receive`` with a re-emitter so the
         downstream handler still sees the body it would have seen otherwise.
    """
    raw_len = request.headers.get("content-length")
    if raw_len is not None:
        try:
            advertised = int(raw_len)
        except ValueError:
            # Malformed header → reject as a bad request rather than leaking 500.
            return JSONResponse(status_code=400, content={"error": "invalid_content_length"})
        if advertised > _MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": "request_body_too_large", "max_bytes": _MAX_REQUEST_BODY_BYTES},
            )

    # Slow path: buffer the body up to the cap.  We tolerate up to one extra
    # byte over the cap so the boundary check is strict.
    body = bytearray()
    more_body = True
    while more_body:
        message = await request.receive()
        if message["type"] != "http.request":
            # Disconnect or other lifecycle message — pass straight through.
            break
        chunk = message.get("body", b"")
        if chunk:
            body.extend(chunk)
            if len(body) > _MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "request_body_too_large",
                        "max_bytes": _MAX_REQUEST_BODY_BYTES,
                    },
                )
        more_body = message.get("more_body", False)

    # Re-emit the buffered body to the downstream handler.  Without this, the
    # next ``await request.body()`` call hangs because the receive channel is
    # already drained.
    sent = False

    async def _replay() -> dict[str, object]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": bytes(body), "more_body": False}

    # Starlette exposes no public API for body replay; _receive reassignment
    # is the standard middleware pattern documented by encode/starlette#1519.
    request._receive = _replay
    return await call_next(request)


def _cli_main() -> None:
    """Entry point for the ``chronos-server`` console script."""
    import uvicorn

    uvicorn.run("chronos.main:app", host="0.0.0.0", port=8000, reload=False)  # noqa: S104


# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter


async def _handle_rate_limit(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, RateLimitExceeded):
        return Response(status_code=500)
    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, _handle_rate_limit)

# ── Request logging middleware ────────────────────────────────────────────────
app.middleware("http")(logging_middleware)

# ── Global error handler ──────────────────────────────────────────────────────
app.add_exception_handler(Exception, error_handler)

# ── Route groups ──────────────────────────────────────────────────────────────
app.include_router(webhooks.router)
app.include_router(demo.router)
app.include_router(incidents.router)
app.include_router(investigations.router)
app.include_router(stats.router)
app.include_router(well_known.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(
        status="healthy",
        version=settings.version,
        service="chronos",
    )

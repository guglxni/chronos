"""
CHRONOS FastAPI application entry point.

Mounts all route groups, registers middleware, and wires up the lifespan handler
for startup/shutdown work (OpenLLMetry init).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chronos.api.middleware import error_handler, logging_middleware
from chronos.api.routes import incidents, investigations, stats, webhooks, well_known
from chronos.config.settings import settings
from chronos.observability.otel_setup import setup_openllmetry

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)-30s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("chronos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs setup before first request, teardown on shutdown."""
    logger.info(
        f"CHRONOS v{settings.version} starting "
        f"(env={settings.environment}, debug={settings.debug})"
    )
    setup_openllmetry()
    yield
    logger.info("CHRONOS shutting down cleanly")


app = FastAPI(
    title="CHRONOS",
    description=(
        "Autonomous Data Incident Root Cause Analysis Agent. "
        "Investigates data quality failures across OpenMetadata, Graphiti, and GitNexus."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ────────────────────────────────────────────────
app.middleware("http")(logging_middleware)

# ── Global error handler ──────────────────────────────────────────────────────
app.add_exception_handler(Exception, error_handler)

# ── Route groups ──────────────────────────────────────────────────────────────
app.include_router(webhooks.router)
app.include_router(incidents.router)
app.include_router(investigations.router)
app.include_router(stats.router)
app.include_router(well_known.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/v1/health", tags=["system"])
async def health():
    """Liveness probe."""
    return {
        "status": "healthy",
        "version": settings.version,
        "service": "chronos",
        "environment": settings.environment,
    }

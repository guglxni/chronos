"""
GET /api/v1/health/components — per-service health probe.

Cached for 30s in ``chronos.health.aggregator`` so a UI badge polling
every 60s causes at most one round-trip per service per minute.

Frontend usage: <SystemStatusBadge /> in chronos-frontend renders a
colored dot in the navbar from this endpoint's ``overall`` field.
"""

from __future__ import annotations

from fastapi import APIRouter

from chronos.health import OverallHealth, get_component_health

router = APIRouter(prefix="/api/v1/health", tags=["system"])


@router.get(
    "/components",
    response_model=OverallHealth,
    summary="Per-component health for all backing services",
)
async def get_components_health(force: bool = False) -> OverallHealth:
    """
    Returns OpenMetadata, FalkorDB, LiteLLM, Slack health.

    Pass ``?force=true`` to bypass the 30s cache (useful for status pages).
    """
    return await get_component_health(force=force)

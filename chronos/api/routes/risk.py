"""Predictive risk scoring endpoints — top at-risk entities + per-entity drill-in."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from chronos.risk import RiskScore, explain_entity, top_at_risk

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


@router.get("/at-risk", response_model=list[RiskScore], summary="Top entities ranked by failure risk")
async def get_top_at_risk(
    limit: int = Query(10, ge=1, le=50),
    window_days: int = Query(30, ge=1, le=365),
) -> list[RiskScore]:
    """Return the top ``limit`` entities ranked by computed risk score.

    Score weights: incident count (35) + severity (25) + diversity (15) +
    open (15) + recency (10) = 100. Each score is fully explainable via
    the per-factor contributions field.
    """
    return top_at_risk(limit=limit, window_days=window_days)


@router.get("/{entity_fqn:path}/explain", response_model=RiskScore, summary="Per-entity risk breakdown")
async def get_entity_risk(
    entity_fqn: str,
    window_days: int = Query(30, ge=1, le=365),
) -> RiskScore:
    """Drill into one entity's risk score with full factor breakdown."""
    score = explain_entity(entity_fqn, window_days=window_days)
    if score is None:
        raise HTTPException(status_code=404, detail=f"No incidents found for entity {entity_fqn!r}")
    return score

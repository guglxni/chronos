"""
Dashboard statistics and recurring pattern detection endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from chronos.api.schemas import PatternsResponse, StatsResponse
from chronos.core import incident_store

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats() -> dict[str, Any]:
    """
    Return aggregate statistics across all investigations.

    Includes counts by root cause category, business impact, status,
    average confidence, and key totals.

    Fix #3: reads typed IncidentReport attributes instead of dict.get() on
    required fields.  Counter dicts still use .get(k, 0) — that's correct
    because a category may legitimately not appear in the result set.
    """
    incidents = incident_store.list_all()

    by_category: dict[str, int] = {}
    by_impact: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total_confidence = 0.0

    for inc in incidents:
        # Typed attribute access — no silent defaults masking serialisation bugs
        cat = inc.root_cause_category.value
        imp = inc.business_impact.value
        sta = inc.status.value

        by_category[cat] = by_category.get(cat, 0) + 1
        by_impact[imp] = by_impact.get(imp, 0) + 1
        by_status[sta] = by_status.get(sta, 0) + 1
        total_confidence += inc.confidence  # float field — always present

    avg_confidence = round(total_confidence / len(incidents), 3) if incidents else 0.0

    return {
        "total_incidents": len(incidents),
        "by_root_cause": by_category,
        "by_impact": by_impact,
        "by_status": by_status,
        "avg_confidence": avg_confidence,
        # Counter-dict .get(k, 0) is correct: a status may not exist yet
        "open_count": by_status.get("open", 0),
        "investigating_count": by_status.get("investigating", 0),
        "critical_count": by_impact.get("critical", 0),
        "resolved_count": by_status.get("resolved", 0),
    }


@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns() -> dict[str, Any]:
    """
    Identify recurring incident patterns — entities that have failed more than once.

    Returns entities sorted by incident count descending, flagged as recurring
    if they have more than one incident.
    """
    incidents = incident_store.list_all()

    entity_counts: dict[str, int] = {}
    entity_categories: dict[str, list[str]] = {}

    for inc in incidents:
        # Typed attribute access — fqn is always a non-empty str on IncidentReport
        fqn = inc.affected_entity_fqn
        cat = inc.root_cause_category.value
        entity_counts[fqn] = entity_counts.get(fqn, 0) + 1
        entity_categories.setdefault(fqn, []).append(cat)

    patterns = [
        {
            "entity_fqn": fqn,
            "incident_count": count,
            "is_recurring": count > 1,
            "root_cause_categories": list(set(entity_categories.get(fqn, []))),
        }
        for fqn, count in sorted(
            entity_counts.items(), key=lambda x: x[1], reverse=True
        )
        if count > 1
    ]

    return {"patterns": patterns[:20], "total_recurring_entities": len(patterns)}

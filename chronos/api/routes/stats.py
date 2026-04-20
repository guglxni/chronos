"""
Dashboard statistics and recurring pattern detection endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from chronos.api.routes.incidents import _incidents

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("")
async def get_stats():
    """
    Return aggregate statistics across all investigations.

    Includes counts by root cause category, business impact, status,
    average confidence, and key totals.
    """
    incidents = list(_incidents.values())

    by_category: dict[str, int] = {}
    by_impact: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total_confidence = 0.0

    for inc in incidents:
        cat = inc.get("root_cause_category", "UNKNOWN")
        imp = inc.get("business_impact", "medium")
        sta = inc.get("status", "open")

        by_category[cat] = by_category.get(cat, 0) + 1
        by_impact[imp] = by_impact.get(imp, 0) + 1
        by_status[sta] = by_status.get(sta, 0) + 1
        total_confidence += float(inc.get("confidence", 0.0))

    avg_confidence = round(total_confidence / len(incidents), 3) if incidents else 0.0

    return {
        "total_incidents": len(incidents),
        "by_root_cause": by_category,
        "by_impact": by_impact,
        "by_status": by_status,
        "avg_confidence": avg_confidence,
        "open_count": by_status.get("open", 0),
        "investigating_count": by_status.get("investigating", 0),
        "critical_count": by_impact.get("critical", 0),
        "resolved_count": by_status.get("resolved", 0),
    }


@router.get("/patterns")
async def get_patterns():
    """
    Identify recurring incident patterns — entities that have failed more than once.

    Returns entities sorted by incident count descending, flagged as recurring
    if they have more than one incident.
    """
    incidents = list(_incidents.values())

    entity_counts: dict[str, int] = {}
    entity_categories: dict[str, list[str]] = {}

    for inc in incidents:
        fqn = inc.get("affected_entity_fqn", "")
        cat = inc.get("root_cause_category", "UNKNOWN")
        if fqn:
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

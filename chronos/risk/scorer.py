"""Predictive risk score per entity, derived from real incident history.

Inputs come from ``chronos.core.incident_store`` (already hydrated from
FalkorDB on startup). Output is a ranked list of at-risk entities with
per-factor breakdowns suitable for a "why is this at risk?" panel.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel

from chronos.core import incident_store
from chronos.models.incident import (
    BusinessImpact,
    IncidentReport,
    IncidentStatus,
    RootCauseCategory,
)


# Severity → 0-1 weight. CRITICAL is 10x LOW so a single critical incident
# meaningfully outweighs many low-severity ones.
_SEVERITY_WEIGHT: dict[BusinessImpact, float] = {
    BusinessImpact.CRITICAL: 1.0,
    BusinessImpact.HIGH:     0.7,
    BusinessImpact.MEDIUM:   0.4,
    BusinessImpact.LOW:      0.1,
}

# Score weights — sum should be exactly 100 so the final score is intuitive.
_WEIGHTS = {
    "incident_count":   35,   # primary signal: more failures = more risk
    "severity":         25,   # how bad were the failures
    "diversity":        15,   # multiple distinct failure modes = unstable
    "open":             15,   # currently-open incidents are a live signal
    "recency":          10,   # how recently did the most recent failure happen
}


class RiskFactors(BaseModel):
    incident_count_window: int          # incidents in the lookback window
    severity_weighted: float            # mean severity weight in [0, 1]
    unique_root_causes: int             # distinct categories seen
    open_count: int                     # currently-open incidents
    days_since_last: float | None       # null when no incidents


class RiskScoreContribution(BaseModel):
    factor: str                         # human label
    raw_value: float                    # the underlying number
    contribution: float                 # 0 - max-weight points contributed to the score
    explanation: str                    # one-line "why this matters" sentence


class RiskScore(BaseModel):
    entity_fqn: str
    score: float                        # 0 - 100, higher = more at risk
    rank: int                           # 1-based rank within at-risk list
    factors: RiskFactors
    contributions: list[RiskScoreContribution]
    last_incident_at: datetime | None
    sparkline_30d: list[int]            # one int per day, oldest -> newest


def _bucket_index(ts: datetime, window_start: datetime) -> int:
    return (ts - window_start).days


def _compute_factors(
    incidents: list[IncidentReport],
    window_days: int,
) -> RiskFactors:
    if not incidents:
        return RiskFactors(
            incident_count_window=0,
            severity_weighted=0.0,
            unique_root_causes=0,
            open_count=0,
            days_since_last=None,
        )
    sev_weights = [_SEVERITY_WEIGHT.get(i.business_impact, 0.4) for i in incidents]
    severity_weighted = sum(sev_weights) / len(sev_weights)
    unique_categories = {i.root_cause_category for i in incidents}
    open_count = sum(1 for i in incidents if i.status in (IncidentStatus.OPEN, IncidentStatus.INVESTIGATING))
    last_at = max(i.detected_at for i in incidents)
    days_since_last = (datetime.now(UTC) - last_at).total_seconds() / 86400

    return RiskFactors(
        incident_count_window=len(incidents),
        severity_weighted=round(severity_weighted, 3),
        unique_root_causes=len(unique_categories),
        open_count=open_count,
        days_since_last=round(days_since_last, 2),
    )


def _score_from_factors(factors: RiskFactors, window_days: int) -> tuple[float, list[RiskScoreContribution]]:
    """Map factors -> 0-100 score with per-factor contributions for explainability."""
    contributions: list[RiskScoreContribution] = []

    # Incident count: 1 incident -> 0.25 of weight, plateaus at 5 incidents
    count_norm = min(factors.incident_count_window / 5.0, 1.0)
    contributions.append(RiskScoreContribution(
        factor="Incident count",
        raw_value=float(factors.incident_count_window),
        contribution=round(count_norm * _WEIGHTS["incident_count"], 1),
        explanation=f"{factors.incident_count_window} incident(s) in the past {window_days} days",
    ))

    # Severity: already normalized 0-1
    contributions.append(RiskScoreContribution(
        factor="Severity weight",
        raw_value=factors.severity_weighted,
        contribution=round(factors.severity_weighted * _WEIGHTS["severity"], 1),
        explanation=(
            "Avg severity high (CRITICAL/HIGH dominate)"
            if factors.severity_weighted > 0.6
            else "Mixed severity"
            if factors.severity_weighted > 0.3
            else "Mostly low-severity"
        ),
    ))

    # Diversity: 1 category -> 0.0, 3+ categories -> 1.0
    diversity_norm = min(max(factors.unique_root_causes - 1, 0) / 2.0, 1.0)
    contributions.append(RiskScoreContribution(
        factor="Failure diversity",
        raw_value=float(factors.unique_root_causes),
        contribution=round(diversity_norm * _WEIGHTS["diversity"], 1),
        explanation=(
            f"{factors.unique_root_causes} distinct failure modes — instability across multiple causes"
            if factors.unique_root_causes >= 2
            else "Single failure mode — predictable"
        ),
    ))

    # Open count: 1 open -> 0.5, 2+ -> 1.0
    open_norm = min(factors.open_count / 2.0, 1.0)
    contributions.append(RiskScoreContribution(
        factor="Currently open",
        raw_value=float(factors.open_count),
        contribution=round(open_norm * _WEIGHTS["open"], 1),
        explanation=(
            f"{factors.open_count} unresolved incident(s) — actively failing"
            if factors.open_count > 0
            else "No open incidents"
        ),
    ))

    # Recency: failed today -> 1.0, 30 days ago -> 0.0
    if factors.days_since_last is None:
        recency_norm = 0.0
        recency_explanation = "Never failed"
    else:
        recency_norm = max(1.0 - (factors.days_since_last / window_days), 0.0)
        recency_explanation = (
            f"Failed {factors.days_since_last:.1f} days ago"
            if factors.days_since_last >= 1
            else f"Failed {int(factors.days_since_last * 24)} hours ago"
        )
    contributions.append(RiskScoreContribution(
        factor="Recency",
        raw_value=factors.days_since_last or 0.0,
        contribution=round(recency_norm * _WEIGHTS["recency"], 1),
        explanation=recency_explanation,
    ))

    score = sum(c.contribution for c in contributions)
    # Clamp to [0, 100] — defensive in case weights drift
    score = round(max(0.0, min(100.0, score)), 1)
    return score, contributions


def _sparkline(incidents: list[IncidentReport], window_days: int) -> list[int]:
    """One bucket per day, oldest first. Length = window_days."""
    now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = now - timedelta(days=window_days - 1)
    buckets = [0] * window_days
    for inc in incidents:
        idx = (inc.detected_at.date() - window_start.date()).days
        if 0 <= idx < window_days:
            buckets[idx] += 1
    return buckets


def _entity_to_incidents(window_days: int) -> dict[str, list[IncidentReport]]:
    """Group incidents by entity FQN within the lookback window."""
    cutoff = datetime.now(UTC) - timedelta(days=window_days)
    grouped: dict[str, list[IncidentReport]] = defaultdict(list)
    for inc in incident_store.list_all():
        if inc.detected_at >= cutoff:
            grouped[inc.affected_entity_fqn].append(inc)
    return grouped


def top_at_risk(limit: int = 10, window_days: int = 30) -> list[RiskScore]:
    """Return entities ranked by risk score. Excludes entities with score 0."""
    grouped = _entity_to_incidents(window_days)

    scored: list[RiskScore] = []
    for fqn, incs in grouped.items():
        factors = _compute_factors(incs, window_days)
        score, contribs = _score_from_factors(factors, window_days)
        if score <= 0:
            continue
        last_at = max(i.detected_at for i in incs) if incs else None
        scored.append(RiskScore(
            entity_fqn=fqn,
            score=score,
            rank=0,  # filled after sort
            factors=factors,
            contributions=contribs,
            last_incident_at=last_at,
            sparkline_30d=_sparkline(incs, window_days),
        ))

    scored.sort(key=lambda s: s.score, reverse=True)
    for i, s in enumerate(scored, start=1):
        s.rank = i
    return scored[:limit]


def explain_entity(entity_fqn: str, window_days: int = 30) -> RiskScore | None:
    """Return the full RiskScore for one entity, or None if it has no incidents."""
    cutoff = datetime.now(UTC) - timedelta(days=window_days)
    matches = [i for i in incident_store.list_all()
               if i.affected_entity_fqn == entity_fqn and i.detected_at >= cutoff]
    if not matches:
        return None
    factors = _compute_factors(matches, window_days)
    score, contribs = _score_from_factors(factors, window_days)
    last_at = max(i.detected_at for i in matches)
    return RiskScore(
        entity_fqn=entity_fqn,
        score=score,
        rank=0,
        factors=factors,
        contributions=contribs,
        last_incident_at=last_at,
        sparkline_30d=_sparkline(matches, window_days),
    )

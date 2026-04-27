"""Windowed KPI stats (total / open / MTTR / token spend) over the incident store."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel

from chronos.core import incident_store
from chronos.models.incident import IncidentReport, IncidentStatus

Range = Literal["24h", "7d", "30d", "all"]

_RANGE_TO_DELTA: dict[Range, timedelta | None] = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "all": None,
}


class StatsResponse(BaseModel):
    range: Range
    window_start: datetime | None      # None when range == "all"
    window_end: datetime
    total: int
    open: int
    acknowledged: int
    resolved: int
    avg_duration_ms: float | None      # None when no incidents have a duration
    avg_confidence: float | None
    total_tokens: int
    by_category: dict[str, int]
    by_severity: dict[str, int]


def _filter_by_window(incidents: list[IncidentReport], start: datetime | None) -> list[IncidentReport]:
    if start is None:
        return incidents
    return [i for i in incidents if i.detected_at >= start]


def compute_stats(range: Range = "24h") -> StatsResponse:
    """Compute aggregated KPIs across the in-process incident store.

    The window is half-open: ``window_start <= detected_at <= window_end``.
    """
    delta = _RANGE_TO_DELTA[range]
    end = datetime.now(UTC)
    start = (end - delta) if delta else None

    incidents = _filter_by_window(incident_store.list_all(), start)

    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    durations: list[int] = []
    confidences: list[float] = []
    tokens = 0
    open_n = ack_n = res_n = 0

    for inc in incidents:
        cat = inc.root_cause_category.value
        sev = inc.business_impact.value
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

        if inc.investigation_duration_ms is not None:
            durations.append(inc.investigation_duration_ms)
        confidences.append(inc.confidence)
        tokens += inc.total_llm_tokens

        if inc.status == IncidentStatus.OPEN:
            open_n += 1
        elif inc.status == IncidentStatus.ACKNOWLEDGED:
            ack_n += 1
        elif inc.status == IncidentStatus.RESOLVED:
            res_n += 1

    avg_duration = round(sum(durations) / len(durations), 1) if durations else None
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else None

    return StatsResponse(
        range=range,
        window_start=start,
        window_end=end,
        total=len(incidents),
        open=open_n,
        acknowledged=ack_n,
        resolved=res_n,
        avg_duration_ms=avg_duration,
        avg_confidence=avg_confidence,
        total_tokens=tokens,
        by_category=by_category,
        by_severity=by_severity,
    )

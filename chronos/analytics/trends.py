"""Time-bucketed trend series + per-category distribution for the dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel

from chronos.analytics.stats import _RANGE_TO_DELTA, Range, _filter_by_window
from chronos.core import incident_store

Bucket = Literal["hour", "day"]

_BUCKET_TO_DELTA: dict[Bucket, timedelta] = {
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
}


class TrendBucket(BaseModel):
    ts: datetime           # bucket start (UTC)
    total: int
    by_category: dict[str, int]


class TrendsResponse(BaseModel):
    range: Range
    bucket: Bucket
    window_start: datetime | None
    window_end: datetime
    series: list[TrendBucket]


class ByCategoryResponse(BaseModel):
    range: Range
    window_start: datetime | None
    window_end: datetime
    counts: dict[str, int]
    total: int


def _bucket_floor(ts: datetime, bucket: Bucket) -> datetime:
    """Floor a timestamp to the start of its bucket (UTC)."""
    if bucket == "day":
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    # hour
    return ts.replace(minute=0, second=0, microsecond=0)


def compute_trends(range: Range = "7d", bucket: Bucket = "day") -> TrendsResponse:
    """Return the count of incidents per ``bucket``, broken down by root cause category."""
    end = datetime.now(UTC)
    delta = _RANGE_TO_DELTA[range]
    start = (end - delta) if delta else None

    incidents = _filter_by_window(incident_store.list_all(), start)

    # Group: bucket_start_ts → category → count
    grouped: dict[datetime, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for inc in incidents:
        bts = _bucket_floor(inc.detected_at, bucket)
        cat = inc.root_cause_category.value
        grouped[bts][cat] += 1

    # Fill empty buckets so the chart x-axis is contiguous
    series: list[TrendBucket] = []
    if start:
        cursor = _bucket_floor(start, bucket)
        bucket_delta = _BUCKET_TO_DELTA[bucket]
        while cursor <= end:
            cats = grouped.get(cursor, {})
            series.append(TrendBucket(
                ts=cursor,
                total=sum(cats.values()),
                by_category=dict(cats),
            ))
            cursor += bucket_delta
    else:
        # ``all`` range — just sort what we have
        for bts in sorted(grouped.keys()):
            cats = grouped[bts]
            series.append(TrendBucket(
                ts=bts,
                total=sum(cats.values()),
                by_category=dict(cats),
            ))

    return TrendsResponse(
        range=range,
        bucket=bucket,
        window_start=start,
        window_end=end,
        series=series,
    )


def compute_by_category(range: Range = "7d") -> ByCategoryResponse:
    """Total incidents per root cause category for the donut chart."""
    end = datetime.now(UTC)
    delta = _RANGE_TO_DELTA[range]
    start = (end - delta) if delta else None

    incidents = _filter_by_window(incident_store.list_all(), start)

    counts: dict[str, int] = {}
    for inc in incidents:
        cat = inc.root_cause_category.value
        counts[cat] = counts.get(cat, 0) + 1

    return ByCategoryResponse(
        range=range,
        window_start=start,
        window_end=end,
        counts=counts,
        total=len(incidents),
    )

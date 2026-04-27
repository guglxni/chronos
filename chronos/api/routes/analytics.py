"""Dashboard analytics endpoints — windowed stats, trends, by-category."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from chronos.analytics import compute_by_category, compute_stats, compute_trends
from chronos.analytics.stats import StatsResponse
from chronos.analytics.trends import Bucket, ByCategoryResponse, TrendsResponse

router = APIRouter(prefix="/api/v1/incidents", tags=["dashboard"])


@router.get("/stats", response_model=StatsResponse, summary="Windowed KPI stats")
async def get_windowed_stats(
    range: Literal["24h", "7d", "30d", "all"] = Query("24h"),
) -> StatsResponse:
    """Return aggregated KPIs over the configured time window."""
    return compute_stats(range=range)


@router.get("/trends", response_model=TrendsResponse, summary="Time-bucketed incident counts")
async def get_trends(
    range: Literal["24h", "7d", "30d", "all"] = Query("7d"),
    bucket: Bucket = Query("day"),
) -> TrendsResponse:
    """Return time-series buckets of incident counts split by root cause category."""
    return compute_trends(range=range, bucket=bucket)


@router.get("/by-category", response_model=ByCategoryResponse, summary="Counts per root cause")
async def get_by_category(
    range: Literal["24h", "7d", "30d", "all"] = Query("7d"),
) -> ByCategoryResponse:
    """Return counts of incidents grouped by root cause category for the donut chart."""
    return compute_by_category(range=range)

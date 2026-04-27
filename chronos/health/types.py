"""Health probe types — pure data classes shared by probes, aggregator, API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ComponentState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    NOT_CONFIGURED = "not_configured"


class ComponentStatus(BaseModel):
    """Single backing service's current state — serialized to JSON in the API."""

    name: str = Field(..., description="Stable identifier: openmetadata|falkordb|litellm|slack")
    state: ComponentState
    latency_ms: float | None = Field(
        default=None,
        description="Round-trip latency for the probe call. None when not_configured/down on connect.",
    )
    detail: str | None = Field(
        default=None,
        description="Human-readable note (sanitized — never contains secrets or full URLs).",
    )
    last_checked: datetime
    required: bool = Field(
        default=True,
        description="When False, a down state degrades overall but does not mark down.",
    )


class OverallHealth(BaseModel):
    overall: Literal["healthy", "degraded", "down"]
    components: list[ComponentStatus]
    cached_at: datetime

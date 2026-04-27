"""
Component health probing for CHRONOS backing services.

Exposes a small async API that the FastAPI route layer uses to surface
per-service status (OpenMetadata, FalkorDB, LiteLLM, Slack) to operators
and to a UI status indicator.

The aggregator caches results for 30 seconds so the endpoint is cheap to
poll from a navbar status badge without hammering external services.
"""

from chronos.health.aggregator import (
    aggregate_overall_state,
    get_component_health,
    invalidate_cache,
)
from chronos.health.types import ComponentState, ComponentStatus, OverallHealth

__all__ = [
    "ComponentState",
    "ComponentStatus",
    "OverallHealth",
    "aggregate_overall_state",
    "get_component_health",
    "invalidate_cache",
]

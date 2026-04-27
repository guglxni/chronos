"""
30-second cache + overall-state rollup for component probes.

The frontend status badge polls every 60s, so a 30s server-side cache
means at most one real probe per minute per service even with multiple
clients connected.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Literal

from chronos.health.probes import run_all_probes
from chronos.health.types import ComponentState, ComponentStatus, OverallHealth

_CACHE_TTL_SECONDS = 30.0

_lock = asyncio.Lock()
_cached_at: float = 0.0
_cached_result: OverallHealth | None = None


def aggregate_overall_state(components: list[ComponentStatus]) -> Literal["healthy", "degraded", "down"]:
    """
    Roll up per-component state into a single overall flag.

    Rules (most severe wins):
      * Any required component DOWN  → overall DOWN
      * Any required component DEGRADED, or optional DOWN → overall DEGRADED
      * Otherwise → overall HEALTHY

    NOT_CONFIGURED is treated as benign (intentional configuration choice).
    """
    has_required_down = False
    has_degradation = False

    for c in components:
        if c.required:
            if c.state == ComponentState.DOWN:
                has_required_down = True
            elif c.state == ComponentState.DEGRADED:
                has_degradation = True
        else:
            if c.state == ComponentState.DOWN:
                has_degradation = True

    if has_required_down:
        return "down"
    if has_degradation:
        return "degraded"
    return "healthy"


def invalidate_cache() -> None:
    """Force the next ``get_component_health`` call to re-probe."""
    global _cached_at, _cached_result
    _cached_at = 0.0
    _cached_result = None


async def get_component_health(*, force: bool = False) -> OverallHealth:
    """
    Return cached or fresh component health.

    The lock prevents thundering-herd re-probing when many clients arrive
    after cache expiry — only one probe round-trip per refresh window.
    """
    global _cached_at, _cached_result

    now = time.monotonic()
    if not force and _cached_result is not None and (now - _cached_at) < _CACHE_TTL_SECONDS:
        return _cached_result

    async with _lock:
        # Double-check inside the lock — another waiter may have refreshed.
        now = time.monotonic()
        if not force and _cached_result is not None and (now - _cached_at) < _CACHE_TTL_SECONDS:
            return _cached_result

        components = await run_all_probes()
        overall = aggregate_overall_state(components)
        result = OverallHealth(
            overall=overall,
            components=components,
            cached_at=datetime.now(UTC),
        )
        _cached_result = result
        _cached_at = time.monotonic()
        return result

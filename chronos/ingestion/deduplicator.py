"""
In-memory event deduplicator with a sliding TTL window.

Prevents the same entity+event combination from spawning multiple investigations
within the dedup window (default: 300 seconds).
"""

from __future__ import annotations

import time

from chronos.config.settings import settings


class EventDeduplicator:
    """
    Thread-safe-ish (single-process async) deduplicator backed by a plain dict.

    The cleanup pass runs on every ``is_duplicate`` call to keep memory bounded.
    For multi-process deployments, replace with a Redis-backed implementation.
    """

    def __init__(self) -> None:
        self._seen: dict[str, float] = {}

    def is_duplicate(self, event_key: str) -> bool:
        """
        Return True if ``event_key`` was already seen within the dedup window.
        Records the key if it is new.
        """
        now = time.time()
        self._cleanup(now)
        if event_key in self._seen:
            return True
        self._seen[event_key] = now
        return False

    def _cleanup(self, now: float) -> None:
        """Remove entries older than the dedup window."""
        window = settings.investigation_dedup_window_seconds
        self._seen = {k: v for k, v in self._seen.items() if now - v < window}

    def reset(self) -> None:
        """Clear all seen events (useful for testing)."""
        self._seen.clear()


# Module-level singleton used by the ingestion layer
deduplicator = EventDeduplicator()

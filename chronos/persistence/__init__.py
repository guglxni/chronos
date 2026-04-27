"""
Durable persistence for the in-memory incident store.

Backed by FalkorDB (separate ``chronos_incidents`` graph from the
Graphiti episodes graph). Public API is async, non-blocking, and
no-ops gracefully when FalkorDB is not configured.

See ``aidlc-docs/units/U-12_falkor_persistence.md``.
"""

from chronos.persistence.falkor_store import (
    delete,
    hydrate,
    is_configured,
    list_recent,
    persist,
)

__all__ = ["delete", "hydrate", "is_configured", "list_recent", "persist"]

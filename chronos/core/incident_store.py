"""
In-memory incident store — a single source of truth for all completed investigations.

Extracted from ``api/routes/incidents.py`` so that:
1. The investigation runner (``core/investigation_runner.py``) can store reports
   without importing from the ``api`` layer — eliminating the circular import.
2. Route handlers remain thin HTTP adapters that delegate to this store.

In production this would be backed by PostgreSQL or DynamoDB; for the hackathon
the in-memory dict is sufficient and the interface is identical regardless of
backend choice.

Concurrency: ``store()`` and ``update_field()`` perform a read-modify-write on
``_incidents`` (check cap → pop oldest → insert).  Two concurrent calls at cap
could both observe ``len > cap``, both call ``next(iter)`` on the same key, and
one would ``KeyError`` on the second ``del``.  ``_write_lock`` serialises all
mutations to make eviction deterministic.  Reads (``get`` / ``list_all``) remain
lock-free because dict reads are atomic under CPython's GIL.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from weakref import WeakSet

from chronos.models.incident import IncidentReport

logger = logging.getLogger("chronos.core.store")

# Track in-flight FalkorDB persistence tasks so we can:
#   1. Bound concurrent writes (cap at _MAX_PENDING_PERSISTS)
#   2. Optionally await them in tests for determinism
_pending_persists: WeakSet[asyncio.Task] = WeakSet()
_MAX_PENDING_PERSISTS = 100


def _schedule_persist(report: IncidentReport) -> None:
    """Fire-and-forget background write to FalkorDB.

    Imports inside the function to avoid a circular import — persistence
    must not import the store back (it doesn't, but keeping defensive).
    Also tolerates being called outside an async context (tests, scripts):
    when there's no running loop, persistence is silently skipped — the
    in-memory store still has the record.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Sync caller (test, CLI script) — no loop to schedule on. Skip.
        return

    if len(_pending_persists) >= _MAX_PENDING_PERSISTS:
        logger.debug("Persist backpressure: %d pending — dropping oldest", len(_pending_persists))
        # WeakSet iteration order isn't guaranteed; this is a best-effort drop.
        try:
            next(iter(_pending_persists)).cancel()
        except Exception:
            pass

    from chronos.persistence import falkor_store

    task = loop.create_task(falkor_store.persist(report), name=f"persist-{report.incident_id}")
    _pending_persists.add(task)

# Keyed by incident_id string.  All mutations go through store() to ensure
# the store always holds validated IncidentReport instances — never raw dicts.
_incidents: dict[str, IncidentReport] = {}

# Cap the in-memory store to prevent unbounded growth on long-running servers.
# Oldest incidents are evicted when the limit is exceeded.
_MAX_STORE_SIZE = 1_000

# Serialises read-modify-write on _incidents.  We use a threading.Lock rather
# than asyncio.Lock because the store is called from both async contexts
# (investigation_runner) and sync contexts (tests, startup seeding).  Python's
# threading.Lock is safe to acquire inside a coroutine when the critical section
# is a few O(1) dict operations.
_write_lock = threading.Lock()


def store(report: IncidentReport | dict) -> None:
    """
    Persist a completed incident report.

    Accepts either a typed ``IncidentReport`` or a raw dict (for backward
    compatibility with callers that produce a dict from LangGraph state).
    Validates and converts dicts so the store is always type-safe.
    """
    if isinstance(report, dict):
        # Validate on ingestion — surfaces schema mismatches immediately
        # rather than silently storing a partial dict that breaks later reads.
        report = IncidentReport.model_validate(report)
    with _write_lock:
        _incidents[report.incident_id] = report
        # Evict in a loop so the store tolerates being briefly over-cap by
        # multiple entries (e.g. if _MAX_STORE_SIZE is lowered at runtime).
        while len(_incidents) > _MAX_STORE_SIZE:
            oldest_key = next(iter(_incidents))
            # popitem+reinsert avoids KeyError if the iter key was racily deleted.
            _incidents.pop(oldest_key, None)
            logger.debug("Evicted oldest incident %s (store at cap)", oldest_key)
    logger.info("Stored incident %s", report.incident_id)
    # Durable write to FalkorDB so the incident survives dyno restarts.
    # Backgrounded so the request-handling thread doesn't wait on the
    # network round-trip — the in-memory store is the read source of truth.
    _schedule_persist(report)


__all__ = ["get", "get_or_raise", "list_all", "store", "update_field"]


def get(incident_id: str) -> IncidentReport | None:
    """Return the incident or None if not found."""
    return _incidents.get(incident_id)


def get_or_raise(incident_id: str) -> IncidentReport:
    """
    Return the incident or raise ``KeyError``.

    Route handlers should catch this and convert to HTTP 404.
    """
    try:
        return _incidents[incident_id]
    except KeyError:
        raise KeyError(f"Incident {incident_id!r} not found") from None


def list_all() -> list[IncidentReport]:
    """Return all stored incidents (insertion order preserved — Python 3.7+)."""
    return list(_incidents.values())


def update_field(incident_id: str, **kwargs: object) -> IncidentReport:
    """
    Update one or more fields on an existing incident (e.g. status, resolved_by).

    Returns the updated report.  Raises ``KeyError`` if incident_id is unknown.
    Serialised via ``_write_lock`` so a concurrent ``store()`` eviction cannot
    resurrect or overwrite the updated record.
    """
    with _write_lock:
        report = _incidents.get(incident_id)
        if report is None:
            raise KeyError(f"Incident {incident_id!r} not found")
        updated = report.model_copy(update=kwargs)
        _incidents[incident_id] = updated
    # Persist the update so acks/resolves survive a dyno restart.
    _schedule_persist(updated)
    return updated

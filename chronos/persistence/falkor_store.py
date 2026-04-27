"""
FalkorDB persistence for IncidentReports — write-on-store + hydrate-on-startup.

The FalkorDB Python client is sync; we wrap every call in ``asyncio.to_thread``
so the event loop is never blocked by network round-trips.

Graceful degradation: when FALKORDB_HOST is the local default (no real config)
every public function returns immediately without raising, and the in-memory
store keeps working.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from chronos.config.settings import secret_or_none, settings
from chronos.models.incident import IncidentReport
from chronos.persistence._cypher import (
    DELETE,
    GRAPH_NAME,
    HYDRATE,
    INDEXES,
    LIST_RECENT,
    PERSIST,
)

logger = logging.getLogger("chronos.persistence.falkor")

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "falkordb"})

# Cap the JSON payload so a single rich incident with 100s of evidence items
# can't blow up the row size. 256KB is plenty for any realistic report.
_MAX_PAYLOAD_BYTES = 256 * 1024

# Module-level handles so we connect once.
_db: Any = None
_graph: Any = None
_lock = asyncio.Lock()


def is_configured() -> bool:
    """True only when a non-local FalkorDB host is set."""
    return settings.falkordb_host not in _LOCAL_HOSTS


async def _get_graph() -> Any | None:
    """Lazy-init the FalkorDB client + graph handle. None when not configured."""
    global _db, _graph
    if not is_configured():
        return None
    if _graph is not None:
        return _graph

    async with _lock:
        if _graph is not None:
            return _graph

        def _init() -> Any:
            from falkordb import FalkorDB
            db = FalkorDB(
                host=settings.falkordb_host,
                port=settings.falkordb_port,
                username=settings.falkordb_username or None,
                password=secret_or_none(settings.falkordb_password),
                ssl=settings.falkordb_tls,
                ssl_cert_reqs="none" if settings.falkordb_tls else None,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            graph = db.select_graph(GRAPH_NAME)
            # Best-effort index creation. FalkorDB tolerates "already exists".
            for stmt in INDEXES:
                try:
                    graph.query(stmt)
                except Exception as exc:
                    logger.debug("Index stmt skipped (likely already exists): %s", exc)
            return db, graph

        try:
            db, graph = await asyncio.to_thread(_init)
            _db = db
            _graph = graph
            logger.info("FalkorDB persistence connected to graph %s", GRAPH_NAME)
            return _graph
        except Exception as exc:
            logger.warning("FalkorDB init failed (persistence disabled): %s", exc)
            return None


def _report_to_params(report: IncidentReport) -> dict[str, Any]:
    """Map an IncidentReport to a Cypher parameter dict."""
    payload = report.model_dump_json()
    if len(payload.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        # Truncate evidence_chain — usually the largest variable-size field.
        truncated = report.model_copy(update={"evidence_chain": report.evidence_chain[:5]})
        payload = truncated.model_dump_json()
        if len(payload.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
            # Last resort: drop downstream + timeline too
            truncated = truncated.model_copy(update={
                "affected_downstream": [],
                "investigation_timeline": [],
            })
            payload = truncated.model_dump_json()

    return {
        "incident_id": report.incident_id,
        "detected_at": int(report.detected_at.timestamp() * 1000),
        "resolved_at": int(report.resolved_at.timestamp() * 1000) if report.resolved_at else None,
        "affected_entity_fqn": report.affected_entity_fqn,
        "root_cause_category": report.root_cause_category.value,
        "business_impact": report.business_impact.value,
        "status": report.status.value,
        "confidence": float(report.confidence),
        "investigation_duration_ms": int(report.investigation_duration_ms or 0),
        "total_llm_tokens": int(report.total_llm_tokens),
        "payload": payload,
    }


async def persist(report: IncidentReport) -> bool:
    """Write or update an IncidentReport in FalkorDB. Returns True on success."""
    graph = await _get_graph()
    if graph is None:
        return False

    params = _report_to_params(report)

    def _do() -> bool:
        try:
            graph.query(PERSIST, params=params)
            return True
        except Exception as exc:
            logger.warning("FalkorDB persist failed for %s: %s", report.incident_id, exc)
            return False

    return await asyncio.to_thread(_do)


async def hydrate(limit: int = 1000) -> list[IncidentReport]:
    """Reconstruct IncidentReports from FalkorDB, newest first. Empty when not configured."""
    graph = await _get_graph()
    if graph is None:
        return []

    def _do() -> list[IncidentReport]:
        try:
            result = graph.query(HYDRATE, params={"limit": limit})
        except Exception as exc:
            logger.warning("FalkorDB hydrate query failed: %s", exc)
            return []

        out: list[IncidentReport] = []
        for row in (result.result_set or []):
            payload = row[1] if len(row) > 1 else None
            if not payload:
                continue
            try:
                data = json.loads(payload)
                out.append(IncidentReport.model_validate(data))
            except Exception as exc:
                # Schema drift or corrupt row — log and skip rather than crash.
                logger.warning("Skipping unhydratable incident: %s", exc)
        return out

    return await asyncio.to_thread(_do)


async def list_recent(limit: int = 50) -> list[IncidentReport]:
    """Same shape as hydrate(), kept separate for future divergence (filters etc)."""
    graph = await _get_graph()
    if graph is None:
        return []

    def _do() -> list[IncidentReport]:
        try:
            result = graph.query(LIST_RECENT, params={"limit": limit})
        except Exception as exc:
            logger.warning("FalkorDB list_recent failed: %s", exc)
            return []
        out: list[IncidentReport] = []
        for row in (result.result_set or []):
            payload = row[1] if len(row) > 1 else None
            if not payload:
                continue
            try:
                out.append(IncidentReport.model_validate(json.loads(payload)))
            except Exception:
                continue
        return out

    return await asyncio.to_thread(_do)


async def delete(incident_id: str) -> bool:
    """Remove a single incident from FalkorDB. Returns True if a row was deleted."""
    graph = await _get_graph()
    if graph is None:
        return False

    def _do() -> bool:
        try:
            result = graph.query(DELETE, params={"incident_id": incident_id})
            rows = result.result_set or []
            return bool(rows and rows[0] and rows[0][0])
        except Exception as exc:
            logger.warning("FalkorDB delete failed for %s: %s", incident_id, exc)
            return False

    return await asyncio.to_thread(_do)

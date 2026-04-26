"""
Investigation orchestration runner.

This is the single place that knows how to:
  1. Build the initial LangGraph state dict from an ``InvestigationTrigger``
  2. Acquire the compiled investigation graph (lazily, on first use)
  3. Invoke the graph, persist the result, and optionally publish SSE events

Route modules (``api/routes/webhooks.py``, ``api/routes/investigations.py``)
import *from* this module at the top level — no inline deferred imports needed —
because this module does **not** import from the ``api`` layer.

The graph itself (``agent/graph.py``) is only compiled on the first call to
``_get_graph()``, not at module import time.  This keeps startup fast and lets
the test suite import ``chronos.api`` without triggering LangGraph compilation.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import ValidationError

from chronos.agent.graph import get_investigation_graph, get_langfuse_callback
from chronos.config.settings import settings
from chronos.core.incident_store import store as store_incident
from chronos.models.events import InvestigationTrigger
from chronos.models.incident import (
    IncidentReport,
    IncidentStatus,
    RootCauseCategory,
)

logger = logging.getLogger("chronos.core.runner")

# ── Lazy graph cache ───────────────────────────────────────────────────────────
_graph_cache = None
_callback_factory_cache: Callable | None = None


def _get_graph() -> tuple[Any, Callable | None]:
    """
    Return the compiled investigation graph and Langfuse callback factory.

    Imports happen here (not at module level) so that importing
    ``chronos.core.investigation_runner`` does *not* trigger LangGraph
    compilation — a relatively expensive one-time operation.
    """
    global _graph_cache, _callback_factory_cache
    if _graph_cache is None:
        _graph_cache = get_investigation_graph()
        _callback_factory_cache = get_langfuse_callback
    return _graph_cache, _callback_factory_cache


# ── Public API ─────────────────────────────────────────────────────────────────

async def run_investigation(
    trigger: InvestigationTrigger,
    incident_id: str | None = None,
    sse_queue: asyncio.Queue | None = None,
) -> str:
    """
    Run the full 10-step CHRONOS investigation pipeline.

    Args:
        trigger: The event that caused this investigation.
        incident_id: Optional caller-provided ID; one is generated if absent.
        sse_queue: If provided, step events are published here for SSE streaming.
                   A ``None`` sentinel is pushed when the investigation ends.

    Returns:
        The incident_id (generated or provided).

    Raises:
        asyncio.CancelledError: Re-raised so the event loop can clean up
            properly — NEVER swallowed in background tasks.
    """
    graph, cb_factory = _get_graph()
    incident_id = incident_id or str(uuid.uuid4())

    investigation_start: datetime = datetime.now(tz=UTC)
    initial_state: dict[str, Any] = {
        "incident_id": incident_id,
        "triggered_at": trigger.timestamp,
        "entity_fqn": trigger.entity_fqn,
        "test_name": trigger.test_name,
        "failure_message": trigger.failure_message,
        "step_results": [],
        "investigation_start": investigation_start,
        "state_schema_version": 1,
    }

    callbacks = []
    if cb_factory is not None:
        cb = cb_factory(incident_id)
        if cb:
            callbacks.append(cb)
    config = {"callbacks": callbacks} if callbacks else {}

    logger.info(
        "Starting investigation %s for entity '%s'", incident_id, trigger.entity_fqn
    )

    # Publish a placeholder so the frontend can show INVESTIGATING status
    # immediately rather than waiting for the full 10-step pipeline.
    placeholder = IncidentReport(
        incident_id=incident_id,
        detected_at=trigger.timestamp,
        affected_entity_fqn=trigger.entity_fqn,
        test_name=trigger.test_name,
        failure_message=trigger.failure_message,
        probable_root_cause="Investigation in progress…",
        root_cause_category=RootCauseCategory.UNKNOWN,
        confidence=0.0,
        status=IncidentStatus.INVESTIGATING,
    )
    store_incident(placeholder)

    try:
        result = await asyncio.wait_for(
            graph.ainvoke(initial_state, config=config),
            timeout=settings.investigation_timeout_seconds,
        )

        elapsed_ms = int(
            (datetime.now(tz=UTC) - investigation_start).total_seconds() * 1000
        )

        report_data = result.get("incident_report")
        if report_data:
            report = IncidentReport.model_validate(report_data)
            report = report.model_copy(update={"investigation_duration_ms": elapsed_ms})
            store_incident(report)
            logger.info(
                "Investigation %s complete — category=%s, confidence=%s, duration_ms=%d",
                incident_id,
                report.root_cause_category.value,
                report.confidence,
                elapsed_ms,
            )

            if sse_queue is not None:
                with contextlib.suppress(asyncio.QueueFull):
                    sse_queue.put_nowait(
                        {
                            "status": "investigation_complete",
                            "incident_id": incident_id,
                            "root_cause_category": report.root_cause_category.value,
                            "confidence": report.confidence,
                        }
                    )

    except asyncio.CancelledError:
        # CRITICAL: always re-raise CancelledError so the event loop can
        # properly cancel the task.  Swallowing it causes resource leaks.
        logger.warning("Investigation %s cancelled", incident_id)
        raise
    except TimeoutError as exc:
        logger.error(
            "Investigation %s timed out after %ds",
            incident_id,
            settings.investigation_timeout_seconds,
        )
        elapsed_ms = int(
            (datetime.now(tz=UTC) - investigation_start).total_seconds() * 1000
        )
        error_report = placeholder.model_copy(
            update={
                "probable_root_cause": f"Investigation timed out after {settings.investigation_timeout_seconds}s",
                "status": IncidentStatus.OPEN,
                "investigation_completed_at": datetime.now(tz=UTC),
                "investigation_duration_ms": elapsed_ms,
            }
        )
        store_incident(error_report)
        if sse_queue is not None:
            with contextlib.suppress(asyncio.QueueFull):
                sse_queue.put_nowait(
                    {"status": "error", "incident_id": incident_id, "error": str(exc)}
                )
    except (httpx.HTTPError, RuntimeError, ValueError, KeyError, ValidationError) as exc:
        logger.error(
            "Investigation %s failed (%s): %s",
            incident_id,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        # Transition the placeholder to a terminal error state so the UI /
        # dashboard don't show it forever as "Investigation in progress…".
        # Without this, any webhook that triggers a handler exception leaves an
        # orphan INVESTIGATING placeholder until FIFO eviction catches up.
        elapsed_ms = int(
            (datetime.now(tz=UTC) - investigation_start).total_seconds() * 1000
        )
        error_report = placeholder.model_copy(
            update={
                "probable_root_cause": f"Investigation failed ({type(exc).__name__})",
                "status": IncidentStatus.OPEN,
                "investigation_completed_at": datetime.now(tz=UTC),
                "investigation_duration_ms": elapsed_ms,
            }
        )
        store_incident(error_report)
        if sse_queue is not None:
            with contextlib.suppress(asyncio.QueueFull):
                sse_queue.put_nowait(
                    {"status": "error", "incident_id": incident_id, "error": str(exc)}
                )
    finally:
        if sse_queue is not None:
            # Non-blocking sentinel — put_nowait never suspends, so it cannot
            # mask a CancelledError or deadlock on a full queue.
            with contextlib.suppress(asyncio.QueueFull):
                sse_queue.put_nowait(None)

    return incident_id

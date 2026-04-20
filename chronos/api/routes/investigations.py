"""
Manual investigation trigger and SSE streaming endpoints.

Allows external systems and the frontend to:
  1. Manually trigger an investigation (POST /api/v1/investigate)
  2. Stream its progress in real-time via SSE (GET /api/v1/investigations/{id}/stream)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from chronos.models.events import InvestigationTrigger

router = APIRouter(prefix="/api/v1", tags=["investigations"])
logger = logging.getLogger("chronos.investigations")

# SSE event queues keyed by incident_id
# A None sentinel signals stream completion to the consumer.
_sse_queues: dict[str, asyncio.Queue] = {}

_SSE_HEARTBEAT_INTERVAL = 25.0  # seconds


@router.post("/investigate")
async def trigger_investigation(trigger: InvestigationTrigger):
    """
    Manually trigger a CHRONOS investigation.

    Returns immediately with an incident_id and SSE stream URL.
    The investigation runs asynchronously in the background.
    """
    from chronos.api.routes.webhooks import _run_investigation

    incident_id = str(uuid.uuid4())

    # Pre-create an SSE queue so clients can connect before the task starts
    _sse_queues[incident_id] = asyncio.Queue()

    asyncio.create_task(
        _run_investigation_with_sse(trigger, incident_id)
    )

    return {
        "status": "triggered",
        "incident_id": incident_id,
        "entity_fqn": trigger.entity_fqn,
        "stream_url": f"/api/v1/investigations/{incident_id}/stream",
    }


@router.get("/investigations/{incident_id}/stream")
async def stream_investigation(incident_id: str):
    """
    Stream investigation progress via Server-Sent Events.

    Events have a ``data`` field containing a JSON object with at minimum:
    - ``status``: 'connected' | 'step_complete' | 'complete' | 'error' | 'heartbeat'
    - ``incident_id``: the investigation ID
    """
    queue = _sse_queues.get(incident_id)
    if queue is None:
        # Client connected after investigation already finished or ID unknown
        queue = asyncio.Queue()
        _sse_queues[incident_id] = queue

    async def event_generator():
        # Initial connection acknowledgement
        yield {
            "event": "connected",
            "data": json.dumps(
                {"status": "connected", "incident_id": incident_id}
            ),
        }

        while True:
            try:
                event = await asyncio.wait_for(
                    queue.get(), timeout=_SSE_HEARTBEAT_INTERVAL
                )
                if event is None:
                    # Sentinel — investigation complete
                    yield {
                        "event": "complete",
                        "data": json.dumps(
                            {"status": "complete", "incident_id": incident_id}
                        ),
                    }
                    break
                yield {"event": "update", "data": json.dumps(event)}
            except asyncio.TimeoutError:
                # Heartbeat to keep the connection alive
                yield {
                    "event": "heartbeat",
                    "data": json.dumps(
                        {"status": "heartbeat", "incident_id": incident_id}
                    ),
                }

    return EventSourceResponse(event_generator())


async def _run_investigation_with_sse(
    trigger: InvestigationTrigger,
    incident_id: str,
) -> None:
    """
    Run investigation and push step progress events to the SSE queue.
    """
    from chronos.agent.graph import get_langfuse_callback, investigation_graph

    queue = _sse_queues.get(incident_id, asyncio.Queue())

    initial_state = {
        "incident_id": incident_id,
        "triggered_at": trigger.timestamp,
        "entity_fqn": trigger.entity_fqn,
        "test_name": trigger.test_name,
        "failure_message": trigger.failure_message,
        "step_results": [],
        "investigation_start": datetime.utcnow(),
    }

    callbacks = []
    langfuse_cb = get_langfuse_callback(incident_id)
    if langfuse_cb:
        callbacks.append(langfuse_cb)

    config = {"callbacks": callbacks} if callbacks else {}

    try:
        result = await investigation_graph.ainvoke(initial_state, config=config)

        # Store completed incident
        from chronos.api.routes.incidents import store_incident

        incident_report = result.get("incident_report")
        if incident_report:
            store_incident(incident_report)

        # Push final report to SSE stream
        await queue.put(
            {
                "status": "investigation_complete",
                "incident_id": incident_id,
                "root_cause_category": incident_report.get("root_cause_category") if incident_report else None,
                "confidence": incident_report.get("confidence") if incident_report else None,
            }
        )

        logger.info(f"Investigation {incident_id} complete (SSE)")
    except Exception as exc:
        logger.error(f"Investigation {incident_id} failed: {exc}", exc_info=True)
        await queue.put(
            {"status": "error", "incident_id": incident_id, "error": str(exc)}
        )
    finally:
        # Push sentinel to close SSE stream
        await queue.put(None)

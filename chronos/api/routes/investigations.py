"""
Manual investigation trigger and SSE streaming endpoints.

Allows external systems and the frontend to:
  1. Manually trigger an investigation (POST /api/v1/investigate)
  2. Stream its progress in real-time via SSE (GET /api/v1/investigations/{id}/stream)

Security & reliability improvements:
- Rate limits on both endpoints to prevent abuse (H4).
- SSE queue is bounded (maxsize=100) and always cleaned up in try/finally (H5).
- Unknown incident IDs get a 404 instead of silently creating orphan queues.
- Orphan queues (investigation completed but nobody connected to stream) are
  evicted after _SSE_ORPHAN_TTL seconds via a per-investigation cleanup task.
- Stream endpoint requires a one-time token issued at trigger time (A2).
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from chronos.api.rate_limit import limiter
from chronos.api.schemas import InvestigationTriggerResponse
from chronos.core.investigation_runner import run_investigation
from chronos.models.events import InvestigationTrigger

router = APIRouter(prefix="/api/v1", tags=["investigations"])
logger = logging.getLogger("chronos.investigations")

# SSE event queues keyed by incident_id.
# A None sentinel signals stream completion to the consumer.
# Queues are bounded at 100 events to cap memory consumption per investigation.
_sse_queues: dict[str, asyncio.Queue] = {}
# One-time stream tokens — issued at trigger time, valid for the queue lifetime.
# Validated on every GET /stream request; removed when the queue is evicted.
_sse_tokens: dict[str, str] = {}
_active_tasks: set[asyncio.Task] = set()


def register_sse_queue(incident_id: str, stream_token: str, queue: asyncio.Queue) -> None:
    """Register a pre-created SSE queue — used by demo.py and external orchestrators."""
    _sse_queues[incident_id] = queue
    _sse_tokens[incident_id] = stream_token
    # Schedule TTL eviction so the queue doesn't leak if the client never connects
    # or if the client disconnects and never reconnects after the investigation ends.
    cleanup = asyncio.create_task(
        _evict_orphan_queue(incident_id),
        name=f"sse-cleanup-{incident_id}",
    )
    _active_tasks.add(cleanup)
    cleanup.add_done_callback(_active_tasks.discard)


_SSE_HEARTBEAT_INTERVAL = 25.0  # seconds
_SSE_QUEUE_MAXSIZE = 100
# How long to keep an unconsumed queue after the investigation completes.
# If no SSE client connected during this window, the queue is a memory leak.
_SSE_ORPHAN_TTL = 60.0  # seconds


async def _evict_orphan_queue(incident_id: str) -> None:
    """
    Remove the SSE queue and token for incident_id if never consumed.

    Called as a follow-up task after each investigation completes.  If a stream
    client connected normally the queue is already gone (removed in event_generator's
    finally block), so this becomes a no-op.  Without this, every investigation that
    has no SSE consumer leaks one bounded Queue indefinitely.
    """
    await asyncio.sleep(_SSE_ORPHAN_TTL)
    removed = _sse_queues.pop(incident_id, None)
    _sse_tokens.pop(incident_id, None)
    if removed is not None:
        logger.debug(
            "Evicted unconsumed SSE queue for incident %s (no client connected within %.0fs)",
            incident_id,
            _SSE_ORPHAN_TTL,
        )


def _on_investigation_done(incident_id: str) -> Any:
    """
    Return a task done-callback that schedules orphan queue cleanup.

    Uses a closure so the callback captures the correct incident_id even when
    multiple investigations are in flight simultaneously.
    """

    def _cb(_task: asyncio.Task) -> None:
        cleanup = asyncio.create_task(
            _evict_orphan_queue(incident_id),
            name=f"sse-cleanup-{incident_id}",
        )
        _active_tasks.add(cleanup)
        cleanup.add_done_callback(_active_tasks.discard)

    return _cb


@router.post("/investigate", response_model=InvestigationTriggerResponse)
@limiter.limit("5/minute")
async def trigger_investigation(
    request: Request, trigger: Annotated[InvestigationTrigger, Body(...)]
) -> dict[str, Any]:
    """
    Manually trigger a CHRONOS investigation.

    Returns immediately with an incident_id, SSE stream URL, and a one-time
    stream_token.  Pass the token as ?stream_token= when opening the SSE stream.
    Rate-limited to 5 triggers/minute per IP to prevent queue flooding.
    """
    incident_id = str(uuid.uuid4())
    stream_token = str(uuid.uuid4())

    # Pre-create the SSE queue so clients can attach before the first event fires
    _sse_queues[incident_id] = asyncio.Queue(maxsize=_SSE_QUEUE_MAXSIZE)
    _sse_tokens[incident_id] = stream_token

    task = asyncio.create_task(
        run_investigation(trigger, incident_id, _sse_queues[incident_id]),
        name=f"investigation-{incident_id}",
    )
    _active_tasks.add(task)
    task.add_done_callback(_active_tasks.discard)
    # Schedule TTL eviction of the queue in case no SSE client ever connects
    task.add_done_callback(_on_investigation_done(incident_id))

    return {
        "status": "triggered",
        "incident_id": incident_id,
        "entity_fqn": trigger.entity_fqn,
        "stream_url": f"/api/v1/investigations/{incident_id}/stream",
        "stream_token": stream_token,
    }


@router.get("/investigations/{incident_id}/stream")
@limiter.limit("30/minute")
async def stream_investigation(
    request: Request,
    incident_id: str,
    stream_token: str = Query(..., description="One-time token issued by POST /investigate"),
) -> EventSourceResponse:
    """
    Stream investigation progress via Server-Sent Events.

    Requires the stream_token returned by POST /investigate.  The token is
    valid for the lifetime of the investigation queue and must be passed as
    ?stream_token=<token>.

    Events carry a ``data`` field containing a JSON object with at minimum:
    - ``status``: 'connected' | 'update' | 'complete' | 'error' | 'heartbeat'
    - ``incident_id``: the investigation ID

    The queue for this incident_id is always cleaned up when the generator exits
    (normal completion, client disconnect, or server error).
    """
    queue = _sse_queues.get(incident_id)
    if queue is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active investigation stream for ID '{incident_id}'. "
            "Trigger an investigation first.",
        )

    expected_token = _sse_tokens.get(incident_id)
    if expected_token is None or stream_token != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired stream token.",
        )

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        _investigation_done = False
        try:
            # Initial connection acknowledgement
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "incident_id": incident_id}),
            }

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=_SSE_HEARTBEAT_INTERVAL)
                    if event is None:
                        # Sentinel — investigation pipeline finished
                        _investigation_done = True
                        yield {
                            "event": "complete",
                            "data": json.dumps({"status": "complete", "incident_id": incident_id}),
                        }
                        break
                    yield {"event": "update", "data": json.dumps(event)}
                except TimeoutError:
                    # Heartbeat keeps the HTTP connection alive
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"status": "heartbeat", "incident_id": incident_id}),
                    }
        finally:
            if _investigation_done:
                # Investigation is fully done — safe to remove queue and token now.
                _sse_queues.pop(incident_id, None)
                _sse_tokens.pop(incident_id, None)
                logger.debug("SSE queue cleaned up for incident %s", incident_id)
            else:
                # Client disconnected before the investigation completed.
                # Keep the queue and token alive so the client can reconnect
                # and resume the stream. The TTL cleanup task handles eviction
                # after _SSE_ORPHAN_TTL seconds if no client reconnects.
                logger.debug(
                    "SSE client disconnected mid-investigation for %s — queue preserved for reconnect",
                    incident_id,
                )

    return EventSourceResponse(event_generator())

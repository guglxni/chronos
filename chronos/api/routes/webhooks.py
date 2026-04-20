"""
Webhook receivers for OpenMetadata and OpenLineage events.

OpenMetadata test failure webhooks trigger full RCA investigations.
All other events are ingested into Graphiti for temporal context.
OpenLineage events enrich pipeline run history.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from chronos.ingestion.deduplicator import deduplicator
from chronos.ingestion.graphiti_ingestor import ingest_om_event
from chronos.ingestion.openlineage_receiver import receive_openlineage_event
from chronos.models.events import (
    InvestigationTrigger,
    OpenLineageRunEvent,
    OpenMetadataWebhookPayload,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
logger = logging.getLogger("chronos.webhooks")

# Track active investigation tasks by incident_id (for observability)
_active_investigations: dict[str, asyncio.Task] = {}

# OpenMetadata event types that should trigger an investigation
_TRIGGER_EVENT_TYPES = {"TEST_CASE_FAILED", "testCaseFailed"}


@router.post("/openmetadata")
async def receive_openmetadata_webhook(
    payload: OpenMetadataWebhookPayload,
    background_tasks: BackgroundTasks,
):
    """
    Receive OpenMetadata webhook events.

    - TEST_CASE_FAILED events trigger a full RCA investigation (de-duplicated).
    - All other events are ingested into Graphiti for temporal context.
    """
    # Always ingest the event into Graphiti for temporal knowledge
    background_tasks.add_task(ingest_om_event, payload)

    if payload.eventType not in _TRIGGER_EVENT_TYPES:
        return {"status": "ingested", "event_type": payload.eventType}

    # De-duplicate: same entity + event type within the window
    event_key = f"{payload.entityFullyQualifiedName}:{payload.eventType}"
    if deduplicator.is_duplicate(event_key):
        logger.info(f"Deduplicated event: {event_key}")
        return {"status": "deduplicated", "event_key": event_key}

    # Build trigger
    entity = payload.entity or {}
    trigger = InvestigationTrigger(
        entity_fqn=payload.entityFullyQualifiedName,
        test_name=entity.get("name", ""),
        failure_message=(
            entity.get("testCaseResult", {}).get("result", "")
            or (payload.testResult.result if payload.testResult else "")
        ),
        triggered_by="openmetadata_webhook",
        timestamp=datetime.utcnow(),
    )

    background_tasks.add_task(_run_investigation, trigger)

    return {
        "status": "investigation_triggered",
        "entity_fqn": payload.entityFullyQualifiedName,
    }


@router.post("/openlineage")
async def receive_openlineage_webhook(
    event: OpenLineageRunEvent,
    background_tasks: BackgroundTasks,
):
    """Receive OpenLineage run events and ingest into Graphiti."""
    background_tasks.add_task(receive_openlineage_event, event)
    return {"status": "ingested", "event_type": event.eventType}


async def _run_investigation(trigger: InvestigationTrigger) -> None:
    """
    Background coroutine that runs the full 10-step investigation pipeline.

    Imports are deferred to avoid circular import issues at module load time.
    """
    from chronos.agent.graph import get_langfuse_callback, investigation_graph

    incident_id = str(uuid.uuid4())

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

    logger.info(
        f"Starting investigation {incident_id} for entity '{trigger.entity_fqn}'"
    )

    try:
        result = await investigation_graph.ainvoke(initial_state, config=config)

        # Store the completed incident report for the REST API
        from chronos.api.routes.incidents import store_incident

        incident_report = result.get("incident_report")
        if incident_report:
            store_incident(incident_report)

        logger.info(
            f"Investigation {incident_id} complete: "
            f"category={result.get('incident_report', {}).get('root_cause_category')}, "
            f"confidence={result.get('incident_report', {}).get('confidence')}"
        )
    except Exception as exc:
        logger.error(
            f"Investigation {incident_id} failed: {exc}", exc_info=True
        )
    finally:
        _active_investigations.pop(incident_id, None)

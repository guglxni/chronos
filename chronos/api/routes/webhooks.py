"""
Webhook receivers for OpenMetadata and OpenLineage events.

OpenMetadata test failure webhooks trigger full RCA investigations.
All other events are ingested into Graphiti for temporal context.
OpenLineage events enrich pipeline run history.

Security hardening (Fix #2):
  Both endpoints validate HMAC-SHA256 signatures via FastAPI dependencies.
  See ``chronos/api/dependencies.py`` for the implementation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from chronos.api.dependencies import (
    verify_openlineage_signature,
    verify_openmetadata_signature,
)
from chronos.api.rate_limit import limiter
from chronos.core.investigation_runner import run_investigation
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

# OpenMetadata event types that should trigger an investigation
# Accept all known casing variants sent by different OM versions and the demo UI
_TRIGGER_EVENT_TYPES = {
    "TEST_CASE_FAILED",
    "testCaseFailed",
    "TestCaseFailed",
    "test_case_failed",
}


@router.post(
    "/openmetadata",
    dependencies=[Depends(verify_openmetadata_signature)],
)
@limiter.limit("30/minute")
async def receive_openmetadata_webhook(
    request: Request,
    payload: OpenMetadataWebhookPayload,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """
    Receive OpenMetadata webhook events.

    - TEST_CASE_FAILED events trigger a full RCA investigation (de-duplicated).
    - All other events are ingested into Graphiti for temporal context.
    - Requests must carry a valid X-OM-Signature when
      WEBHOOK_SIGNATURE_REQUIRED=true (production).
    """
    # Always ingest the event into Graphiti for temporal knowledge
    background_tasks.add_task(ingest_om_event, payload)

    if payload.eventType not in _TRIGGER_EVENT_TYPES:
        return {"status": "ingested", "event_type": payload.eventType}

    # De-duplicate: same entity + event type within the window
    event_key = f"{payload.entityFullyQualifiedName}:{payload.eventType}"
    if deduplicator.is_duplicate(event_key):
        logger.info("Deduplicated event: %s", event_key)
        return {"status": "deduplicated", "event_key": event_key}

    # Build trigger
    entity = payload.entity or {}
    test_case_result = entity.get("testCaseResult")
    if not isinstance(test_case_result, dict):
        test_case_result = {}
    trigger = InvestigationTrigger(
        entity_fqn=payload.entityFullyQualifiedName,
        test_name=entity.get("name", ""),
        failure_message=(
            test_case_result.get("result", "")
            or (payload.testResult.result if payload.testResult else "")
        ),
        triggered_by="openmetadata_webhook",
        timestamp=datetime.now(tz=UTC),
    )

    background_tasks.add_task(run_investigation, trigger)

    return {
        "status": "investigation_triggered",
        "entity_fqn": payload.entityFullyQualifiedName,
    }


@router.post(
    "/openlineage",
    dependencies=[Depends(verify_openlineage_signature)],
)
@limiter.limit("30/minute")
async def receive_openlineage_webhook(
    request: Request,
    event: OpenLineageRunEvent,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Receive OpenLineage run events and ingest into Graphiti."""
    background_tasks.add_task(receive_openlineage_event, event)
    return {"status": "ingested", "event_type": event.eventType}

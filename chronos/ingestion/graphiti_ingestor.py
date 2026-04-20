"""
Ingests OpenMetadata webhook payloads into Graphiti as temporal episodes.

Every event — not just failures — is ingested so that Graphiti can build a rich
temporal knowledge graph of all entity activity.
"""

from __future__ import annotations

import json
import logging

from chronos.models.events import OpenMetadataWebhookPayload
from chronos.mcp.tools import graphiti_add_episode

logger = logging.getLogger("chronos.ingestion.graphiti")

GROUP_ID = "chronos-om-events"


async def ingest_om_event(payload: OpenMetadataWebhookPayload) -> bool:
    """
    Ingest an OpenMetadata webhook event as a Graphiti episode.

    The episode content is a JSON blob containing the event metadata so that
    Graphiti can extract entities and facts from it.

    Returns True on success, False on failure.
    """
    content = json.dumps(
        {
            "event_type": payload.eventType,
            "entity_fqn": payload.entityFullyQualifiedName,
            "entity_type": payload.entityType,
            "user": payload.userName,
            "timestamp": payload.timestamp,
            # Include a compact snapshot of the entity for richer fact extraction
            "entity_snapshot": {
                k: v
                for k, v in payload.entity.items()
                if k in ("name", "fullyQualifiedName", "columns", "testCaseResult", "tags")
            },
        },
        default=str,
    )

    name = (
        f"{payload.eventType}:{payload.entityFullyQualifiedName}:{payload.timestamp}"
    )

    try:
        result = await graphiti_add_episode(
            group_id=GROUP_ID,
            name=name,
            content=content,
            source_type="json",
        )
        success = bool(result)
        if success:
            logger.debug(f"Ingested OM event: {name}")
        else:
            logger.warning(f"Graphiti returned empty result for episode: {name}")
        return success
    except Exception as exc:
        logger.error(f"Failed to ingest OM event {name}: {exc}", exc_info=True)
        return False

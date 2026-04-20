"""
Receives OpenLineage run events and ingests them into Graphiti.

OpenLineage events enrich the temporal knowledge graph with pipeline execution
context — which jobs ran, when, what datasets they read and wrote.
"""

from __future__ import annotations

import json
import logging

from chronos.models.events import OpenLineageRunEvent
from chronos.mcp.tools import graphiti_add_episode

logger = logging.getLogger("chronos.ingestion.openlineage")

GROUP_ID = "chronos-openlineage"


async def receive_openlineage_event(event: OpenLineageRunEvent) -> bool:
    """
    Ingest an OpenLineage run event into Graphiti as a temporal episode.

    Returns True on success, False on failure.
    """
    content = json.dumps(
        {
            "event_type": event.eventType,
            "event_time": event.eventTime,
            "job": event.job,
            "run": {k: v for k, v in event.run.items() if k in ("runId", "facets")},
            "inputs": [
                {"namespace": inp.namespace, "name": inp.name}
                for inp in event.inputs
            ],
            "outputs": [
                {"namespace": out.namespace, "name": out.name}
                for out in event.outputs
            ],
        },
        default=str,
    )

    # Use job name + event type + time as a stable, human-readable episode name
    job_name = event.job.get("name", "unknown_job")
    name = f"openlineage:{job_name}:{event.eventType}:{event.eventTime}"

    try:
        result = await graphiti_add_episode(
            group_id=GROUP_ID,
            name=name,
            content=content,
            source_type="json",
        )
        success = bool(result)
        if success:
            logger.debug(f"Ingested OpenLineage event: {name}")
        else:
            logger.warning(f"Graphiti returned empty result for OL episode: {name}")
        return success
    except Exception as exc:
        logger.error(f"Failed to ingest OpenLineage event {name}: {exc}", exc_info=True)
        return False

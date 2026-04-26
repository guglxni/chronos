"""
Step 2 — Temporal Diff

Combines Graphiti temporal facts (recent events) with OpenMetadata entity version
history to surface schema and metadata changes within the investigation window.
"""

from __future__ import annotations

from datetime import UTC, datetime

from chronos.agent.state import InvestigationState
from chronos.config.settings import settings
from chronos.mcp.tools import graphiti_search_facts, om_get_version_history

GROUP_ID = "chronos-om-events"


async def temporal_diff_node(state: InvestigationState) -> InvestigationState:
    """Fetch temporal changes from Graphiti and version history from OpenMetadata."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.now(tz=UTC)

    # Graphiti: query for recent events in the investigation window
    temporal_changes = await graphiti_search_facts(
        query=(
            f"changes to {entity_fqn} in last "
            f"{settings.investigation_window_hours} hours"
        ),
        group_id=GROUP_ID,
        limit=20,
    )

    # OpenMetadata: full version history for the entity
    version_history = await om_get_version_history(entity_fqn)

    # Filter to versions that touched columns (schema changes)
    schema_changes = [
        v
        for v in version_history
        if "columns" in str(v.get("changeDescription", {}))
        or "column" in str(v.get("changeDescription", {})).lower()
    ]

    # Most recent version diff (first in list is usually most recent)
    latest_version_diff = version_history[0] if version_history else {}

    step_result = {
        "step": 2,
        "name": "temporal_diff",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": (
            f"Found {len(temporal_changes)} temporal changes, "
            f"{len(schema_changes)} schema changes, "
            f"{len(version_history)} total versions"
        ),
    }

    return {
        **state,
        "temporal_changes": temporal_changes,
        "schema_changes": schema_changes,
        "entity_version_diff": latest_version_diff,
        "step_results": [*state.get("step_results", []), step_result],
    }

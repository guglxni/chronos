"""
Step 6 — Audit Correlation

Fetches OpenMetadata audit logs for the affected entity within the investigation
window and cross-references with Graphiti for user-action signals.
Flags suspicious operations (updates, deletions, schema changes).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from chronos.agent.state import InvestigationState
from chronos.config.settings import settings
from chronos.mcp.tools import graphiti_search_facts, om_get_audit_logs

GROUP_ID = "chronos-om-events"

# Event types that are suspicious in the context of a data quality failure
_SUSPICIOUS_EVENT_TYPES = {
    "ENTITY_UPDATED",
    "ENTITY_DELETED",
    "COLUMN_DELETED",
    "ENTITY_SOFT_DELETED",
    "ENTITY_NO_LONGER_USED_AS_HEADER",
}


async def audit_correlation_node(state: InvestigationState) -> InvestigationState:
    """Fetch audit logs and cross-reference with Graphiti user-action facts."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.now(tz=UTC)

    window_hours = settings.investigation_window_hours
    now_ms = int(datetime.now(tz=UTC).timestamp() * 1000)
    start_ms = int(
        (datetime.now(tz=UTC) - timedelta(hours=window_hours)).timestamp() * 1000
    )

    # Fetch audit logs from OpenMetadata
    audit_events = await om_get_audit_logs(
        fqn=entity_fqn,
        start_ts=start_ms,
        end_ts=now_ms,
    )

    # Cross-reference with Graphiti for user-action patterns
    graphiti_facts = await graphiti_search_facts(
        query=f"user action on {entity_fqn}",
        group_id=GROUP_ID,
        limit=10,
    )

    # Flag suspicious event types
    suspicious_actions = [
        e for e in audit_events if e.get("eventType") in _SUSPICIOUS_EVENT_TYPES
    ]

    # Also flag any Graphiti facts mentioning user-initiated changes
    for fact in graphiti_facts:
        fact_content = str(fact.get("fact", fact.get("description", ""))).lower()
        if any(kw in fact_content for kw in ("deleted", "modified", "updated", "dropped")):
            suspicious_actions.append({"source": "graphiti", "fact": fact})

    step_result = {
        "step": 6,
        "name": "audit_correlation",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": (
            f"Found {len(audit_events)} audit events "
            f"({len(suspicious_actions)} suspicious) "
            f"+ {len(graphiti_facts)} Graphiti user-action facts"
        ),
    }

    return {
        **state,
        "audit_events": audit_events,
        "suspicious_actions": suspicious_actions,
        "step_results": [*state.get("step_results", []), step_result],
    }

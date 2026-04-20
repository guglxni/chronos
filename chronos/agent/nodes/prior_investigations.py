"""
Step 0 — Prior Investigations

Queries Graphiti for past incidents on the same entity so that the RCA synthesis
node can detect recurring patterns.
"""

from __future__ import annotations

from datetime import datetime

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import graphiti_search_facts, graphiti_search_nodes

GROUP_ID = "chronos-investigation-traces"


async def prior_investigations_node(state: InvestigationState) -> InvestigationState:
    """Query Graphiti for past incidents and related nodes on the same entity."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.utcnow()

    # Search for past incident facts linked to this entity
    prior_facts = await graphiti_search_facts(
        query=f"incident on {entity_fqn}",
        group_id=GROUP_ID,
        limit=5,
    )

    # Also search for entity nodes to find related investigation traces
    related_nodes = await graphiti_search_nodes(
        query=entity_fqn,
        group_id=GROUP_ID,
        limit=3,
    )

    combined = prior_facts + related_nodes

    step_result = {
        "step": 0,
        "name": "prior_investigations",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "summary": (
            f"Found {len(prior_facts)} prior investigation facts "
            f"and {len(related_nodes)} related nodes for {entity_fqn}"
        ),
    }

    return {
        **state,
        "prior_investigations": combined,
        "step_results": state.get("step_results", []) + [step_result],
    }

"""
Step 5 — Downstream Impact

Walks downstream lineage to identify all assets that depend on the failing
entity, classifies business impact based on OpenMetadata Tier tags, and —
when a graphify graph is available — records short code-level paths from
the failing entity to each Tier-1 downstream asset. This "architectural
blast radius" complements the data-lineage view by surfacing the actual
Python/SQL modules that connect the failure to the high-impact dashboards.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from chronos.agent.state import InvestigationState
from chronos.config.settings import settings
from chronos.mcp.tools import graphify_shortest_path, om_get_lineage

logger = logging.getLogger("chronos.agent.downstream_impact")

_MAX_BLAST_PATHS = 5


async def downstream_impact_node(state: InvestigationState) -> InvestigationState:
    """Walk downstream lineage and classify business impact by tier."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.now(tz=UTC)

    lineage = await om_get_lineage(
        fqn=entity_fqn,
        direction="downstream",
        depth=settings.lineage_downstream_depth,
    )

    downstream_nodes: list[dict[str, Any]] = lineage.get("nodes", [])
    downstream_assets: list[dict[str, Any]] = []
    all_owners: list[str] = []

    for node in downstream_nodes:
        # Extract tier from tags
        tags = node.get("tags", [])
        tier = next(
            (
                t.get("tagFQN", "")
                for t in tags
                if "Tier" in t.get("tagFQN", "") or "tier" in t.get("tagFQN", "")
            ),
            "",
        )

        # Extract owners
        owners_raw = node.get("owners", node.get("owner", []))
        if isinstance(owners_raw, dict):
            owners_raw = [owners_raw]
        owner_names = [
            o.get("displayName") or o.get("name", "") for o in owners_raw
        ]
        owner_names = [n for n in owner_names if n]

        downstream_assets.append(
            {
                "fqn": node.get("fullyQualifiedName", ""),
                "display_name": node.get("displayName") or node.get("name", ""),
                "tier": tier,
                "owners": owner_names,
                "asset_type": node.get("entityType", node.get("type", "")),
            }
        )
        all_owners.extend(owner_names)

    # Business impact based on highest tier present in downstream
    tiers = [a.get("tier", "") for a in downstream_assets]
    if any("Tier1" in t or "tier1" in t.lower() for t in tiers):
        business_impact_score = "critical"
    elif any("Tier2" in t or "tier2" in t.lower() for t in tiers):
        business_impact_score = "high"
    elif downstream_assets:
        business_impact_score = "medium"
    else:
        business_impact_score = "low"

    # Architectural blast radius: shortest code paths from the failing
    # entity to each Tier-1 downstream asset. Best-effort — empty list
    # when the graphify graph is missing or has no matching nodes.
    architectural_blast_radius: list[dict[str, Any]] = []
    high_impact_assets = [
        a for a in downstream_assets
        if "tier1" in a.get("tier", "").lower()
        or "tier2" in a.get("tier", "").lower()
    ][:_MAX_BLAST_PATHS]

    if entity_fqn and high_impact_assets:
        for asset in high_impact_assets:
            asset_fqn = asset.get("fqn", "")
            if not asset_fqn:
                continue
            try:
                path = await graphify_shortest_path(entity_fqn, asset_fqn)
            except Exception as exc:
                logger.debug(
                    "graphify_shortest_path(%s, %s) failed: %s",
                    entity_fqn, asset_fqn, exc,
                )
                path = []
            if path:
                architectural_blast_radius.append(
                    {
                        "from": entity_fqn,
                        "to": asset_fqn,
                        "tier": asset.get("tier", ""),
                        "hops": path,
                    }
                )

    step_result = {
        "step": 5,
        "name": "downstream_impact",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": (
            f"Found {len(downstream_assets)} downstream assets; "
            f"business_impact={business_impact_score}; "
            f"code_blast_paths={len(architectural_blast_radius)}"
        ),
    }

    return {
        **state,
        "downstream_assets": downstream_assets,
        "business_impact_score": business_impact_score,
        "affected_owners": list(set(all_owners)),
        "architectural_blast_radius": architectural_blast_radius,
        "step_results": [*state.get("step_results", []), step_result],
    }

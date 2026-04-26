"""
LangGraph TypedDict state for a CHRONOS investigation run.

``InvestigationInputs`` contains the required trigger fields that every node
can rely on being present.  ``InvestigationState`` extends it with
``total=False`` optional keys that nodes progressively accumulate.

Splitting the two removes the need for defensive ``.get()`` on trigger fields
and gives mypy enough type information to catch missing-key bugs in nodes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Required, TypedDict


class InvestigationInputs(TypedDict):
    """Required fields — always present from the start of the pipeline."""

    incident_id: str
    triggered_at: datetime
    entity_fqn: str
    test_name: str
    failure_message: str
    step_results: list[dict[str, Any]]
    investigation_start: datetime
    # Bump this integer on every breaking state-shape change so rolling deploys
    # and future migration paths can detect version mismatches.
    state_schema_version: int


class InvestigationState(InvestigationInputs, total=False):
    """Full investigation state — required inputs plus optional accumulated outputs."""

    # ── Step 0: Prior investigations ──────────────────────────────────────────
    prior_investigations: list[dict[str, Any]]

    # ── Step 1: Scope failure ─────────────────────────────────────────────────
    failed_test: dict[str, Any]
    affected_entity: dict[str, Any]
    affected_columns: list[str]
    last_passed_at: datetime | None

    # ── Step 2: Temporal diff ─────────────────────────────────────────────────
    temporal_changes: list[dict[str, Any]]
    schema_changes: list[dict[str, Any]]
    entity_version_diff: dict[str, Any]

    # ── Step 3: Lineage walk ──────────────────────────────────────────────────
    upstream_lineage: list[dict[str, Any]]
    upstream_failures: list[dict[str, Any]]
    upstream_changes: list[dict[str, Any]]

    # ── Step 4: Code blast radius ─────────────────────────────────────────────
    related_code_files: list[dict[str, Any]]
    recent_commits: list[dict[str, Any]]
    code_dependencies: list[str]
    dbt_upstream_models: list[dict[str, Any]]
    dbt_downstream_models: list[dict[str, Any]]
    code_graph_neighbors: list[dict[str, Any]]
    architectural_community: dict[str, Any]
    architectural_blast_radius: list[dict[str, Any]]

    # ── Step 5: Downstream impact ─────────────────────────────────────────────
    downstream_assets: list[dict[str, Any]]
    business_impact_score: str
    affected_owners: list[str]

    # ── Step 6: Audit correlation ─────────────────────────────────────────────
    audit_events: list[dict[str, Any]]
    suspicious_actions: list[dict[str, Any]]

    # ── Step 7: RCA synthesis ─────────────────────────────────────────────────
    incident_report: dict[str, Any] | None

    # ── Step 8: Notify ────────────────────────────────────────────────────────
    notification_status: str

    # ── Step 9: Persist trace ─────────────────────────────────────────────────
    trace_persisted: bool

    # ── Meta ──────────────────────────────────────────────────────────────────
    error: str | None


# Re-export Required so importing modules don't need to touch typing directly
__all__ = ["InvestigationInputs", "InvestigationState", "Required"]

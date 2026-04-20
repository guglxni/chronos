"""
LangGraph TypedDict state for a CHRONOS investigation run.

Every node receives and returns a (partial) InvestigationState. Keys are optional
(total=False) so nodes only need to return the fields they populate.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict


class InvestigationState(TypedDict, total=False):
    # ── Trigger ──────────────────────────────────────────────────────────────
    incident_id: str
    triggered_at: datetime
    entity_fqn: str
    test_name: str
    failure_message: str

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
    step_results: list[dict[str, Any]]
    investigation_start: datetime
    error: str | None

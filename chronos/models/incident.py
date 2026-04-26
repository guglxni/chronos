from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RootCauseCategory(StrEnum):
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    CODE_CHANGE = "CODE_CHANGE"
    DATA_DRIFT = "DATA_DRIFT"
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    UNKNOWN = "UNKNOWN"


class BusinessImpact(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class EvidenceSource(StrEnum):
    OPENMETADATA = "openmetadata"
    GRAPHITI = "graphiti"
    GITNEXUS = "gitnexus"
    GRAPHIFY = "graphify"
    AUDIT_LOG = "audit_log"
    # Used when the LLM returns an evidence source label we don't recognise.
    # Keeps PROV-O provenance honest — previously unrecognised labels silently
    # defaulted to OPENMETADATA, falsifying provenance chains.
    UNKNOWN = "unknown"


class EvidenceItem(BaseModel):
    source: EvidenceSource
    description: str
    raw_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class AffectedAsset(BaseModel):
    fqn: str
    display_name: str = ""
    tier: str = ""
    owners: list[str] = Field(default_factory=list)
    domain: str = ""


class RemediationStep(BaseModel):
    description: str
    priority: str  # "immediate", "short_term", "long_term"
    owner: str = ""


class InvestigationTimelineEntry(BaseModel):
    step: int
    name: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    summary: str = ""


class RelatedIncident(BaseModel):
    incident_id: str
    root_cause_category: RootCauseCategory
    affected_entity_fqn: str
    detected_at: datetime
    confidence: float


class IncidentReport(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    investigation_completed_at: datetime | None = None
    investigation_duration_ms: int | None = None

    affected_entity_fqn: str
    test_name: str
    test_type: str = ""
    failure_message: str = ""

    probable_root_cause: str
    root_cause_category: RootCauseCategory
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)

    affected_downstream: list[AffectedAsset] = Field(default_factory=list)
    upstream_assets: list[AffectedAsset] = Field(default_factory=list)
    business_impact: BusinessImpact = BusinessImpact.MEDIUM
    business_impact_reasoning: str = ""

    recommended_actions: list[RemediationStep] = Field(default_factory=list)
    investigation_timeline: list[InvestigationTimelineEntry] = Field(default_factory=list)
    related_past_incidents: list[RelatedIncident] = Field(default_factory=list)
    graphify_context: str = ""

    # Observability / provenance metadata populated by the runner.
    # Spec'd in PRD §4.1 but previously absent from the model.
    agent_version: str = ""
    llm_model_used: str = ""
    total_mcp_calls: int = 0
    total_llm_tokens: int = 0

    status: IncidentStatus = IncidentStatus.OPEN
    acknowledged_by: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None

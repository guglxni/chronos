"""
Pydantic response schemas for CHRONOS API routes.

Using explicit response models on every FastAPI route:
- Generates accurate OpenAPI docs (schemas, types, examples)
- Validates outbound responses — surfaces serialisation bugs at the boundary
- Enables client code generation from the OpenAPI spec
"""
from __future__ import annotations

from pydantic import BaseModel

from chronos.models.incident import IncidentReport


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


class WebhookAckResponse(BaseModel):
    status: str
    event_type: str | None = None
    event_key: str | None = None
    entity_fqn: str | None = None


class InvestigationTriggerResponse(BaseModel):
    status: str
    incident_id: str
    entity_fqn: str
    stream_url: str
    stream_token: str


class IncidentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    incidents: list[IncidentReport]


class AcknowledgeResponse(BaseModel):
    status: str
    incident_id: str
    acknowledged_by: str | None = None


class ResolveResponse(BaseModel):
    status: str
    incident_id: str
    resolved_by: str | None = None
    resolved_at: str | None = None


class StatsResponse(BaseModel):
    total_incidents: int
    by_root_cause: dict[str, int]
    by_impact: dict[str, int]
    by_status: dict[str, int]
    avg_confidence: float
    open_count: int
    investigating_count: int
    critical_count: int
    resolved_count: int


class PatternEntry(BaseModel):
    entity_fqn: str
    incident_count: int
    is_recurring: bool
    root_cause_categories: list[str]


class PatternsResponse(BaseModel):
    patterns: list[PatternEntry]
    total_recurring_entities: int

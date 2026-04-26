from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DataAssetEntity(BaseModel):
    name: str
    fqn: str
    asset_type: str  # table, dashboard, pipeline, model
    tier: str = ""
    domain: str = ""
    service: str = ""
    owner: str = ""


class DataTestEntity(BaseModel):
    name: str
    test_name: str
    test_type: str
    target_entity_fqn: str
    target_column: str = ""
    last_status: str = "unknown"
    last_run_at: datetime | None = None


class SchemaStateEntity(BaseModel):
    name: str
    entity_fqn: str
    column_count: int = 0
    column_names: list[str] = Field(default_factory=list)
    column_types: dict[str, str] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineRunEntity(BaseModel):
    name: str
    pipeline_fqn: str
    run_id: str
    status: str  # success, failed, partial_success
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error_message: str = ""


class IncidentEntity(BaseModel):
    name: str
    incident_id: str
    root_cause_category: str
    confidence: float
    affected_entity_fqn: str
    test_name: str
    resolved: bool = False
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str = ""


class GraphitiEdge(BaseModel):
    source_name: str
    target_name: str
    relation_type: str
    properties: dict[str, Any] = Field(default_factory=dict)

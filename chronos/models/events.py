from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class OpenMetadataTestResult(BaseModel):
    testCaseStatus: str
    timestamp: int
    result: str = ""
    testResultValue: list[dict] = Field(default_factory=list)


class OpenMetadataTestCase(BaseModel):
    id: str = ""
    name: str = ""
    fullyQualifiedName: str = ""
    entityLink: str = ""
    testSuite: dict = Field(default_factory=dict)
    testDefinition: dict = Field(default_factory=dict)


class OpenMetadataWebhookPayload(BaseModel):
    eventType: str
    entityType: str = ""
    entityId: str = ""
    entityFullyQualifiedName: str = ""
    userName: str = ""
    timestamp: int = 0
    entity: dict[str, Any] = Field(default_factory=dict)
    previousVersion: dict[str, Any] | None = None
    changeDescription: dict[str, Any] | None = None
    testResult: OpenMetadataTestResult | None = None


class OpenLineageFacet(BaseModel):
    _producer: str = ""
    _schemaURL: str = ""


class OpenLineageDataset(BaseModel):
    namespace: str
    name: str
    facets: dict[str, Any] = Field(default_factory=dict)


class OpenLineageRunEvent(BaseModel):
    eventType: str
    eventTime: str
    run: dict[str, Any] = Field(default_factory=dict)
    job: dict[str, Any] = Field(default_factory=dict)
    inputs: list[OpenLineageDataset] = Field(default_factory=list)
    outputs: list[OpenLineageDataset] = Field(default_factory=list)
    producer: str = ""
    schemaURL: str = ""


class InvestigationTrigger(BaseModel):
    entity_fqn: str
    test_name: str = ""
    failure_message: str = ""
    triggered_by: str = "manual"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

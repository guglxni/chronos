from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class OpenMetadataTestResult(BaseModel):
    testCaseStatus: str = "Failed"
    timestamp: int = 0
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

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Accept entityFQN as alias for entityFullyQualifiedName (demo compat)
        if "entityFQN" in data and not data.get("entityFullyQualifiedName"):
            data["entityFullyQualifiedName"] = data.pop("entityFQN")
        # Accept testCaseResult as alias for testResult (demo compat)
        if "testCaseResult" in data and "testResult" not in data:
            data["testResult"] = data.pop("testCaseResult")
        return data


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

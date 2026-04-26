"""Demo investigation endpoint — pre-seeded scenarios for the CHRONOS live demo."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from chronos.api.rate_limit import limiter
from chronos.api.routes.investigations import register_sse_queue
from chronos.core.incident_store import store as store_incident
from chronos.demo.scenarios import SCENARIOS
from chronos.llm.client import synthesize_rca
from chronos.models.incident import (
    AffectedAsset,
    BusinessImpact,
    IncidentReport,
    IncidentStatus,
    InvestigationTimelineEntry,
    RemediationStep,
    RootCauseCategory,
)

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])
logger = logging.getLogger("chronos.demo")

_active_tasks: set[asyncio.Task] = set()

_NODE_STEPS = [
    ("prior_investigations", "Checking prior incident knowledge graph…"),
    ("scope_failure", "Scoping failure — identifying affected assets and tests…"),
    ("temporal_diff", "Scanning temporal changes in the last 72 hours…"),
    ("lineage_walk", "Walking upstream lineage 5 hops deep…"),
    ("code_blast_radius", "Scanning recent code changes in dbt + ETL pipelines…"),
    ("downstream_impact", "Computing downstream blast radius…"),
    ("audit_correlation", "Correlating audit log events and schema changes…"),
    ("rca_synthesis", "Synthesizing root cause analysis with LLM…"),
]


def _push(queue: asyncio.Queue, event: dict) -> None:
    with contextlib.suppress(asyncio.QueueFull):
        queue.put_nowait(event)


async def _run_demo_investigation(
    incident_id: str,
    scenario: dict[str, Any],
    queue: asyncio.Queue,
) -> None:
    start = datetime.now(UTC)
    step_results = []

    for i, (name, message) in enumerate(_NODE_STEPS[:-1]):
        step_start = datetime.now(UTC)
        _push(queue, {"status": "update", "step": i, "node": name, "message": message})
        await asyncio.sleep(0.5)
        step_end = datetime.now(UTC)
        step_results.append({
            "step": i,
            "name": name,
            "started_at": step_start.isoformat(),
            "completed_at": step_end.isoformat(),
            "duration_ms": int((step_end - step_start).total_seconds() * 1000),
            "summary": f"[demo] {message}",
        })

    _push(queue, {"status": "update", "step": 7, "node": "rca_synthesis", "message": _NODE_STEPS[-1][1]})

    evidence = {
        "entity_fqn": scenario.get("entity_fqn", ""),
        "test_name": scenario.get("test_name", ""),
        "failure_message": scenario.get("failure_message", ""),
        "failed_test": {"name": scenario.get("test_name", ""), "entity_fqn": scenario.get("entity_fqn", ""), "result": "FAILED"},
        "temporal_changes": scenario.get("temporal_changes", []),
        "schema_changes": scenario.get("schema_changes", []),
        "upstream_failures": scenario.get("upstream_failures", []),
        "related_code_files": scenario.get("related_code_files", []),
        "downstream_assets": scenario.get("downstream_assets", []),
        "audit_events": scenario.get("audit_events", []),
        "prior_investigations": [],
        "business_impact_score": scenario.get("business_impact_score", "high"),
    }

    llm_result = await synthesize_rca(evidence)

    downstream = [
        AffectedAsset(
            fqn=a["fqn"],
            display_name=a.get("display_name", ""),
            tier=a.get("tier", ""),
            owners=a.get("owners", []),
        )
        for a in scenario.get("downstream_assets", [])
    ]

    timeline = [
        InvestigationTimelineEntry(
            step=sr["step"],
            name=sr["name"],
            started_at=datetime.fromisoformat(sr["started_at"]),
            completed_at=datetime.fromisoformat(sr["completed_at"]),
            duration_ms=sr["duration_ms"],
            summary=sr["summary"],
        )
        for sr in step_results
    ]

    recommended_actions: list[RemediationStep] = []
    for action in (llm_result.get("recommended_actions") or [])[:5]:
        if isinstance(action, dict) and action.get("description"):
            priority = str(action.get("priority", "short_term")).lower()
            if priority not in ("immediate", "short_term", "long_term"):
                priority = "short_term"
            recommended_actions.append(RemediationStep(
                description=str(action["description"])[:300],
                priority=priority,
                owner=str(action.get("owner", ""))[:100],
            ))

    if recommended_actions and not any(a.priority == "immediate" for a in recommended_actions):
        recommended_actions.insert(0, RemediationStep(
            description="Immediately halt downstream processing and assess data quality impact.",
            priority="immediate",
            owner="data-engineering",
        ))

    raw_category = llm_result.get("root_cause_category", "UNKNOWN")
    try:
        root_cause_category = RootCauseCategory(raw_category)
    except ValueError:
        root_cause_category = RootCauseCategory.UNKNOWN

    raw_impact = str(llm_result.get("business_impact") or scenario.get("business_impact_score") or "high").lower()
    try:
        business_impact = BusinessImpact(raw_impact)
    except ValueError:
        business_impact = BusinessImpact.HIGH

    try:
        confidence = max(0.0, min(1.0, float(llm_result.get("confidence", 0.75))))
    except (TypeError, ValueError):
        confidence = 0.75

    elapsed_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)

    report = IncidentReport(
        incident_id=incident_id,
        detected_at=start,
        investigation_completed_at=datetime.now(UTC),
        investigation_duration_ms=elapsed_ms,
        affected_entity_fqn=scenario.get("entity_fqn", ""),
        test_name=scenario.get("test_name", ""),
        failure_message=scenario.get("failure_message", ""),
        probable_root_cause=str(llm_result.get("probable_root_cause", "Unable to determine root cause"))[:1000],
        root_cause_category=root_cause_category,
        confidence=confidence,
        evidence_chain=[],
        affected_downstream=downstream,
        business_impact=business_impact,
        business_impact_reasoning=str(llm_result.get("business_impact_reasoning", ""))[:500],
        recommended_actions=recommended_actions,
        investigation_timeline=timeline,
        agent_version="2.0.0",
        llm_model_used="groq/llama-4-scout-17b",
        status=IncidentStatus.OPEN,
    )

    store_incident(report)

    _push(queue, {
        "status": "investigation_complete",
        "incident_id": incident_id,
        "root_cause_category": report.root_cause_category.value,
        "confidence": report.confidence,
    })

    with contextlib.suppress(asyncio.QueueFull):
        queue.put_nowait(None)

    logger.info("Demo investigation %s complete — %s %.2f", incident_id, report.root_cause_category, report.confidence)


class DemoRunRequest(BaseModel):
    scenario: str = "row_count_failure"
    entity_fqn: str = ""
    test_name: str = ""


@router.post("/run")
@limiter.limit("10/minute")
async def run_demo(request: Request, body: DemoRunRequest) -> dict[str, Any]:
    """Run a pre-seeded demo investigation with real LLM synthesis and SSE streaming."""
    scenario = SCENARIOS.get(body.scenario)
    if not scenario:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{body.scenario}'. Valid: {sorted(SCENARIOS)}",
        )

    scenario_data = dict(scenario)
    if body.entity_fqn:
        scenario_data["entity_fqn"] = body.entity_fqn
    if body.test_name:
        scenario_data["test_name"] = body.test_name

    incident_id = str(uuid.uuid4())
    stream_token = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    register_sse_queue(incident_id, stream_token, queue)

    task = asyncio.create_task(
        _run_demo_investigation(incident_id, scenario_data, queue),
        name=f"demo-{incident_id}",
    )
    _active_tasks.add(task)
    task.add_done_callback(_active_tasks.discard)

    return {
        "status": "triggered",
        "incident_id": incident_id,
        "stream_url": f"/api/v1/investigations/{incident_id}/stream",
        "stream_token": stream_token,
        "scenario": body.scenario,
        "entity_fqn": scenario_data["entity_fqn"],
    }


@router.get("/scenarios")
async def list_scenarios() -> dict[str, Any]:
    """List available demo scenarios."""
    return {
        "scenarios": [
            {
                "id": k,
                "entity_fqn": v["entity_fqn"],
                "test_name": v["test_name"],
                "failure_message": v["failure_message"][:100] + "…",
            }
            for k, v in SCENARIOS.items()
        ]
    }

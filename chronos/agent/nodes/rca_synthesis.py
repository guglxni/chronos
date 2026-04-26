"""
Step 7 — RCA Synthesis

Calls the LiteLLM-backed synthesis model with all collected evidence and builds
a fully-populated IncidentReport from the LLM output.

Key improvements over the original stub:
- evidence_chain and recommended_actions from the LLM response are parsed into
  typed model instances and persisted on the IncidentReport (previously dropped).
- affected_downstream is built from state["downstream_assets"] so the Slack
  notification and frontend Downstream tab show real data.
- investigation_timeline is assembled from all prior step_results.
- related_past_incidents is extracted from Graphiti prior-investigation facts.
- failure_message is clipped to 500 chars to limit prompt-injection surface.
- incident_id / entity_fqn parsed from Graphiti facts are regex-validated so
  attacker-influenced webhook payloads can't inject long strings into Slack/UI.
- All datetime usage is timezone-aware (UTC).

Duration: the runner (``core/investigation_runner.py``) computes the authoritative
end-to-end elapsed time and patches it onto the report after this node returns —
we do not duplicate that computation here.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from chronos.agent.state import InvestigationState
from chronos.config.settings import settings
from chronos.enrichment.graphify_context import get_graphify_context
from chronos.llm.client import synthesize_rca
from chronos.models.incident import (
    AffectedAsset,
    BusinessImpact,
    EvidenceItem,
    EvidenceSource,
    IncidentReport,
    InvestigationTimelineEntry,
    RelatedIncident,
    RemediationStep,
    RootCauseCategory,
)

logger = logging.getLogger("chronos.agent.rca_synthesis")

# Map LLM-returned source strings → EvidenceSource enum
_SOURCE_MAP: dict[str, EvidenceSource] = {
    "openmetadata": EvidenceSource.OPENMETADATA,
    "graphiti": EvidenceSource.GRAPHITI,
    "gitnexus": EvidenceSource.GITNEXUS,
    "audit_log": EvidenceSource.AUDIT_LOG,
    "graphify": EvidenceSource.GRAPHIFY,
}

_VALID_PRIORITIES = frozenset({"immediate", "short_term", "long_term"})

# Clip fields that flow from Graphiti (originally sourced from webhook payloads)
# before surfacing them to Slack / UI.  Bounds chosen conservatively:
#   - incident_id: UUID-like, max 64 chars
#   - entity_fqn:  FQN path, max 256 chars (spec allows nested schemas)
_SAFE_INCIDENT_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_SAFE_FQN_RE = re.compile(r"^[A-Za-z0-9_\-.]{1,256}$")


def _parse_evidence_chain(raw_chain: list[Any]) -> list[EvidenceItem]:
    """Convert raw LLM evidence list into typed EvidenceItem instances.

    Unrecognised source labels map to ``EvidenceSource.UNKNOWN`` rather than
    silently defaulting to OPENMETADATA — otherwise PROV-O provenance chains
    claim OpenMetadata derivation for evidence the LLM actually sourced from
    somewhere else (or fabricated).
    """
    items: list[EvidenceItem] = []
    for item in raw_chain[:10]:
        if not isinstance(item, dict):
            continue
        description = str(item.get("description", "")).strip()[:500]
        if not description:
            continue
        raw_source = str(item.get("source", "")).lower().replace("-", "_")
        source = _SOURCE_MAP.get(raw_source, EvidenceSource.UNKNOWN)
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
        except (TypeError, ValueError):
            confidence = 0.5
        items.append(EvidenceItem(source=source, description=description, confidence=confidence))
    return items


def _parse_remediation_steps(raw_actions: list[Any]) -> list[RemediationStep]:
    """Convert raw LLM action list into typed RemediationStep instances."""
    steps: list[RemediationStep] = []
    for action in raw_actions[:5]:
        if not isinstance(action, dict):
            continue
        description = str(action.get("description", "")).strip()[:300]
        if not description:
            continue
        priority = str(action.get("priority", "short_term")).lower()
        if priority not in _VALID_PRIORITIES:
            priority = "short_term"
        owner = str(action.get("owner", ""))[:100]
        steps.append(RemediationStep(description=description, priority=priority, owner=owner))

    # Ensure at least one immediate step (LLM prompt rule #5).
    # Previously we rewrote the LLM's first step's priority to "immediate",
    # misrepresenting intent.  Now we prepend a synthetic "manual review" step
    # instead so the LLM's own categorisation is preserved.
    if steps and not any(s.priority == "immediate" for s in steps):
        steps.insert(
            0,
            RemediationStep(
                description="Manually review the analysis and prioritise remediation.",
                priority="immediate",
                owner="data-team",
            ),
        )
    return steps


def _parse_downstream_assets(raw_assets: list[Any]) -> list[AffectedAsset]:
    """Convert downstream_assets state dicts to typed AffectedAsset instances."""
    assets: list[AffectedAsset] = []
    for asset in raw_assets[:20]:
        if not isinstance(asset, dict):
            continue
        fqn = str(asset.get("fqn", "")).strip()
        if not fqn:
            continue
        assets.append(
            AffectedAsset(
                fqn=fqn,
                display_name=str(asset.get("display_name", "")),
                tier=str(asset.get("tier", "")),
                owners=[str(o) for o in asset.get("owners", []) if o],
                domain=str(asset.get("domain", "")),
            )
        )
    return assets


def _parse_related_incidents(raw_priors: list[Any]) -> list[RelatedIncident]:
    """
    Extract RelatedIncident instances from Graphiti prior-investigation facts.

    Graphiti returns facts as dicts; investigation traces are stored as JSON
    inside the "fact" or "description" key by persist_trace_node.
    """
    incidents: list[RelatedIncident] = []
    for item in raw_priors[:5]:
        if not isinstance(item, dict):
            continue

        raw = item.get("fact") or item.get("description") or ""
        try:
            parsed: dict[str, Any] = (
                json.loads(raw) if isinstance(raw, str) and raw.lstrip().startswith("{") else item
            )
        except (json.JSONDecodeError, TypeError):
            parsed = item

        incident_id = str(parsed.get("incident_id", "")).strip()
        entity_fqn = str(parsed.get("entity_fqn") or parsed.get("affected_entity_fqn", "")).strip()
        # Drop entries with identifiers that don't match the safe charset —
        # prevents Graphiti-sourced strings from smuggling control chars,
        # markdown, or overlong values into the UI / Slack message.
        if not _SAFE_INCIDENT_ID_RE.match(incident_id):
            continue
        if not _SAFE_FQN_RE.match(entity_fqn):
            continue

        raw_category = parsed.get("root_cause_category", "UNKNOWN")
        try:
            category = RootCauseCategory(raw_category)
        except ValueError:
            category = RootCauseCategory.UNKNOWN

        try:
            confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.5))))
        except (TypeError, ValueError):
            confidence = 0.5

        detected_at_raw = parsed.get("detected_at", "")
        try:
            detected_at = (
                datetime.fromisoformat(str(detected_at_raw))
                if detected_at_raw
                else datetime.now(UTC)
            )
            if detected_at.tzinfo is None:
                detected_at = detected_at.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            detected_at = datetime.now(UTC)

        incidents.append(
            RelatedIncident(
                incident_id=incident_id,
                root_cause_category=category,
                affected_entity_fqn=entity_fqn,
                detected_at=detected_at,
                confidence=confidence,
            )
        )
    return incidents


def _build_timeline(
    step_results: list[dict[str, Any]],
) -> list[InvestigationTimelineEntry]:
    """Assemble InvestigationTimelineEntry list from accumulated step_results."""
    entries: list[InvestigationTimelineEntry] = []
    for sr in step_results:
        if not isinstance(sr, dict):
            continue
        try:
            started = datetime.fromisoformat(sr["started_at"])
            if started.tzinfo is None:
                started = started.replace(tzinfo=UTC)

            completed: datetime | None = None
            completed_raw = sr.get("completed_at")
            if completed_raw:
                completed = datetime.fromisoformat(completed_raw)
                if completed.tzinfo is None:
                    completed = completed.replace(tzinfo=UTC)

            duration_ms = int((completed - started).total_seconds() * 1000) if completed else None
            entries.append(
                InvestigationTimelineEntry(
                    step=int(sr.get("step", 0)),
                    name=str(sr.get("name", "")),
                    started_at=started,
                    completed_at=completed,
                    duration_ms=duration_ms,
                    summary=str(sr.get("summary", "")),
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug("Skipping malformed step_result: %s", exc)
    return entries


async def rca_synthesis_node(state: InvestigationState) -> InvestigationState:
    """Synthesize all evidence into a fully-populated IncidentReport via LLM."""
    start_time = datetime.now(tz=UTC)

    evidence = {
        "entity_fqn": state.get("entity_fqn", ""),
        "test_name": state.get("test_name", ""),
        # Clip free-text — limits prompt-injection via attacker-controlled webhook payloads
        "failure_message": str(state.get("failure_message", ""))[:500],
        "failed_test": state.get("failed_test", {}),
        "temporal_changes": state.get("temporal_changes", [])[:5],
        "schema_changes": state.get("schema_changes", [])[:3],
        "upstream_failures": state.get("upstream_failures", [])[:5],
        "related_code_files": state.get("related_code_files", [])[:5],
        "downstream_assets": state.get("downstream_assets", [])[:10],
        "audit_events": state.get("audit_events", [])[:5],
        "suspicious_actions": state.get("suspicious_actions", [])[:3],
        "prior_investigations": state.get("prior_investigations", [])[:3],
        "business_impact_score": state.get("business_impact_score", "medium"),
    }

    llm_result = await synthesize_rca(evidence)

    # ── Coerce scalar fields ───────────────────────────────────────────────────
    raw_category = llm_result.get("root_cause_category", "UNKNOWN")
    try:
        root_cause_category = RootCauseCategory(raw_category)
    except ValueError:
        root_cause_category = RootCauseCategory.UNKNOWN

    raw_impact = str(
        llm_result.get("business_impact") or state.get("business_impact_score") or "medium"
    ).lower()
    try:
        business_impact = BusinessImpact(raw_impact)
    except ValueError:
        business_impact = BusinessImpact.MEDIUM

    try:
        confidence = max(0.0, min(1.0, float(llm_result.get("confidence", 0.5))))
    except (TypeError, ValueError):
        confidence = 0.5

    # ── Parse rich LLM-generated fields ───────────────────────────────────────
    evidence_chain = _parse_evidence_chain(llm_result.get("evidence_chain") or [])
    recommended_actions = _parse_remediation_steps(llm_result.get("recommended_actions") or [])

    # ── Enrich from pipeline state ─────────────────────────────────────────────
    affected_downstream = _parse_downstream_assets(state.get("downstream_assets") or [])
    upstream_assets = _parse_downstream_assets(state.get("upstream_lineage") or [])
    graphify_context = get_graphify_context(state.get("entity_fqn", ""))
    investigation_timeline = _build_timeline(state.get("step_results") or [])
    related_past_incidents = _parse_related_incidents(state.get("prior_investigations") or [])

    # ── Normalise triggered_at timezone ───────────────────────────────────────
    triggered_at = state.get("triggered_at")
    if triggered_at is not None and getattr(triggered_at, "tzinfo", None) is None:
        triggered_at = triggered_at.replace(tzinfo=UTC)

    # ── Observability metadata ────────────────────────────────────────────────
    # MCP call / LLM token counts are tracked as monotonic state counters that
    # each tool/LLM helper increments.  Default 0 is honest — indicates nothing
    # was observed rather than lying with a fabricated value.
    business_impact_reasoning = str(llm_result.get("business_impact_reasoning", ""))[:500]
    llm_model_used = str(llm_result.get("model") or state.get("llm_model_used", ""))[:64]
    raw_mcp = state.get("total_mcp_calls") or 0
    raw_tokens = state.get("total_llm_tokens") or 0
    try:
        total_mcp_calls = int(raw_mcp)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        total_mcp_calls = 0
    try:
        total_llm_tokens = int(raw_tokens)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        total_llm_tokens = 0

    incident_report = IncidentReport(
        incident_id=state.get("incident_id", ""),
        detected_at=triggered_at or datetime.now(tz=UTC),
        investigation_completed_at=datetime.now(tz=UTC),
        # Runner patches investigation_duration_ms with the authoritative
        # end-to-end elapsed time — leave None here.
        affected_entity_fqn=state.get("entity_fqn", ""),
        test_name=state.get("test_name", ""),
        failure_message=str(state.get("failure_message", ""))[:500],
        probable_root_cause=str(llm_result.get("probable_root_cause", "Unknown"))[:1000],
        root_cause_category=root_cause_category,
        confidence=confidence,
        evidence_chain=evidence_chain,
        business_impact=business_impact,
        business_impact_reasoning=business_impact_reasoning,
        recommended_actions=recommended_actions,
        affected_downstream=affected_downstream,
        upstream_assets=upstream_assets,
        investigation_timeline=investigation_timeline,
        related_past_incidents=related_past_incidents,
        graphify_context=graphify_context,
        agent_version=settings.version,
        llm_model_used=llm_model_used,
        total_mcp_calls=total_mcp_calls,
        total_llm_tokens=total_llm_tokens,
    )

    completed_time = datetime.now(tz=UTC)
    step_result = {
        "step": 7,
        "name": "rca_synthesis",
        "started_at": start_time.isoformat(),
        "completed_at": completed_time.isoformat(),
        "summary": (
            f"RCA: {incident_report.root_cause_category}, "
            f"confidence={incident_report.confidence:.2f}, "
            f"evidence={len(evidence_chain)}, "
            f"actions={len(recommended_actions)}, "
            f"downstream={len(affected_downstream)}"
        ),
    }

    return {
        **state,
        "incident_report": incident_report.model_dump(mode="json"),
        "step_results": [*state.get("step_results", []), step_result],
    }

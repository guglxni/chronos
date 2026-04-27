"""
Historical demo data seeder.

Populates Graphiti with synthetic past incidents so the dashboard shows a
realistic backlog on first load. Distributed plausibly over the past 30 days
across multiple entities and root cause categories.

Usage:
    python -m chronos.demo seed --count 30
    python -m chronos.demo seed --count 30 --clear   (clear flag is informational)

When FalkorDB is not configured (default dev setup) the seeder no-ops via the
graceful degradation in chronos.graphiti_client.
"""

from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta

from chronos.core import incident_store
from chronos.graphiti_client import _is_configured, add_episode
from chronos.models.incident import (
    BusinessImpact,
    IncidentReport,
    IncidentStatus,
    RootCauseCategory,
)

logger = logging.getLogger("chronos.demo.seeder")

GROUP_ID = "chronos-historical-incidents"

# Realistic mix matching the live demo scenarios + a wider entity surface area
# so the dashboard doesn't look like only 3 things ever break.
ENTITIES: tuple[tuple[str, str], ...] = (
    ("prod.orders.orders_daily",            "Orders pipeline"),
    ("prod.customers.customer_profiles",    "Customer 360"),
    ("prod.payments.payments_raw",          "Payments ingestion"),
    ("prod.analytics.daily_kpis",           "Analytics rollup"),
    ("prod.marketing.email_campaigns",      "Marketing attribution"),
    ("prod.inventory.warehouse_stock",      "Inventory sync"),
    ("prod.users.user_sessions",            "Session tracking"),
    ("prod.finance.revenue_ledger",         "Finance ledger"),
    ("prod.support.ticket_metrics",         "Support metrics"),
    ("prod.product.feature_usage",          "Feature usage"),
)

# Each tuple: (RootCauseCategory enum value, narrative). Enum values are the
# canonical strings on the IncidentReport model.
ROOT_CAUSES: tuple[tuple[str, str], ...] = (
    ("UPSTREAM_FAILURE",
     "Upstream ETL job completed with 0 rows; downstream tables emptied"),
    ("SCHEMA_CHANGE",
     "Source API v2.4 introduced a required NOT NULL column not in the schema"),
    ("DATA_DRIFT",
     "Null-rate for primary key column exceeded 5% threshold"),
    ("PIPELINE_FAILURE",
     "Snowflake warehouse paused mid-run; partial commit left orphan records"),
    ("CODE_CHANGE",
     "dbt model regression — JOIN condition lost a key after recent refactor"),
    ("PERMISSION_CHANGE",
     "Service account JWT rotated; ingestion failed silently for 6 hours"),
    ("DATA_DRIFT",
     "Source CDC stream lag exceeded SLA; downstream rolled up incomplete data"),
    ("UPSTREAM_FAILURE",
     "Upstream connector failed authentication; downstream pipeline received empty payload"),
    ("CONFIGURATION_CHANGE",
     "dbt project_config.yml change toggled vars that flipped a model from incremental to full-refresh"),
)

SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
SEVERITY_WEIGHTS = (0.15, 0.35, 0.35, 0.15)  # most are MEDIUM/HIGH


_SEVERITY_TO_IMPACT: dict[str, BusinessImpact] = {
    "LOW":      BusinessImpact.LOW,
    "MEDIUM":   BusinessImpact.MEDIUM,
    "HIGH":     BusinessImpact.HIGH,
    "CRITICAL": BusinessImpact.CRITICAL,
}

_STATUS_MAP: dict[str, IncidentStatus] = {
    "resolved":     IncidentStatus.RESOLVED,
    "acknowledged": IncidentStatus.ACKNOWLEDGED,
    "open":         IncidentStatus.OPEN,
}


async def seed_incidents(count: int = 30, days_back: int = 30, *, seed: int | None = None) -> int:
    """Populate the in-process incident store + Graphiti with ``count`` synthetic incidents.

    The dashboard reads from the in-process store, so seeding to the store is
    what makes the seeded data show up immediately. The Graphiti episodes are
    a bonus — they give the agent's "related past incidents" lookup something
    real to find when investigations run.

    Returns the number of incidents stored. When Graphiti is not configured
    we still seed the in-process store so the dashboard works in fixture mode.
    """
    rng = random.Random(seed)
    now = datetime.now(UTC)
    seeded = 0
    graphiti_ok = _is_configured()

    if not graphiti_ok:
        logger.info("Graphiti not configured — seeding in-process store only (no FalkorDB writes)")

    for i in range(count):
        entity_fqn, entity_label = rng.choice(ENTITIES)
        category_str, narrative = rng.choice(ROOT_CAUSES)
        severity = rng.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
        days_ago = rng.uniform(0.1, days_back)
        when = now - timedelta(days=days_ago)
        duration_ms = rng.randint(5_000, 28_000)
        status_str = rng.choices(("resolved", "acknowledged", "open"), weights=(0.7, 0.2, 0.1))[0]
        confidence = round(rng.uniform(0.62, 0.96), 3)
        tokens = rng.randint(1500, 3500)

        # Map the synthetic strings to the typed enums the IncidentReport requires
        try:
            root_cause_enum = RootCauseCategory(category_str)
        except ValueError:
            # Defensive fallback — should not trigger now that ROOT_CAUSES uses
            # canonical enum values, but keeps the seeder resilient to drift.
            root_cause_enum = RootCauseCategory.UNKNOWN

        report = IncidentReport(
            incident_id=f"demo-seed-{i:03d}-{uuid.uuid4().hex[:8]}",
            detected_at=when,
            investigation_completed_at=when + timedelta(milliseconds=duration_ms),
            investigation_duration_ms=duration_ms,
            affected_entity_fqn=entity_fqn,
            test_name="row_count_check" if "rows" in narrative else "data_quality_check",
            test_type="DQ",
            failure_message=narrative,
            probable_root_cause=narrative,
            root_cause_category=root_cause_enum,
            confidence=confidence,
            business_impact=_SEVERITY_TO_IMPACT[severity],
            business_impact_reasoning=f"Affects {rng.randint(2, 14)} downstream consumers",
            status=_STATUS_MAP[status_str],
            agent_version="2.0.0-seed",
            llm_model_used="meta-llama/llama-4-scout-17b-16e-instruct",
            total_mcp_calls=rng.randint(3, 12),
            total_llm_tokens=tokens,
            resolved_at=when + timedelta(hours=rng.uniform(0.5, 6)) if status_str == "resolved" else None,
        )
        incident_store.store(report)
        seeded += 1

        if graphiti_ok:
            content = json.dumps(
                {
                    "incident_id": report.incident_id,
                    "entity_fqn": entity_fqn,
                    "entity_label": entity_label,
                    "root_cause_category": category_str,
                    "probable_root_cause": narrative,
                    "severity": severity,
                    "occurred_at": when.isoformat(),
                    "investigation_duration_ms": duration_ms,
                    "demo_seed": True,
                    "status": status_str,
                },
                default=str,
            )
            name = f"historical-incident:{entity_fqn}:{when.strftime('%Y%m%dT%H%M%S')}"
            try:
                await add_episode(
                    group_id=GROUP_ID,
                    name=name,
                    content=content,
                    source_type="json",
                    reference_time=when,
                )
            except Exception as exc:  # episode write is best-effort
                logger.debug("Graphiti episode write failed for #%d (non-fatal): %s", i, exc)

        logger.debug("Seeded #%d: %s @ %s (%s)", i, entity_fqn, when.isoformat(), severity)

    return seeded

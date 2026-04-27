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
from datetime import UTC, datetime, timedelta

from chronos.graphiti_client import _is_configured, add_episode

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

ROOT_CAUSES: tuple[tuple[str, str], ...] = (
    ("upstream_data_failure",
     "Upstream ETL job completed with 0 rows; downstream tables emptied"),
    ("schema_drift",
     "Source API v2.4 introduced a required NOT NULL column not in the schema"),
    ("data_quality",
     "Null-rate for primary key column exceeded 5% threshold"),
    ("infra",
     "Snowflake warehouse paused mid-run; partial commit left orphan records"),
    ("logic_error",
     "dbt model regression — JOIN condition lost a key after recent refactor"),
    ("permissions",
     "Service account JWT rotated; ingestion failed silently for 6 hours"),
    ("late_data",
     "Source CDC stream lag exceeded SLA; downstream rolled up incomplete data"),
    ("dependency_failure",
     "Upstream connector failed authentication; downstream pipeline received empty payload"),
)

SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
SEVERITY_WEIGHTS = (0.15, 0.35, 0.35, 0.15)  # most are MEDIUM/HIGH


async def seed_incidents(count: int = 30, days_back: int = 30, *, seed: int | None = None) -> int:
    """Populate Graphiti with ``count`` synthetic incidents over the past ``days_back`` days.

    Returns the number of episodes successfully written. When Graphiti is
    not configured (e.g., FalkorDB env vars unset), returns 0 with a warning.
    """
    if not _is_configured():
        logger.warning(
            "Graphiti not configured (FALKORDB_HOST is local default). "
            "Seeder will no-op. Configure FalkorDB Cloud and re-run — see SETUP.md."
        )
        return 0

    rng = random.Random(seed)
    now = datetime.now(UTC)
    seeded = 0

    for i in range(count):
        entity_fqn, entity_label = rng.choice(ENTITIES)
        category, narrative = rng.choice(ROOT_CAUSES)
        severity = rng.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
        days_ago = rng.uniform(0.1, days_back)
        when = now - timedelta(days=days_ago)
        duration_ms = rng.randint(5_000, 28_000)

        content = json.dumps(
            {
                "incident_id": f"demo-seed-{i:03d}",
                "entity_fqn": entity_fqn,
                "entity_label": entity_label,
                "root_cause_category": category,
                "probable_root_cause": narrative,
                "severity": severity,
                "occurred_at": when.isoformat(),
                "investigation_duration_ms": duration_ms,
                "demo_seed": True,
                "status": rng.choices(("resolved", "acknowledged", "open"), weights=(0.7, 0.2, 0.1))[0],
            },
            default=str,
        )
        name = f"historical-incident:{entity_fqn}:{when.strftime('%Y%m%dT%H%M%S')}"

        result = await add_episode(
            group_id=GROUP_ID,
            name=name,
            content=content,
            source_type="json",
            reference_time=when,
        )
        if result:
            seeded += 1
            logger.debug("Seeded #%d: %s @ %s (%s)", i, entity_fqn, when.isoformat(), severity)

    return seeded

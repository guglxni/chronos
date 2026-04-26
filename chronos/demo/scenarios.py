"""Pre-seeded investigation scenarios for the CHRONOS live demo."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


def _days_ago(n: int) -> str:
    return (datetime.now(UTC) - timedelta(days=n)).isoformat()

def _hours_ago(n: int) -> str:
    return (datetime.now(UTC) - timedelta(hours=n)).isoformat()


SCENARIOS: dict[str, dict[str, Any]] = {
    "row_count_failure": {
        "entity_fqn": "prod.orders.orders_daily",
        "test_name": "row_count_check",
        "failure_message": "Row count check failed: 0 rows found. Expected > 50,000. ETL job 'load_raw_orders' aborted at 03:14 UTC due to source DB connection timeout.",
        "temporal_changes": [
            {"type": "data_change", "table": "prod.orders.orders_daily", "description": "Row count dropped from 54,231 to 0 at 03:20 UTC", "timestamp": _hours_ago(6), "severity": "critical"},
            {"type": "job_failure", "table": "prod.sources.raw_orders", "description": "ETL job 'load_raw_orders' failed — connection timeout to orders-db-prod after 30s", "timestamp": _hours_ago(8), "severity": "high"},
        ],
        "schema_changes": [
            {"table": "prod.sources.raw_orders", "change": "Index on order_date removed in migration v2.1.4 — queries now doing full scans", "author": "pipeline-bot", "timestamp": _days_ago(2)},
        ],
        "upstream_failures": [
            {"table": "prod.sources.raw_orders", "failure": "Connection timeout to orders-db-prod OLTP — database under heavy load due to missing index", "duration_minutes": 47, "timestamp": _hours_ago(8)},
        ],
        "related_code_files": [
            {"file": "dbt/models/orders/orders_daily.sql", "change": "Changed source ref from raw_orders_v1 to raw_orders — dropped backward-compat alias", "commit": "a3f9e21", "author": "data-eng@company.com", "timestamp": _days_ago(3)},
            {"file": "pipelines/load_raw_orders.py", "change": "Removed retry logic on connection failure — PR #412 merged without review", "commit": "b8c2d14", "author": "pipeline-bot", "timestamp": _days_ago(2)},
        ],
        "downstream_assets": [
            {"fqn": "prod.reporting.revenue_daily", "display_name": "Revenue Daily", "tier": "Tier 1", "owners": ["analytics@company.com"]},
            {"fqn": "prod.reporting.customer_ltv", "display_name": "Customer LTV", "tier": "Tier 1", "owners": ["data-science@company.com"]},
            {"fqn": "prod.marketing.orders_agg", "display_name": "Orders Aggregate", "tier": "Tier 2", "owners": ["marketing@company.com"]},
        ],
        "audit_events": [
            {"user": "pipeline-bot", "action": "deploy", "resource": "pipelines/load_raw_orders.py", "timestamp": _days_ago(2)},
            {"user": "data-eng@company.com", "action": "merge_pr", "resource": "dbt/models/orders/orders_daily.sql", "timestamp": _days_ago(3)},
        ],
        "business_impact_score": "high",
    },
    "null_values": {
        "entity_fqn": "prod.customers.customer_profiles",
        "test_name": "not_null_customer_id",
        "failure_message": "Not-null check failed: 2,841 rows have NULL customer_id (5.3% of total). Affected records entered via CRM v3 migration.",
        "temporal_changes": [
            {"type": "schema_change", "table": "prod.customers.customer_profiles", "description": "Column 'customer_id' constraint changed from NOT NULL to NULLABLE — migration script dropped constraint without backfill", "timestamp": _days_ago(3), "severity": "high"},
            {"type": "data_load", "table": "prod.sources.crm_contacts", "description": "2,841 legacy CRM contacts imported without customer_id assignment", "timestamp": _days_ago(4), "severity": "medium"},
        ],
        "schema_changes": [
            {"table": "prod.customers.customer_profiles", "change": "ALTER TABLE customer_profiles ALTER COLUMN customer_id DROP NOT NULL — executed as part of CRM v3 migration", "author": "john.doe@company.com", "timestamp": _days_ago(3)},
        ],
        "upstream_failures": [],
        "related_code_files": [
            {"file": "dbt/models/customers/customer_profiles.sql", "change": "Removed COALESCE(customer_id, generate_uuid()) fallback — assumed CRM would provide IDs", "commit": "f2a8c93", "author": "john.doe@company.com", "timestamp": _days_ago(3)},
        ],
        "downstream_assets": [
            {"fqn": "prod.marketing.email_campaigns", "display_name": "Email Campaigns", "tier": "Tier 2", "owners": ["marketing@company.com"]},
            {"fqn": "prod.analytics.customer_segments", "display_name": "Customer Segments", "tier": "Tier 1", "owners": ["analytics@company.com"]},
        ],
        "audit_events": [
            {"user": "john.doe@company.com", "action": "schema_migration", "resource": "prod.customers.customer_profiles", "timestamp": _days_ago(3), "note": "CRM v3 migration — approved JIRA-4821"},
        ],
        "business_impact_score": "medium",
    },
    "schema_drift": {
        "entity_fqn": "prod.payments.payments_raw",
        "test_name": "schema_check_processor_fee",
        "failure_message": "Schema check failed: required column 'processor_fee' missing from 100% of new records ingested in the last 12 hours.",
        "temporal_changes": [
            {"type": "schema_change", "table": "prod.payments.payments_raw", "description": "New required field 'processor_fee' added by Stripe API v2.4 — ingestion pipeline does not extract it", "timestamp": _hours_ago(12), "severity": "high"},
        ],
        "schema_changes": [
            {"table": "prod.payments.payments_raw", "change": "Stripe API v2.4 (breaking): 'processor_fee' now required in all payment events — existing pipeline uses SELECT * without schema evolution", "author": "stripe-api-changelog", "timestamp": _hours_ago(12)},
        ],
        "upstream_failures": [
            {"table": "ext.stripe.payments", "failure": "Stripe API v2.4 breaking change: 'processor_fee' required in all payment objects — connector does not map this field", "duration_minutes": 720, "timestamp": _hours_ago(12)},
        ],
        "related_code_files": [
            {"file": "ingestion/stripe_payments_connector.py", "change": "No recent changes — last updated 45 days ago, hardcoded field list does not include 'processor_fee'", "commit": "old-stable", "author": "platform-team", "timestamp": _days_ago(45)},
        ],
        "downstream_assets": [
            {"fqn": "prod.finance.revenue_reconciliation", "display_name": "Revenue Reconciliation", "tier": "Tier 1", "owners": ["finance@company.com"]},
            {"fqn": "prod.finance.fee_analysis", "display_name": "Fee Analysis", "tier": "Tier 2", "owners": ["finance@company.com"]},
        ],
        "audit_events": [],
        "business_impact_score": "high",
    },
}

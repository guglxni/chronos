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
        "test_name": "dbt_expectations.expect_table_row_count_to_be_between",
        "failure_message": (
            "Table prod.orders.orders_daily has 0 rows. Expected between 45000 and 80000."
        ),
        "temporal_changes": [
            {
                "type": "data_change",
                "table": "prod.orders.orders_daily",
                "description": (
                    "Row count dropped 100% — from 61,842 rows at 02:00 UTC to 0 rows at 03:22 UTC"
                ),
                "timestamp": _hours_ago(6),
                "severity": "critical",
            },
            {
                "type": "job_failure",
                "table": "raw.orders.order_events",
                "description": (
                    "ETL job 'load_raw_orders' aborted at 03:14 UTC — connection pool to "
                    "orders-db-prod exhausted after 30s timeout. Source DB under full-table-scan "
                    "load following index removal in migration v2.1.4."
                ),
                "timestamp": _hours_ago(8),
                "severity": "critical",
            },
        ],
        "schema_changes": [
            {
                "table": "raw.orders.order_events",
                "change": (
                    "Index on 'order_date' (idx_order_events_date) dropped in DB migration v2.1.4. "
                    "All queries on order_date now execute full table scans on a 200M-row table."
                ),
                "author": "pipeline-bot",
                "timestamp": _hours_ago(6),
            },
        ],
        "upstream_failures": [
            {
                "table": "raw.orders.order_events",
                "failure": (
                    "Source DB connection pool exhausted — orders-db-prod under full-table-scan "
                    "load after idx_order_events_date was removed in migration v2.1.4. "
                    "All 20 connection pool slots occupied. ETL job timed out after 30s."
                ),
                "duration_minutes": 47,
                "timestamp": _hours_ago(8),
            },
        ],
        "related_code_files": [
            {
                "file": "pipelines/load_raw_orders.py",
                "change": (
                    "retry_on_failure decorator removed — PR #412 'simplify ETL error handling' "
                    "merged 3 days ago without data-eng review. Previously retried 3x with "
                    "exponential backoff on connection errors."
                ),
                "commit": "b8c2d14",
                "author": "pipeline-bot",
                "timestamp": _days_ago(3),
            },
            {
                "file": "migrations/v2_1_4_drop_order_date_index.sql",
                "change": (
                    "DROP INDEX idx_order_events_date ON order_events; — migration executed "
                    "6 hours ago as part of schema cleanup sprint. No rollback script included."
                ),
                "commit": "c9a1f03",
                "author": "data-eng@company.com",
                "timestamp": _hours_ago(6),
            },
        ],
        "downstream_assets": [
            {
                "fqn": "analytics.revenue_daily",
                "display_name": "Revenue Daily",
                "tier": "Tier 1",
                "owners": ["analytics@company.com"],
            },
            {
                "fqn": "analytics.customer_ltv",
                "display_name": "Customer LTV",
                "tier": "Tier 1",
                "owners": ["data-science@company.com"],
            },
            {
                "fqn": "reporting.orders_aggregate",
                "display_name": "Orders Aggregate",
                "tier": "Tier 2",
                "owners": ["marketing@company.com"],
            },
        ],
        "audit_events": [
            {
                "user": "data-eng@company.com",
                "action": "execute_migration",
                "resource": "migrations/v2_1_4_drop_order_date_index.sql",
                "timestamp": _hours_ago(6),
                "note": (
                    "Migration v2.1.4 executed against orders-db-prod. "
                    "Approved in JIRA-8834 (schema cleanup). No downtime window reserved."
                ),
            },
            {
                "user": "pipeline-bot",
                "action": "merge_pr",
                "resource": "pipelines/load_raw_orders.py",
                "timestamp": _days_ago(3),
                "note": "PR #412 auto-merged after 1 approval. retry_on_failure removed.",
            },
            {
                "user": "alerting-system",
                "action": "alert_fired",
                "resource": "orders-db-prod",
                "timestamp": _hours_ago(8),
                "note": "PagerDuty: DB connection pool at 100% — orders-db-prod",
            },
        ],
        "business_impact_score": "critical",
    },
    "null_values": {
        "entity_fqn": "prod.customers.customer_profiles",
        "test_name": "not_null.customer_id",
        "failure_message": (
            "53.2% of rows in prod.customers.customer_profiles have NULL customer_id. "
            "0 failures expected."
        ),
        "temporal_changes": [
            {
                "type": "data_change",
                "table": "prod.customers.customer_profiles",
                "description": (
                    "NULL rate on customer_id jumped from 0.0% to 53.2% immediately after "
                    "CRM migration batch completed at 14:30 UTC yesterday."
                ),
                "timestamp": _hours_ago(18),
                "severity": "high",
            },
            {
                "type": "data_load",
                "table": "raw.crm.contacts",
                "description": (
                    "CRM migration batch job inserted 184,392 records from legacy CRM export. "
                    "Batch ran incomplete — 98,097 records inserted without customer_id mapping."
                ),
                "timestamp": _hours_ago(20),
                "severity": "high",
            },
        ],
        "schema_changes": [
            {
                "table": "prod.customers.customer_profiles",
                "change": (
                    "Column renamed: cust_uuid → customer_id (CRM v3 migration). "
                    "NOT NULL constraint dropped on customer_id to accommodate legacy records "
                    "without UUIDs. Migration script used INSERT INTO ... SELECT without "
                    "mapping the renamed column."
                ),
                "author": "john.doe@company.com",
                "timestamp": _hours_ago(22),
            },
        ],
        "upstream_failures": [
            {
                "table": "raw.crm.contacts",
                "failure": (
                    "CRM migration batch job (crm_v3_migration.sql) ran incomplete — "
                    "INSERT INTO ... SELECT statement did not map legacy 'cust_uuid' column "
                    "to renamed 'customer_id' column. 98,097 of 184,392 inserted rows have "
                    "NULL customer_id."
                ),
                "duration_minutes": 0,
                "timestamp": _hours_ago(20),
            },
        ],
        "related_code_files": [
            {
                "file": "migrations/crm_v3_migration.sql",
                "change": (
                    "INSERT INTO customer_profiles (email, phone, created_at, ...) "
                    "SELECT email, phone, created_at, ... FROM legacy_crm_contacts — "
                    "cust_uuid column omitted from SELECT, customer_id receives NULL for "
                    "all legacy records."
                ),
                "commit": "f2a8c93",
                "author": "john.doe@company.com",
                "timestamp": _hours_ago(22),
            },
        ],
        "downstream_assets": [
            {
                "fqn": "analytics.user_segments",
                "display_name": "User Segments",
                "tier": "Tier 1",
                "owners": ["analytics@company.com"],
            },
            {
                "fqn": "ml.propensity_scores",
                "display_name": "Propensity Scores",
                "tier": "Tier 1",
                "owners": ["ml-platform@company.com"],
            },
            {
                "fqn": "reporting.crm_dashboard",
                "display_name": "CRM Dashboard",
                "tier": "Tier 2",
                "owners": ["sales@company.com"],
            },
        ],
        "audit_events": [
            {
                "user": "john.doe@company.com",
                "action": "execute_migration",
                "resource": "migrations/crm_v3_migration.sql",
                "timestamp": _hours_ago(22),
                "note": (
                    "CRM v3 migration approved JIRA-9201. Migration script not reviewed by "
                    "data engineering — approved by CRM team lead only."
                ),
            },
            {
                "user": "john.doe@company.com",
                "action": "schema_change",
                "resource": "prod.customers.customer_profiles",
                "timestamp": _hours_ago(22),
                "note": "ALTER TABLE: renamed cust_uuid → customer_id, dropped NOT NULL constraint.",
            },
            {
                "user": "dbt-cloud",
                "action": "test_failure",
                "resource": "not_null.customer_id",
                "timestamp": _hours_ago(16),
                "note": (
                    "dbt test not_null_customer_profiles_customer_id FAILED — "
                    "98097 failures out of 184392 records."
                ),
            },
        ],
        "business_impact_score": "high",
    },
    "schema_drift": {
        "entity_fqn": "prod.payments.payments_raw",
        "test_name": "schema_change_detector",
        "failure_message": (
            "Schema drift detected in prod.payments.payments_raw: column 'processor_fee' "
            "added as NOT NULL with no default, breaking 847 pipeline jobs."
        ),
        "temporal_changes": [
            {
                "type": "schema_change",
                "table": "prod.payments.payments_raw",
                "description": (
                    "100% of new rows failing schema validation since Stripe API v2.4 rollout "
                    "12 hours ago. Column 'processor_fee DECIMAL(10,4) NOT NULL' added by API "
                    "but not extracted by Stripe connector v1.8.2."
                ),
                "timestamp": _hours_ago(12),
                "severity": "high",
            },
        ],
        "schema_changes": [
            {
                "table": "prod.payments.payments_raw",
                "change": (
                    "Stripe API v2.4 (breaking change): 'processor_fee DECIMAL(10,4) NOT NULL' "
                    "added as a required field in all payment event objects. "
                    "Stripe connector v1.8.2 hardcodes field extraction list — "
                    "processor_fee not included, resulting in NULL on a NOT NULL column."
                ),
                "author": "stripe-api-changelog",
                "timestamp": _hours_ago(12),
            },
        ],
        "upstream_failures": [
            {
                "table": "ext.stripe.payments",
                "failure": (
                    "Stripe webhook connector v1.8.2 missing 'processor_fee' field extraction. "
                    "Connector last updated 45 days ago with hardcoded field list. "
                    "Stripe API v2.4 made processor_fee required in all payment objects — "
                    "all new inserts attempt NULL into a NOT NULL column."
                ),
                "duration_minutes": 720,
                "timestamp": _hours_ago(12),
            },
        ],
        "related_code_files": [
            {
                "file": "ingestion/stripe_connector/field_extractor.py",
                "change": (
                    "PAYMENT_FIELDS = ['id', 'amount', 'currency', 'status', 'created', ...] — "
                    "hardcoded list does not include 'processor_fee'. "
                    "Last modified 45 days ago (v1.8.2). No dynamic schema discovery."
                ),
                "commit": "a1b2c3d",
                "author": "platform-team@company.com",
                "timestamp": _days_ago(45),
            },
            {
                "file": "dbt/models/payments/payments_raw.sql",
                "change": (
                    "Schema test 'schema_change_detector' added 30 days ago but threshold "
                    "set to warn-only — alert was suppressed, not escalated."
                ),
                "commit": "e4f5a6b",
                "author": "data-eng@company.com",
                "timestamp": _days_ago(30),
            },
        ],
        "downstream_assets": [
            {
                "fqn": "analytics.payment_reconciliation",
                "display_name": "Payment Reconciliation",
                "tier": "Tier 1",
                "owners": ["finance@company.com"],
            },
            {
                "fqn": "finance.stripe_settlements",
                "display_name": "Stripe Settlements",
                "tier": "Tier 1",
                "owners": ["finance@company.com"],
            },
            {
                "fqn": "reporting.revenue_by_processor",
                "display_name": "Revenue by Processor",
                "tier": "Tier 2",
                "owners": ["analytics@company.com"],
            },
        ],
        "audit_events": [
            {
                "user": "stripe-webhook-system",
                "action": "api_version_upgrade",
                "resource": "ext.stripe.payments",
                "timestamp": _hours_ago(12),
                "note": (
                    "Stripe API version upgraded to v2.4 on Stripe dashboard. "
                    "Breaking change: processor_fee now required in all payment objects."
                ),
            },
            {
                "user": "alerting-system",
                "action": "schema_drift_alert",
                "resource": "prod.payments.payments_raw",
                "timestamp": _hours_ago(11),
                "note": (
                    "847 pipeline jobs failed with NOT NULL constraint violation on processor_fee. "
                    "Alert severity: warn — escalation suppressed by dbt project config."
                ),
            },
        ],
        "business_impact_score": "high",
    },
}

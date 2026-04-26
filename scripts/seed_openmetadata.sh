#!/usr/bin/env bash
# Seed OpenMetadata with a demo data pipeline for CHRONOS hackathon.
#
# Creates:
#   - Database service "analytics_warehouse"
#   - Tables: orders (Tier1), order_items (Tier1), dim_products (Tier2),
#             daily_revenue (Tier1), executive_dashboard (Tier1)
#   - Lineage: order_items + dim_products → orders → daily_revenue → executive_dashboard
#   - Test cases on "orders" with a recent failure
#   - Tier tags and owner annotations
#
# Usage:
#   ./scripts/seed_openmetadata.sh [--host http://localhost:8585] [--token <jwt>]

set -euo pipefail

OM_HOST="${OM_HOST:-http://localhost:8585}"
OM_TOKEN="${OM_TOKEN:-}"  # leave empty for no-auth mode

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) OM_HOST="$2"; shift 2 ;;
    --token) OM_TOKEN="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

API="${OM_HOST}/api/v1"
AUTH_HEADER=""
[[ -n "${OM_TOKEN}" ]] && AUTH_HEADER="Authorization: Bearer ${OM_TOKEN}"

curl_om() {
  local method="$1"; local path="$2"; local body="${3:-}"
  local args=(-s -X "${method}" "${API}${path}"
    -H "Content-Type: application/json"
    -H "Accept: application/json")
  [[ -n "${AUTH_HEADER}" ]] && args+=(-H "${AUTH_HEADER}")
  [[ -n "${body}" ]] && args+=(-d "${body}")
  curl "${args[@]}"
}

echo "→ Waiting for OpenMetadata at ${OM_HOST}…"
until curl_om GET "/system/status" | grep -q '"healthy"'; do
  sleep 3
done
echo "  OK"

# ── 1. Database service ───────────────────────────────────────────────────────
echo "→ Creating database service 'analytics_warehouse'…"
curl_om PUT "/services/databaseServices" "$(cat <<'JSON'
{
  "name": "analytics_warehouse",
  "serviceType": "BigQuery",
  "connection": {
    "config": {
      "type": "BigQuery",
      "credentials": {"gcpConfig": {"type": "external"}}
    }
  }
}
JSON
)" > /dev/null

# ── 2. Database ───────────────────────────────────────────────────────────────
echo "→ Creating database 'analytics_db'…"
curl_om PUT "/databases" "$(cat <<'JSON'
{
  "name": "analytics_db",
  "service": "analytics_warehouse"
}
JSON
)" > /dev/null

# ── 3. Schema ─────────────────────────────────────────────────────────────────
echo "→ Creating schema 'public'…"
curl_om PUT "/databaseSchemas" "$(cat <<'JSON'
{
  "name": "public",
  "database": "analytics_warehouse.analytics_db"
}
JSON
)" > /dev/null

# Helper: create a table
create_table() {
  local name="$1"; local description="$2"
  curl_om PUT "/tables" "$(cat <<JSON
{
  "name": "${name}",
  "description": "${description}",
  "tableType": "Regular",
  "databaseSchema": "analytics_warehouse.analytics_db.public",
  "columns": [
    {"name": "id",         "dataType": "BIGINT",    "constraint": "PRIMARY_KEY"},
    {"name": "created_at", "dataType": "TIMESTAMP", "nullable": false},
    {"name": "updated_at", "dataType": "TIMESTAMP", "nullable": true}
  ]
}
JSON
)" > /dev/null
  echo "  Created table '${name}'"
}

# ── 4. Tables ─────────────────────────────────────────────────────────────────
echo "→ Creating tables…"
create_table "orders"               "Core orders fact table — Tier1 critical"
create_table "order_items"          "Line items for each order — Tier1 upstream"
create_table "dim_products"         "Product dimension — Tier2 upstream"
create_table "daily_revenue"        "Aggregated daily revenue — Tier1 downstream"
create_table "executive_dashboard"  "Executive KPI dashboard feed — Tier1 downstream"

# ── 5. Tier tags ──────────────────────────────────────────────────────────────
echo "→ Applying tier tags…"
apply_tier() {
  local fqn="analytics_warehouse.analytics_db.public.${1}"
  local tier="$2"
  curl_om PATCH "/tables/name/${fqn}" "$(cat <<JSON
[{"op": "add", "path": "/tags", "value": [{"tagFQN": "Tier.${tier}"}]}]
JSON
)" > /dev/null
  echo "  Tagged '${1}' as ${tier}"
}
apply_tier "orders"               "Tier1"
apply_tier "order_items"          "Tier1"
apply_tier "dim_products"         "Tier2"
apply_tier "daily_revenue"        "Tier1"
apply_tier "executive_dashboard"  "Tier1"

# ── 6. Lineage ────────────────────────────────────────────────────────────────
echo "→ Creating lineage…"
add_lineage() {
  local from_fqn="analytics_warehouse.analytics_db.public.${1}"
  local to_fqn="analytics_warehouse.analytics_db.public.${2}"
  curl_om PUT "/lineage" "$(cat <<JSON
{
  "edge": {
    "fromEntity": {"type": "table", "fullyQualifiedName": "${from_fqn}"},
    "toEntity":   {"type": "table", "fullyQualifiedName": "${to_fqn}"}
  }
}
JSON
)" > /dev/null
  echo "  ${1} → ${2}"
}
add_lineage "order_items"   "orders"
add_lineage "dim_products"  "orders"
add_lineage "orders"        "daily_revenue"
add_lineage "daily_revenue" "executive_dashboard"

# ── 7. Test cases on 'orders' ─────────────────────────────────────────────────
echo "→ Creating test cases on 'orders'…"
ORDERS_FQN="analytics_warehouse.analytics_db.public.orders"

create_test() {
  local test_name="$1"; local definition="$2"; local entity_link="$3"
  local params_json="$4"
  curl_om PUT "/dataQuality/testCases" "$(cat <<JSON
{
  "name": "${test_name}",
  "entityLink": "${entity_link}",
  "testDefinition": "${definition}",
  "parameterValues": ${params_json}
}
JSON
)" > /dev/null
  echo "  Created test '${test_name}' (${definition})"
}

# Table-level test: row count >= 1000
create_test "orders_row_count_check" \
  "tableRowCountToBeBetween" \
  "<#E::table::${ORDERS_FQN}>" \
  '[{"name": "minValue", "value": "1000"}, {"name": "maxValue", "value": "10000000"}]'

# Column-level test: order_id has no nulls (will be failed below)
create_test "orders_not_null_order_id" \
  "columnValuesToBeNotNull" \
  "<#E::table::${ORDERS_FQN}::columns::id>" \
  '[]'

# Column-level test: id values are unique
create_test "orders_unique_order_id" \
  "columnValuesToBeUnique" \
  "<#E::table::${ORDERS_FQN}::columns::id>" \
  '[]'

# ── 8. Inject a test failure ──────────────────────────────────────────────────
echo "→ Injecting test failure on 'orders_not_null_order_id'…"
NOW_MS=$(date +%s)000
curl_om POST "/dataQuality/testCases/analytics_warehouse.analytics_db.public.orders.orders_not_null_order_id/testCaseResult" \
  "$(cat <<JSON
{
  "timestamp": ${NOW_MS},
  "testCaseStatus": "Failed",
  "result": "Found 42 null values in column 'id'",
  "testResultValue": [{"name": "nullCount", "value": "42"}]
}
JSON
)" > /dev/null
echo "  Failure injected"

# ── 9. Owner annotations ──────────────────────────────────────────────────────
# OpenMetadata 1.3+ replaces the scalar `/owner` field with an `/owners` array
# (EntityReference[]).  Using the old path silently drops the annotation.
echo "→ Adding owner 'data-engineering-team' to Tier1 tables…"
for tbl in orders order_items daily_revenue executive_dashboard; do
  FQN="analytics_warehouse.analytics_db.public.${tbl}"
  curl_om PATCH "/tables/name/${FQN}" "$(cat <<JSON
[{"op": "add", "path": "/owners", "value": [{"type": "team", "name": "data-engineering-team"}]}]
JSON
)" > /dev/null
done
echo "  Done"

echo ""
echo "Seed complete. OpenMetadata demo data is ready at ${OM_HOST}."
echo "Trigger a CHRONOS investigation with:"
echo "  python scripts/demo_inject_failure.py \\"
echo "    --entity analytics_warehouse.analytics_db.public.orders \\"
echo "    --test orders_not_null_order_id"

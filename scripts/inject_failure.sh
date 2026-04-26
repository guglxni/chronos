#!/usr/bin/env bash
# Demo wrapper: inject a test-case-failed webhook into CHRONOS with HMAC signing.
#
# Production (`ENVIRONMENT=production`) forces `webhook_signature_required=True`;
# this wrapper signs the POST body with HMAC-SHA256 of `{timestamp}.{body}` using
# WEBHOOK_HMAC_SECRET (matching chronos.api.dependencies._compute_hmac).
#
# Usage:
#   WEBHOOK_HMAC_SECRET=<secret> ./scripts/inject_failure.sh \
#     [--host http://localhost:8100] \
#     [--entity sample_db.default.orders] \
#     [--test column_values_to_be_not_null]
#
# Unsigned mode (development only):
#   ./scripts/inject_failure.sh --unsigned

set -euo pipefail

HOST="${HOST:-http://localhost:8100}"
ENTITY="${ENTITY:-sample_db.default.orders}"
TEST_NAME="${TEST_NAME:-column_values_to_be_not_null}"
COLUMN="${COLUMN:-order_id}"
SECRET="${WEBHOOK_HMAC_SECRET:-}"
UNSIGNED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --entity) ENTITY="$2"; shift 2 ;;
    --test) TEST_NAME="$2"; shift 2 ;;
    --column) COLUMN="$2"; shift 2 ;;
    --unsigned) UNSIGNED=1; shift ;;
    -h|--help)
      grep -E '^#' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

if [[ "${UNSIGNED}" -eq 0 && -z "${SECRET}" ]]; then
  echo "ERROR: WEBHOOK_HMAC_SECRET is required (or pass --unsigned for dev)." >&2
  exit 2
fi

TIMESTAMP_MS=$(date +%s)000
TIMESTAMP_SEC=$(($(date +%s)))
ENTITY_FQN="${ENTITY}.${TEST_NAME}.${COLUMN}"

BODY=$(cat <<JSON
{
  "eventType": "TEST_CASE_FAILED",
  "entityType": "testCase",
  "entityId": "demo-test-$(date +%s)",
  "entityFullyQualifiedName": "${ENTITY_FQN}",
  "userName": "openmetadata_bot",
  "timestamp": ${TIMESTAMP_MS},
  "entity": {
    "id": "demo-test-$(date +%s)",
    "name": "${TEST_NAME}",
    "fullyQualifiedName": "${ENTITY_FQN}",
    "entityLink": "<#E::table::${ENTITY}::columns::${COLUMN}>",
    "testCaseResult": {
      "testCaseStatus": "Failed",
      "result": "Found 1523 null values in ${COLUMN} column. Expected 0 nulls.",
      "testResultValue": [{"value": "1523", "name": "nullCount"}]
    }
  }
}
JSON
)

HEADERS=(-H "Content-Type: application/json")

if [[ "${UNSIGNED}" -eq 0 ]]; then
  # Sign {timestamp}.{body} with HMAC-SHA256 — matches _compute_hmac in dependencies.py
  SIG_PAYLOAD="${TIMESTAMP_SEC}.${BODY}"
  SIGNATURE=$(printf '%s' "${SIG_PAYLOAD}" \
    | openssl dgst -sha256 -hmac "${SECRET}" \
    | awk '{print $2}')
  HEADERS+=(-H "X-OM-Timestamp: ${TIMESTAMP_SEC}")
  HEADERS+=(-H "X-OM-Signature: sha256=${SIGNATURE}")
  echo "→ Sending signed webhook (ts=${TIMESTAMP_SEC})…"
else
  echo "→ Sending UNSIGNED webhook (dev mode)…"
fi

RESPONSE=$(curl -sS -X POST "${HOST}/api/v1/webhooks/openmetadata" \
  "${HEADERS[@]}" \
  --data-raw "${BODY}")

echo "→ Response:"
echo "${RESPONSE}" | python3 -m json.tool 2>/dev/null || echo "${RESPONSE}"

INCIDENT_ID=$(echo "${RESPONSE}" | python3 -c "import json, sys; print(json.load(sys.stdin).get('incident_id', ''))" 2>/dev/null || echo "")

if [[ -n "${INCIDENT_ID}" ]]; then
  echo ""
  echo "  Dashboard : http://localhost:3000/incidents/${INCIDENT_ID}"
  echo "  Stream    : ${HOST}/api/v1/investigations/${INCIDENT_ID}/stream"
  echo "  PROV-O    : ${HOST}/api/v1/incidents/${INCIDENT_ID}/provenance.jsonld"
fi

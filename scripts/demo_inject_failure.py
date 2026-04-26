#!/usr/bin/env python3
"""
Demo script: inject a schema change test failure into CHRONOS.

Usage:
    python scripts/demo_inject_failure.py [--host http://localhost:8100] [--secret <hmac_secret>]

What it does:
1. POSTs a TEST_CASE_FAILED webhook to CHRONOS (with optional HMAC signing)
2. Polls until the incident appears (no hard-coded sleep)
3. Prints the incident report summary
"""
import argparse
import asyncio
import hashlib
import hmac
import json
import sys
import time

import httpx


WEBHOOK_PAYLOAD_TEMPLATE = {
    "eventType": "TEST_CASE_FAILED",
    "entityType": "testCase",
    "entityId": "demo-test-uuid-001",
    "entityFullyQualifiedName": "sample_db.default.orders.column_values_to_be_not_null.order_id",
    "userName": "openmetadata_bot",
    "entity": {
        "id": "demo-test-uuid-001",
        "name": "column_values_to_be_not_null",
        "fullyQualifiedName": "sample_db.default.orders.column_values_to_be_not_null.order_id",
        "entityLink": "<#E::table::sample_db.default.orders::columns::order_id>",
        "testCaseResult": {
            "testCaseStatus": "Failed",
            "result": "Found 1523 null values in order_id column. Expected 0 nulls.",
            "testResultValue": [{"value": "1523", "name": "nullCount"}],
        },
    },
}


def _sign_payload(body_bytes: bytes, secret: str, timestamp: str) -> str:
    """Return sha256=<hmac> over f'{timestamp}.{body}', matching _compute_hmac in dependencies.py."""
    payload = f"{timestamp}.".encode() + body_bytes
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def main(host: str, secret: str | None) -> None:
    ts = str(int(time.time()))
    payload = {**WEBHOOK_PAYLOAD_TEMPLATE, "timestamp": int(ts) * 1000}
    body_bytes = json.dumps(payload).encode()

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if secret:
        headers["X-OM-Timestamp"] = ts
        headers["X-OM-Signature"] = _sign_payload(body_bytes, secret, ts)
        print(f"[demo] HMAC signing enabled (timestamp={ts})")

    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"[demo] Sending TEST_CASE_FAILED webhook to {host}...")
        resp = await client.post(
            f"{host}/api/v1/webhooks/openmetadata",
            content=body_bytes,
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"[demo] ERROR {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)

        result = resp.json()
        print(f"[demo] Webhook accepted: {json.dumps(result, indent=2)}")

        # Poll until the incident appears (up to 90 s)
        incident_id: str | None = result.get("incident_id")
        print(f"\n[demo] Polling for investigation result (incident_id={incident_id})...")
        deadline = time.time() + 90
        incident = None
        while time.time() < deadline:
            await asyncio.sleep(3)
            if incident_id:
                r = await client.get(f"{host}/api/v1/incidents/{incident_id}")
                if r.status_code == 200:
                    incident = r.json()
                    break
            else:
                r = await client.get(f"{host}/api/v1/incidents?limit=1")
                if r.status_code == 200 and r.json().get("incidents"):
                    incident = r.json()["incidents"][0]
                    break

        if not incident:
            print("[demo] Investigation still running — check the dashboard.", file=sys.stderr)
            sys.exit(1)

        sep = "=" * 60
        print(f"\n{sep}")
        print("INCIDENT REPORT SUMMARY")
        print(sep)
        print(f"  Incident ID   : {incident.get('incident_id')}")
        print(f"  Entity FQN    : {incident.get('affected_entity_fqn')}")
        print(f"  Root Cause    : {incident.get('root_cause_category')}")
        print(f"  Confidence    : {incident.get('confidence', 0) * 100:.0f}%")
        print(f"  Impact        : {incident.get('business_impact', '').upper()}")
        print(f"  Duration (ms) : {incident.get('investigation_duration_ms', 'N/A')}")
        print(f"  Analysis      : {incident.get('probable_root_cause', '')}")
        print(f"  Status        : {incident.get('status')}")
        print(f"\n  Dashboard     : http://localhost:3000/incidents/{incident.get('incident_id')}")
        print(
            f"  PROV-O        : {host}/api/v1/incidents/"
            f"{incident.get('incident_id')}/provenance.jsonld"
        )
        print(sep)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CHRONOS demo — inject test failure")
    parser.add_argument("--host", default="http://localhost:8100", help="CHRONOS server URL")
    parser.add_argument("--secret", default=None, help="WEBHOOK_HMAC_SECRET for signing")
    args = parser.parse_args()
    asyncio.run(main(args.host, args.secret))

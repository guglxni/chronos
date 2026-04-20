#!/usr/bin/env python3
"""
Demo script: inject a schema change test failure into CHRONOS.

Usage:
    python scripts/demo_inject_failure.py [--host http://localhost:8100]

What it does:
1. POSTs a TEST_CASE_FAILED webhook to CHRONOS
2. Polls for the investigation result
3. Prints the incident report summary
"""
import argparse
import asyncio
import json
import sys
import time
import httpx


WEBHOOK_PAYLOAD = {
    "eventType": "TEST_CASE_FAILED",
    "entityType": "testCase",
    "entityId": "demo-test-uuid-001",
    "entityFullyQualifiedName": "sample_db.default.orders.column_values_to_be_not_null.order_id",
    "userName": "openmetadata_bot",
    "timestamp": int(time.time() * 1000),
    "entity": {
        "id": "demo-test-uuid-001",
        "name": "column_values_to_be_not_null",
        "fullyQualifiedName": "sample_db.default.orders.column_values_to_be_not_null.order_id",
        "entityLink": "<#E::table::sample_db.default.orders::columns::order_id>",
        "testCaseResult": {
            "testCaseStatus": "Failed",
            "timestamp": int(time.time() * 1000),
            "result": "Found 1523 null values in order_id column. Expected 0 nulls.",
            "testResultValue": [{"value": "1523", "name": "nullCount"}],
        },
    },
}


async def main(host: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"[demo] Sending TEST_CASE_FAILED webhook to {host}...")
        resp = await client.post(
            f"{host}/api/v1/webhooks/openmetadata",
            json=WEBHOOK_PAYLOAD,
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"[demo] Webhook response: {json.dumps(result, indent=2)}")

        print("\n[demo] Waiting 10s for investigation to start...")
        await asyncio.sleep(10)

        print("[demo] Fetching latest incident...")
        incidents_resp = await client.get(f"{host}/api/v1/incidents?limit=1")
        incidents_resp.raise_for_status()
        data = incidents_resp.json()

        if not data.get("incidents"):
            print("[demo] No incidents found yet — investigation may still be running.")
            return

        incident = data["incidents"][0]
        print(f"\n{'='*60}")
        print(f"INCIDENT REPORT SUMMARY")
        print(f"{'='*60}")
        print(f"  Incident ID  : {incident.get('incident_id')}")
        print(f"  Entity FQN   : {incident.get('affected_entity_fqn')}")
        print(f"  Root Cause   : {incident.get('root_cause_category')}")
        print(f"  Confidence   : {incident.get('confidence', 0) * 100:.0f}%")
        print(f"  Impact       : {incident.get('business_impact', '').upper()}")
        print(f"  Analysis     : {incident.get('probable_root_cause', '')}")
        print(f"  Status       : {incident.get('status')}")
        print(f"\n  Dashboard    : http://localhost:3000/incidents/{incident.get('incident_id')}")
        print(f"  PROV-O       : {host}/api/v1/incidents/{incident.get('incident_id')}/provenance.jsonld")
        print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CHRONOS demo — inject test failure")
    parser.add_argument("--host", default="http://localhost:8100", help="CHRONOS server URL")
    args = parser.parse_args()
    asyncio.run(main(args.host))

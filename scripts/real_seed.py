#!/usr/bin/env python
"""
Populate CHRONOS with REAL investigations against REAL OpenMetadata entities.

Replaces the synthetic seeder. For each entity:
  1. Fetch a real table FQN from the live OpenMetadata sandbox
  2. POST it to CHRONOS /api/v1/demo/run with a realistic test scenario
  3. The CHRONOS agent runs the live LangGraph pipeline (real LLM call,
     real lineage walk, real evidence chain) — typically 10-15s per
     investigation
  4. Poll until the IncidentReport is stored

The dashboard then shows actual investigations, not mocks.

Usage:
    # against the deployed Heroku backend
    python scripts/real_seed.py --count 8

    # against a different host
    python scripts/real_seed.py --api https://localhost:8100 --count 3
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import time
from typing import Any

import httpx

DEFAULT_API = "https://chronos-api-0e8635fe890d.herokuapp.com"
DEFAULT_OM = "https://sandbox.open-metadata.org"

# Map of (scenario_id, test_name) — these match the scenarios in
# chronos/api/routes/demo.py and produce different RCA narratives.
SCENARIOS: list[tuple[str, str]] = [
    ("row_count_failure",  "row_count_check"),
    ("null_values",        "not_null_customer_id"),
    ("schema_drift",       "schema_check"),
    ("row_count_failure",  "freshness_check"),
    ("null_values",        "not_null_email"),
]


def green(msg: str) -> None: print(f"\033[32m✓\033[0m {msg}")
def red(msg: str) -> None: print(f"\033[31m✗\033[0m {msg}", file=sys.stderr)
def dim(msg: str) -> None: print(f"\033[2m  {msg}\033[0m")
def bold(msg: str) -> None: print(f"\033[1m{msg}\033[0m")


async def fetch_real_entities(om_host: str, om_jwt: str | None, limit: int) -> list[dict[str, Any]]:
    """Fetch real table entities from OpenMetadata. Returns up to `limit` tables."""
    url = f"{om_host.rstrip('/')}/api/v1/tables?limit={limit}&fields=name,fullyQualifiedName,owners,tags"
    headers = {"Authorization": f"Bearer {om_jwt}"} if om_jwt else {}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    tables = data.get("data", [])
    dim(f"Fetched {len(tables)} real tables from OpenMetadata (out of paging.total = {data.get('paging', {}).get('total', '?')})")
    return tables


async def trigger_investigation(api: str, entity_fqn: str, scenario: str, test_name: str) -> str | None:
    """POST to /api/v1/demo/run and return the incident_id."""
    payload = {"scenario": scenario, "entity_fqn": entity_fqn, "test_name": test_name}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{api.rstrip('/')}/api/v1/demo/run", json=payload)
        if resp.status_code != 200:
            red(f"trigger failed for {entity_fqn}: HTTP {resp.status_code} — {resp.text[:120]}")
            return None
        return resp.json().get("incident_id")


async def poll_until_complete(api: str, incident_id: str, timeout_s: int = 60) -> dict[str, Any] | None:
    """Poll /api/v1/incidents/{id} until probable_root_cause is set."""
    deadline = time.time() + timeout_s
    async with httpx.AsyncClient(timeout=10) as client:
        while time.time() < deadline:
            try:
                resp = await client.get(f"{api.rstrip('/')}/api/v1/incidents/{incident_id}")
                if resp.status_code == 200:
                    body = resp.json()
                    if body.get("probable_root_cause"):
                        return body
            except Exception:
                pass
            await asyncio.sleep(2)
    return None


async def run(api: str, om_host: str, om_jwt: str | None, count: int, *, seed: int | None = None) -> int:
    bold("\nReal-investigation seeder")
    print("═══════════════════════════════════════════════════════════════")
    dim(f"CHRONOS API   : {api}")
    dim(f"OpenMetadata  : {om_host}")
    dim(f"Target count  : {count}\n")

    # Step 1 — pull real tables
    try:
        tables = await fetch_real_entities(om_host, om_jwt, max(count * 3, 30))
    except Exception as exc:
        red(f"Could not fetch entities from OM: {exc}")
        return 1

    if not tables:
        red("OpenMetadata returned 0 tables — cannot seed.")
        return 1

    rng = random.Random(seed)
    rng.shuffle(tables)
    selected = tables[:count]

    print()
    bold(f"Triggering {len(selected)} real investigations (rate-limited: 10/min)")
    print("─────────────────────────────────────────────────────────────────")

    successes = 0
    for i, table in enumerate(selected, 1):
        fqn = table.get("fullyQualifiedName") or table.get("name") or "unknown"
        scenario, test_name = rng.choice(SCENARIOS)
        print(f"\n[{i}/{len(selected)}] {fqn}")
        dim(f"  scenario={scenario} · test={test_name}")

        incident_id = await trigger_investigation(api, fqn, scenario, test_name)
        if not incident_id:
            continue
        dim(f"  triggered incident_id={incident_id}")

        report = await poll_until_complete(api, incident_id, timeout_s=45)
        if report:
            green(f"completed: '{report.get('probable_root_cause', '')[:80]}…' "
                  f"(confidence {report.get('confidence', 0):.2f}, "
                  f"{report.get('total_llm_tokens', 0)} tokens, "
                  f"{report.get('investigation_duration_ms', 0)/1000:.1f}s)")
            successes += 1
        else:
            red(f"timed out waiting for {incident_id}")

        # Respect the demo route's 10/minute rate limit
        if i < len(selected):
            await asyncio.sleep(7)

    print("\n═══════════════════════════════════════════════════════════════")
    if successes == len(selected):
        green(f"All {successes} investigations completed against live OpenMetadata.")
    else:
        red(f"{successes}/{len(selected)} succeeded. Check Heroku logs for the rest.")
    return 0 if successes else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default=DEFAULT_API, help="CHRONOS API base URL")
    parser.add_argument("--om",  default=DEFAULT_OM,  help="OpenMetadata base URL")
    parser.add_argument("--om-jwt", default=None,
                        help="OpenMetadata bearer token (optional for sandbox)")
    parser.add_argument("--count", type=int, default=8, help="Number of investigations")
    parser.add_argument("--seed",  type=int, default=None, help="Reproducible RNG seed")
    args = parser.parse_args()

    return asyncio.run(run(args.api, args.om, args.om_jwt, args.count, seed=args.seed))


if __name__ == "__main__":
    raise SystemExit(main())

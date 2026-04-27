#!/usr/bin/env python
"""
One-shot connection verifier — checks FalkorDB + OpenMetadata are reachable
with the given credentials before pushing anything to .env or Heroku.

Usage:
    python scripts/verify_connections.py \
        --falkor-host r-xxxxx.aws.cloud.falkordb.io \
        --falkor-port 12345 \
        --falkor-password 'uoW7uu8stixi' \
        --om-host https://sandbox.open-metadata.org \
        --om-jwt 'eyJ...'
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import httpx
import redis.asyncio as aioredis


def green(msg: str) -> None:
    print(f"\033[32m✓\033[0m {msg}")


def red(msg: str) -> None:
    print(f"\033[31m✗\033[0m {msg}", file=sys.stderr)


def dim(msg: str) -> None:
    print(f"\033[2m  {msg}\033[0m")


async def verify_falkor(host: str, port: int, password: str, username: str | None = None) -> bool:
    print(f"\nFalkorDB → {host}:{port} (user={username or 'default'})")
    client: aioredis.Redis | None = None
    try:
        kwargs: dict = {
            "host": host,
            "port": port,
            "password": password,
            "ssl": True,                    # FalkorDB Cloud requires TLS
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "decode_responses": True,
        }
        if username:
            kwargs["username"] = username
        client = aioredis.Redis(**kwargs)
        pong = await asyncio.wait_for(client.ping(), timeout=5)
        if pong:
            green(f"PING → PONG ({host}:{port})")
            # Try a no-op graph command to verify FalkorDB module is loaded
            try:
                modules = await client.execute_command("MODULE", "LIST")
                has_graph = any(
                    "graph" in str(m).lower() if isinstance(m, (str, bytes))
                    else any("graph" in str(item).lower() for item in m)
                    for m in (modules or [])
                )
                dim(f"MODULE LIST → graph module {'present' if has_graph else 'unknown'}")
            except Exception as exc:
                dim(f"(MODULE LIST not supported on this plan: {exc})")
            return True
        red(f"PING returned falsy: {pong!r}")
        return False
    except Exception as exc:
        red(f"FalkorDB unreachable: {type(exc).__name__}: {exc}")
        return False
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


async def verify_om(host: str, jwt: str) -> bool:
    print(f"\nOpenMetadata → {host}")
    headers = {"Authorization": f"Bearer {jwt}"}
    async with httpx.AsyncClient(timeout=5) as client:
        # Step 1: version endpoint (sanity check — should always return 200)
        try:
            resp = await client.get(f"{host.rstrip('/')}/api/v1/system/version", headers=headers)
            if resp.status_code != 200:
                red(f"GET /api/v1/system/version → {resp.status_code}")
                return False
            data = resp.json()
            green(f"version endpoint → {data.get('version', '<no version field>')}")
        except Exception as exc:
            red(f"version endpoint failed: {type(exc).__name__}: {exc}")
            return False

        # Step 2: authenticated endpoint — list tables (verifies JWT is valid)
        try:
            resp = await client.get(f"{host.rstrip('/')}/api/v1/tables?limit=1", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                paging = data.get("paging", {})
                green(f"GET /api/v1/tables → 200 (total={paging.get('total', '?')} tables in catalog)")
                return True
            if resp.status_code in (401, 403):
                red(f"GET /api/v1/tables → {resp.status_code} — JWT invalid or insufficient permissions")
                dim(f"   response body: {resp.text[:200]}")
                return False
            red(f"GET /api/v1/tables → unexpected status {resp.status_code}")
            return False
        except Exception as exc:
            red(f"tables endpoint failed: {type(exc).__name__}: {exc}")
            return False


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--falkor-host", required=True)
    parser.add_argument("--falkor-port", type=int, required=True)
    parser.add_argument("--falkor-password", required=True)
    parser.add_argument("--falkor-username", default=None,
                        help="ACL username (e.g. 'falkordb' for FalkorDB Cloud)")
    parser.add_argument("--om-host", required=True)
    parser.add_argument("--om-jwt", required=True)
    args = parser.parse_args()

    print("CHRONOS connection verifier")
    print("═══════════════════════════════════════════════════════════════")

    falkor_ok = await verify_falkor(
        args.falkor_host, args.falkor_port, args.falkor_password,
        username=args.falkor_username,
    )
    om_ok = await verify_om(args.om_host, args.om_jwt)

    print("\n═══════════════════════════════════════════════════════════════")
    print(f"  FalkorDB:     {'✓ reachable' if falkor_ok else '✗ FAILED'}")
    print(f"  OpenMetadata: {'✓ reachable' if om_ok else '✗ FAILED'}")
    print("═══════════════════════════════════════════════════════════════\n")

    if falkor_ok and om_ok:
        green("Both services verified. Safe to set Heroku config + restart dyno.")
        return 0
    red("One or more services failed verification. Review above and re-check credentials.")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

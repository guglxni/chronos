"""CLI entry point: ``python -m chronos.demo <subcommand>``."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from chronos.demo.seeder import seed_incidents


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m chronos.demo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    seed = sub.add_parser("seed", help="Populate Graphiti with synthetic historical incidents")
    seed.add_argument("--count", type=int, default=30, help="Number of incidents (default 30)")
    seed.add_argument("--days-back", type=int, default=30, help="Time window in days (default 30)")
    seed.add_argument(
        "--seed", type=int, default=None,
        help="Optional RNG seed for reproducible sample data",
    )
    seed.add_argument(
        "--clear", action="store_true",
        help="Reserved — clearing requires direct FalkorDB access; use Cloud console for now",
    )
    seed.add_argument("-v", "--verbose", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )

    if args.cmd == "seed":
        if args.clear:
            print(
                "⚠ --clear is not implemented yet; use the FalkorDB Cloud console "
                "to drop the chronos-historical-incidents group manually.",
                file=sys.stderr,
            )
        seeded = asyncio.run(seed_incidents(count=args.count, days_back=args.days_back, seed=args.seed))
        if seeded == 0:
            print("✗ Seeded 0 incidents — check FalkorDB configuration (see SETUP.md)", file=sys.stderr)
            return 1
        print(f"✓ Seeded {seeded}/{args.count} historical incidents into Graphiti")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

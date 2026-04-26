"""
CHRONOS MCP Server — expose CHRONOS as an MCP tool provider.

AI agents (Claude, OpenClaw, Hermes, LangChain, AutoGen, …) can connect
to this server via stdio or SSE and invoke CHRONOS capabilities as
first-class MCP tools.

Transport options
-----------------
* ``stdio``  — default; ideal for Claude Desktop / local agent frameworks
* ``sse``    — HTTP + Server-Sent Events; ideal for remote agents / cloud runners
* ``http``   — Streamable HTTP; ideal for Vercel / serverless deployments

Usage
-----
  # stdio (for Claude Desktop, local agents)
  chronos-mcp

  # SSE (for remote agents — listens on 0.0.0.0:8101)
  chronos-mcp --transport sse --host 0.0.0.0 --port 8101

  # Python API
  import asyncio
  from chronos.mcp.server import mcp
  asyncio.run(mcp.run_stdio_async())

Monitoring loop
---------------
Pass ``--monitor`` to also start a 24/7 polling loop that queries
OpenMetadata for fresh test-case failures and auto-triggers investigations.
The polling interval defaults to 60 s; override with ``--poll-interval N``.

Tools exposed
-------------
* ``trigger_investigation``  — start a full 10-step RCA investigation
* ``get_incident``           — fetch a completed incident report (read-only)
* ``list_incidents``         — list/filter recent incidents (read-only)
* ``query_lineage``          — walk dbt DAG up or downstream (read-only)
* ``search_entity``          — ripgrep code references (read-only)
* ``get_graph_context``      — graphify community + blast-radius query (read-only)
* ``poll_failures``          — pull recent OM test failures (monitoring hook)

Resources exposed
-----------------
* ``chronos://incidents``              — live incident list JSON
* ``chronos://incident/{incident_id}`` — single incident report JSON
* ``chronos://health``                 — service health summary
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from chronos.code_intel import code_search as _code_search
from chronos.code_intel import dbt_manifest as _dbt
from chronos.code_intel import graphify_adapter as _graphify
from chronos.config.settings import settings
from chronos.core import incident_store
from chronos.core.investigation_runner import run_investigation
from chronos.models.events import InvestigationTrigger

logger = logging.getLogger("chronos.mcp.server")

# ── Annotation singletons ─────────────────────────────────────────────────────
# readOnlyHint=True: agent can call without confirmation prompts
# idempotentHint=True: calling multiple times has no additional side effects
_READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True)
_TRIGGER = ToolAnnotations(readOnlyHint=False, destructiveHint=False)
_MONITOR = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)


# ── FastMCP app ───────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="CHRONOS",
    instructions=(
        "CHRONOS is an autonomous data-incident RCA (root-cause analysis) agent. "
        "Use trigger_investigation to start a full investigation for any data quality "
        "test failure — it returns immediately with an incident_id you should poll. "
        "Use get_incident(incident_id) to check progress and retrieve the completed report. "
        "Use list_incidents for recent incident history. "
        "Use query_lineage / search_entity / get_graph_context for targeted forensics "
        "without running a full investigation. "
        "Use poll_failures to discover recent OpenMetadata test-case failures."
    ),
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _secret(val: Any) -> str | None:
    """Unwrap SecretStr to plain str, or None."""
    if val is None:
        return None
    try:
        return val.get_secret_value()
    except AttributeError:
        return str(val)


# ── Tools ─────────────────────────────────────────────────────────────────────


@mcp.tool(
    annotations=_TRIGGER,
    description=(
        "Start a CHRONOS root-cause analysis investigation for a data quality failure. "
        "Returns immediately with an incident_id — poll get_incident(incident_id) until "
        "the status field is present in the response."
    ),
)
async def trigger_investigation(
    entity_fqn: str,
    test_name: str = "",
    failure_message: str = "",
    triggered_by: str = "mcp_agent",
) -> dict[str, Any]:
    """
    Start a full 10-step CHRONOS RCA investigation.

    The investigation pipeline runs asynchronously. Call get_incident with the
    returned incident_id to retrieve the completed IncidentReport, which includes
    root_cause_category, confidence_score, evidence_chain, recommended_actions,
    and affected_assets.

    Args:
        entity_fqn: Fully qualified name of the failing entity, e.g.
            ``analytics.marts.fct_orders`` or
            ``default.public.orders.row_count_test``.
        test_name: Name of the failing test case (recommended for precision).
        failure_message: Raw failure message / assertion text.
        triggered_by: Audit-trail label — defaults to "mcp_agent".

    Returns:
        ``{incident_id, status: "running", entity_fqn, triggered_at, hint}``
    """
    fqn = entity_fqn.strip() if entity_fqn else ""
    if not fqn:
        raise ToolError("entity_fqn is required and must not be blank")

    trigger = InvestigationTrigger(
        entity_fqn=fqn,
        test_name=test_name,
        failure_message=failure_message,
        triggered_by=triggered_by,
    )
    incident_id = str(uuid.uuid4())

    async def _run() -> None:
        try:
            await run_investigation(trigger, incident_id=incident_id)
        except Exception:
            logger.exception("Investigation %s failed", incident_id)

    # Store task reference to prevent garbage-collection before completion.
    task = asyncio.create_task(_run(), name=f"investigation-{incident_id}")
    task.add_done_callback(lambda _t: None)

    logger.info(
        "MCP: queued investigation %s for '%s' (triggered_by=%s)",
        incident_id,
        fqn,
        triggered_by,
    )
    return {
        "incident_id": incident_id,
        "status": "running",
        "entity_fqn": fqn,
        "triggered_at": _now_iso(),
        "hint": f"Call get_incident('{incident_id}') — retry every 5-10s until the report appears.",
    }


@mcp.tool(
    annotations=_READ_ONLY,
    description=(
        "Fetch a completed CHRONOS incident report by ID. "
        "Returns 'not found' while the investigation is still running — poll every 5-10s."
    ),
)
async def get_incident(incident_id: str) -> dict[str, Any]:
    """
    Fetch a CHRONOS incident report.

    Args:
        incident_id: UUID returned by trigger_investigation.

    Returns:
        Full IncidentReport with root_cause_category, confidence_score,
        evidence_chain, recommended_actions, and affected_assets. Raises
        ToolError if the ID is unknown (investigation still running or ID invalid).
    """
    if not incident_id or not incident_id.strip():
        raise ToolError("incident_id must not be blank")
    report = incident_store.get(incident_id.strip())
    if report is None:
        raise ToolError(
            f"Incident '{incident_id}' not found — the investigation may still be running. "
            "Retry in 5-10 seconds."
        )
    return report.model_dump(mode="json")


@mcp.tool(
    annotations=_READ_ONLY,
    description="List recent CHRONOS incident reports, newest first. Filterable by status and root cause.",
)
async def list_incidents(
    limit: int = 20,
    status: str | None = None,
    root_cause: str | None = None,
) -> dict[str, Any]:
    """
    List recent CHRONOS incident reports.

    Args:
        limit: Maximum incidents to return (1-100, default 20).
        status: Filter by lifecycle status — one of ``open``, ``acknowledged``,
            ``resolved``, or ``failed``.
        root_cause: Filter by root cause category — one of ``schema_change``,
            ``upstream_data_failure``, ``pipeline_failure``, ``data_drift``,
            ``infrastructure``, or ``unknown``.

    Returns:
        ``{total, returned, incidents: [IncidentReport, ...]}``
    """
    limit = max(1, min(limit, 100))
    valid_statuses = {"open", "acknowledged", "resolved", "failed"}
    valid_causes = {
        "schema_change",
        "upstream_data_failure",
        "pipeline_failure",
        "data_drift",
        "infrastructure",
        "unknown",
    }

    if status and status not in valid_statuses:
        raise ToolError(
            f"Invalid status {status!r}. Must be one of: {', '.join(sorted(valid_statuses))}"
        )
    if root_cause and root_cause not in valid_causes:
        raise ToolError(
            f"Invalid root_cause {root_cause!r}. Must be one of: {', '.join(sorted(valid_causes))}"
        )

    incidents = incident_store.list_all()
    if status:
        incidents = [i for i in incidents if i.status == status]
    if root_cause:
        incidents = [
            i
            for i in incidents
            if i.root_cause_category and i.root_cause_category.value == root_cause
        ]

    page = incidents[:limit]
    return {
        "total": len(incidents),
        "returned": len(page),
        "incidents": [i.model_dump(mode="json") for i in page],
    }


@mcp.tool(
    annotations=_READ_ONLY,
    description=(
        "Walk the dbt DAG upstream (parents) or downstream (children) from any model or source. "
        "Uses the local manifest — no API calls required."
    ),
)
async def query_lineage(
    entity_fqn: str,
    direction: str = "upstream",
    depth: int = 3,
) -> dict[str, Any]:
    """
    Walk the dbt DAG to find upstream dependencies or downstream consumers.

    Args:
        entity_fqn: Model name, e.g. ``fct_orders`` or ``analytics.marts.fct_orders``.
        direction: ``"upstream"`` to find parents, ``"downstream"`` to find children.
        depth: BFS hops to traverse (1-10, default 3).

    Returns:
        ``{entity, direction, depth, node_count, nodes: [dbt node dicts], node_names: [str]}``
    """
    if not entity_fqn or not entity_fqn.strip():
        raise ToolError("entity_fqn must not be blank")
    if direction not in ("upstream", "downstream"):
        raise ToolError(f"Invalid direction {direction!r}. Must be 'upstream' or 'downstream'.")

    depth = max(1, min(depth, 10))
    manifest_path = settings.dbt_manifest_path or None

    if direction == "upstream":
        nodes = _dbt.walk_upstream(entity_fqn.strip(), depth=depth, manifest_path=manifest_path)
    else:
        nodes = _dbt.walk_downstream(entity_fqn.strip(), depth=depth, manifest_path=manifest_path)

    # walk_upstream/downstream returns list[dict] — node dicts directly
    node_names = [n.get("name", n.get("alias", "")) for n in nodes if isinstance(n, dict)]
    return {
        "entity": entity_fqn.strip(),
        "direction": direction,
        "depth": depth,
        "node_count": len(nodes),
        "nodes": nodes,
        "node_names": node_names,
        "manifest_available": _dbt.is_available(manifest_path),
    }


@mcp.tool(
    annotations=_READ_ONLY,
    description=(
        "Search the codebase for references to a table, model, or column using ripgrep. "
        "Shell-injection safe (alphanumeric + ._- only). Works fully offline."
    ),
)
async def search_entity(
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Full-codebase code search for a table or entity name.

    Args:
        query: Entity name — alphanumeric, dots, underscores, hyphens only.
            Shell metacharacters are rejected at the safe-charset gate.
        limit: Maximum results (1-50, default 10).

    Returns:
        ``{query, result_count, results: [{file, line, text}, ...]}``
    """
    if not query or not query.strip():
        raise ToolError("query must not be blank")

    limit = max(1, min(limit, 50))
    repo = Path(settings.code_repo_path).expanduser().resolve()  # noqa: ASYNC240
    results = _code_search.search_entity_references(query.strip(), repo, limit=limit)
    return {"query": query.strip(), "result_count": len(results), "results": results}


@mcp.tool(
    annotations=_READ_ONLY,
    description=(
        "Query the graphify code-knowledge graph for community, blast-radius, and BFS context "
        "around any entity. Uses the local graph.json — no API calls."
    ),
)
async def get_graph_context(
    entity_fqn: str,
    depth: int = 2,
    limit: int = 30,
) -> dict[str, Any]:
    """
    Retrieve code-graph context for an entity from the graphify artifact.

    Args:
        entity_fqn: Entity name or concept to look up in the code graph.
        depth: BFS depth to traverse (1-4, default 2).
        limit: Max nodes to return (1-100, default 30).

    Returns:
        ``{entity, node, community, graph_context, graph_available}`` — all
        fields are empty-safe when the graph is not loaded.
    """
    if not entity_fqn or not entity_fqn.strip():
        raise ToolError("entity_fqn must not be blank")

    depth = max(1, min(depth, 4))
    limit = max(1, min(limit, 100))
    graph_path = settings.graphify_graph_path or None
    fqn = entity_fqn.strip()

    return {
        "entity": fqn,
        "node": _graphify.get_node(fqn, graph_path=graph_path),
        "community": _graphify.get_community(fqn, graph_path=graph_path),
        "graph_context": _graphify.query_graph(
            fqn, depth=depth, limit=limit, graph_path=graph_path
        ),
        "graph_available": _graphify.is_available(graph_path),
    }


@mcp.tool(
    annotations=_MONITOR,
    description=(
        "Pull recent test-case failures from OpenMetadata. "
        "The monitoring hook — call on a schedule to discover new failures. "
        "Returns an empty list (not an error) when OpenMetadata is unreachable."
    ),
)
async def poll_failures(
    lookback_minutes: int = 60,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Query OpenMetadata for recent test-case failures.

    Args:
        lookback_minutes: How far back to look (1-1440 minutes = up to 24 hours).
        limit: Maximum failures to return (1-100).

    Returns:
        ``{failures: [{entity_fqn, test_name, failure_message, timestamp}],
           polled_at, source, lookback_minutes, error?}``
        The ``error`` field is present only when the OM endpoint was unreachable;
        ``failures`` is always an empty list in that case rather than missing.
    """
    lookback_minutes = max(1, min(lookback_minutes, 1440))
    limit = max(1, min(limit, 100))

    om_host = settings.openmetadata_host
    token = _secret(settings.openmetadata_jwt_token)

    base: dict[str, Any] = {
        "failures": [],
        "polled_at": _now_iso(),
        "source": om_host or "openmetadata",
        "lookback_minutes": lookback_minutes,
    }

    if not om_host:
        return {**base, "error": "OPENMETADATA_HOST not configured — set the env var and restart"}

    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    cutoff_ms = int((datetime.now(UTC).timestamp() - lookback_minutes * 60) * 1000)
    failures: list[dict[str, Any]] = []
    error_msg: str | None = None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{om_host}/api/v1/dataQuality/testCases/testCaseResults",
                params={"testCaseStatus": "Failed", "startTs": cutoff_ms, "limit": limit},
                headers=headers,
            )
            if resp.status_code == 200:
                for item in resp.json().get("data", []):
                    tc = item.get("testCase", {})
                    failures.append(
                        {
                            "entity_fqn": tc.get("entityFQN", ""),
                            "test_name": tc.get("name", ""),
                            "failure_message": item.get("result", ""),
                            "timestamp": item.get("timestamp", 0),
                        }
                    )
            else:
                error_msg = f"OpenMetadata returned HTTP {resp.status_code}"
    except httpx.HTTPError as exc:
        error_msg = f"Could not reach OpenMetadata at {om_host}: {exc}"
    except Exception as exc:
        error_msg = f"Unexpected error polling OpenMetadata: {exc}"

    result = {**base, "failures": failures}
    if error_msg:
        result["error"] = error_msg
    return result


# ── Resources ─────────────────────────────────────────────────────────────────


@mcp.resource("chronos://health")
async def health_resource() -> str:
    """CHRONOS service health — dbt manifest, graphify graph, and incident store status."""
    from chronos.code_intel.dbt_manifest import manifest_stats
    from chronos.code_intel.graphify_adapter import graph_stats

    return json.dumps(
        {
            "service": "CHRONOS",
            "version": settings.version,
            "status": "ok",
            "checked_at": _now_iso(),
            "dbt_manifest": manifest_stats(settings.dbt_manifest_path or None),
            "graphify": graph_stats(settings.graphify_graph_path or None),
            "incidents_in_store": len(incident_store.list_all()),
        },
        indent=2,
    )


@mcp.resource("chronos://incidents")
async def incidents_resource() -> str:
    """Live list of all incidents in the in-memory store (newest first, JSON)."""
    incidents = incident_store.list_all()
    return json.dumps(
        {
            "total": len(incidents),
            "incidents": [i.model_dump(mode="json") for i in incidents],
        },
        indent=2,
    )


@mcp.resource("chronos://incident/{incident_id}")
async def incident_resource(incident_id: str) -> str:
    """Full IncidentReport JSON for a specific incident_id."""
    report = incident_store.get(incident_id)
    if report is None:
        return json.dumps({"error": f"Incident '{incident_id}' not found"})
    return report.model_dump_json(indent=2)


# ── 24/7 Monitoring loop ──────────────────────────────────────────────────────


async def _monitoring_loop(poll_interval: int = 60) -> None:
    """
    Background coroutine: polls OpenMetadata for new test failures and
    auto-triggers CHRONOS investigations.

    Deduplication: each (entity_fqn, test_name) pair is investigated at most
    once per session. The dedup set is pruned at 10 000 entries to prevent
    unbounded memory growth on long-running servers.
    """
    logger.info("CHRONOS monitor started — polling every %ds", poll_interval)
    investigated: set[str] = set()

    while True:
        try:
            result = await poll_failures(lookback_minutes=max(2, poll_interval // 30))
            if "error" in result:
                logger.warning("Monitor poll error: %s", result["error"])

            new = 0
            for f in result.get("failures", []):
                fqn = f.get("entity_fqn", "")
                if not fqn:
                    continue
                key = f"{fqn}:{f.get('test_name', '')}"
                if key in investigated:
                    continue
                investigated.add(key)

                trigger = InvestigationTrigger(
                    entity_fqn=fqn,
                    test_name=f.get("test_name", ""),
                    failure_message=f.get("failure_message", ""),
                    triggered_by="monitor",
                )
                iid = str(uuid.uuid4())

                async def _run(t: InvestigationTrigger = trigger, iid: str = iid) -> None:
                    try:
                        await run_investigation(t, incident_id=iid)
                    except Exception:
                        logger.exception("Monitor investigation %s failed", iid)

                task = asyncio.create_task(_run(), name=f"monitor-{iid}")
                task.add_done_callback(lambda _t: None)
                new += 1
                logger.info("Monitor: queued investigation %s for '%s'", iid, fqn)

            if new:
                logger.info("Monitor: %d new investigation(s) queued", new)

            if len(investigated) > 10_000:
                investigated.clear()

        except asyncio.CancelledError:
            logger.info("CHRONOS monitor stopped")
            return
        except Exception:
            logger.exception("Monitor loop unhandled error — will retry")

        await asyncio.sleep(poll_interval)


# ── CLI entry point ───────────────────────────────────────────────────────────


def _cli_main() -> None:
    """
    ``chronos-mcp`` CLI — start the CHRONOS MCP server.

    Examples::

        # stdio (Claude Desktop, Cursor, local agents)
        chronos-mcp

        # SSE — remote agents over HTTP
        chronos-mcp --transport sse --host 0.0.0.0 --port 8101

        # 24/7 autonomous monitoring + SSE
        chronos-mcp --transport sse --port 8101 --monitor --poll-interval 120
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="chronos-mcp",
        description="CHRONOS MCP Server — AI agent data-incident RCA tools",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address for SSE/HTTP")
    parser.add_argument("--port", type=int, default=8101, help="Port for SSE/HTTP (default: 8101)")
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Enable 24/7 OpenMetadata failure monitoring loop",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Monitoring poll interval in seconds (default: 60)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        stream=sys.stderr,
    )

    async def _run() -> None:
        monitor_task: asyncio.Task[None] | None = None
        if args.monitor:
            monitor_task = asyncio.create_task(
                _monitoring_loop(args.poll_interval),
                name="chronos-monitor",
            )
        try:
            if args.transport == "stdio":
                await mcp.run_stdio_async()
            elif args.transport == "sse":
                await mcp.run_sse_async(host=args.host, port=args.port)
            else:
                await mcp.run_streamable_http_async(host=args.host, port=args.port)
        finally:
            if monitor_task:
                monitor_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await monitor_task

    asyncio.run(_run())

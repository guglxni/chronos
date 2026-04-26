# CHRONOS — Agent Integration Guide

CHRONOS is a **tool harness** — a set of MCP tools your agent calls *within its own agentic flow* to investigate data quality failures. It is not a separate peer agent: OpenClaw, Hermes, AutoGen, and Claude call CHRONOS tools the same way they call a database query or a web search, and get back structured results they can reason over.

---

## Install the skill (Claude Code / any skills-compatible agent)

The fastest path is the CHRONOS agent skill — one command drops `/chronos` into any Claude Code session or MCP-compatible agent:

```bash
npx skills add guglxni/chronos-skill
```

Then invoke directly:

```
/chronos investigate analytics.marts.fct_orders --test row_count_check
/chronos list --status open
/chronos lineage analytics.marts.fct_orders --direction downstream
```

Skill source: <https://github.com/guglxni/chronos-skill>

---

## Quick start (MCP server — embed into your agent's tool loop)

### Option A — Claude Desktop (stdio)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "chronos": {
      "command": "/Volumes/MacExt/chronos/.venv/bin/chronos-mcp",
      "env": {
        "CHRONOS_ENV": "production",
        "OPENMETADATA_HOST": "http://your-om-host:8585",
        "OPENMETADATA_JWT_TOKEN": "your-jwt-token",
        "DBT_MANIFEST_PATH": "/path/to/dbt/target/manifest.json",
        "GRAPHIFY_GRAPH_PATH": "/path/to/graphify-out/graph.json",
        "CODE_REPO_PATH": "/path/to/your/repo"
      }
    }
  }
}
```

Restart Claude Desktop. CHRONOS tools appear automatically.

### Option B — Remote agents (SSE transport)

Start the MCP server on a reachable host:

```bash
# Basic SSE
chronos-mcp --transport sse --host 0.0.0.0 --port 8101

# With 24/7 monitoring loop (auto-triggers investigations for OM failures)
chronos-mcp --transport sse --host 0.0.0.0 --port 8101 \
    --monitor --poll-interval 60
```

Connect from any MCP-compatible agent:

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("http://your-server:8101/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool(
            "trigger_investigation",
            {"entity_fqn": "analytics.marts.fct_orders",
             "test_name": "row_count_test",
             "failure_message": "Expected 10000, got 0"}
        )
```

### Option C — Python / LangChain / AutoGen

```python
from chronos.mcp.server import (
    trigger_investigation, get_incident, list_incidents,
    query_lineage, search_entity, get_graph_context, poll_failures,
)

# Trigger an investigation
result = await trigger_investigation(
    entity_fqn="analytics.marts.fct_orders",
    test_name="freshness_check",
    failure_message="Table not refreshed in 6 hours",
)
incident_id = result["incident_id"]

# Poll until complete
import asyncio
while True:
    report = await get_incident(incident_id)
    if "error" not in report:
        break
    await asyncio.sleep(5)

print(report["root_cause_category"])
print(report["recommended_actions"])
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `trigger_investigation` | Start a full 10-step RCA investigation; returns `incident_id` immediately |
| `get_incident` | Fetch completed `IncidentReport` by ID |
| `list_incidents` | List/filter recent incidents (by status or root cause) |
| `query_lineage` | Walk dbt DAG upstream or downstream from any entity |
| `search_entity` | Ripgrep code references for a table/model (shell-safe, offline) |
| `get_graph_context` | Graphify community + BFS subgraph for an entity |
| `poll_failures` | Pull recent OpenMetadata test-case failures |

## Available Resources

| URI | Description |
|-----|-------------|
| `chronos://health` | Service health + dbt/graphify availability summary |
| `chronos://incidents` | Live incident list (JSON) |
| `chronos://incident/{id}` | Single incident report (JSON) |

---

## 24/7 Autonomous Monitoring

The `--monitor` flag starts a background loop that:

1. Calls OpenMetadata's `/api/v1/dataQuality/testCases/testCaseResults?testCaseStatus=Failed` on each poll cycle.
2. Deduplicates failures (same entity + test pair is only investigated once per session).
3. Auto-triggers a CHRONOS investigation for each new failure.
4. Reports complete via `incident_store` — accessible via `get_incident` / `chronos://incidents`.

```bash
# Production: monitor every 2 minutes, bind to internal network
OPENMETADATA_HOST=http://om-prod:8585 \
OPENMETADATA_JWT_TOKEN=<token> \
DBT_MANIFEST_PATH=/prod/target/manifest.json \
chronos-mcp --transport sse --host 0.0.0.0 --port 8101 \
    --monitor --poll-interval 120
```

For production use, run behind a process supervisor (systemd, supervisord, or
Docker) and add bearer token auth in front (nginx / API gateway).

---

## How OpenClaw / Hermes / AutoGen use CHRONOS

These agents don't talk *to* CHRONOS as a peer — they pull CHRONOS tools *into their own tool loop*, the same way they'd add a SQL executor or a web search. CHRONOS becomes another capability in the agent's toolbelt.

**OpenClaw / any MCP-native agent** — point it at the SSE endpoint:

```bash
# Start CHRONOS MCP server (SSE)
chronos-mcp --transport sse --host 0.0.0.0 --port 8101

# OpenClaw mcp config
{
  "servers": [{ "url": "http://localhost:8101/sse", "name": "chronos" }]
}
```

OpenClaw then sees `trigger_investigation`, `get_incident`, `query_lineage`, etc. as native tools it can call mid-flow — no wrapper, no glue code.

**AutoGen** — wrap the async functions and register as `FunctionTool`:

```python
from autogen_core.tools import FunctionTool
from chronos.mcp.server import trigger_investigation, get_incident

tools = [
    FunctionTool(trigger_investigation, description="Trigger CHRONOS RCA"),
    FunctionTool(get_incident, description="Fetch CHRONOS incident report"),
]
```

**Hermes / LangChain** — use `langchain_mcp_adapters` against the SSE endpoint:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

async with MultiServerMCPClient({"chronos": {"url": "http://localhost:8101/sse", "transport": "sse"}}) as client:
    tools = client.get_tools()  # CHRONOS tools appear in the tool list
```

### The A2A card is for discovery, not separation

`/.well-known/agent-card.json` lets an agent *auto-configure* — it reads the card, learns what CHRONOS can do, and sets itself up without a human writing config. Once configured, the agent uses CHRONOS via MCP, not via A2A calls. Think of A2A as the handshake; MCP is the ongoing conversation.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENMETADATA_HOST` | `http://localhost:8585` | OM API base URL |
| `OPENMETADATA_JWT_TOKEN` | — | OM bearer token |
| `DBT_MANIFEST_PATH` | — | Path to `manifest.json` |
| `GRAPHIFY_GRAPH_PATH` | `graphify-out/graph.json` | Path to graphify artifact |
| `CODE_REPO_PATH` | `.` | Repo root for code search |
| `LITELLM_MODEL` | `gpt-4o` | LLM model for RCA synthesis |
| `LITELLM_API_KEY` | — | API key for LLM provider |

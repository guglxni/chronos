"""
A2A Agent Card endpoint for agent discovery (Linux Foundation A2A Protocol).

Content-negotiated:
  Accept: application/json  →  machine-readable JSON (default, API clients, AI agents)
  Accept: text/html         →  beautiful rendered HTML page (browsers)

The JSON payload is the canonical A2A agent card; the HTML view is a
human-readable rendering of the same data styled to match the CHRONOS
design system.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from chronos.config.settings import settings

router = APIRouter(tags=["discovery"])

# ── Agent card data ───────────────────────────────────────────────────────────


def _build_card() -> dict:
    return {
        "schemaVersion": "1.0",
        "name": "CHRONOS",
        "description": (
            "Autonomous Data Incident Root Cause Analysis Agent. "
            "Investigates data quality test failures by reasoning across "
            "OpenMetadata, Graphiti temporal knowledge graph, and local code intelligence. "
            "Exposes a native MCP server for direct AI agent integration."
        ),
        "version": settings.version,
        "homepage": "https://github.com/chronos-data/chronos",
        "provider": {
            "name": "CHRONOS",
            "url": settings.api_base_url
            if hasattr(settings, "api_base_url")
            else "https://chronos-api-0e8635fe890d.herokuapp.com",
        },
        "authentication": {
            "type": "none",
            "description": "Internal use only — no auth required for local deployment",
        },
        "skills": [
            {
                "id": "investigate",
                "name": "Investigate Data Incident",
                "icon": "⚡",
                "description": (
                    "Given an entity FQN and test name, runs a full 10-step RCA "
                    "investigation and returns a structured incident report with "
                    "confidence scoring, evidence chain, and recommended actions."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_fqn": {
                            "type": "string",
                            "description": "Fully qualified name of the affected entity",
                        },
                        "test_name": {
                            "type": "string",
                            "description": "Name of the failing test case",
                        },
                        "failure_message": {"type": "string"},
                    },
                    "required": ["entity_fqn"],
                },
                "outputSchema": {
                    "type": "object",
                    "description": (
                        "IncidentReport with root_cause_category, confidence_score, "
                        "evidence_chain, recommended_actions, affected_assets"
                    ),
                },
            },
            {
                "id": "blast_radius_assessment",
                "name": "Blast Radius Assessment",
                "icon": "◈",
                "description": (
                    "Given an entity FQN, walks downstream lineage up to N hops to identify "
                    "all affected assets, downstream owners, and exposure surface."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_fqn": {"type": "string"},
                        "depth": {"type": "integer", "default": 3},
                    },
                    "required": ["entity_fqn"],
                },
            },
            {
                "id": "compliance_report_generation",
                "name": "Compliance Report Generation",
                "icon": "⬡",
                "description": (
                    "Generates W3C PROV-O provenance artifacts "
                    "(JSON-LD, Turtle, PROV-N) for a given incident investigation "
                    "— suitable for audit and regulatory filings."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "incident_id": {"type": "string"},
                        "format": {
                            "type": "string",
                            "enum": ["jsonld", "ttl", "provn"],
                        },
                    },
                    "required": ["incident_id"],
                },
            },
        ],
        "mcp_tools": [
            "trigger_investigation",
            "get_incident",
            "list_incidents",
            "query_lineage",
            "search_entity",
            "get_graph_context",
            "poll_failures",
        ],
        "mcp_resources": [
            "chronos://health",
            "chronos://incidents",
            "chronos://incident/{id}",
        ],
        "capabilities": {
            "streaming": True,
            "asyncInvocation": True,
            "provenance": True,
            "mcp": True,
            "monitoring": True,
            "protocols": ["HTTP", "SSE", "MCP/stdio", "MCP/SSE"],
        },
        "endpoints": {
            "investigate": "POST /api/v1/investigate",
            "incidents": "GET /api/v1/incidents",
            "stream": "GET /api/v1/investigations/{incident_id}/stream",
            "provenance": "GET /api/v1/incidents/{incident_id}/provenance.{format}",
            "health": "GET /api/v1/health",
            "agent_card": "GET /.well-known/agent-card.json",
        },
    }


# ── HTML renderer ─────────────────────────────────────────────────────────────


def _render_html(card: dict) -> str:
    skills_html = ""
    for skill in card["skills"]:
        icon = skill.get("icon", "◎")
        required = skill.get("inputSchema", {}).get("required", [])
        props = skill.get("inputSchema", {}).get("properties", {})
        params_html = ""
        for prop, meta in props.items():
            is_req = prop in required
            params_html += f"""
            <div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <span style="font-family:monospace;font-size:12px;color:#0057FF;white-space:nowrap;padding-top:1px;">{prop}</span>
              <span style="font-family:monospace;font-size:11px;color:#404040;flex-shrink:0;padding-top:2px;">{meta.get("type", "string")}</span>
              {"<span style='font-size:10px;color:#ef4444;flex-shrink:0;padding-top:3px;'>required</span>" if is_req else ""}
              <span style="font-size:12px;color:#555;line-height:1.4;">{meta.get("description", "")}</span>
            </div>"""

        skills_html += f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:4px;padding:32px;display:flex;flex-direction:column;">
          <span style="font-size:28px;color:#0057FF;margin-bottom:20px;display:block;">{icon}</span>
          <h3 style="font-family:Georgia,serif;font-size:20px;color:#ffffff;font-weight:normal;margin:0 0 6px;">{skill["name"]}</h3>
          <p style="font-size:10px;color:#404040;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 16px;font-family:system-ui,sans-serif;">{skill["id"]}</p>
          <p style="font-size:13px;color:#707072;line-height:1.6;margin:0 0 20px;font-family:system-ui,sans-serif;">{skill["description"]}</p>
          <div style="margin-top:auto;border-top:1px solid rgba(255,255,255,0.06);padding-top:16px;">
            <p style="font-size:10px;color:#404040;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 8px;font-family:system-ui,sans-serif;">Input Parameters</p>
            {params_html}
          </div>
        </div>"""

    endpoints_html = ""
    for name, path in card["endpoints"].items():
        method = "POST" if path.startswith("POST") else "GET"
        path_clean = path.replace("POST ", "").replace("GET ", "")
        method_color = "#0057FF" if method == "POST" else "#22c55e"
        endpoints_html += f"""
        <div style="display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
          <span style="font-family:monospace;font-size:11px;padding:3px 8px;border-radius:3px;background:{method_color}18;color:{method_color};flex-shrink:0;">{method}</span>
          <span style="font-family:monospace;font-size:13px;color:#F5F5F5;flex:1;">{path_clean}</span>
          <span style="font-size:12px;color:#404040;font-family:system-ui,sans-serif;">{name.replace("_", " ")}</span>
        </div>"""

    caps = card["capabilities"]
    cap_chips = ""
    cap_map = {
        "streaming": ("Streaming SSE", "#0057FF"),
        "asyncInvocation": ("Async Invocation", "#a855f7"),
        "provenance": ("W3C PROV-O", "#22c55e"),
        "mcp": ("MCP Server", "#f59e0b"),
        "monitoring": ("24/7 Monitor", "#ef4444"),
    }
    for key, (label, color) in cap_map.items():
        if caps.get(key):
            cap_chips += f"""<span style="font-family:system-ui,sans-serif;font-size:11px;padding:6px 14px;border-radius:999px;background:{color}18;color:{color};letter-spacing:0.08em;border:1px solid {color}30;">{label}</span>"""

    protocol_chips = ""
    for p in caps.get("protocols", []):
        protocol_chips += f"""<span style="font-family:monospace;font-size:11px;padding:5px 12px;border-radius:999px;background:rgba(255,255,255,0.05);color:#F5F5F5;border:1px solid rgba(255,255,255,0.1);">{p}</span>"""

    mcp_tools_html = ""
    tool_icons = {
        "trigger_investigation": ("⚡", "#0057FF", "Action"),
        "get_incident": ("◎", "#22c55e", "Read"),
        "list_incidents": ("☰", "#22c55e", "Read"),
        "query_lineage": ("⬡", "#a855f7", "Graph"),
        "search_entity": ("⌕", "#f59e0b", "Code"),
        "get_graph_context": ("◈", "#a855f7", "Graph"),
        "poll_failures": ("⟳", "#ef4444", "Monitor"),
    }
    tool_descs = {
        "trigger_investigation": "Start a full 10-step RCA pipeline",
        "get_incident": "Fetch a completed incident report",
        "list_incidents": "Filter and list recent incidents",
        "query_lineage": "Walk dbt DAG up or downstream",
        "search_entity": "Ripgrep code references (shell-safe)",
        "get_graph_context": "Community + blast-radius graph query",
        "poll_failures": "Pull OM test-case failures",
    }
    for tool in card.get("mcp_tools", []):
        icon, color, badge = tool_icons.get(tool, ("◎", "#707072", "Tool"))
        desc = tool_descs.get(tool, "")
        mcp_tools_html += f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:4px;padding:16px 20px;display:flex;align-items:center;gap:16px;transition:border-color 0.2s;">
          <span style="font-size:18px;color:{color};flex-shrink:0;">{icon}</span>
          <div style="flex:1;">
            <span style="font-family:monospace;font-size:12px;color:#F5F5F5;display:block;margin-bottom:2px;">{tool}</span>
            <span style="font-size:11px;color:#555;font-family:system-ui,sans-serif;">{desc}</span>
          </div>
          <span style="font-size:10px;padding:3px 8px;border-radius:999px;background:{color}18;color:{color};letter-spacing:0.08em;font-family:system-ui,sans-serif;">{badge}</span>
        </div>"""

    raw_json = json.dumps(
        {k: v for k, v in card.items() if k not in ("mcp_tools", "mcp_resources")}, indent=2
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CHRONOS — Agent Card</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      background: #111111;
      color: #F5F5F5;
      font-family: system-ui, -apple-system, 'Helvetica Neue', sans-serif;
      line-height: 1.6;
      min-height: 100vh;
    }}
    /* Grid texture */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px);
      background-size: 60px 60px;
      opacity: 0.025;
      pointer-events: none;
      z-index: 0;
    }}
    .wrap {{ position: relative; z-index: 1; max-width: 1100px; margin: 0 auto; padding: 0 24px; }}
    /* Nav */
    nav {{
      position: sticky;
      top: 0;
      z-index: 50;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(17,17,17,0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255,255,255,0.07);
      padding: 0 32px;
    }}
    .nav-logo {{
      font-family: Georgia, serif;
      font-size: 18px;
      color: #fff;
      text-decoration: none;
      letter-spacing: 0.05em;
    }}
    .nav-links {{ display: flex; align-items: center; gap: 24px; }}
    .nav-links a {{
      font-size: 12px;
      color: #707072;
      text-decoration: none;
      letter-spacing: 0.08em;
      transition: color 0.2s;
    }}
    .nav-links a:hover {{ color: #F5F5F5; }}
    .badge-version {{
      font-family: monospace;
      font-size: 11px;
      padding: 3px 10px;
      border-radius: 999px;
      background: rgba(0,87,255,0.15);
      color: #0057FF;
      border: 1px solid rgba(0,87,255,0.3);
    }}
    /* Hero */
    .hero {{
      padding: 80px 0 64px;
    }}
    .eyebrow {{
      font-size: 11px;
      letter-spacing: 0.3em;
      text-transform: uppercase;
      color: #0057FF;
      margin-bottom: 24px;
      font-family: system-ui, sans-serif;
    }}
    h1 {{
      font-family: Georgia, serif;
      font-size: clamp(48px, 7vw, 88px);
      font-weight: normal;
      line-height: 0.95;
      color: #fff;
      margin-bottom: 24px;
    }}
    .hero-desc {{
      font-size: 16px;
      color: #707072;
      max-width: 580px;
      line-height: 1.7;
      margin-bottom: 36px;
    }}
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 48px; }}
    .chip {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      font-size: 12px;
      color: #F5F5F5;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      font-family: system-ui, sans-serif;
    }}
    .chip-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #0057FF;
      flex-shrink: 0;
    }}
    /* Section */
    .section {{ padding: 56px 0; border-top: 1px solid rgba(255,255,255,0.06); }}
    .section-label {{
      font-size: 10px;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: #404040;
      margin-bottom: 32px;
      font-family: system-ui, sans-serif;
    }}
    h2 {{
      font-family: Georgia, serif;
      font-size: clamp(28px, 4vw, 48px);
      font-weight: normal;
      color: #fff;
      line-height: 1.05;
      margin-bottom: 32px;
    }}
    /* Skills grid */
    .skills-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
    }}
    /* MCP tools grid */
    .tools-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
    }}
    /* Caps */
    .caps-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
    /* JSON block */
    .json-block {{
      background: #0A0A0A;
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 4px;
      overflow: hidden;
    }}
    .json-header {{
      padding: 12px 20px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
    .json-filename {{ font-family: monospace; font-size: 11px; color: #404040; margin-left: auto; }}
    pre {{
      padding: 24px;
      overflow-x: auto;
      font-family: monospace;
      font-size: 12px;
      line-height: 1.7;
      color: #E0E0E0;
      white-space: pre;
    }}
    /* Footer */
    footer {{
      padding: 40px 0;
      border-top: 1px solid rgba(255,255,255,0.06);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }}
    footer p {{ font-size: 11px; color: #404040; font-family: system-ui, sans-serif; }}
    footer a {{ font-size: 12px; color: #707072; text-decoration: none; transition: color 0.2s; }}
    footer a:hover {{ color: #F5F5F5; }}
    @media (max-width: 640px) {{
      nav {{ padding: 0 16px; }}
      .skills-grid, .tools-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<nav>
  <a href="/" class="nav-logo">CHRONOS</a>
  <div class="nav-links">
    <span class="badge-version">v{card["version"]}</span>
    <a href="#skills">Skills</a>
    <a href="#mcp">MCP Tools</a>
    <a href="#endpoints">Endpoints</a>
    <a href="#raw">Raw JSON</a>
  </div>
</nav>

<div class="wrap">

  <!-- Hero -->
  <section class="hero">
    <p class="eyebrow">A2A Agent Card · Linux Foundation Protocol</p>
    <h1>CHRONOS<br>Agent Card.</h1>
    <p class="hero-desc">{card["description"]}</p>

    <div class="chip-row">
      <div class="chip"><span class="chip-dot"></span>A2A v{card["schemaVersion"]}</div>
      <div class="chip"><span class="chip-dot"></span>MCP 1.x</div>
      <div class="chip"><span class="chip-dot"></span>{len(card["skills"])} Skills</div>
      <div class="chip"><span class="chip-dot"></span>{len(card.get("mcp_tools", []))} MCP Tools</div>
      <div class="chip"><span class="chip-dot"></span>10-Step Pipeline</div>
    </div>

    <!-- Caps -->
    <div class="caps-row">
      {cap_chips}
    </div>
    <div class="caps-row">
      {protocol_chips}
    </div>
  </section>

  <!-- Skills -->
  <section class="section" id="skills">
    <p class="section-label">A2A Skills · {len(card["skills"])} registered</p>
    <h2>What CHRONOS<br>knows how to do.</h2>
    <div class="skills-grid">
      {skills_html}
    </div>
  </section>

  <!-- MCP Tools -->
  <section class="section" id="mcp">
    <p class="section-label">MCP Server · {len(card.get("mcp_tools", []))} tools · {len(card.get("mcp_resources", []))} resources</p>
    <h2>Native tool layer<br>for AI agents.</h2>
    <p style="font-size:13px;color:#707072;max-width:540px;margin-bottom:28px;line-height:1.7;">
      CHRONOS runs a native MCP server — start with
      <code style="font-family:monospace;font-size:12px;background:rgba(0,87,255,0.12);color:#0057FF;padding:2px 8px;border-radius:3px;">chronos-mcp</code>
      for stdio (Claude Desktop) or
      <code style="font-family:monospace;font-size:12px;background:rgba(0,87,255,0.12);color:#0057FF;padding:2px 8px;border-radius:3px;">chronos-mcp --transport sse</code>
      for remote agents.
    </p>
    <div class="tools-grid">
      {mcp_tools_html}
    </div>
    <div style="margin-top:20px;display:flex;flex-wrap:wrap;gap:10px;">
      {"".join(f'<span style="font-family:monospace;font-size:11px;padding:5px 12px;border-radius:999px;background:rgba(0,87,255,0.08);color:#0057FF;border:1px solid rgba(0,87,255,0.2);">{r}</span>' for r in card.get("mcp_resources", []))}
    </div>
  </section>

  <!-- Endpoints -->
  <section class="section" id="endpoints">
    <p class="section-label">REST Endpoints · {len(card["endpoints"])} routes</p>
    <h2>API surface.</h2>
    <div style="border:1px solid rgba(255,255,255,0.07);border-radius:4px;overflow:hidden;">
      <div style="padding:0 20px;">
        {endpoints_html}
      </div>
    </div>
  </section>

  <!-- Raw JSON -->
  <section class="section" id="raw">
    <p class="section-label">Machine-Readable</p>
    <h2>Raw JSON.</h2>
    <p style="font-size:13px;color:#707072;margin-bottom:24px;line-height:1.7;">
      AI agents and agent orchestration frameworks should fetch
      <code style="font-family:monospace;font-size:12px;background:rgba(255,255,255,0.06);color:#F5F5F5;padding:2px 8px;border-radius:3px;">/.well-known/agent-card.json</code>
      with <code style="font-family:monospace;font-size:12px;background:rgba(255,255,255,0.06);color:#F5F5F5;padding:2px 8px;border-radius:3px;">Accept: application/json</code>
      to receive the canonical payload.
    </p>
    <div class="json-block">
      <div class="json-header">
        <span class="dot" style="background:#ef4444;"></span>
        <span class="dot" style="background:#eab308;"></span>
        <span class="dot" style="background:#22c55e;"></span>
        <span class="json-filename">agent-card.json</span>
      </div>
      <pre>{raw_json}</pre>
    </div>
  </section>

  <!-- Footer -->
  <footer>
    <p>© 2026 CHRONOS · Autonomous Data Incident RCA · A2A v{card["schemaVersion"]}</p>
    <div style="display:flex;gap:24px;flex-wrap:wrap;">
      <a href="/.well-known/agent-card.json">Raw JSON ↗</a>
      <a href="/api/v1/health">Health ↗</a>
      <a href="/docs">API Docs ↗</a>
      <a href="{card["homepage"]}" target="_blank" rel="noopener">GitHub ↗</a>
    </div>
  </footer>

</div>
</body>
</html>"""


# ── Route ─────────────────────────────────────────────────────────────────────


@router.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    """
    Return the CHRONOS A2A Agent Card.

    Content-negotiated:
    - Browsers (Accept: text/html)          → beautiful rendered page
    - API clients (Accept: application/json) → raw JSON
    """
    card = _build_card()
    accept = request.headers.get("accept", "")

    # Serve HTML when a browser is requesting (prefers text/html over application/json)
    if "text/html" in accept and "application/json" not in accept.split(",")[0]:
        html = _render_html(card)
        return HTMLResponse(
            content=html,
            headers={
                "Link": '</.well-known/agent-card.json>; rel="canonical"; type="application/json"',
                "Cache-Control": "public, max-age=300",
            },
        )

    # API clients, curl, AI agents → clean JSON
    return JSONResponse(
        content={k: v for k, v in card.items() if k not in ("mcp_tools", "mcp_resources")},
        headers={
            "Link": '</.well-known/agent-card.json>; rel="alternate"; type="text/html"',
            "Cache-Control": "public, max-age=300",
        },
    )

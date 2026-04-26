import { useState } from 'react';

// ── Tool catalogue ────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: 'trigger_investigation',
    symbol: '⚡',
    short: 'Kick off a full 10-step RCA pipeline for any failing entity. Returns immediately with an incident_id you can poll.',
    badge: 'Async',
    badgeColor: '#0057FF',
  },
  {
    name: 'get_incident',
    symbol: '◎',
    short: 'Fetch the structured IncidentReport — root cause, confidence score, evidence chain, recommended actions.',
    badge: 'Read',
    badgeColor: '#22c55e',
  },
  {
    name: 'list_incidents',
    symbol: '☰',
    short: 'List and filter recent incidents by status (open · acknowledged · resolved) or root cause category.',
    badge: 'Read',
    badgeColor: '#22c55e',
  },
  {
    name: 'query_lineage',
    symbol: '⬡',
    short: 'Walk the dbt DAG upstream or downstream from any model. Uses the local manifest — no API calls.',
    badge: 'Graph',
    badgeColor: '#a855f7',
  },
  {
    name: 'search_entity',
    symbol: '⌕',
    short: 'Ripgrep the entire codebase for references to a table or model. Shell-injection safe, works offline.',
    badge: 'Code',
    badgeColor: '#f59e0b',
  },
  {
    name: 'get_graph_context',
    symbol: '◈',
    short: 'Query the graphify code graph — community members, BFS subgraph, blast-radius — for any entity.',
    badge: 'Graph',
    badgeColor: '#a855f7',
  },
  {
    name: 'poll_failures',
    symbol: '⟳',
    short: 'Pull fresh test-case failures from OpenMetadata. The monitoring hook — call it on a schedule.',
    badge: 'Monitor',
    badgeColor: '#ef4444',
  },
] as const;

// ── Code snippets ─────────────────────────────────────────────────────────────

const SNIPPETS = {
  claude: `// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "chronos": {
      "command": "/path/to/.venv/bin/chronos-mcp",
      "env": {
        "OPENMETADATA_HOST": "http://your-om:8585",
        "DBT_MANIFEST_PATH": "/path/to/manifest.json"
      }
    }
  }
}`,
  python: `from chronos.mcp.server import (
    trigger_investigation,
    get_incident,
    query_lineage,
)

# 1. Trigger an investigation
result = await trigger_investigation(
    entity_fqn="analytics.marts.fct_orders",
    test_name="row_count_check",
    failure_message="Expected 50000 rows, got 0",
)
incident_id = result["incident_id"]

# 2. Poll until complete
import asyncio
while True:
    report = await get_incident(incident_id)
    if "error" not in report:
        break
    await asyncio.sleep(5)

print(report["root_cause_category"])   # e.g. "upstream_data_failure"
print(report["confidence_score"])       # 0.0 – 1.0
print(report["recommended_actions"])    # list[str]`,
  sse: `# Start the MCP server (SSE transport)
chronos-mcp --transport sse --host 0.0.0.0 --port 8101

# With 24/7 autonomous monitoring
chronos-mcp --transport sse --port 8101 \\
  --monitor --poll-interval 60

# Connect from any MCP-compatible agent
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("http://your-server:8101/sse") as (r, w):
    async with ClientSession(r, w) as session:
        await session.initialize()
        result = await session.call_tool(
            "trigger_investigation",
            {"entity_fqn": "analytics.marts.fct_orders"}
        )`,
};

type SnippetKey = keyof typeof SNIPPETS;

const TAB_LABELS: { key: SnippetKey; label: string }[] = [
  { key: 'claude', label: 'Claude Desktop' },
  { key: 'python', label: 'Python / LangChain' },
  { key: 'sse',    label: 'SSE · Remote Agents' },
];

const COMPATIBLE = [
  'Claude', 'Cursor', 'LangChain', 'AutoGen', 'OpenClaw', 'Hermes', 'Zed', 'Any MCP Client',
];

// ── Sub-components ────────────────────────────────────────────────────────────

function ToolCard({ tool }: { tool: typeof TOOLS[number] }) {
  return (
    <div
      className="group p-6 flex flex-col transition-all duration-200 cursor-default"
      style={{
        backgroundColor: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '4px',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(0,87,255,0.5)';
        (e.currentTarget as HTMLDivElement).style.backgroundColor = 'rgba(0,87,255,0.06)';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(255,255,255,0.07)';
        (e.currentTarget as HTMLDivElement).style.backgroundColor = 'rgba(255,255,255,0.04)';
      }}
    >
      {/* Icon + badge row */}
      <div className="flex items-start justify-between mb-5">
        <span
          className="font-heading text-2xl leading-none"
          style={{ color: '#0057FF' }}
        >
          {tool.symbol}
        </span>
        <span
          className="font-body text-xs px-2 py-0.5 rounded-full tracking-wider"
          style={{
            backgroundColor: `${tool.badgeColor}18`,
            color: tool.badgeColor,
            letterSpacing: '0.1em',
          }}
        >
          {tool.badge}
        </span>
      </div>

      {/* Tool name */}
      <p
        className="font-mono text-sm mb-3 tracking-tight"
        style={{ color: '#F5F5F5' }}
      >
        {tool.name}
      </p>

      {/* Description */}
      <p
        className="font-body text-sm leading-relaxed flex-1"
        style={{ color: '#707072' }}
      >
        {tool.short}
      </p>
    </div>
  );
}

function CodeBlock({ snippetKey }: { snippetKey: SnippetKey }) {
  const [copied, setCopied] = useState(false);
  const code = SNIPPETS[snippetKey];

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div
      style={{
        backgroundColor: '#0A0A0A',
        borderRadius: '4px',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Window chrome */}
      <div
        className="px-5 py-3 flex items-center gap-3"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#ef4444' }} />
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#eab308' }} />
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#22c55e' }} />
        <span className="ml-auto font-mono text-xs" style={{ color: '#404040' }}>
          {snippetKey === 'claude' ? 'claude_desktop_config.json' : snippetKey === 'python' ? 'agent.py' : 'bash'}
        </span>
        <button
          onClick={handleCopy}
          className="font-body text-xs transition-colors px-2 py-0.5 rounded"
          style={{
            color: copied ? '#22c55e' : '#707072',
            backgroundColor: copied ? 'rgba(34,197,94,0.1)' : 'transparent',
          }}
        >
          {copied ? 'copied ✓' : 'copy'}
        </button>
      </div>

      {/* Code */}
      <pre
        className="px-6 py-5 overflow-x-auto font-mono text-xs leading-loose"
        style={{ color: '#E0E0E0', tabSize: 2 }}
      >
        {code.split('\n').map((line, i) => {
          const isComment = line.trim().startsWith('#') || line.trim().startsWith('//');
          const isKey = /^[\s]*"[\w_]+"\s*:/.test(line);
          const isString = !isKey && line.includes('"') && !line.trim().startsWith('"mcpServers"');
          return (
            <span
              key={i}
              className="block"
              style={{
                color: isComment ? '#404040' : isKey ? '#0057FF' : isString ? '#F5F5F5' : '#E0E0E0',
              }}
            >
              {line || '​'}
            </span>
          );
        })}
      </pre>
    </div>
  );
}

// ── Main section ──────────────────────────────────────────────────────────────

export default function AgentSection() {
  const [activeTab, setActiveTab] = useState<SnippetKey>('claude');

  return (
    <section
      id="for-agents"
      className="py-32 px-6 md:px-16 relative overflow-hidden"
      style={{ backgroundColor: '#111111' }}
    >
      {/* Subtle grid texture */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          pointerEvents: 'none',
        }}
      />

      {/* Blue glow — top-left */}
      <div
        className="absolute top-0 left-0 w-[600px] h-[600px] pointer-events-none"
        style={{
          background: 'radial-gradient(circle at top left, rgba(0,87,255,0.08) 0%, transparent 60%)',
        }}
      />

      <div className="relative z-10 max-w-6xl mx-auto">

        {/* ── Header ── */}
        <p
          className="text-xs tracking-[0.3em] uppercase mb-6 font-body"
          style={{ color: '#0057FF' }}
        >
          Model Context Protocol · MCP
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-20 items-end">
          <div>
            <h2
              className="font-heading text-white leading-[0.95]"
              style={{ fontSize: 'clamp(40px, 6vw, 80px)' }}
            >
              CHRONOS
              <br />
              for agents.
            </h2>
          </div>
          <div>
            <p
              className="font-body text-base leading-relaxed mb-6"
              style={{ color: '#707072' }}
            >
              CHRONOS exposes a native MCP server — every investigation tool,
              lineage query, and monitoring hook available as a first-class
              agent capability. Plug in via stdio or SSE. No API key gymnastics.
              No wrapper code.
            </p>
            <div className="flex flex-wrap gap-3">
              {COMPATIBLE.map(agent => (
                <span
                  key={agent}
                  className="font-body text-xs px-3 py-1.5 rounded-full"
                  style={{
                    backgroundColor: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: '#F5F5F5',
                  }}
                >
                  {agent}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Tool grid ── */}
        <div
          className="mb-6 pb-2"
          style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
        >
          <p
            className="font-body text-xs tracking-[0.2em] uppercase"
            style={{ color: '#404040', letterSpacing: '0.18em' }}
          >
            7 tools · 3 resources
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 mb-24">
          {TOOLS.map(tool => (
            <ToolCard key={tool.name} tool={tool} />
          ))}

          {/* Resources mini-card */}
          <div
            className="p-6 flex flex-col justify-between"
            style={{
              backgroundColor: 'rgba(0,87,255,0.06)',
              border: '1px solid rgba(0,87,255,0.2)',
              borderRadius: '4px',
            }}
          >
            <span
              className="font-heading text-2xl leading-none mb-5 block"
              style={{ color: '#0057FF' }}
            >
              ∷
            </span>
            <div>
              <p className="font-body text-xs tracking-wider uppercase mb-4" style={{ color: '#0057FF', letterSpacing: '0.12em' }}>
                Resources
              </p>
              {['chronos://health', 'chronos://incidents', 'chronos://incident/{id}'].map(r => (
                <p key={r} className="font-mono text-xs mb-2" style={{ color: '#707072' }}>
                  {r}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* ── Agent self-install ── */}
        <div
          className="mb-24 p-8 md:p-12"
          style={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '4px',
          }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">

            {/* Left — narrative */}
            <div>
              <p
                className="font-body text-xs tracking-[0.3em] uppercase mb-4"
                style={{ color: '#0057FF', letterSpacing: '0.2em' }}
              >
                Autonomous Setup
              </p>
              <h3
                className="font-heading text-white mb-4 leading-tight"
                style={{ fontSize: 'clamp(28px, 3.5vw, 44px)' }}
              >
                Install yourself.
                <br />
                No human needed.
              </h3>
              <p
                className="font-body text-sm leading-relaxed mb-8"
                style={{ color: '#707072' }}
              >
                CHRONOS publishes a machine-readable{' '}
                <code
                  className="font-mono px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: 'rgba(255,255,255,0.06)', color: '#F5F5F5', fontSize: '0.85em' }}
                >
                  /.well-known/agent-card.json
                </code>{' '}
                endpoint. Any A2A-compatible agent can discover capabilities,
                required environment variables, and bootstrap commands without
                reading a README. Three shell commands install and start the
                full stack.
              </p>

              {/* Step list */}
              <div className="space-y-4">
                {[
                  {
                    n: '1',
                    cmd: 'curl -s https://chronos-api-0e8635fe890d.herokuapp.com/.well-known/agent-card.json | jq .skills',
                    label: 'Discover capabilities',
                  },
                  {
                    n: '2',
                    cmd: 'pip install chronos-data && chronos-server --help',
                    label: 'Install & verify',
                  },
                  {
                    n: '3',
                    cmd: 'OPENMETADATA_HOST=http://your-om:8585 chronos-mcp',
                    label: 'Start MCP server',
                  },
                ].map(({ n, cmd, label }) => (
                  <div key={n} className="flex gap-4 items-start">
                    <span
                      className="font-heading text-xs w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{
                        backgroundColor: 'rgba(0,87,255,0.15)',
                        color: '#0057FF',
                        fontSize: '11px',
                      }}
                    >
                      {n}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-body text-xs mb-1.5" style={{ color: '#707072' }}>{label}</p>
                      <code
                        className="font-mono text-xs block px-3 py-2 rounded overflow-x-auto"
                        style={{
                          backgroundColor: '#0A0A0A',
                          color: '#F5F5F5',
                          border: '1px solid rgba(255,255,255,0.06)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {cmd}
                      </code>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — env var checklist + agent-card preview */}
            <div className="space-y-6">

              {/* Env var checklist */}
              <div>
                <p
                  className="font-body text-xs tracking-widest uppercase mb-4"
                  style={{ color: '#404040', letterSpacing: '0.15em' }}
                >
                  Required environment
                </p>
                <div className="space-y-2">
                  {[
                    { var: 'OPENMETADATA_HOST', desc: 'OpenMetadata API base URL', required: true },
                    { var: 'DBT_MANIFEST_PATH', desc: 'Path to dbt manifest.json', required: true },
                    { var: 'ANTHROPIC_API_KEY', desc: 'Or any LiteLLM-compatible key', required: false },
                    { var: 'NEO4J_URI', desc: 'Graphiti knowledge graph', required: false },
                    { var: 'SLACK_BOT_TOKEN', desc: 'Incident notifications', required: false },
                  ].map(({ var: v, desc, required }) => (
                    <div
                      key={v}
                      className="flex items-center gap-3 px-4 py-2.5 rounded"
                      style={{
                        backgroundColor: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.05)',
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: required ? '#0057FF' : '#404040' }}
                      />
                      <span className="font-mono text-xs flex-1" style={{ color: '#F5F5F5' }}>{v}</span>
                      <span className="font-body text-xs" style={{ color: '#404040' }}>{desc}</span>
                      {!required && (
                        <span
                          className="font-body text-xs px-1.5 py-0.5 rounded"
                          style={{
                            backgroundColor: 'rgba(255,255,255,0.04)',
                            color: '#404040',
                            fontSize: '10px',
                          }}
                        >
                          optional
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Agent-card CTA */}
              <div
                className="p-5 flex items-center justify-between gap-4 rounded"
                style={{
                  backgroundColor: 'rgba(0,87,255,0.07)',
                  border: '1px solid rgba(0,87,255,0.2)',
                }}
              >
                <div>
                  <p className="font-body text-xs mb-1" style={{ color: '#0057FF' }}>
                    A2A Discovery Endpoint
                  </p>
                  <p className="font-mono text-xs" style={{ color: '#707072' }}>
                    /.well-known/agent-card.json
                  </p>
                </div>
                <a
                  href="https://chronos-api-0e8635fe890d.herokuapp.com/.well-known/agent-card.json"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-body text-xs px-4 py-2 rounded-full flex-shrink-0 transition-all"
                  style={{
                    backgroundColor: '#0057FF',
                    color: '#FFFFFF',
                    textDecoration: 'none',
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.backgroundColor = '#003ED4'; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.backgroundColor = '#0057FF'; }}
                >
                  View JSON →
                </a>
              </div>

            </div>
          </div>
        </div>

        {/* ── Quick start ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 mb-24">
          <div>
            <p
              className="text-xs tracking-[0.3em] uppercase mb-4 font-body"
              style={{ color: '#0057FF' }}
            >
              Quick Start
            </p>
            <h3
              className="font-heading text-white mb-6 leading-tight"
              style={{ fontSize: 'clamp(28px, 3.5vw, 44px)' }}
            >
              Up in
              <br />
              two minutes.
            </h3>
            <p
              className="font-body text-sm leading-relaxed mb-8"
              style={{ color: '#707072' }}
            >
              Install via pip, configure your environment, and CHRONOS
              appears as a native tool in any MCP-compatible agent. Three
              transports: stdio for local agents, SSE for remote, and
              streamable HTTP for cloud-native deployments.
            </p>

            {/* Install command */}
            <div
              className="flex items-center gap-4 px-5 py-4 mb-6"
              style={{
                backgroundColor: '#0A0A0A',
                borderRadius: '4px',
                border: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <span className="font-mono text-xs" style={{ color: '#0057FF' }}>$</span>
              <span className="font-mono text-sm flex-1" style={{ color: '#F5F5F5' }}>
                pip install chronos-data
              </span>
              <span className="font-mono text-xs" style={{ color: '#404040' }}>then</span>
              <span className="font-mono text-sm" style={{ color: '#F5F5F5' }}>
                chronos-mcp
              </span>
            </div>

            {/* Transport chips */}
            <div className="flex flex-wrap gap-3">
              {[
                { label: 'stdio', desc: 'Claude Desktop · Local' },
                { label: 'SSE', desc: 'Remote · Cloud' },
                { label: 'HTTP', desc: 'Streamable · Vercel' },
              ].map(({ label, desc }) => (
                <div
                  key={label}
                  className="px-4 py-2.5 rounded-full flex items-center gap-3"
                  style={{
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: '#0057FF' }}
                  />
                  <span className="font-mono text-xs" style={{ color: '#F5F5F5' }}>{label}</span>
                  <span className="font-body text-xs" style={{ color: '#404040' }}>{desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Code block with tabs */}
          <div>
            {/* Tab bar */}
            <div
              className="flex gap-1 mb-0 p-1 rounded-t"
              style={{
                backgroundColor: '#0A0A0A',
                borderTop: '1px solid rgba(255,255,255,0.06)',
                borderLeft: '1px solid rgba(255,255,255,0.06)',
                borderRight: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              {TAB_LABELS.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className="font-body text-xs px-3 py-2 rounded transition-all duration-150"
                  style={{
                    color: activeTab === key ? '#F5F5F5' : '#404040',
                    backgroundColor: activeTab === key ? 'rgba(255,255,255,0.07)' : 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            <CodeBlock snippetKey={activeTab} />
          </div>
        </div>

        {/* ── Monitoring callout ── */}
        <div
          className="relative overflow-hidden p-10 md:p-16"
          style={{
            backgroundColor: '#0057FF',
            borderRadius: '4px',
          }}
        >
          {/* Subtle texture inside the blue block */}
          <div
            className="absolute inset-0 opacity-[0.06]"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
              pointerEvents: 'none',
            }}
          />

          <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
            <div>
              <p
                className="font-body text-xs tracking-[0.25em] uppercase mb-5"
                style={{ color: 'rgba(255,255,255,0.6)', letterSpacing: '0.2em' }}
              >
                Autonomous Monitoring
              </p>
              <h3
                className="font-heading text-white leading-[0.92] mb-6"
                style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}
              >
                Zero humans
                <br />
                required.
              </h3>
              <p
                className="font-body text-sm leading-relaxed"
                style={{ color: 'rgba(255,255,255,0.7)' }}
              >
                Start CHRONOS with <code
                  className="font-mono px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: 'rgba(255,255,255,0.15)', fontSize: '0.9em' }}
                >--monitor</code> and it continuously polls
                OpenMetadata for new test-case failures — deduplicates,
                auto-triggers RCA investigations, and stores structured
                incident reports. Your agents retrieve findings on demand.
              </p>
            </div>

            <div className="space-y-3">
              {[
                { step: '01', label: 'Poll', desc: 'Query OM every N seconds for fresh failures' },
                { step: '02', label: 'Deduplicate', desc: 'Skip incidents already under investigation' },
                { step: '03', label: 'Investigate', desc: 'Fire full 10-step RCA pipeline automatically' },
                { step: '04', label: 'Surface', desc: 'Agents retrieve via get_incident or chronos://incidents' },
              ].map(({ step, label, desc }) => (
                <div
                  key={step}
                  className="flex items-start gap-4 p-4"
                  style={{
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                  }}
                >
                  <span
                    className="font-heading text-sm flex-shrink-0"
                    style={{ color: 'rgba(255,255,255,0.4)', lineHeight: 1 }}
                  >
                    {step}
                  </span>
                  <div>
                    <p className="font-body text-sm text-white mb-0.5">{label}</p>
                    <p className="font-body text-xs" style={{ color: 'rgba(255,255,255,0.6)' }}>{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Bottom CTA ── */}
        <div
          className="mt-16 pt-12 flex flex-col md:flex-row items-start md:items-center justify-between gap-8"
          style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
        >
          <div>
            <p className="font-body text-sm mb-1" style={{ color: '#707072' }}>
              Production-ready · MCP 1.x · Python 3.11+
            </p>
            <p className="font-body text-xs" style={{ color: '#404040' }}>
              0 CVE in the MCP transport layer · HMAC-validated webhooks · SecretStr for all credentials
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a
              href="https://chronos-api-0e8635fe890d.herokuapp.com/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="chronos-btn-outline text-sm px-6 py-3"
            >
              API Docs →
            </a>
            <a
              href="https://chronos-api-0e8635fe890d.herokuapp.com/.well-known/agent-card.json"
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm flex items-center gap-2 px-6 py-3 rounded-full transition-colors"
              style={{
                color: '#707072',
                border: '1.5px solid rgba(255,255,255,0.1)',
                borderRadius: '30px',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = '#F5F5F5'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = '#707072'; }}
            >
              Agent Card (A2A)
            </a>
          </div>
        </div>

      </div>
    </section>
  );
}

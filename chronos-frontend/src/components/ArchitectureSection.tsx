const PIPELINE = [
  {
    phase: 'Ingest',
    desc: 'Events in',
    tools: ['OpenMetadata', 'OpenLineage', 'dbt manifest'],
  },
  {
    phase: 'Scope',
    desc: 'Agent pipeline',
    tools: ['LangGraph', '10 async nodes', 'Blast radius'],
  },
  {
    phase: 'Memory',
    desc: 'Knowledge graph',
    tools: ['Graphiti', 'FalkorDB', 'Episode search'],
  },
  {
    phase: 'Synthesize',
    desc: 'LLM reasoning',
    tools: ['LiteLLM', 'Groq · Anthropic', 'OpenAI'],
  },
  {
    phase: 'Surface',
    desc: 'Findings out',
    tools: ['REST + SSE', 'MCP tools', 'Slack alerts'],
  },
];

const PILLARS = [
  {
    name: 'OpenMetadata',
    role: 'Asset Catalog · Lineage Source',
    description:
      'CHRONOS integrates with OpenMetadata to receive real-time webhook events, walk the upstream and downstream lineage graph, and enrich incidents with data asset context — owners, tiers, domains, and SLA metadata.',
    tech: ['Webhooks', 'Lineage API', 'Asset Catalog', 'Test Results'],
    logos: [
      // Org avatar IS the correct OpenMetadata project logo (no parent company mismatch)
      { src: 'https://github.com/open-metadata.png?size=80', alt: 'OpenMetadata', square: true },
    ],
  },
  {
    name: 'OpenLineage + dbt',
    role: 'Lineage Events · Transform Graph',
    description:
      'CHRONOS listens for OpenLineage events from Spark, dbt, Airflow, and any OL-compatible emitter. The dbt manifest is parsed directly to walk the transformation DAG — no extra API round-trips required.',
    tech: ['OL Events', 'dbt Manifest', 'DAG Walk', 'Airflow · Spark'],
    logos: [
      // Official project logo committed in the OpenLineage repo
      { src: 'https://raw.githubusercontent.com/OpenLineage/OpenLineage/main/doc/openlineage-logo.png', alt: 'OpenLineage', square: false },
      // dbt Labs org avatar IS the dbt project logo
      { src: 'https://github.com/dbt-labs.png?size=80', alt: 'dbt', square: true },
    ],
  },
  {
    name: 'LangGraph',
    role: 'Agentic State Machine',
    description:
      'The investigation pipeline is a 10-node LangGraph state machine. Each node — scope failure, lineage walk, temporal diff, blast radius, prior correlations, RCA synthesis — is independently testable and fully async.',
    tech: ['10-Step Pipeline', 'LangChain Core', 'Stateful Graph', 'Async Nodes'],
    logos: [
      // LangGraph-specific logo committed in the langgraph repo (dark variant = dark icon on light bg)
      { src: 'https://raw.githubusercontent.com/langchain-ai/langgraph/main/.github/images/logo-dark.svg', alt: 'LangGraph', square: false },
    ],
  },
  {
    name: 'Graphiti (FalkorDB)',
    role: 'Temporal Knowledge Graph',
    description:
      'Every incident, finding, and correlation is persisted as a Graphiti episode on FalkorDB — a Redis-wire-compatible graph database. CHRONOS detects recurring patterns and builds institutional memory across investigations.',
    tech: ['FalkorDB', 'Temporal Graph', 'Entity Memory', 'Episode Search'],
    logos: [
      // Graphiti has no project-specific logo — Zep org is the creator
      { src: 'https://github.com/getzep.png?size=80', alt: 'Graphiti by Zep', square: true },
      // FalkorDB org avatar IS the FalkorDB project logo (standalone org, no parent mismatch)
      { src: 'https://github.com/FalkorDB.png?size=80', alt: 'FalkorDB', square: true },
    ],
  },
  {
    name: 'LiteLLM',
    role: 'LLM-Agnostic Synthesis',
    description:
      'CHRONOS routes all evidence through LiteLLM — a unified proxy supporting Groq, OpenAI, Anthropic, Mistral, and any OpenAI-compatible endpoint. Swap providers or models without changing a line of agent code.',
    tech: ['LiteLLM proxy', 'Groq · llama-4-scout', 'OpenAI · Anthropic', 'LangGraph'],
    logos: [
      // Actual LiteLLM project logo from the litellm repo (NOT BerriAI company logo)
      { src: 'https://raw.githubusercontent.com/BerriAI/litellm/main/ui/litellm-dashboard/public/assets/logos/litellm_logo.jpg', alt: 'LiteLLM', square: true },
    ],
  },
  {
    name: 'OpenTelemetry + Langfuse',
    role: 'Observability · Compliance',
    description:
      'Every investigation span is traced end-to-end via OpenTelemetry with OTLP export. LLM calls are captured by Langfuse for token usage, latency, and prompt inspection. W3C PROV-O provenance documents are generated per investigation for compliance.',
    tech: ['OpenTelemetry', 'Langfuse', 'OTLP Export', 'W3C PROV-O'],
    logos: [
      // OpenTelemetry CNCF org avatar IS the project logo
      { src: 'https://github.com/open-telemetry.png?size=80', alt: 'OpenTelemetry', square: true },
      // Langfuse org avatar IS the project logo (standalone company = product)
      { src: 'https://github.com/langfuse.png?size=80', alt: 'Langfuse', square: true },
    ],
  },
];

const SUPPORTING = [
  { name: 'FastAPI', desc: 'REST API · SSE streaming' },
  { name: 'MCP', desc: '4 tool servers · stdio · SSE · HTTP' },
  { name: 'Slack', desc: 'Block Kit incident alerts' },
  { name: 'SQLGlot', desc: 'SQL AST parsing · entity extraction' },
  { name: 'NetworkX', desc: 'Graph analysis · community detection' },
  { name: 'Pydantic v2', desc: 'Data validation · settings' },
  { name: 'Redis', desc: 'Caching · SSE queue · dedup' },
  { name: 'Elasticsearch', desc: 'Full-text entity search' },
  { name: 'W3C PROV-O', desc: 'Compliance provenance records' },
  { name: 'Docker', desc: 'Containerised deployment' },
];

function LogoStack({ logos }: { logos: { src: string; alt: string; square: boolean }[] }) {
  return (
    <div className="flex items-center gap-2.5 mb-6">
      {logos.map(({ src, alt, square }) => (
        <img
          key={src}
          src={src}
          alt={alt}
          style={square ? {
            width: '36px',
            height: '36px',
            objectFit: 'cover',
            borderRadius: '8px',
            border: '1px solid rgba(0,0,0,0.08)',
            backgroundColor: '#F5F5F5',
            flexShrink: 0,
          } : {
            height: '32px',
            width: 'auto',
            maxWidth: '110px',
            objectFit: 'contain',
            flexShrink: 0,
          }}
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = 'none';
          }}
        />
      ))}
    </div>
  );
}

export default function ArchitectureSection() {
  return (
    <section
      id="architecture"
      className="py-32 px-6 md:px-16"
      style={{ backgroundColor: '#F5F5F5' }}
    >
      <div className="max-w-6xl mx-auto">

        {/* ── Header ── */}
        <p
          className="text-xs tracking-[0.3em] uppercase mb-6 font-body"
          style={{ color: '#5B8AFF' }}
        >
          Architecture
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-16 items-end">
          <div>
            <h2
              className="font-heading text-chronos-black leading-tight"
              style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}
            >
              Built on the best
              <br />
              open standards.
            </h2>
          </div>
          <div>
            <p
              className="font-body text-base leading-relaxed"
              style={{ color: '#4A4A4C' }}
            >
              CHRONOS is built on OpenMetadata, OpenLineage, dbt, LangGraph,
              Graphiti (FalkorDB), and LiteLLM — all battle-tested, open-source
              infrastructure. Every layer is observable, swappable, and
              self-documenting.
            </p>
          </div>
        </div>

        {/* ── Pipeline strip ── */}
        <div
          className="mb-16 p-6 md:p-8 overflow-x-auto"
          style={{
            backgroundColor: '#111111',
            borderRadius: '4px',
          }}
        >
          <div className="flex items-stretch min-w-max md:min-w-0 gap-0">
            {PIPELINE.map((step, i) => (
              <div key={step.phase} className="flex items-stretch flex-1 min-w-[140px]">
                <div className="flex-1 px-4 py-3">
                  <p
                    className="font-body text-xs tracking-[0.2em] uppercase mb-2"
                    style={{ color: '#5B8AFF', letterSpacing: '0.15em' }}
                  >
                    {step.phase}
                  </p>
                  <p
                    className="font-body text-xs mb-3"
                    style={{ color: '#9A9A9C' }}
                  >
                    {step.desc}
                  </p>
                  <div className="space-y-1">
                    {step.tools.map(t => (
                      <p key={t} className="font-mono text-xs" style={{ color: '#C8C8CA' }}>
                        {t}
                      </p>
                    ))}
                  </div>
                </div>
                {i < PIPELINE.length - 1 && (
                  <div className="flex items-center px-2 flex-shrink-0">
                    <span
                      className="font-heading text-lg select-none"
                      style={{ color: '#5B8AFF', opacity: 0.4 }}
                    >
                      →
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ── 6 primary pillar cards ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-10">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.name}
              className="p-8 flex flex-col"
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '4px',
              }}
            >
              <LogoStack logos={pillar.logos} />

              <h3
                className="font-heading mb-1"
                style={{ fontSize: '22px', color: '#111111' }}
              >
                {pillar.name}
              </h3>

              <p
                className="font-body text-xs tracking-wider uppercase mb-5"
                style={{ color: '#4A4A4C', letterSpacing: '0.12em' }}
              >
                {pillar.role}
              </p>

              <p
                className="font-body text-sm leading-relaxed flex-1"
                style={{ color: '#4A4A4C' }}
              >
                {pillar.description}
              </p>

              <div className="flex flex-wrap gap-2 mt-8">
                {pillar.tech.map((t) => (
                  <span
                    key={t}
                    className="font-body text-xs px-3 py-1 rounded-full"
                    style={{
                      backgroundColor: '#F5F5F5',
                      color: '#111111',
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* ── Supporting tech shelf ── */}
        <div
          className="p-6 md:p-8"
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '4px',
          }}
        >
          <p
            className="font-body text-xs tracking-[0.2em] uppercase mb-6"
            style={{ color: '#4A4A4C', letterSpacing: '0.15em' }}
          >
            Also in the stack
          </p>
          <div className="flex flex-wrap gap-3">
            {SUPPORTING.map(({ name, desc }) => (
              <div
                key={name}
                className="flex items-center gap-2.5 px-4 py-2.5 rounded-full"
                style={{
                  backgroundColor: '#F5F5F5',
                  border: '1px solid rgba(0,0,0,0.06)',
                }}
                title={desc}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: '#5B8AFF' }}
                />
                <span
                  className="font-mono text-xs"
                  style={{ color: '#111111' }}
                >
                  {name}
                </span>
                <span
                  className="font-body text-xs hidden sm:inline"
                  style={{ color: '#4A4A4C' }}
                >
                  {desc}
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}

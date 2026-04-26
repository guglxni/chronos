const PILLARS = [
  {
    name: 'OpenMetadata',
    role: 'Asset catalog + lineage source',
    description:
      'CHRONOS integrates with OpenMetadata to receive real-time webhook events, walk the upstream and downstream lineage graph, and enrich incidents with data asset context — owners, tiers, domains, and SLA metadata.',
    tech: ['Webhooks', 'Lineage API', 'Asset Catalog'],
    icon: '⬡',
  },
  {
    name: 'Graphiti (FalkorDB)',
    role: 'Knowledge graph memory',
    description:
      'Every incident, finding, and correlation is persisted into Graphiti — a temporal knowledge graph on FalkorDB. This lets CHRONOS detect recurring patterns, link related past incidents, and build institutional memory over time.',
    tech: ['FalkorDB', 'Temporal Graph', 'Entity Memory'],
    icon: '◈',
  },
  {
    name: 'LiteLLM / Groq',
    role: 'LLM synthesis layer',
    description:
      'The agentic investigation graph feeds all gathered evidence to an LLM via LiteLLM — a unified proxy that works with Groq, OpenAI, Anthropic, and others. The model synthesizes a structured RCA with confidence scoring.',
    tech: ['LiteLLM', 'Groq Inference', 'LangGraph'],
    icon: '◎',
  },
];

export default function ArchitectureSection() {
  return (
    <section
      id="architecture"
      className="py-32 px-6 md:px-16"
      style={{ backgroundColor: '#F5F5F5' }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Section label */}
        <p
          className="text-xs tracking-[0.3em] uppercase mb-6 font-body"
          style={{ color: '#0057FF' }}
        >
          Architecture
        </p>

        <h2
          className="font-heading text-chronos-black mb-4 leading-tight"
          style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}
        >
          Built on the best
          <br />
          open standards.
        </h2>
        <p
          className="font-body text-base mb-20 max-w-xl"
          style={{ color: '#707072' }}
        >
          CHRONOS is built on top of OpenMetadata, FalkorDB, LangGraph, and LiteLLM — all battle-tested, open-source infrastructure.
        </p>

        {/* 3-column cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.name}
              className="p-8 flex flex-col"
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '4px',
              }}
            >
              {/* Icon */}
              <span
                className="text-3xl mb-6 block font-heading"
                style={{ color: '#0057FF' }}
              >
                {pillar.icon}
              </span>

              {/* Name */}
              <h3
                className="font-heading mb-1"
                style={{ fontSize: '24px', color: '#111111' }}
              >
                {pillar.name}
              </h3>

              {/* Role */}
              <p
                className="font-body text-xs tracking-wider uppercase mb-5"
                style={{ color: '#707072', letterSpacing: '0.12em' }}
              >
                {pillar.role}
              </p>

              {/* Description */}
              <p
                className="font-body text-sm leading-relaxed flex-1"
                style={{ color: '#707072' }}
              >
                {pillar.description}
              </p>

              {/* Tech tags */}
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
      </div>
    </section>
  );
}

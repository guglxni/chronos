const STEPS = [
  {
    number: '01',
    title: 'Detect',
    body: 'OpenMetadata or OpenLineage sends a webhook the moment a data test fails, a schema changes, or a pipeline stalls. CHRONOS receives the event and immediately opens an investigation.',
    tag: 'Webhook Ingestion',
  },
  {
    number: '02',
    title: 'Investigate',
    body: 'CHRONOS walks the lineage graph five layers deep, checks recent code commits, queries the Graphiti knowledge graph for similar past incidents, and correlates audit logs — all in parallel.',
    tag: 'Agentic Graph Walk',
  },
  {
    number: '03',
    title: 'Synthesize',
    body: 'An LLM produces a structured root cause analysis with a confidence score, affected asset map, evidence chain, and prioritized remediation actions — delivered in under 30 seconds.',
    tag: 'LLM Synthesis',
  },
];

export default function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="py-32 px-6 md:px-16"
      style={{ backgroundColor: '#FFFFFF' }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Section label */}
        <p
          className="text-xs tracking-[0.3em] uppercase mb-6 font-body"
          style={{ color: '#0057FF' }}
        >
          How It Works
        </p>

        <h2
          className="font-heading text-chronos-black mb-20 leading-tight"
          style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}
        >
          Three steps from
          <br />
          failure to fix.
        </h2>

        {/* Steps */}
        <div className="space-y-0 divide-y" style={{ borderColor: '#E8E8E8' }}>
          {STEPS.map((step, idx) => (
            <div
              key={step.number}
              className="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-12 py-16 group"
            >
              {/* Step number */}
              <div className="md:col-span-2">
                <span
                  className="font-heading text-8xl md:text-9xl leading-none select-none"
                  style={{ color: idx === 0 ? '#0057FF' : '#E8E8E8' }}
                >
                  {step.number}
                </span>
              </div>

              {/* Step content */}
              <div className="md:col-span-5 flex flex-col justify-center">
                <h3
                  className="font-heading mb-4"
                  style={{ fontSize: 'clamp(28px, 3.5vw, 44px)' }}
                >
                  {step.title}
                </h3>
                <p
                  className="font-body text-base leading-relaxed"
                  style={{ color: '#707072', maxWidth: '420px' }}
                >
                  {step.body}
                </p>
              </div>

              {/* Tag */}
              <div className="md:col-span-5 flex items-center justify-start md:justify-end">
                <span
                  className="font-body text-xs tracking-widest uppercase px-4 py-2 rounded-full"
                  style={{
                    backgroundColor: '#F5F5F5',
                    color: '#707072',
                    letterSpacing: '0.15em',
                  }}
                >
                  {step.tag}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

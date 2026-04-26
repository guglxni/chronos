export default function HeroSection() {
  const scrollToDemo = () => {
    document.getElementById('live-demo')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      id="hero"
      style={{ backgroundColor: '#111111' }}
      className="relative min-h-screen flex flex-col justify-center px-6 md:px-16 pt-20 pb-24 overflow-hidden"
    >
      {/* Subtle grid texture */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      <div className="relative z-10 max-w-6xl mx-auto w-full">
        {/* Eyebrow */}
        <p
          className="text-xs tracking-[0.3em] uppercase mb-8 font-body"
          style={{ color: '#0057FF' }}
        >
          AI Data Infrastructure Intelligence
        </p>

        {/* Main headline */}
        <h1
          className="font-heading text-white leading-[0.95] mb-8"
          style={{ fontSize: 'clamp(56px, 9vw, 120px)' }}
        >
          AI-Powered
          <br />
          Data Incident
          <br />
          Investigation
        </h1>

        {/* Subheading */}
        <p
          className="font-body text-lg md:text-xl max-w-2xl mb-12 leading-relaxed"
          style={{ color: '#707072' }}
        >
          CHRONOS watches your data pipelines, detects failures, and synthesizes
          root cause analyses in seconds — automatically.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-wrap items-center gap-4 mb-20">
          <button
            onClick={scrollToDemo}
            className="chronos-btn-primary text-base px-8 py-4"
          >
            Run Live Demo
          </button>
          <a
            href="https://chronos-api-0e8635fe890d.herokuapp.com/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="chronos-btn-outline text-base px-8 py-4"
          >
            Read the Docs
          </a>
        </div>

        {/* Metric chips */}
        <div className="flex flex-wrap gap-4">
          {[
            { label: '< 30s RCA', desc: 'Root cause analysis in seconds' },
            { label: '5-Layer Lineage', desc: 'Full upstream + downstream walk' },
            { label: 'LLM-Powered', desc: 'Groq + LiteLLM synthesis' },
          ].map(({ label, desc }) => (
            <div
              key={label}
              className="flex items-center gap-3 px-5 py-3 rounded-full font-body"
              style={{
                backgroundColor: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.12)',
              }}
              title={desc}
            >
              <span
                className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: '#0057FF' }}
              />
              <span
                className="text-sm tracking-widest uppercase font-body"
                style={{ color: '#F5F5F5', letterSpacing: '0.12em' }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div
        className="absolute bottom-0 left-0 right-0 h-32"
        style={{
          background: 'linear-gradient(to bottom, transparent, #111111)',
        }}
      />
    </section>
  );
}

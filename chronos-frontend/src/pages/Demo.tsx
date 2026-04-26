import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useSSE } from '../hooks/useSSE';
import DemoTerminal from '../components/DemoTerminal';
import RCACard from '../components/RCACard';
import HeroSection from '../components/HeroSection';
import HowItWorks from '../components/HowItWorks';
import ArchitectureSection from '../components/ArchitectureSection';
import AgentSection from '../components/AgentSection';
import type { IncidentReport } from '../types';

const API_BASE = 'https://chronos-api-0e8635fe890d.herokuapp.com';

const DEMO_SCENARIOS = [
  {
    id: 'row_count_failure',
    label: 'Row Count Failure',
    table: 'prod.orders.orders_daily',
    test: 'row_count_check',
    severity: 'CRITICAL',
    desc: 'ETL job failed — orders_daily has 0 rows',
  },
  {
    id: 'null_values',
    label: 'Null Values Detected',
    table: 'prod.customers.customer_profiles',
    test: 'not_null_customer_id',
    severity: 'HIGH',
    desc: '5.3% of customer records have NULL IDs',
  },
  {
    id: 'schema_drift',
    label: 'Schema Drift',
    table: 'prod.payments.payments_raw',
    test: 'schema_check',
    severity: 'HIGH',
    desc: 'Stripe API v2.4 added a required field',
  },
] as const;

type DemoScenario = (typeof DEMO_SCENARIOS)[number];

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f59e0b',
  MEDIUM: '#3b82f6',
  LOW: '#22c55e',
};

function LiveDemoSection() {
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario>(DEMO_SCENARIOS[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);
  const [streamToken, setStreamToken] = useState<string | null>(null);
  const [rcaReport, setRcaReport] = useState<IncidentReport | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [phase, setPhase] = useState<'idle' | 'posting' | 'streaming' | 'done' | 'error'>('idle');

  const { events, isConnected, error: sseError, markComplete } = useSSE(incidentId, streamToken ?? undefined);

  const runInvestigation = useCallback(async () => {
    if (isRunning || !selectedScenario) return;
    setIsRunning(true);
    setRcaReport(null);
    setIncidentId(null);
    setStreamToken(null);
    setStatusMsg(null);
    setPhase('posting');

    try {
      setStatusMsg('Launching investigation…');
      const res = await fetch(`${API_BASE}/api/v1/demo/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: selectedScenario.id }),
      });
      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(`Demo API failed (${res.status}): ${errBody}`);
      }
      const body = await res.json() as { incident_id: string; stream_token: string };
      setIncidentId(body.incident_id);
      setStreamToken(body.stream_token);
      setPhase('streaming');
      setStatusMsg(null);

      // Poll for the completed report — LLM synthesis can take 5-20s.
      // Stop as soon as the report is available (max 30s).
      let reportData: IncidentReport | null = null;
      for (let attempt = 0; attempt < 12; attempt++) {
        await new Promise<void>((resolve) => setTimeout(resolve, 2500));
        try {
          const reportRes = await fetch(`${API_BASE}/api/v1/incidents/${body.incident_id}`);
          if (reportRes.ok) {
            const data = await reportRes.json() as IncidentReport;
            if (data.probable_root_cause) { reportData = data; break; }
          }
        } catch { /* network hiccup — keep polling */ }
      }

      setPhase('done');
      if (reportData) {
        setRcaReport(reportData);
        // Definitive safety net: stop SSE retries once we have the report,
        // even if the spec-guaranteed ordering (data before error) was violated.
        markComplete();
      }
    } catch (err) {
      setPhase('error');
      setStatusMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setIsRunning(false);
    }
  }, [selectedScenario, isRunning, markComplete]);

  const reset = () => {
    setIncidentId(null);
    setStreamToken(null);
    setRcaReport(null);
    setStatusMsg(null);
    setPhase('idle');
    setIsRunning(false);
  };

  return (
    <section
      id="live-demo"
      className="py-32 px-6 md:px-16"
      style={{ backgroundColor: '#F5F5F5' }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Section label */}
        <p
          className="text-xs tracking-[0.3em] uppercase mb-6 font-body"
          style={{ color: '#0057FF' }}
        >
          Interactive Demo
        </p>

        <h2
          className="font-heading text-chronos-black mb-4 leading-tight"
          style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}
        >
          See CHRONOS
          <br />
          work in real time.
        </h2>
        <p
          className="font-body text-base mb-16 max-w-xl"
          style={{ color: '#707072' }}
        >
          Pick a pre-seeded failure scenario and watch the agentic investigation pipeline run live.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* LEFT: Scenario picker */}
          <div
            className="p-8"
            style={{ backgroundColor: '#FFFFFF' }}
          >
            <h3
              className="font-heading mb-2"
              style={{ fontSize: '28px', color: '#111111' }}
            >
              Try It Live
            </h3>
            <p className="font-body text-sm mb-8" style={{ color: '#707072' }}>
              Select a failure scenario and watch CHRONOS investigate in real time.
            </p>

            {/* Scenario cards */}
            <div className="space-y-3 mb-8">
              {DEMO_SCENARIOS.map((scenario) => {
                const isSelected = selectedScenario.id === scenario.id;
                return (
                  <button
                    key={scenario.id}
                    onClick={() => !isRunning && setSelectedScenario(scenario)}
                    disabled={isRunning}
                    className="w-full text-left p-4 transition-all"
                    style={{
                      backgroundColor: '#F5F5F5',
                      border: `2px solid ${isSelected ? '#0057FF' : 'transparent'}`,
                      cursor: isRunning ? 'not-allowed' : 'pointer',
                      opacity: isRunning && !isSelected ? 0.5 : 1,
                    }}
                  >
                    <div className="flex items-start justify-between gap-3 mb-1">
                      <span className="font-body text-sm font-medium" style={{ color: '#111111' }}>
                        {scenario.label}
                      </span>
                      <span
                        className="font-body text-xs px-2 py-0.5 rounded flex-shrink-0"
                        style={{
                          backgroundColor: (SEVERITY_COLORS[scenario.severity] ?? '#707072') + '20',
                          color: SEVERITY_COLORS[scenario.severity] ?? '#707072',
                        }}
                      >
                        {scenario.severity}
                      </span>
                    </div>
                    <p className="font-mono text-xs mb-1" style={{ color: '#707072' }}>{scenario.table}</p>
                    <p className="font-body text-xs" style={{ color: '#707072' }}>{scenario.desc}</p>
                  </button>
                );
              })}
            </div>

            {/* Run button */}
            <div className="flex gap-3">
              <button
                onClick={runInvestigation}
                disabled={isRunning}
                className="chronos-btn-primary flex-1 py-4"
                style={{
                  opacity: isRunning ? 0.6 : 1,
                  cursor: isRunning ? 'not-allowed' : 'pointer',
                }}
              >
                {isRunning ? (
                  <span className="flex items-center justify-center gap-2">
                    <span
                      className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin"
                      style={{ display: 'inline-block' }}
                    />
                    Investigating...
                  </span>
                ) : (
                  'Run Investigation →'
                )}
              </button>
              {phase !== 'idle' && (
                <button
                  onClick={reset}
                  className="chronos-btn-outline-dark px-5 py-4"
                >
                  Reset
                </button>
              )}
            </div>

            {/* Status message */}
            {statusMsg && (
              <p
                className="font-body text-xs animate-fade-in mt-4"
                style={{
                  color: phase === 'error' ? '#ef4444' : '#707072',
                  padding: '10px 16px',
                  backgroundColor: phase === 'error' ? '#ef444410' : '#F5F5F5',
                  borderRadius: '8px',
                }}
              >
                {statusMsg}
              </p>
            )}

            {/* Step guide */}
            <div
              className="mt-8 pt-6"
              style={{ borderTop: '1px solid #F5F5F5' }}
            >
              <p
                className="font-body text-xs tracking-widest uppercase mb-4"
                style={{ color: '#707072', letterSpacing: '0.12em' }}
              >
                What happens
              </p>
              {[
                'POST scenario → /api/v1/demo/run',
                'SSE stream → /api/v1/investigations/{id}/stream',
                'View full formatted report →',
              ].map((step, i) => (
                <div key={i} className="flex gap-3 items-start mb-3">
                  <span
                    className="font-heading text-lg leading-none flex-shrink-0"
                    style={{ color: '#E8E8E8' }}
                  >
                    {i + 1}
                  </span>
                  <span
                    className="font-mono text-xs pt-0.5"
                    style={{ color: '#707072' }}
                  >
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT: Terminal + RCA */}
          <div className="flex flex-col gap-6">
            {/* Terminal */}
            <DemoTerminal
              events={events}
              isConnected={isConnected}
              error={rcaReport ? null : sseError}
              isIdle={phase === 'idle'}
            />

            {/* RCA Card */}
            {rcaReport && <RCACard report={rcaReport} />}

            {/* Incident link */}
            {incidentId && phase === 'done' && (
              <div
                className="p-4 flex items-center justify-between"
                style={{ backgroundColor: '#111111' }}
              >
                <span className="font-body text-xs" style={{ color: '#707072' }}>
                  Full incident report
                </span>
                <Link
                  to={`/report/${incidentId}`}
                  className="font-body text-xs"
                  style={{ color: '#0057FF', textDecoration: 'none' }}
                >
                  View Full Report →
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function APIReferenceSection() {
  const curlSnippet = `# Trigger an investigation
curl -X POST https://chronos-api-0e8635fe890d.herokuapp.com/api/v1/webhooks/openmetadata \\
  -H "Content-Type: application/json" \\
  -d '{
    "eventType": "TestCaseFailed",
    "entityType": "table",
    "entityFQN": "prod.orders.orders_daily",
    "testCaseResult": {
      "testCaseFQN": "prod.orders.orders_daily.row_count_check",
      "testCaseStatus": "Failed",
      "severity": "HIGH"
    }
  }'`;

  return (
    <section
      id="api"
      className="py-32 px-6 md:px-16"
      style={{ backgroundColor: '#FFFFFF' }}
    >
      <div className="max-w-6xl mx-auto">
        <p
          className="text-xs tracking-[0.3em] uppercase mb-6 font-body"
          style={{ color: '#0057FF' }}
        >
          API Reference
        </p>

        <h2
          className="font-heading text-chronos-black mb-4 leading-tight"
          style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}
        >
          One webhook.
          <br />
          Full investigation.
        </h2>
        <p
          className="font-body text-base mb-14 max-w-xl"
          style={{ color: '#707072' }}
        >
          Any system that can fire a webhook can trigger CHRONOS. No SDK required.
        </p>

        <div
          className="overflow-auto"
          style={{
            backgroundColor: '#111111',
            borderRadius: '4px',
          }}
        >
          {/* Code header */}
          <div
            className="px-5 py-3 flex items-center gap-3"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}
          >
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444' }} />
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308' }} />
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#22c55e' }} />
            <span
              className="ml-3 font-mono text-xs"
              style={{ color: '#707072' }}
            >
              bash
            </span>
          </div>

          <pre
            className="px-6 py-6 overflow-x-auto font-mono text-sm leading-loose"
            style={{ color: '#F5F5F5' }}
          >
            {curlSnippet.split('\n').map((line, i) => {
              const isComment = line.trim().startsWith('#');
              const isKey = line.includes('"') && line.includes(':');
              return (
                <div key={i}>
                  <span
                    style={{
                      color: isComment
                        ? '#707072'
                        : line.includes('-H') || line.includes('-d') || line.includes('-X')
                        ? '#0057FF'
                        : isKey
                        ? '#F5F5F5'
                        : '#F5F5F5',
                    }}
                  >
                    {line}
                  </span>
                </div>
              );
            })}
          </pre>
        </div>

        {/* Endpoint list */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-0 divide-y md:divide-y-0 md:divide-x" style={{ borderColor: '#E8E8E8', border: '1px solid #E8E8E8' }}>
          {[
            {
              method: 'POST',
              path: '/api/v1/webhooks/openmetadata',
              desc: 'Trigger investigation via OpenMetadata webhook',
            },
            {
              method: 'GET',
              path: '/api/v1/incidents',
              desc: 'List all incidents with filtering + pagination',
            },
            {
              method: 'GET',
              path: '/api/v1/investigations/{id}/stream',
              desc: 'SSE stream for live investigation progress',
            },
          ].map(({ method, path, desc }) => (
            <div key={path} className="p-6">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="font-mono text-xs px-2 py-0.5 rounded"
                  style={{
                    backgroundColor: method === 'POST' ? '#0057FF20' : '#22c55e20',
                    color: method === 'POST' ? '#0057FF' : '#22c55e',
                  }}
                >
                  {method}
                </span>
              </div>
              <p className="font-mono text-sm mb-2" style={{ color: '#111111' }}>
                {path}
              </p>
              <p className="font-body text-xs" style={{ color: '#707072' }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer
      className="py-16 px-6 md:px-16"
      style={{ backgroundColor: '#111111' }}
    >
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
          <div>
            <h4
              className="font-heading text-white mb-2"
              style={{ fontSize: '28px' }}
            >
              CHRONOS
            </h4>
            <p className="font-body text-xs" style={{ color: '#707072' }}>
              Built with LangGraph, Graphiti, OpenMetadata
            </p>
          </div>

          <div className="flex flex-wrap gap-6 items-center">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm transition-colors hover:text-white"
              style={{ color: '#707072' }}
            >
              GitHub
            </a>
            <a
              href="https://chronos-api-0e8635fe890d.herokuapp.com/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm transition-colors hover:text-white"
              style={{ color: '#707072' }}
            >
              API Docs
            </a>
            <a
              href="https://chronos-api-0e8635fe890d.herokuapp.com/api/v1/incidents"
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm transition-colors hover:text-white"
              style={{ color: '#707072' }}
            >
              Live API
            </a>
          </div>
        </div>

        <div
          className="mt-12 pt-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
          style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}
        >
          <p className="font-body text-xs" style={{ color: '#404040' }}>
            © 2026 CHRONOS. AI-powered data incident investigation.
          </p>
          <p className="font-body text-xs" style={{ color: '#404040' }}>
            LangGraph · Graphiti · FalkorDB · LiteLLM · Groq
          </p>
        </div>
      </div>
    </footer>
  );
}

export default function Demo() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#FFFFFF' }}>
      <HeroSection />
      <HowItWorks />
      <LiveDemoSection />
      <ArchitectureSection />
      <APIReferenceSection />
      <AgentSection />
      <Footer />
    </div>
  );
}

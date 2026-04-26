import { useState, useCallback, useRef } from 'react';
import { useSSE } from '../hooks/useSSE';
import DemoTerminal from '../components/DemoTerminal';
import RCACard from '../components/RCACard';
import HeroSection from '../components/HeroSection';
import HowItWorks from '../components/HowItWorks';
import ArchitectureSection from '../components/ArchitectureSection';
import type { IncidentReport } from '../types';

const API_BASE = 'https://chronos-api-0e8635fe890d.herokuapp.com';

const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;
type Severity = (typeof SEVERITIES)[number];

function buildWebhookPayload(tableName: string, testName: string, severity: Severity) {
  const fqn = `prod.orders.${tableName}`;
  const now = new Date().toISOString();
  return {
    eventType: 'TestCaseFailed',
    timestamp: now,
    entityType: 'table',
    entityFQN: fqn,
    userName: 'chronos-demo',
    changeDescription: {
      fieldsUpdated: [
        {
          name: 'testCaseResult',
          newValue: JSON.stringify({
            testCaseFQN: `${fqn}.${testName}`,
            result: 'FAILED',
            testResultValue: [{ name: 'rowCount', value: '0' }],
            timestamp: now,
            testCaseStatus: 'Failed',
            incidentId: null,
          }),
        },
      ],
    },
    entity: {
      id: `demo-table-${tableName}`,
      type: 'table',
      name: tableName,
      fullyQualifiedName: fqn,
      description: `Demo table: ${tableName}`,
      href: `${API_BASE}/api/v1/tables/${tableName}`,
    },
    testCaseResult: {
      testCaseFQN: `${fqn}.${testName}`,
      result: 'FAILED',
      testCaseStatus: 'Failed',
      severity: severity,
      timestamp: now,
      testResultValue: [{ name: 'rowCount', value: '0' }],
      failureMessage: `Test ${testName} failed: row count dropped to 0. Expected > 1000.`,
    },
  };
}

async function pollForIncident(
  tableName: string,
  maxAttempts = 15
): Promise<string | null> {
  const fqn = `prod.orders.${tableName}`;
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 2000));
    try {
      const res = await fetch(`${API_BASE}/api/v1/incidents?limit=20`);
      if (!res.ok) continue;
      const body = (await res.json()) as {
        incidents?: IncidentReport[];
        items?: IncidentReport[];
      };
      const list = body.incidents ?? body.items ?? [];
      const match = list.find(
        (inc) =>
          inc.affected_entity_fqn === fqn ||
          inc.affected_entity_fqn?.includes(tableName)
      );
      if (match) return match.incident_id;
    } catch {
      // network error — keep polling
    }
  }
  return null;
}

async function fetchIncidentReport(incidentId: string): Promise<IncidentReport | null> {
  for (let i = 0; i < 10; i++) {
    await new Promise((r) => setTimeout(r, 3000));
    try {
      const res = await fetch(`${API_BASE}/api/v1/incidents/${incidentId}`);
      if (!res.ok) continue;
      const report = (await res.json()) as IncidentReport;
      if (report.probable_root_cause) return report;
    } catch {
      // keep waiting
    }
  }
  return null;
}

function LiveDemoSection() {
  const [tableName, setTableName] = useState('orders_daily');
  const [testName, setTestName] = useState('row_count_check');
  const [severity, setSeverity] = useState<Severity>('HIGH');
  const [isRunning, setIsRunning] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);
  const [rcaReport, setRcaReport] = useState<IncidentReport | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [phase, setPhase] = useState<'idle' | 'posting' | 'polling' | 'streaming' | 'done' | 'error'>('idle');
  const abortRef = useRef<AbortController | null>(null);

  const { events, isConnected, error: sseError } = useSSE(incidentId);

  const runInvestigation = useCallback(async () => {
    if (isRunning) return;

    setIsRunning(true);
    setRcaReport(null);
    setIncidentId(null);
    setStatusMsg(null);
    setPhase('posting');

    abortRef.current = new AbortController();

    try {
      // Step 1: POST webhook
      setStatusMsg('Sending failure event to CHRONOS...');
      const payload = buildWebhookPayload(tableName, testName, severity);

      const res = await fetch(`${API_BASE}/api/v1/webhooks/openmetadata`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(`Webhook failed (${res.status}): ${errBody}`);
      }

      // Try to get incident_id directly from response
      let id: string | null = null;
      try {
        const body = (await res.json()) as {
          incident_id?: string;
          id?: string;
          investigation_id?: string;
        };
        id = body.incident_id ?? body.id ?? body.investigation_id ?? null;
      } catch {
        // response not JSON
      }

      // Step 2: Poll for incident if not in response
      if (!id) {
        setPhase('polling');
        setStatusMsg('Event received. Polling for incident ID...');
        id = await pollForIncident(tableName);
      }

      if (!id) {
        throw new Error('Investigation started but could not locate incident ID. Check the API logs.');
      }

      // Step 3: Connect SSE stream
      setPhase('streaming');
      setStatusMsg(null);
      setIncidentId(id);

      // Step 4: Wait for RCA report
      setStatusMsg('Streaming investigation... Fetching RCA report when complete.');
      const report = await fetchIncidentReport(id);
      if (report) {
        setRcaReport(report);
        setPhase('done');
        setStatusMsg(null);
      } else {
        setPhase('done');
        setStatusMsg('Investigation complete. RCA report not yet available — try refreshing.');
      }
    } catch (err) {
      setPhase('error');
      setStatusMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setIsRunning(false);
    }
  }, [tableName, testName, severity, isRunning]);

  const reset = () => {
    abortRef.current?.abort();
    setIncidentId(null);
    setRcaReport(null);
    setStatusMsg(null);
    setPhase('idle');
    setIsRunning(false);
  };

  const inputStyle: React.CSSProperties = {
    backgroundColor: '#F5F5F5',
    border: '1.5px solid #E8E8E8',
    borderRadius: '30px',
    padding: '12px 20px',
    fontFamily: '"CM Geom", system-ui, sans-serif',
    fontSize: '14px',
    color: '#111111',
    width: '100%',
    outline: 'none',
    transition: 'border-color 0.15s',
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
          Inject a failure event and watch the agentic investigation pipeline run live.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* LEFT: Form */}
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
              Simulate a data quality failure and watch CHRONOS investigate in real time.
            </p>

            <div className="space-y-5">
              {/* Table Name */}
              <div>
                <label
                  className="font-body text-xs tracking-widest uppercase block mb-2"
                  style={{ color: '#707072', letterSpacing: '0.12em' }}
                >
                  Table Name
                </label>
                <input
                  type="text"
                  value={tableName}
                  onChange={(e) => setTableName(e.target.value)}
                  style={inputStyle}
                  placeholder="orders_daily"
                  disabled={isRunning}
                />
              </div>

              {/* Test Name */}
              <div>
                <label
                  className="font-body text-xs tracking-widest uppercase block mb-2"
                  style={{ color: '#707072', letterSpacing: '0.12em' }}
                >
                  Test Name
                </label>
                <input
                  type="text"
                  value={testName}
                  onChange={(e) => setTestName(e.target.value)}
                  style={inputStyle}
                  placeholder="row_count_check"
                  disabled={isRunning}
                />
              </div>

              {/* Severity */}
              <div>
                <label
                  className="font-body text-xs tracking-widest uppercase block mb-2"
                  style={{ color: '#707072', letterSpacing: '0.12em' }}
                >
                  Severity
                </label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value as Severity)}
                  style={{
                    ...inputStyle,
                    cursor: 'pointer',
                    appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23707072' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 16px center',
                    paddingRight: '40px',
                  }}
                  disabled={isRunning}
                >
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Run button */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={runInvestigation}
                  disabled={isRunning || !tableName || !testName}
                  className="chronos-btn-primary flex-1 py-4"
                  style={{
                    opacity: isRunning || !tableName || !testName ? 0.6 : 1,
                    cursor: isRunning || !tableName || !testName ? 'not-allowed' : 'pointer',
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
                  className="font-body text-xs animate-fade-in"
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
            </div>

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
                'POST webhook → /api/v1/webhooks/openmetadata',
                'SSE stream → /api/v1/investigations/{id}/stream',
                'View full RCA results below',
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
              error={sseError}
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
                <a
                  href={`${API_BASE}/api/v1/incidents/${incidentId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-body text-xs"
                  style={{ color: '#0057FF' }}
                >
                  {incidentId} →
                </a>
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
      <Footer />
    </div>
  );
}

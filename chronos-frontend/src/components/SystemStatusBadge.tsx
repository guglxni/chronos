import { useEffect, useRef, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8100';
const POLL_INTERVAL_MS = 60_000;

type ComponentState = 'healthy' | 'degraded' | 'down' | 'not_configured';
type Overall = 'healthy' | 'degraded' | 'down';

interface Component {
  name: string;
  state: ComponentState;
  latency_ms: number | null;
  detail: string | null;
  last_checked: string;
  required: boolean;
}

interface OverallHealth {
  overall: Overall;
  components: Component[];
  cached_at: string;
}

const STATE_COLORS: Record<ComponentState, string> = {
  healthy: '#22c55e',
  degraded: '#f59e0b',
  down: '#ef4444',
  not_configured: '#6B7280',
};

const STATE_LABELS: Record<ComponentState, string> = {
  healthy: 'Healthy',
  degraded: 'Degraded',
  down: 'Down',
  not_configured: 'Not configured',
};

const OVERALL_COLORS: Record<Overall, string> = {
  healthy: '#22c55e',
  degraded: '#f59e0b',
  down: '#ef4444',
};

function PrettyName({ name }: { name: string }) {
  const map: Record<string, string> = {
    openmetadata: 'OpenMetadata',
    falkordb: 'FalkorDB',
    litellm: 'LiteLLM',
    slack: 'Slack',
  };
  return <>{map[name] ?? name}</>;
}

export default function SystemStatusBadge({ darkMode = true }: { darkMode?: boolean }) {
  const [health, setHealth] = useState<OverallHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const tick = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/health/components`);
        if (res.ok) {
          const data = (await res.json()) as OverallHealth;
          if (!cancelled) {
            setHealth(data);
            setLoading(false);
          }
        }
      } catch {
        // Network blip — keep last known state
      }
      if (!cancelled) {
        timer = setTimeout(tick, POLL_INTERVAL_MS);
      }
    };

    tick();
    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, []);

  // Close panel on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const overall: Overall = health?.overall ?? 'down';
  const dotColor = loading ? '#6B7280' : OVERALL_COLORS[overall];
  const labelColor = darkMode ? 'rgba(255,255,255,0.6)' : '#4A4A4C';

  const overallLabel = loading ? 'Checking…' : overall === 'healthy' ? 'Live' : overall === 'degraded' ? 'Degraded' : 'Down';

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 font-body text-xs px-3 py-1.5 rounded-full transition-colors"
        style={{
          backgroundColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
          border: `1px solid ${darkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'}`,
          color: labelColor,
          cursor: 'pointer',
        }}
        aria-label={`System status: ${overallLabel}`}
      >
        <span
          className="relative flex h-2 w-2"
          aria-hidden
        >
          {!loading && overall === 'healthy' && (
            <span
              className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
              style={{ backgroundColor: dotColor }}
            />
          )}
          <span
            className="relative inline-flex rounded-full h-2 w-2"
            style={{ backgroundColor: dotColor }}
          />
        </span>
        <span className="tracking-wider uppercase" style={{ letterSpacing: '0.1em', fontSize: '11px' }}>
          {overallLabel}
        </span>
      </button>

      {open && health && (
        <div
          className="absolute right-0 mt-2 w-80 z-50"
          style={{
            backgroundColor: darkMode ? '#1a1a1a' : '#FFFFFF',
            border: `1px solid ${darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'}`,
            borderRadius: '8px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          }}
        >
          <div
            className="px-4 py-3"
            style={{ borderBottom: `1px solid ${darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'}` }}
          >
            <p
              className="font-body text-xs tracking-[0.2em] uppercase"
              style={{ color: darkMode ? '#9A9A9C' : '#4A4A4C', letterSpacing: '0.15em' }}
            >
              System Status — {overallLabel}
            </p>
          </div>
          <div className="p-3 space-y-2">
            {health.components.map((c) => (
              <div
                key={c.name}
                className="flex items-start gap-3 px-3 py-2 rounded"
                style={{
                  backgroundColor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                }}
              >
                <span
                  className="relative inline-flex rounded-full h-2 w-2 mt-1.5 flex-shrink-0"
                  style={{ backgroundColor: STATE_COLORS[c.state] }}
                  aria-hidden
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 justify-between">
                    <span
                      className="font-mono text-xs"
                      style={{ color: darkMode ? '#F5F5F5' : '#111111' }}
                    >
                      <PrettyName name={c.name} />
                      {!c.required && (
                        <span
                          className="ml-2 px-1 py-0.5 rounded font-body"
                          style={{
                            color: darkMode ? '#686868' : '#808082',
                            backgroundColor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)',
                            fontSize: '9px',
                          }}
                        >
                          optional
                        </span>
                      )}
                    </span>
                    <span
                      className="font-body text-xs"
                      style={{ color: STATE_COLORS[c.state] }}
                    >
                      {STATE_LABELS[c.state]}
                      {c.latency_ms !== null && (
                        <span
                          className="ml-1.5 font-mono"
                          style={{ color: darkMode ? '#686868' : '#808082' }}
                        >
                          {Math.round(c.latency_ms)}ms
                        </span>
                      )}
                    </span>
                  </div>
                  {c.detail && (
                    <p
                      className="font-body text-xs mt-1"
                      style={{ color: darkMode ? '#9A9A9C' : '#4A4A4C', wordBreak: 'break-word' }}
                    >
                      {c.detail}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div
            className="px-4 py-2 font-body text-xs"
            style={{
              borderTop: `1px solid ${darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)'}`,
              color: darkMode ? '#686868' : '#808082',
            }}
          >
            Cached {new Date(health.cached_at).toLocaleTimeString()} · refreshes every 60s
          </div>
        </div>
      )}
    </div>
  );
}

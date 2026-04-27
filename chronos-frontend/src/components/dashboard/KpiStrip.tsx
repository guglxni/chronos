import type { StatsResponse } from '../../lib/dashboardApi';

interface Props {
  stats: StatsResponse | null;
  loading: boolean;
}

interface KpiCard {
  label: string;
  value: string;
  hint: string;
  accent?: string;
}

function formatDuration(ms: number | null): string {
  if (ms === null || ms === 0) return '—';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60_000).toFixed(1)}min`;
}

function formatTokens(n: number): string {
  if (n < 1_000) return String(n);
  if (n < 1_000_000) return `${(n / 1_000).toFixed(1)}k`;
  return `${(n / 1_000_000).toFixed(2)}M`;
}

export default function KpiStrip({ stats, loading }: Props) {
  const cards: KpiCard[] = [
    {
      label: 'Total Incidents',
      value: loading ? '…' : String(stats?.total ?? 0),
      hint: 'in window',
    },
    {
      label: 'Open',
      value: loading ? '…' : String(stats?.open ?? 0),
      hint: `${stats?.acknowledged ?? 0} ack · ${stats?.resolved ?? 0} resolved`,
      accent: (stats?.open ?? 0) > 0 ? '#ef4444' : '#22c55e',
    },
    {
      label: 'Avg Time-to-RCA',
      value: loading ? '…' : formatDuration(stats?.avg_duration_ms ?? null),
      hint: stats?.avg_confidence !== null && stats?.avg_confidence !== undefined
        ? `confidence ${(stats.avg_confidence * 100).toFixed(0)}%`
        : 'no data',
    },
    {
      label: 'LLM Tokens',
      value: loading ? '…' : formatTokens(stats?.total_tokens ?? 0),
      hint: 'consumed in window',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="p-6"
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '4px',
            borderTop: c.accent ? `2px solid ${c.accent}` : '2px solid #5B8AFF',
          }}
        >
          <p
            className="font-body text-xs tracking-[0.15em] uppercase mb-3"
            style={{ color: '#4A4A4C' }}
          >
            {c.label}
          </p>
          <p
            className="font-heading mb-1"
            style={{ fontSize: '36px', color: '#111111', lineHeight: 1 }}
          >
            {c.value}
          </p>
          <p className="font-body text-xs mt-2" style={{ color: '#5A5A5C' }}>
            {c.hint}
          </p>
        </div>
      ))}
    </div>
  );
}

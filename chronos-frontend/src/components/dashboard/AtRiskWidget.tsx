import type { RiskScore } from '../../lib/dashboardApi';

interface Props {
  scores: RiskScore[];
  loading: boolean;
  onSelect: (score: RiskScore) => void;
}

function scoreColor(score: number): string {
  if (score >= 70) return '#ef4444';   // red
  if (score >= 40) return '#f59e0b';   // amber
  if (score >= 20) return '#5B8AFF';   // blue
  return '#22c55e';                    // green
}

function Sparkline({ values, color }: { values: number[]; color: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const w = 80;
  const h = 22;
  const barW = w / values.length;
  return (
    <svg width={w} height={h} aria-hidden>
      {values.map((v, i) => {
        const bh = max ? (v / max) * h : 0;
        return (
          <rect
            key={i}
            x={i * barW}
            y={h - bh}
            width={Math.max(barW - 1, 1)}
            height={bh}
            fill={color}
            opacity={v ? 0.85 : 0.15}
            rx={1}
          />
        );
      })}
    </svg>
  );
}

export default function AtRiskWidget({ scores, loading, onSelect }: Props) {
  return (
    <div
      className="p-6"
      style={{ backgroundColor: '#FFFFFF', borderRadius: '4px' }}
    >
      <div className="flex items-center justify-between mb-4">
        <p
          className="font-body text-xs tracking-[0.15em] uppercase"
          style={{ color: '#4A4A4C' }}
        >
          🔮 Top At-Risk Entities
        </p>
        <p className="font-body text-xs" style={{ color: '#5A5A5C' }}>
          predicted from 30d history
        </p>
      </div>

      {loading ? (
        <p className="font-body text-sm py-8 text-center" style={{ color: '#5A5A5C' }}>
          Loading…
        </p>
      ) : scores.length === 0 ? (
        <div className="py-10 text-center">
          <p className="font-body text-sm" style={{ color: '#4A4A4C' }}>
            No entities have past incidents to score yet
          </p>
          <p className="font-mono text-xs mt-2" style={{ color: '#5A5A5C' }}>
            python scripts/real_seed.py --count 12
          </p>
        </div>
      ) : (
        <div className="space-y-1">
          {scores.map((s) => {
            const color = scoreColor(s.score);
            return (
              <button
                key={s.entity_fqn}
                onClick={() => onSelect(s)}
                className="w-full grid grid-cols-12 items-center gap-3 px-3 py-2.5 rounded transition-colors hover:bg-black/[0.03] text-left"
                style={{ cursor: 'pointer', border: 'none', background: 'transparent' }}
              >
                <span
                  className="col-span-1 font-heading text-sm"
                  style={{ color: '#5A5A5C' }}
                >
                  #{s.rank}
                </span>
                <span
                  className="col-span-5 font-mono text-xs truncate"
                  style={{ color: '#111111' }}
                  title={s.entity_fqn}
                >
                  {s.entity_fqn}
                </span>
                <div className="col-span-3 flex items-center gap-2">
                  <Sparkline values={s.sparkline_30d} color={color} />
                </div>
                <div className="col-span-3 flex items-center justify-end gap-2">
                  <div
                    className="flex-1 h-1.5 rounded-full overflow-hidden"
                    style={{ backgroundColor: 'rgba(0,0,0,0.06)' }}
                  >
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${s.score}%`, backgroundColor: color }}
                    />
                  </div>
                  <span
                    className="font-mono text-sm font-medium tabular-nums"
                    style={{ color, minWidth: 32, textAlign: 'right' }}
                  >
                    {Math.round(s.score)}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

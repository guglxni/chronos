import { useEffect } from 'react';
import type { RiskScore } from '../../lib/dashboardApi';

interface Props {
  score: RiskScore | null;
  onClose: () => void;
}

function scoreColor(score: number): string {
  if (score >= 70) return '#ef4444';
  if (score >= 40) return '#f59e0b';
  if (score >= 20) return '#5B8AFF';
  return '#22c55e';
}

export default function RiskExplainerModal({ score, onClose }: Props) {
  useEffect(() => {
    if (!score) return;
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onEsc);
    return () => document.removeEventListener('keydown', onEsc);
  }, [score, onClose]);

  if (!score) return null;
  const color = scoreColor(score.score);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(17,17,17,0.5)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl max-h-[85vh] overflow-auto"
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '6px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="px-8 py-6"
          style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p
                className="font-body text-xs tracking-[0.15em] uppercase mb-2"
                style={{ color: '#4A4A4C' }}
              >
                Risk Score Explanation
              </p>
              <p
                className="font-mono text-sm break-all"
                style={{ color: '#111111' }}
              >
                {score.entity_fqn}
              </p>
            </div>
            <div className="flex items-center gap-4 flex-shrink-0">
              <div className="text-right">
                <p
                  className="font-heading"
                  style={{ fontSize: '36px', color, lineHeight: 1 }}
                >
                  {Math.round(score.score)}
                </p>
                <p className="font-body text-xs mt-1" style={{ color: '#5A5A5C' }}>
                  out of 100
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="text-2xl leading-none"
                style={{
                  color: '#5A5A5C',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0 4px',
                }}
              >
                ×
              </button>
            </div>
          </div>
        </div>

        {/* Factors */}
        <div className="px-8 py-6">
          <p
            className="font-body text-xs tracking-[0.15em] uppercase mb-4"
            style={{ color: '#4A4A4C' }}
          >
            Contributing Factors
          </p>
          <div className="space-y-3">
            {score.contributions.map((c) => (
              <div
                key={c.factor}
                className="grid grid-cols-12 items-center gap-3 px-3 py-2.5 rounded"
                style={{ backgroundColor: '#F5F5F5' }}
              >
                <div className="col-span-5">
                  <p className="font-body text-sm" style={{ color: '#111111' }}>
                    {c.factor}
                  </p>
                </div>
                <div className="col-span-5">
                  <p className="font-body text-xs" style={{ color: '#4A4A4C' }}>
                    {c.explanation}
                  </p>
                </div>
                <div className="col-span-2 text-right">
                  <span
                    className="font-mono text-sm font-medium tabular-nums"
                    style={{ color: c.contribution > 0 ? color : '#5A5A5C' }}
                  >
                    +{c.contribution.toFixed(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Factor stats */}
        <div className="px-8 py-6" style={{ borderTop: '1px solid rgba(0,0,0,0.06)' }}>
          <p
            className="font-body text-xs tracking-[0.15em] uppercase mb-4"
            style={{ color: '#4A4A4C' }}
          >
            Factor Breakdown
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <p style={{ color: '#5A5A5C' }} className="font-body mb-1">Incidents (window)</p>
              <p className="font-mono" style={{ color: '#111111' }}>{score.factors.incident_count_window}</p>
            </div>
            <div>
              <p style={{ color: '#5A5A5C' }} className="font-body mb-1">Open</p>
              <p className="font-mono" style={{ color: '#111111' }}>{score.factors.open_count}</p>
            </div>
            <div>
              <p style={{ color: '#5A5A5C' }} className="font-body mb-1">Distinct causes</p>
              <p className="font-mono" style={{ color: '#111111' }}>{score.factors.unique_root_causes}</p>
            </div>
            <div>
              <p style={{ color: '#5A5A5C' }} className="font-body mb-1">Avg severity</p>
              <p className="font-mono" style={{ color: '#111111' }}>{score.factors.severity_weighted.toFixed(2)}</p>
            </div>
            <div>
              <p style={{ color: '#5A5A5C' }} className="font-body mb-1">Days since last</p>
              <p className="font-mono" style={{ color: '#111111' }}>
                {score.factors.days_since_last !== null
                  ? `${score.factors.days_since_last.toFixed(1)}d`
                  : '—'}
              </p>
            </div>
            <div>
              <p style={{ color: '#5A5A5C' }} className="font-body mb-1">Last incident</p>
              <p className="font-mono" style={{ color: '#111111' }}>
                {score.last_incident_at
                  ? new Date(score.last_incident_at).toLocaleString()
                  : '—'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

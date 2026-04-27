import type { IncidentReport } from '../types';

interface RCACardProps {
  report: IncidentReport;
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    value >= 0.7 ? '#22c55e' : value >= 0.4 ? '#eab308' : '#ef4444';
  const label =
    value >= 0.7 ? 'HIGH' : value >= 0.4 ? 'MEDIUM' : 'LOW';

  return (
    <div className="flex items-center gap-2">
      <span
        className="font-body text-xs tracking-widest uppercase px-3 py-1 rounded-full font-medium"
        style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}50` }}
      >
        {label} CONFIDENCE
      </span>
      <span
        className="font-heading text-2xl"
        style={{ color }}
      >
        {pct}%
      </span>
    </div>
  );
}

const PRIORITY_ORDER = { immediate: 0, short_term: 1, long_term: 2 } as const;
const PRIORITY_LABEL = {
  immediate: 'Immediate',
  short_term: 'Short-term',
  long_term: 'Long-term',
} as const;
const PRIORITY_COLOR = {
  immediate: '#ef4444',
  short_term: '#eab308',
  long_term: '#22c55e',
} as const;

export default function RCACard({ report }: RCACardProps) {
  const sortedActions = [...report.recommended_actions].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  const duration = report.investigation_duration_ms
    ? `${(report.investigation_duration_ms / 1000).toFixed(1)}s`
    : null;

  return (
    <div
      className="rounded-none animate-slide-up"
      style={{ backgroundColor: '#FFFFFF' }}
    >
      {/* Header strip */}
      <div
        className="px-6 py-4 flex items-center justify-between"
        style={{ backgroundColor: '#111111' }}
      >
        <div>
          <p className="font-body text-xs tracking-widest uppercase mb-1" style={{ color: '#5B8AFF' }}>
            Root Cause Analysis
          </p>
          <p className="font-body text-xs" style={{ color: '#4A4A4C' }}>
            {report.incident_id}
            {duration && <span className="ml-3">· {duration}</span>}
          </p>
        </div>
        <ConfidenceBadge value={report.confidence} />
      </div>

      <div className="p-6 space-y-8">
        {/* Probable Root Cause */}
        <div>
          <p
            className="font-body text-xs tracking-widest uppercase mb-3"
            style={{ color: '#4A4A4C', letterSpacing: '0.15em' }}
          >
            Probable Root Cause
          </p>
          <h3
            className="font-heading leading-tight"
            style={{ fontSize: 'clamp(20px, 2.5vw, 28px)', color: '#111111' }}
          >
            {report.probable_root_cause}
          </h3>
          <div className="mt-3 flex items-center gap-3">
            <span
              className="font-body text-xs px-3 py-1 rounded-full tracking-wider uppercase"
              style={{ backgroundColor: '#F5F5F5', color: '#111111' }}
            >
              {report.root_cause_category.replace(/_/g, ' ')}
            </span>
            <span
              className="font-body text-xs px-3 py-1 rounded-full tracking-wider uppercase"
              style={{
                backgroundColor:
                  report.business_impact === 'critical'
                    ? '#ef444420'
                    : report.business_impact === 'high'
                    ? '#f9731620'
                    : '#eab30820',
                color:
                  report.business_impact === 'critical'
                    ? '#ef4444'
                    : report.business_impact === 'high'
                    ? '#f97316'
                    : '#eab308',
              }}
            >
              {report.business_impact} impact
            </span>
          </div>
        </div>

        {/* Evidence Chain */}
        {report.evidence_chain && report.evidence_chain.length > 0 && (
          <div>
            <p
              className="font-body text-xs tracking-widest uppercase mb-4"
              style={{ color: '#4A4A4C', letterSpacing: '0.15em' }}
            >
              Evidence Chain
            </p>
            <div className="space-y-3">
              {report.evidence_chain.slice(0, 5).map((ev, i) => (
                <div key={i} className="flex gap-4 items-start">
                  {/* Timeline dot */}
                  <div className="flex flex-col items-center flex-shrink-0 mt-1">
                    <div
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: '#5B8AFF' }}
                    />
                    {i < Math.min(report.evidence_chain.length, 5) - 1 && (
                      <div
                        className="w-px flex-1 mt-1"
                        style={{ backgroundColor: '#E8E8E8', minHeight: '20px' }}
                      />
                    )}
                  </div>
                  <div className="flex-1 pb-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span
                        className="font-body text-xs uppercase tracking-wider"
                        style={{ color: '#5B8AFF' }}
                      >
                        {ev.source}
                      </span>
                      <span className="font-body text-xs" style={{ color: '#E8E8E8' }}>·</span>
                      <span className="font-body text-xs" style={{ color: '#4A4A4C' }}>
                        {Math.round(ev.confidence * 100)}% conf.
                      </span>
                    </div>
                    <p className="font-body text-sm" style={{ color: '#111111' }}>
                      {ev.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommended Actions */}
        {sortedActions.length > 0 && (
          <div>
            <p
              className="font-body text-xs tracking-widest uppercase mb-4"
              style={{ color: '#4A4A4C', letterSpacing: '0.15em' }}
            >
              Recommended Actions
            </p>
            <div className="space-y-3">
              {sortedActions.map((action, i) => (
                <div
                  key={i}
                  className="flex gap-4 items-start p-4"
                  style={{ backgroundColor: '#F5F5F5' }}
                >
                  <span
                    className="font-heading text-2xl leading-none flex-shrink-0 mt-1"
                    style={{ color: '#E8E8E8' }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="font-body text-xs uppercase tracking-wider"
                        style={{ color: PRIORITY_COLOR[action.priority] }}
                      >
                        {PRIORITY_LABEL[action.priority]}
                      </span>
                      {action.owner && (
                        <>
                          <span className="font-body text-xs" style={{ color: '#E8E8E8' }}>·</span>
                          <span className="font-body text-xs" style={{ color: '#4A4A4C' }}>
                            {action.owner}
                          </span>
                        </>
                      )}
                    </div>
                    <p className="font-body text-sm" style={{ color: '#111111' }}>
                      {action.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Affected assets */}
        {report.affected_downstream && report.affected_downstream.length > 0 && (
          <div>
            <p
              className="font-body text-xs tracking-widest uppercase mb-4"
              style={{ color: '#4A4A4C', letterSpacing: '0.15em' }}
            >
              Downstream Impact ({report.affected_downstream.length} assets)
            </p>
            <div className="flex flex-wrap gap-2">
              {report.affected_downstream.slice(0, 8).map((asset, i) => (
                <span
                  key={i}
                  className="font-body text-xs px-3 py-1.5 rounded-full"
                  style={{
                    backgroundColor: '#F5F5F5',
                    color: '#111111',
                    fontFamily: 'monospace',
                  }}
                  title={asset.fqn}
                >
                  {asset.display_name || asset.fqn.split('.').pop()}
                </span>
              ))}
              {report.affected_downstream.length > 8 && (
                <span
                  className="font-body text-xs px-3 py-1.5 rounded-full"
                  style={{ backgroundColor: '#F5F5F5', color: '#4A4A4C' }}
                >
                  +{report.affected_downstream.length - 8} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Footer meta */}
        <div
          className="pt-4 flex flex-wrap gap-4 items-center"
          style={{ borderTop: '1px solid #F5F5F5' }}
        >
          {[
            { label: 'Model', value: report.llm_model_used },
            { label: 'Analysis Steps', value: report.total_mcp_calls ? String(report.total_mcp_calls) : undefined },
            { label: 'LLM Tokens', value: report.total_llm_tokens ? report.total_llm_tokens.toLocaleString() : undefined },
          ].map(({ label, value }) =>
            value ? (
              <div key={label} className="flex items-center gap-1.5">
                <span className="font-body text-xs" style={{ color: '#4A4A4C' }}>{label}</span>
                <span
                  className="font-body text-xs px-2 py-0.5 rounded"
                  style={{ backgroundColor: '#F5F5F5', color: '#111111', fontFamily: 'monospace' }}
                >
                  {value}
                </span>
              </div>
            ) : null
          )}
        </div>
      </div>
    </div>
  );
}

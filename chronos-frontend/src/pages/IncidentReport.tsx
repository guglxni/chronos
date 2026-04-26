import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { IncidentReport } from '../types';

const API_BASE = 'https://chronos-api-0e8635fe890d.herokuapp.com';

const PRIORITY_COLORS: Record<string, string> = {
  immediate: '#ef4444',
  short_term: '#f59e0b',
  long_term: '#22c55e',
};

const CATEGORY_LABELS: Record<string, string> = {
  SCHEMA_CHANGE: 'Schema Change',
  CODE_CHANGE: 'Code Change',
  DATA_DRIFT: 'Data Drift',
  PIPELINE_FAILURE: 'Pipeline Failure',
  PERMISSION_CHANGE: 'Permission Change',
  UPSTREAM_FAILURE: 'Upstream Failure',
  CONFIGURATION_CHANGE: 'Configuration Change',
  UNKNOWN: 'Unknown',
};

function fmt(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 70 ? '#22c55e' : pct >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <span
      className="font-body text-sm px-3 py-1 rounded-full"
      style={{ backgroundColor: color + '20', color, border: `1px solid ${color}40` }}
    >
      {pct}% confidence
    </span>
  );
}

export default function IncidentReport() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const [report, setReport] = useState<IncidentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!incidentId) return;
    setLoading(true);
    fetch(`${API_BASE}/api/v1/incidents/${incidentId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<IncidentReport>;
      })
      .then((data) => { setReport(data); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, [incidentId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F5F5F5' }}>
        <div className="text-center">
          <div className="w-8 h-8 rounded-full border-2 border-chronos-blue border-t-transparent animate-spin mx-auto mb-4" />
          <p className="font-body text-sm" style={{ color: '#707072' }}>Loading incident report…</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#F5F5F5' }}>
        <div className="text-center max-w-md">
          <h2 className="font-heading mb-4" style={{ fontSize: '32px', color: '#111111' }}>Report not found</h2>
          <p className="font-body text-sm mb-6" style={{ color: '#707072' }}>{error ?? 'Incident could not be loaded.'}</p>
          <Link to="/" className="chronos-btn-primary">← Back to CHRONOS</Link>
        </div>
      </div>
    );
  }

  const impactColor: Record<string, string> = { critical: '#ef4444', high: '#f59e0b', medium: '#3b82f6', low: '#22c55e' };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F5F5F5' }}>
      {/* Nav */}
      <nav className="sticky top-0 z-50 px-6 md:px-16 h-16 flex items-center" style={{ backgroundColor: '#111111' }}>
        <Link to="/" className="font-heading text-white mr-auto" style={{ fontSize: '20px', textDecoration: 'none' }}>
          CHRONOS
        </Link>
        <span className="font-body text-xs" style={{ color: '#707072' }}>Incident Report</span>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Back link */}
        <Link
          to="/"
          className="font-body text-xs tracking-widest uppercase mb-10 inline-flex items-center gap-2"
          style={{ color: '#707072', letterSpacing: '0.12em', textDecoration: 'none' }}
        >
          ← Back to Demo
        </Link>

        {/* Header card */}
        <div className="p-8 mb-6" style={{ backgroundColor: '#111111' }}>
          <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
            <div>
              <p className="font-body text-xs tracking-widest uppercase mb-2" style={{ color: '#707072', letterSpacing: '0.12em' }}>
                Incident Report
              </p>
              <h1 className="font-heading text-white leading-tight" style={{ fontSize: 'clamp(24px, 4vw, 40px)' }}>
                {report.affected_entity_fqn}
              </h1>
              <p className="font-body text-sm mt-2" style={{ color: '#707072' }}>
                {report.test_name} · Detected {fmt(report.detected_at)}
              </p>
            </div>
            <div className="flex flex-col gap-2 items-end">
              <span
                className="font-body text-xs px-3 py-1 rounded-full uppercase tracking-wider"
                style={{
                  backgroundColor: (impactColor[report.business_impact] ?? '#3b82f6') + '20',
                  color: impactColor[report.business_impact] ?? '#3b82f6',
                  border: `1px solid ${impactColor[report.business_impact] ?? '#3b82f6'}40`,
                }}
              >
                {report.business_impact} impact
              </span>
              <span className="font-mono text-xs" style={{ color: '#404040' }}>
                ID: {report.incident_id.slice(0, 8)}…
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Duration', value: report.investigation_duration_ms ? `${(report.investigation_duration_ms / 1000).toFixed(1)}s` : '—' },
              { label: 'Status', value: report.status.toUpperCase() },
              { label: 'Confidence', value: `${Math.round((report.confidence ?? 0) * 100)}%` },
              { label: 'Downstream', value: String(report.affected_downstream?.length ?? 0) + ' tables' },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="font-body text-xs mb-1" style={{ color: '#707072', letterSpacing: '0.08em' }}>{label}</p>
                <p className="font-body text-sm font-medium" style={{ color: '#F5F5F5' }}>{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Root Cause */}
        <div className="p-8 mb-6" style={{ backgroundColor: '#FFFFFF' }}>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <p className="font-body text-xs tracking-widest uppercase" style={{ color: '#0057FF', letterSpacing: '0.12em' }}>
              Probable Root Cause
            </p>
            <ConfidenceBadge confidence={report.confidence ?? 0} />
            <span
              className="font-body text-xs px-3 py-1 rounded-full"
              style={{ backgroundColor: '#F5F5F5', color: '#111111' }}
            >
              {CATEGORY_LABELS[report.root_cause_category] ?? report.root_cause_category}
            </span>
          </div>
          <h2 className="font-heading text-chronos-black leading-snug" style={{ fontSize: 'clamp(20px, 3vw, 32px)' }}>
            {report.probable_root_cause}
          </h2>
          {report.failure_message && (
            <p className="font-mono text-xs mt-4 p-3 rounded" style={{ backgroundColor: '#F5F5F5', color: '#707072' }}>
              {report.failure_message}
            </p>
          )}
          {report.business_impact_reasoning && (
            <p className="font-body text-sm mt-4 leading-relaxed" style={{ color: '#707072' }}>
              {report.business_impact_reasoning}
            </p>
          )}
        </div>

        {/* Recommended Actions */}
        {(report.recommended_actions?.length ?? 0) > 0 && (
          <div className="p-8 mb-6" style={{ backgroundColor: '#FFFFFF' }}>
            <p className="font-body text-xs tracking-widest uppercase mb-6" style={{ color: '#0057FF', letterSpacing: '0.12em' }}>
              Recommended Actions
            </p>
            <div className="space-y-3">
              {report.recommended_actions.map((action, i) => (
                <div
                  key={i}
                  className="flex gap-4 items-start p-4"
                  style={{ backgroundColor: '#F5F5F5', borderLeft: `3px solid ${PRIORITY_COLORS[action.priority] ?? '#707072'}` }}
                >
                  <span
                    className="font-body text-xs px-2 py-0.5 rounded flex-shrink-0 uppercase tracking-wider"
                    style={{
                      backgroundColor: (PRIORITY_COLORS[action.priority] ?? '#707072') + '20',
                      color: PRIORITY_COLORS[action.priority] ?? '#707072',
                    }}
                  >
                    {action.priority.replace('_', ' ')}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm" style={{ color: '#111111' }}>{action.description}</p>
                    {action.owner && (
                      <p className="font-body text-xs mt-1" style={{ color: '#707072' }}>Owner: {action.owner}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Downstream Impact */}
        {(report.affected_downstream?.length ?? 0) > 0 && (
          <div className="p-8 mb-6" style={{ backgroundColor: '#FFFFFF' }}>
            <p className="font-body text-xs tracking-widest uppercase mb-6" style={{ color: '#0057FF', letterSpacing: '0.12em' }}>
              Downstream Impact — {report.affected_downstream.length} table{report.affected_downstream.length !== 1 ? 's' : ''} affected
            </p>
            <div className="space-y-2">
              {report.affected_downstream.map((asset) => (
                <div
                  key={asset.fqn}
                  className="flex items-center justify-between p-4"
                  style={{ backgroundColor: '#F5F5F5' }}
                >
                  <div>
                    <p className="font-body text-sm" style={{ color: '#111111' }}>{asset.display_name || asset.fqn}</p>
                    <p className="font-mono text-xs mt-0.5" style={{ color: '#707072' }}>{asset.fqn}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {asset.tier && (
                      <span className="font-body text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: '#E8E8E8', color: '#111111' }}>
                        {asset.tier}
                      </span>
                    )}
                    {asset.owners?.[0] && (
                      <span className="font-body text-xs" style={{ color: '#707072' }}>{asset.owners[0]}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Investigation Timeline */}
        {(report.investigation_timeline?.length ?? 0) > 0 && (
          <div className="p-8 mb-6" style={{ backgroundColor: '#FFFFFF' }}>
            <p className="font-body text-xs tracking-widest uppercase mb-6" style={{ color: '#0057FF', letterSpacing: '0.12em' }}>
              Investigation Timeline
            </p>
            <div className="space-y-2">
              {report.investigation_timeline.map((step) => (
                <div
                  key={step.step}
                  className="flex gap-4 items-start p-4"
                  style={{ backgroundColor: '#F5F5F5' }}
                >
                  <span
                    className="font-heading text-2xl flex-shrink-0 w-8 text-center leading-none"
                    style={{ color: '#E8E8E8' }}
                  >
                    {step.step + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm font-medium mb-0.5" style={{ color: '#111111' }}>
                      {step.name.replace(/_/g, ' ')}
                    </p>
                    <p className="font-body text-xs leading-relaxed" style={{ color: '#707072' }}>{step.summary}</p>
                  </div>
                  {step.duration_ms !== null && step.duration_ms !== undefined && (
                    <span className="font-mono text-xs flex-shrink-0" style={{ color: '#707072' }}>
                      {step.duration_ms}ms
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Meta footer */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4" style={{ borderTop: '1px solid #E8E8E8' }}>
          <p className="font-body text-xs" style={{ color: '#707072' }}>
            CHRONOS v{report.agent_version} · {report.llm_model_used || 'LLM-powered'} · Completed {fmt(report.investigation_completed_at)}
          </p>
          <Link to="/" className="font-body text-xs" style={{ color: '#0057FF', textDecoration: 'none' }}>
            Run another investigation →
          </Link>
        </div>
      </div>
    </div>
  );
}

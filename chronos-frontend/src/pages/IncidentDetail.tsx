import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertTriangle,
  GitBranch,
  Shield,
  Layers,
  FileCode,
  BarChart2,
  RefreshCw,
} from 'lucide-react';
import clsx from 'clsx';
import { useIncidentDetail } from '../hooks/useIncidentDetail';
import { api } from '../lib/api';
import SeverityBadge from '../components/SeverityBadge';
import InvestigationReplay from '../components/InvestigationReplay';
import LineageFailureMap from '../components/LineageFailureMap';
import EvidenceChain from '../components/EvidenceChain';
import BlastRadiusPanel from '../components/BlastRadiusPanel';
import ProvenanceDownload from '../components/ProvenanceDownload';
import LoadingSpinner from '../components/LoadingSpinner';
import type { IncidentStatus } from '../types';

type Tab =
  | 'overview'
  | 'timeline'
  | 'lineage'
  | 'evidence'
  | 'blast'
  | 'provenance';

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'overview',   label: 'Overview',    icon: <BarChart2 className="w-4 h-4" /> },
  { key: 'timeline',   label: 'Timeline',    icon: <Clock className="w-4 h-4" /> },
  { key: 'lineage',    label: 'Lineage Map', icon: <GitBranch className="w-4 h-4" /> },
  { key: 'evidence',   label: 'Evidence',    icon: <Shield className="w-4 h-4" /> },
  { key: 'blast',      label: 'Blast Radius',icon: <Layers className="w-4 h-4" /> },
  { key: 'provenance', label: 'Provenance',  icon: <FileCode className="w-4 h-4" /> },
];

const STATUS_LABEL: Record<IncidentStatus, { label: string; classes: string }> = {
  open:          { label: 'Open',          classes: 'bg-red-900/60 text-red-300 border border-red-800' },
  investigating: { label: 'Investigating', classes: 'bg-yellow-900/60 text-yellow-300 border border-yellow-800' },
  acknowledged:  { label: 'Acknowledged',  classes: 'bg-blue-900/60 text-blue-300 border border-blue-800' },
  resolved:      { label: 'Resolved',      classes: 'bg-green-900/60 text-green-300 border border-green-800' },
};

const PRIORITY_CONFIG = {
  immediate:   { label: 'Immediate',   classes: 'bg-red-900/40 text-red-300 border border-red-800' },
  short_term:  { label: 'Short-term',  classes: 'bg-yellow-900/40 text-yellow-300 border border-yellow-800' },
  long_term:   { label: 'Long-term',   classes: 'bg-blue-900/40 text-blue-300 border border-blue-800' },
} as const;

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [actionLoading, setActionLoading] = useState<'ack' | 'resolve' | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { incident, isLoading, error, refetch } = useIncidentDetail(id);

  async function handleAction(type: 'ack' | 'resolve') {
    if (!id) return;
    setActionLoading(type);
    setActionError(null);
    try {
      if (type === 'ack') await api.acknowledgeIncident(id);
      else await api.resolveIncident(id);
      refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setActionLoading(null);
    }
  }

  if (isLoading) return <LoadingSpinner size="lg" />;

  if (error || !incident) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="card border border-red-800/40">
          <p className="text-red-400 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            {error?.message ?? 'Incident not found'}
          </p>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-secondary mt-3"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const statusCfg = STATUS_LABEL[incident.status] ?? STATUS_LABEL.open;
  const fqnParts = incident.affected_entity_fqn.split('.');
  const entityShort = fqnParts[fqnParts.length - 1];

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Back button */}
      <button
        type="button"
        onClick={() => navigate('/')}
        className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      {/* Header */}
      <div className="card mb-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <SeverityBadge impact={incident.business_impact} size="md" />
              <span className={clsx('text-xs px-2 py-0.5 rounded font-medium', statusCfg.classes)}>
                {statusCfg.label}
              </span>
              <span className="text-xs text-gray-500 font-mono">
                #{incident.incident_id.slice(0, 8)}
              </span>
            </div>
            <h1
              className="text-lg font-bold text-white font-mono truncate"
              title={incident.affected_entity_fqn}
            >
              {entityShort}
            </h1>
            <p
              className="text-xs text-gray-500 font-mono truncate mt-0.5"
              title={incident.affected_entity_fqn}
            >
              {incident.affected_entity_fqn}
            </p>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 flex-wrap">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Detected {format(new Date(incident.detected_at), 'MMM d, yyyy HH:mm')}
              </span>
              {incident.investigation_duration_ms && (
                <span>
                  Investigated in {(incident.investigation_duration_ms / 1000).toFixed(1)}s
                </span>
              )}
              <span className="font-medium text-gray-400">
                {incident.root_cause_category.replace(/_/g, ' ')}
              </span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={() => refetch()}
              className="btn-secondary flex items-center gap-1.5"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            {incident.status !== 'acknowledged' && incident.status !== 'resolved' && (
              <button
                type="button"
                onClick={() => void handleAction('ack')}
                disabled={actionLoading === 'ack'}
                className="btn-secondary flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                {actionLoading === 'ack' ? 'Acknowledging…' : 'Acknowledge'}
              </button>
            )}
            {incident.status !== 'resolved' && (
              <button
                type="button"
                onClick={() => void handleAction('resolve')}
                disabled={actionLoading === 'resolve'}
                className="btn-primary flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                {actionLoading === 'resolve' ? 'Resolving…' : 'Resolve'}
              </button>
            )}
          </div>
        </div>
        {actionError && (
          <p className="text-xs text-red-400 mt-2">{actionError}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-gray-800 mb-6 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'flex items-center gap-1.5 px-4 py-2.5 text-sm whitespace-nowrap transition-colors',
              activeTab === tab.key
                ? 'tab-active'
                : 'tab-inactive'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Root cause & confidence */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2 card">
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Probable Root Cause
                </h2>
                <p className="text-sm text-gray-200 leading-relaxed">
                  {incident.probable_root_cause}
                </p>
              </div>
              <div className="card flex flex-col items-center justify-center text-center">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Confidence
                </p>
                <p
                  className={clsx(
                    'text-4xl font-bold',
                    incident.confidence >= 0.8
                      ? 'text-green-400'
                      : incident.confidence >= 0.5
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  )}
                >
                  {Math.round(incident.confidence * 100)}%
                </p>
                <div className="w-full mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full',
                      incident.confidence >= 0.8
                        ? 'bg-green-500'
                        : incident.confidence >= 0.5
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    )}
                    style={{ width: `${incident.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Failure message */}
            <div className="card">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Failure Message
              </h2>
              <pre className="text-sm text-red-300 bg-red-950/20 rounded-lg p-3 whitespace-pre-wrap break-all font-mono border border-red-900/30">
                {incident.failure_message}
              </pre>
            </div>

            {/* Recommended actions */}
            {incident.recommended_actions && incident.recommended_actions.length > 0 && (
              <div className="card">
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Recommended Actions ({incident.recommended_actions.length})
                </h2>
                <ul className="space-y-3">
                  {incident.recommended_actions.map((action, idx) => {
                    const pcfg = PRIORITY_CONFIG[action.priority] ?? PRIORITY_CONFIG.long_term;
                    return (
                      <li key={idx} className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center text-xs text-gray-400 font-mono mt-0.5">
                          {idx + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span className={clsx('text-xs px-1.5 py-0.5 rounded font-medium', pcfg.classes)}>
                              {pcfg.label}
                            </span>
                            {action.owner && (
                              <span className="text-xs text-gray-500">
                                Owner: <span className="text-gray-400">{action.owner}</span>
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-300">{action.description}</p>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Graphify context */}
            {incident.graphify_context && (
              <div className="card">
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Graph Context (Graphify)
                </h2>
                <p className="text-sm text-gray-400 leading-relaxed">{incident.graphify_context}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" />
              Investigation Timeline
              <span className="text-xs text-gray-500 font-normal">
                ({incident.investigation_timeline?.length ?? 0} steps)
              </span>
            </h2>
            <InvestigationReplay timeline={incident.investigation_timeline ?? []} />
          </div>
        )}

        {activeTab === 'lineage' && (
          <div>
            <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-sky-400" />
              Lineage Failure Map
            </h2>
            <LineageFailureMap incident={incident} />
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-sky-400" />
              Evidence Chain
            </h2>
            <EvidenceChain evidence={incident.evidence_chain ?? []} />
          </div>
        )}

        {activeTab === 'blast' && (
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              Blast Radius
            </h2>
            <BlastRadiusPanel assets={incident.affected_downstream ?? []} />
          </div>
        )}

        {activeTab === 'provenance' && (
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-sky-400" />
              Provenance Artifacts
            </h2>
            <ProvenanceDownload incidentId={incident.incident_id} />
          </div>
        )}
      </div>
    </div>
  );
}

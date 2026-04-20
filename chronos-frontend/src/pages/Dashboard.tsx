import { useState } from 'react';
import { AlertTriangle, Activity, TrendingUp, CheckCircle2, RefreshCw, Plus } from 'lucide-react';
import clsx from 'clsx';
import { useIncidents } from '../hooks/useIncidents';
import IncidentCard from '../components/IncidentCard';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { api } from '../lib/api';

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: '',             label: 'All Statuses' },
  { value: 'open',         label: 'Open' },
  { value: 'investigating',label: 'Investigating' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'resolved',     label: 'Resolved' },
];

const ROOT_CAUSE_OPTIONS: { value: string; label: string }[] = [
  { value: '',                     label: 'All Root Causes' },
  { value: 'SCHEMA_CHANGE',        label: '🏗️ Schema Change' },
  { value: 'CODE_CHANGE',          label: '💻 Code Change' },
  { value: 'DATA_DRIFT',           label: '📊 Data Drift' },
  { value: 'PIPELINE_FAILURE',     label: '⚙️ Pipeline Failure' },
  { value: 'PERMISSION_CHANGE',    label: '🔐 Permission Change' },
  { value: 'UPSTREAM_FAILURE',     label: '⬆️ Upstream Failure' },
  { value: 'CONFIGURATION_CHANGE', label: '🔧 Configuration Change' },
  { value: 'UNKNOWN',              label: '❓ Unknown' },
];

function StatCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={clsx('p-3 rounded-xl', color)}>{icon}</div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
        {sub && <p className="text-xs text-gray-500">{sub}</p>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [statusFilter, setStatusFilter] = useState('');
  const [rootCauseFilter, setRootCauseFilter] = useState('');
  const [triggerFqn, setTriggerFqn] = useState('');
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const [showTriggerForm, setShowTriggerForm] = useState(false);

  const { incidents, stats, isLoading, error, refetch } = useIncidents({
    status: statusFilter || undefined,
    root_cause: rootCauseFilter || undefined,
  });

  async function handleTrigger(e: React.FormEvent) {
    e.preventDefault();
    if (!triggerFqn.trim()) return;
    setTriggering(true);
    setTriggerError(null);
    try {
      await api.triggerInvestigation(triggerFqn.trim());
      setTriggerFqn('');
      setShowTriggerForm(false);
      setTimeout(() => refetch(), 1500);
    } catch (err) {
      setTriggerError(err instanceof Error ? err.message : 'Failed to trigger investigation');
    } finally {
      setTriggering(false);
    }
  }

  const avgConfPct = stats ? Math.round((stats.avg_confidence ?? 0) * 100) : null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Incident Dashboard</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Autonomous root cause analysis — auto-refreshes every 30s
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => refetch()}
            className="btn-secondary flex items-center gap-1.5"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => setShowTriggerForm((v) => !v)}
            className="btn-primary flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Investigate
          </button>
        </div>
      </div>

      {/* Trigger Investigation Form */}
      {showTriggerForm && (
        <div className="mb-6 card border border-sky-800/40 bg-sky-950/20">
          <h2 className="text-sm font-semibold text-sky-300 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Trigger Manual Investigation
          </h2>
          <form onSubmit={(e) => void handleTrigger(e)} className="flex gap-3">
            <input
              type="text"
              placeholder="Entity FQN (e.g. default.orders_table)"
              value={triggerFqn}
              onChange={(e) => setTriggerFqn(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <button
              type="submit"
              disabled={triggering || !triggerFqn.trim()}
              className="btn-primary"
            >
              {triggering ? 'Triggering…' : 'Investigate'}
            </button>
          </form>
          {triggerError && (
            <p className="text-xs text-red-400 mt-2">{triggerError}</p>
          )}
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={<Activity className="w-5 h-5 text-sky-400" />}
          label="Total Incidents"
          value={stats?.total_incidents ?? '—'}
          color="bg-sky-900/40"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
          label="Open"
          value={stats?.open_count ?? '—'}
          sub="Requires attention"
          color="bg-red-900/40"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-orange-400" />}
          label="Critical"
          value={stats?.critical_count ?? '—'}
          sub="High business impact"
          color="bg-orange-900/40"
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5 text-green-400" />}
          label="Avg Confidence"
          value={avgConfPct !== null ? `${avgConfPct}%` : '—'}
          sub="RCA accuracy"
          color="bg-green-900/40"
        />
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={rootCauseFilter}
          onChange={(e) => setRootCauseFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          {ROOT_CAUSE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <span className="text-xs text-gray-500 ml-auto">
          {incidents.length} incident{incidents.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Incident List */}
      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="card border border-red-800/40 bg-red-950/20">
          <p className="text-sm text-red-400 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Failed to load incidents: {error.message}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="btn-secondary mt-3 text-xs"
          >
            Retry
          </button>
        </div>
      ) : incidents.length === 0 ? (
        <EmptyState
          title="No incidents found"
          description={
            statusFilter || rootCauseFilter
              ? 'Try adjusting your filters to see more results.'
              : 'No data incidents have been detected yet. The system is monitoring your data pipeline.'
          }
        />
      ) : (
        <div className="space-y-3">
          {incidents.map((incident) => (
            <IncidentCard key={incident.incident_id} incident={incident} />
          ))}
        </div>
      )}
    </div>
  );
}

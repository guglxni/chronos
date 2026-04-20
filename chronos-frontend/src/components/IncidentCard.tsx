import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { ChevronRight, Clock } from 'lucide-react';
import clsx from 'clsx';
import type { IncidentReport, RootCauseCategory, IncidentStatus } from '../types';
import SeverityBadge from './SeverityBadge';

const ROOT_CAUSE_EMOJI: Record<RootCauseCategory, string> = {
  SCHEMA_CHANGE:        '🏗️',
  CODE_CHANGE:          '💻',
  DATA_DRIFT:           '📊',
  PIPELINE_FAILURE:     '⚙️',
  PERMISSION_CHANGE:    '🔐',
  UPSTREAM_FAILURE:     '⬆️',
  CONFIGURATION_CHANGE: '🔧',
  UNKNOWN:              '❓',
};

const STATUS_CONFIG: Record<IncidentStatus, { label: string; dot: string }> = {
  open:          { label: 'Open',          dot: 'bg-red-500'    },
  investigating: { label: 'Investigating', dot: 'bg-yellow-500 animate-pulse' },
  acknowledged:  { label: 'Acknowledged',  dot: 'bg-blue-500'   },
  resolved:      { label: 'Resolved',      dot: 'bg-green-500'  },
};

interface IncidentCardProps {
  incident: IncidentReport;
}

export default function IncidentCard({ incident }: IncidentCardProps) {
  const navigate = useNavigate();
  const statusCfg = STATUS_CONFIG[incident.status] ?? STATUS_CONFIG.open;
  const emoji = ROOT_CAUSE_EMOJI[incident.root_cause_category] ?? '❓';

  const fqn = incident.affected_entity_fqn;
  const truncatedFqn = fqn.length > 60 ? `…${fqn.slice(-57)}` : fqn;

  return (
    <button
      type="button"
      onClick={() => navigate(`/incidents/${incident.incident_id}`)}
      className={clsx(
        'w-full text-left card hover:border-gray-600 hover:bg-gray-750 transition-all cursor-pointer group',
        'focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-gray-900'
      )}
    >
      <div className="flex items-start gap-3">
        {/* Root cause emoji */}
        <div className="text-2xl mt-0.5 select-none" aria-hidden="true">
          {emoji}
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Top row */}
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <SeverityBadge impact={incident.business_impact} />
            <span className="text-xs text-gray-400 bg-gray-700 rounded px-1.5 py-0.5 font-mono">
              {incident.root_cause_category.replace(/_/g, ' ')}
            </span>
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <span className={clsx('w-1.5 h-1.5 rounded-full inline-block', statusCfg.dot)} />
              {statusCfg.label}
            </span>
          </div>

          {/* Entity FQN */}
          <p
            className="text-sm text-gray-200 font-mono truncate mb-1"
            title={fqn}
          >
            {truncatedFqn}
          </p>

          {/* Test name */}
          <p className="text-xs text-gray-500 truncate mb-2">{incident.test_name}</p>

          {/* Bottom row */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDistanceToNow(new Date(incident.detected_at), { addSuffix: true })}
            </span>
            <span>
              Confidence:{' '}
              <span
                className={clsx(
                  'font-semibold',
                  incident.confidence >= 0.8
                    ? 'text-green-400'
                    : incident.confidence >= 0.5
                    ? 'text-yellow-400'
                    : 'text-red-400'
                )}
              >
                {Math.round(incident.confidence * 100)}%
              </span>
            </span>
            <span className="text-gray-600 font-mono text-xs">
              #{incident.incident_id.slice(0, 8)}
            </span>
          </div>
        </div>

        {/* Chevron */}
        <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors flex-shrink-0 mt-1" />
      </div>
    </button>
  );
}

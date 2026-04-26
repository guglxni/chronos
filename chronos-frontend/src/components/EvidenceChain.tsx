import clsx from 'clsx';
import { ShieldCheck } from 'lucide-react';
import type { EvidenceItem, EvidenceSource } from '../types';
import EmptyState from './EmptyState';

interface EvidenceChainProps {
  evidence: EvidenceItem[];
}

const SOURCE_CONFIG: Record<EvidenceSource, { label: string; classes: string }> = {
  openmetadata: { label: 'OpenMetadata', classes: 'bg-blue-900/60 text-blue-300 border border-blue-700' },
  graphiti:     { label: 'Graphiti',     classes: 'bg-purple-900/60 text-purple-300 border border-purple-700' },
  gitnexus:     { label: 'GitNexus',     classes: 'bg-green-900/60 text-green-300 border border-green-700' },
  graphify:     { label: 'Graphify',     classes: 'bg-indigo-900/60 text-indigo-300 border border-indigo-700' },
  audit_log:    { label: 'Audit Log',    classes: 'bg-orange-900/60 text-orange-300 border border-orange-700' },
  unknown:      { label: 'Unknown',      classes: 'bg-gray-800/60 text-gray-400 border border-gray-700' },
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className={clsx(
          'text-xs font-mono w-8 text-right',
          pct >= 80 ? 'text-green-400' : pct >= 50 ? 'text-yellow-400' : 'text-red-400'
        )}
      >
        {pct}%
      </span>
    </div>
  );
}

export default function EvidenceChain({ evidence }: EvidenceChainProps) {
  if (!evidence || evidence.length === 0) {
    return (
      <EmptyState
        title="No evidence collected"
        description="The investigation did not collect evidence items for this incident."
        icon={<ShieldCheck className="w-12 h-12" />}
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-400">
        {evidence.length} evidence item{evidence.length !== 1 ? 's' : ''} in chain
      </p>
      <ol className="space-y-3">
        {evidence.map((item, idx) => {
          const src = SOURCE_CONFIG[item.source] ?? {
            label: item.source,
            classes: 'bg-gray-700 text-gray-300 border border-gray-600',
          };

          return (
            <li key={idx} className="card border border-gray-700">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-500 font-mono">#{idx + 1}</span>
                  <span className={clsx('text-xs px-2 py-0.5 rounded font-medium', src.classes)}>
                    {src.label}
                  </span>
                </div>
                {item.timestamp && (
                  <span className="text-xs text-gray-500 font-mono flex-shrink-0">
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-300 mb-3 leading-relaxed">{item.description}</p>

              <div className="mb-2">
                <span className="text-xs text-gray-500 mb-1 block">Confidence</span>
                <ConfidenceBar value={item.confidence} />
              </div>

              {Object.keys(item.raw_data ?? {}).length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400 transition-colors">
                    Raw data
                  </summary>
                  <pre className="text-xs bg-gray-900 border border-gray-700 rounded p-2 mt-2 text-gray-400 overflow-x-auto whitespace-pre-wrap break-all">
                    {JSON.stringify(item.raw_data, null, 2)}
                  </pre>
                </details>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

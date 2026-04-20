import { GitCompare } from 'lucide-react';
import EmptyState from './EmptyState';

interface TemporalChange {
  field?: string;
  before?: unknown;
  after?: unknown;
  timestamp?: string;
  description?: string;
}

interface TemporalDiffProps {
  changes: unknown[];
}

function renderValue(val: unknown): string {
  if (val === null || val === undefined) return '(null)';
  if (typeof val === 'object') return JSON.stringify(val, null, 2);
  return String(val);
}

export default function TemporalDiff({ changes }: TemporalDiffProps) {
  if (!changes || changes.length === 0) {
    return (
      <EmptyState
        title="No temporal changes detected"
        description="No schema or data changes were found in the investigation window."
        icon={<GitCompare className="w-12 h-12" />}
      />
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-400">
        {changes.length} temporal change{changes.length !== 1 ? 's' : ''} detected
      </p>
      {changes.map((change, idx) => {
        const c = change as TemporalChange;
        const hasBeforeAfter = c.before !== undefined || c.after !== undefined;

        return (
          <div key={idx} className="card border border-gray-700 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <GitCompare className="w-4 h-4 text-sky-400" />
                <span className="text-sm font-medium text-gray-200">
                  {c.field ?? `Change #${idx + 1}`}
                </span>
              </div>
              {c.timestamp && (
                <span className="text-xs text-gray-500 font-mono">
                  {new Date(c.timestamp).toLocaleString()}
                </span>
              )}
            </div>

            {c.description && (
              <p className="text-sm text-gray-400 mb-3">{c.description}</p>
            )}

            {hasBeforeAfter && (
              <div className="grid grid-cols-2 gap-3">
                {/* Before */}
                <div>
                  <div className="text-xs font-semibold text-red-400 mb-1.5 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                    Before
                  </div>
                  <pre className="text-xs bg-red-950/30 border border-red-900/40 rounded p-3 text-red-300 overflow-x-auto whitespace-pre-wrap break-all">
                    {renderValue(c.before)}
                  </pre>
                </div>
                {/* After */}
                <div>
                  <div className="text-xs font-semibold text-green-400 mb-1.5 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                    After
                  </div>
                  <pre className="text-xs bg-green-950/30 border border-green-900/40 rounded p-3 text-green-300 overflow-x-auto whitespace-pre-wrap break-all">
                    {renderValue(c.after)}
                  </pre>
                </div>
              </div>
            )}

            {!hasBeforeAfter && (
              <pre className="text-xs bg-gray-900 border border-gray-700 rounded p-3 text-gray-400 overflow-x-auto whitespace-pre-wrap break-all">
                {renderValue(change)}
              </pre>
            )}
          </div>
        );
      })}
    </div>
  );
}

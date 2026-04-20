import clsx from 'clsx';
import { CheckCircle2, Clock, Loader2 } from 'lucide-react';
import type { InvestigationTimelineEntry } from '../types';
import EmptyState from './EmptyState';

interface InvestigationReplayProps {
  timeline: InvestigationTimelineEntry[];
}

function formatStep(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDuration(ms: number | null): string {
  if (ms === null) return '—';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export default function InvestigationReplay({ timeline }: InvestigationReplayProps) {
  if (!timeline || timeline.length === 0) {
    return (
      <EmptyState
        title="No timeline data"
        description="Investigation timeline steps have not been recorded for this incident."
      />
    );
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-5 top-0 bottom-0 w-px bg-gray-700" />

      <ol className="space-y-0">
        {timeline.map((entry, idx) => {
          const isCompleted = entry.completed_at !== null;
          const isLast = idx === timeline.length - 1;

          return (
            <li key={entry.step} className="relative flex gap-4 pb-6">
              {/* Step indicator */}
              <div
                className={clsx(
                  'relative z-10 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors',
                  isCompleted
                    ? 'bg-sky-900/60 border-sky-600 text-sky-400'
                    : 'bg-gray-800 border-gray-600 text-gray-500'
                )}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 text-sky-400" />
                ) : (
                  <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
                )}
              </div>

              {/* Content */}
              <div className={clsx('flex-1 min-w-0 pt-1.5', !isLast && 'pb-2')}>
                <div className="flex items-center gap-3 mb-1 flex-wrap">
                  <span className="font-medium text-sm text-gray-200">
                    {formatStep(entry.name)}
                  </span>
                  <span
                    className={clsx(
                      'text-xs rounded px-1.5 py-0.5 font-mono',
                      isCompleted
                        ? 'bg-sky-900/40 text-sky-400'
                        : 'bg-gray-700 text-gray-400'
                    )}
                  >
                    Step {entry.step}
                  </span>
                  {entry.duration_ms !== null && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {formatDuration(entry.duration_ms)}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-400 leading-relaxed">{entry.summary}</p>
                {entry.started_at && (
                  <p className="text-xs text-gray-600 mt-1 font-mono">
                    {new Date(entry.started_at).toLocaleTimeString()}
                    {entry.completed_at && (
                      <> — {new Date(entry.completed_at).toLocaleTimeString()}</>
                    )}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

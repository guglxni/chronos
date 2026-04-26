import { useEffect, useRef } from 'react';
import type { SSEEvent } from '../hooks/useSSE';

interface DemoTerminalProps {
  events: SSEEvent[];
  isConnected: boolean;
  error: string | null;
  isIdle: boolean;
}

function formatEventLine(ev: SSEEvent): { icon: string; text: string } {
  const data = ev.data as Record<string, unknown> | null | undefined;
  const node = typeof data?.node === 'string' ? data.node : null;
  const message = typeof data?.message === 'string' ? data.message : null;
  const summary = typeof data?.summary === 'string' ? data.summary : null;

  const text = summary ?? message ?? (node ? `Running node: ${node}` : JSON.stringify(ev.data));

  const iconMap: Record<string, string> = {
    scope_failure: '⚡',
    lineage_walk: '🔗',
    temporal_diff: '📅',
    audit_correlation: '🔍',
    code_blast_radius: '💥',
    prior_investigations: '📚',
    downstream_impact: '🌊',
    rca_synthesis: '🧠',
    persist_trace: '💾',
    notify: '📣',
    complete: '✅',
    connected: '🔌',
    heartbeat: '💓',
    update: '→',
  };

  const evType = ev.type ?? '';
  const icon = iconMap[node ?? ''] ?? iconMap[evType] ?? '›';
  return { icon, text };
}

export default function DemoTerminal({ events, isConnected, error, isIdle }: DemoTerminalProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  return (
    <div
      className="relative rounded-none overflow-hidden"
      style={{
        backgroundColor: '#111111',
        minHeight: '320px',
        fontFamily: '"CM Geom", ui-monospace, monospace',
      }}
    >
      {/* Terminal title bar */}
      <div
        className="flex items-center gap-2 px-4 py-2.5"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}
      >
        <span
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: isConnected ? '#22c55e' : '#ef4444' }}
        />
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308' }} />
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6' }} />
        <span
          className="ml-3 text-xs font-body tracking-widest uppercase"
          style={{ color: '#707072', letterSpacing: '0.12em' }}
        >
          chronos — investigation stream
        </span>
        {isConnected && (
          <span
            className="ml-auto flex items-center gap-1.5 text-xs font-body"
            style={{ color: '#22c55e' }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            LIVE
          </span>
        )}
      </div>

      {/* Terminal body */}
      <div
        className="px-5 py-4 overflow-y-auto font-mono"
        style={{ minHeight: '280px', maxHeight: '480px', fontSize: '13px' }}
      >
        {isIdle && events.length === 0 && (
          <div className="flex flex-col gap-1">
            <span style={{ color: '#707072' }}>
              <span style={{ color: '#0057FF' }}>chronos@live</span>
              <span style={{ color: '#ffffff60' }}> ~ </span>
              <span style={{ color: '#F5F5F5' }}>Waiting for investigation...</span>
            </span>
            <span style={{ color: '#707072' }}>
              Fill in the form and click{' '}
              <span style={{ color: '#0057FF' }}>Run Investigation →</span>{' '}
              to see CHRONOS in action.
            </span>
            <div style={{ marginTop: '8px' }}>
              <span style={{ color: '#707072' }}>{'>'} </span>
              <span className="terminal-cursor" />
            </div>
          </div>
        )}

        {events.map((ev, i) => {
          const { icon, text } = formatEventLine(ev);
          const isComplete = ev.type === 'complete';
          const isConnectedEv = ev.type === 'connected';

          return (
            <div
              key={ev.id + i}
              className="flex gap-2 items-start mb-1 animate-fade-in"
            >
              <span
                className="flex-shrink-0 w-5 text-center"
                style={{ color: isComplete ? '#22c55e' : isConnectedEv ? '#22c55e' : '#0057FF' }}
              >
                {icon}
              </span>
              <span
                style={{
                  color: isComplete
                    ? '#22c55e'
                    : isConnectedEv
                    ? '#22c55e'
                    : '#F5F5F5',
                  wordBreak: 'break-word',
                  lineHeight: '1.5',
                }}
              >
                {text}
              </span>
            </div>
          );
        })}

        {error && (
          <div className="mt-2 flex gap-2 items-start">
            <span style={{ color: '#ef4444' }}>✗</span>
            <span style={{ color: '#ef4444', fontSize: '12px' }}>{error}</span>
          </div>
        )}

        {isConnected && (
          <div className="mt-1 flex gap-2 items-center">
            <span style={{ color: '#0057FF' }}>›</span>
            <span className="terminal-cursor" />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}

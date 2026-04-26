import { useState, useEffect, useRef, useCallback } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8100';

const MAX_EVENTS = 200;
const MAX_RETRIES = 5;
const RETRY_BASE_MS = 1000;

export interface SSEEvent {
  id: string;
  type: string;
  data: unknown;
  timestamp: string;
}

interface UseSSEResult {
  events: SSEEvent[];
  isConnected: boolean;
  error: string | null;
  retryCount: number;
}

function parseEventData(ev: MessageEvent): SSEEvent {
  try {
    const parsed = JSON.parse(ev.data as string) as unknown;
    return {
      id: ev.lastEventId || String(Date.now()),
      type: ev.type,
      data: parsed,
      timestamp: new Date().toISOString(),
    };
  } catch {
    return {
      id: ev.lastEventId || String(Date.now()),
      type: ev.type,
      data: ev.data,
      timestamp: new Date().toISOString(),
    };
  }
}

function isInvestigationComplete(ev: MessageEvent): boolean {
  if (ev.type === 'complete') return true;
  // The backend pushes an "investigation_complete" status update event before
  // the None sentinel that closes the connection. Detecting it here means
  // completedRef is set *before* the connection close fires onerror.
  if (ev.type === 'update') {
    try {
      const d = JSON.parse(ev.data as string) as { status?: string };
      return d?.status === 'investigation_complete';
    } catch { /* non-JSON update */ }
  }
  return false;
}

export function useSSE(incidentId: string | null, streamToken?: string): UseSSEResult {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const esRef = useRef<EventSource | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);
  const completedRef = useRef(false);

  const appendEvent = useCallback((ev: SSEEvent) => {
    setEvents((prev) => {
      const next = [...prev, ev];
      return next.length > MAX_EVENTS ? next.slice(next.length - MAX_EVENTS) : next;
    });
  }, []);

  const connect = useCallback(() => {
    if (!incidentId) return;

    esRef.current?.close();
    const base = `${BASE_URL}/api/v1/investigations/${incidentId}/stream`;
    const url = streamToken ? `${base}?stream_token=${encodeURIComponent(streamToken)}` : base;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setError(null);
      retryCountRef.current = 0;
      setRetryCount(0);
    };

    const handleNamedEvent = (ev: MessageEvent) => {
      appendEvent(parseEventData(ev));

      if (isInvestigationComplete(ev)) {
        completedRef.current = true;
        setIsConnected(false);
        setError(null);
        es.close();
      }
    };

    es.addEventListener('connected', handleNamedEvent);
    es.addEventListener('update', handleNamedEvent);
    es.addEventListener('complete', handleNamedEvent);
    es.addEventListener('heartbeat', handleNamedEvent);

    es.onerror = () => {
      setIsConnected(false);

      // Defer error handling by one macrotask so any already-buffered named
      // events (e.g. 'complete') are dispatched first. Calling es.close()
      // synchronously here would drop those pending events.
      setTimeout(() => {
        es.close();

        if (completedRef.current) {
          setError(null);
          return;
        }

        const attempt = retryCountRef.current + 1;
        if (attempt > MAX_RETRIES) {
          setError(`SSE connection lost after ${MAX_RETRIES} retries`);
          return;
        }

        retryCountRef.current = attempt;
        setRetryCount(attempt);
        setError(`SSE disconnected — reconnecting (attempt ${attempt}/${MAX_RETRIES})…`);

        const delay = RETRY_BASE_MS * 2 ** (attempt - 1);
        retryTimerRef.current = setTimeout(() => {
          if (!completedRef.current) connect();
          else setError(null);
        }, delay);
      }, 0);
    };
  }, [incidentId, streamToken, appendEvent]);

  useEffect(() => {
    if (!incidentId) return;

    completedRef.current = false;
    retryCountRef.current = 0;
    setRetryCount(0);
    setEvents([]);
    connect();

    return () => {
      esRef.current?.close();
      esRef.current = null;
      if (retryTimerRef.current !== null) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      setIsConnected(false);
    };
  }, [incidentId, connect]);

  return { events, isConnected, error, retryCount };
}

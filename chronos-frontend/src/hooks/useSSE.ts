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
  markComplete: () => void;
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

function checkComplete(ev: MessageEvent): boolean {
  // Named 'complete' event from the backend sentinel
  if (ev.type === 'complete') return true;
  // 'investigation_complete' status in an update event — sent BEFORE the
  // sentinel, so this fires while the connection is still alive and sets
  // completedRef before the server-side close triggers onerror.
  if (ev.type === 'update') {
    try {
      const d = JSON.parse(ev.data as string) as { status?: string };
      return d?.status === 'investigation_complete';
    } catch { /* non-JSON update, ignore */ }
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

  // Exposed so the parent component can signal completion externally (e.g.
  // after successfully fetching the finished incident report). Stops retries
  // and clears the error banner even if the SSE race was lost.
  const markComplete = useCallback(() => {
    completedRef.current = true;
    if (retryTimerRef.current !== null) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    esRef.current?.close();
    setError(null);
    setIsConnected(false);
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

      if (checkComplete(ev)) {
        // Mark done immediately — before the server-side close can fire onerror.
        // Per the HTML EventSource spec, data events are always dispatched before
        // the error event for the same TCP session, so this flag is set first.
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
      // Synchronous close is essential — deferring allows the browser's built-in
      // EventSource auto-reconnect to fire before we can stop it, which caused
      // a triple-connection loop. We close immediately to prevent that.
      setIsConnected(false);
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
      // Don't show the error banner while retries are in flight — the reconnect
      // will succeed once the backend's queue is still alive. Only show error
      // when we've exhausted all attempts.
      setError(null);

      const delay = RETRY_BASE_MS * 2 ** (attempt - 1);
      retryTimerRef.current = setTimeout(() => {
        if (!completedRef.current) connect();
        else setError(null);
      }, delay);
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

  return { events, isConnected, error, retryCount, markComplete };
}

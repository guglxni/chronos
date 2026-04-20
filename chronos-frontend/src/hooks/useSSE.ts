import { useState, useEffect, useRef } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8100';

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
}

export function useSSE(incidentId: string | null): UseSSEResult {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!incidentId) return;

    const url = `${BASE_URL}/api/v1/incidents/${incidentId}/stream`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    es.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data as string) as unknown;
        const event: SSEEvent = {
          id: ev.lastEventId || String(Date.now()),
          type: ev.type,
          data: parsed,
          timestamp: new Date().toISOString(),
        };
        setEvents((prev) => [...prev, event]);
      } catch {
        const event: SSEEvent = {
          id: String(Date.now()),
          type: ev.type,
          data: ev.data,
          timestamp: new Date().toISOString(),
        };
        setEvents((prev) => [...prev, event]);
      }
    };

    es.onerror = () => {
      setIsConnected(false);
      setError('SSE connection error — stream may have ended');
      es.close();
    };

    return () => {
      es.close();
      esRef.current = null;
      setIsConnected(false);
    };
  }, [incidentId]);

  return { events, isConnected, error };
}

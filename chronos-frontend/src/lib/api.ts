import type { IncidentReport, DashboardStats } from '../types';
import { DEMO_INCIDENTS, DEMO_STATS } from './demoFixtures';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8100';

// Demo mode: when VITE_DEMO_MODE=true, the API layer returns realistic fixture
// data instead of hitting the network.  Lets a deployed static URL demonstrate
// the full CHRONOS experience without requiring a publicly-hosted backend.
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

/** Simulated latency for demo mode — makes loading states visible. */
function delay<T>(value: T, ms = 250): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

/** Parse FastAPI error detail from a non-ok Response and throw. */
async function throwApiError(res: Response): Promise<never> {
  let message = `HTTP ${res.status}`;
  try {
    const body = await res.json() as { detail?: string; error?: string } | null;
    if (body) message = body.detail ?? body.error ?? message;
  } catch {
    // ignore JSON parse failure — use status code message
  }
  throw new Error(message);
}

export const api = {
  async listIncidents(params?: {
    status?: string;
    root_cause?: string;
    limit?: number;
  }): Promise<{ total: number; incidents: IncidentReport[] }> {
    if (DEMO_MODE) {
      let incidents = [...DEMO_INCIDENTS];
      if (params?.status) incidents = incidents.filter((i) => i.status === params.status);
      if (params?.root_cause) incidents = incidents.filter((i) => i.root_cause_category === params.root_cause);
      return delay({ total: incidents.length, incidents });
    }
    const url = new URL(`${BASE_URL}/api/v1/incidents`);
    if (params?.status) url.searchParams.set('status', params.status);
    if (params?.root_cause) url.searchParams.set('root_cause', params.root_cause);
    if (params?.limit) url.searchParams.set('limit', String(params.limit));
    const res = await fetch(url.toString());
    if (!res.ok) await throwApiError(res);
    return res.json() as Promise<{ total: number; incidents: IncidentReport[] }>;
  },

  async getIncident(id: string): Promise<IncidentReport> {
    if (DEMO_MODE) {
      const found = DEMO_INCIDENTS.find((i) => i.incident_id === id);
      if (!found) throw new Error(`Incident ${id} not found`);
      return delay(found);
    }
    const res = await fetch(`${BASE_URL}/api/v1/incidents/${id}`);
    if (!res.ok) await throwApiError(res);
    return res.json() as Promise<IncidentReport>;
  },

  async acknowledgeIncident(id: string): Promise<void> {
    if (DEMO_MODE) {
      const idx = DEMO_INCIDENTS.findIndex((i) => i.incident_id === id);
      if (idx === -1) throw new Error(`Incident ${id} not found`);
      const current = DEMO_INCIDENTS[idx];
      if (current) {
        DEMO_INCIDENTS[idx] = { ...current, status: 'acknowledged', acknowledged_by: 'demo-user' };
      }
      return delay(undefined, 200);
    }
    const res = await fetch(`${BASE_URL}/api/v1/incidents/${id}/acknowledge`, {
      method: 'POST',
    });
    if (!res.ok) await throwApiError(res);
  },

  async resolveIncident(id: string): Promise<void> {
    if (DEMO_MODE) {
      const idx = DEMO_INCIDENTS.findIndex((i) => i.incident_id === id);
      if (idx === -1) throw new Error(`Incident ${id} not found`);
      const current = DEMO_INCIDENTS[idx];
      if (current) {
        DEMO_INCIDENTS[idx] = {
          ...current,
          status: 'resolved',
          resolved_by: 'demo-user',
          resolved_at: new Date().toISOString(),
        };
      }
      return delay(undefined, 200);
    }
    const res = await fetch(`${BASE_URL}/api/v1/incidents/${id}/resolve`, {
      method: 'POST',
    });
    if (!res.ok) await throwApiError(res);
  },

  async getStats(): Promise<DashboardStats> {
    if (DEMO_MODE) return delay(DEMO_STATS);
    const res = await fetch(`${BASE_URL}/api/v1/stats`);
    if (!res.ok) await throwApiError(res);
    return res.json() as Promise<DashboardStats>;
  },

  async triggerInvestigation(
    entityFqn: string,
    testName?: string
  ): Promise<{ incident_id: string; stream_url: string; stream_token: string }> {
    if (DEMO_MODE) {
      const id = `inc-demo-trigger-${Date.now()}`;
      return delay({ incident_id: id, stream_url: `#demo-${id}`, stream_token: 'demo' });
    }
    const res = await fetch(`${BASE_URL}/api/v1/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_fqn: entityFqn,
        test_name: testName,
        triggered_by: 'manual',
      }),
    });
    if (!res.ok) await throwApiError(res);
    return res.json() as Promise<{ incident_id: string; stream_url: string; stream_token: string }>;
  },

  getProvenanceUrl(
    incidentId: string,
    format: 'jsonld' | 'ttl' | 'provn'
  ): string {
    if (DEMO_MODE) {
      // Return a data: URL with a minimal stub document so the download button
      // produces something useful in demo mode rather than 404-ing.
      const stub = {
        '@context': 'https://www.w3.org/ns/prov',
        'prov:wasGeneratedBy': `agent_chronos_${incidentId}`,
        note: 'Demo-mode stub — real PROV-O document generated by the backend.',
      };
      const body =
        format === 'jsonld'
          ? JSON.stringify(stub, null, 2)
          : format === 'ttl'
            ? `@prefix prov: <https://www.w3.org/ns/prov#> .\n# Demo stub for ${incidentId}\n`
            : `document\n  // Demo stub for ${incidentId}\nendDocument`;
      const mime =
        format === 'jsonld'
          ? 'application/ld+json'
          : format === 'ttl'
            ? 'text/turtle'
            : 'text/plain';
      return `data:${mime};charset=utf-8,${encodeURIComponent(body)}`;
    }
    return `${BASE_URL}/api/v1/incidents/${incidentId}/provenance.${format}`;
  },

  /** True when the app is running against fixtures instead of a live backend. */
  isDemoMode(): boolean {
    return DEMO_MODE;
  },
};

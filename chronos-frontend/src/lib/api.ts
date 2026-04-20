import type { IncidentReport, DashboardStats } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8100';

export const api = {
  async listIncidents(params?: {
    status?: string;
    root_cause?: string;
    limit?: number;
  }): Promise<{ total: number; incidents: IncidentReport[] }> {
    const url = new URL(`${BASE_URL}/api/v1/incidents`);
    if (params?.status) url.searchParams.set('status', params.status);
    if (params?.root_cause) url.searchParams.set('root_cause', params.root_cause);
    if (params?.limit) url.searchParams.set('limit', String(params.limit));
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<{ total: number; incidents: IncidentReport[] }>;
  },

  async getIncident(id: string): Promise<IncidentReport> {
    const res = await fetch(`${BASE_URL}/api/v1/incidents/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<IncidentReport>;
  },

  async acknowledgeIncident(id: string): Promise<void> {
    await fetch(`${BASE_URL}/api/v1/incidents/${id}/acknowledge`, {
      method: 'POST',
    });
  },

  async resolveIncident(id: string): Promise<void> {
    await fetch(`${BASE_URL}/api/v1/incidents/${id}/resolve`, {
      method: 'POST',
    });
  },

  async getStats(): Promise<DashboardStats> {
    const res = await fetch(`${BASE_URL}/api/v1/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<DashboardStats>;
  },

  async triggerInvestigation(
    entityFqn: string,
    testName?: string
  ): Promise<{ incident_id: string; stream_url: string }> {
    const res = await fetch(`${BASE_URL}/api/v1/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_fqn: entityFqn,
        test_name: testName,
        triggered_by: 'manual',
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<{ incident_id: string; stream_url: string }>;
  },

  getProvenanceUrl(
    incidentId: string,
    format: 'jsonld' | 'ttl' | 'provn'
  ): string {
    return `${BASE_URL}/api/v1/incidents/${incidentId}/provenance.${format}`;
  },
};

/**
 * Dashboard analytics API client.
 *
 * All endpoints accept ?range=24h|7d|30d|all. Trends additionally accepts
 * ?bucket=hour|day. Backend is documented at U-11_aggregated_dashboard.md.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8100';

export type DashboardRange = '24h' | '7d' | '30d' | 'all';
export type TrendBucket = 'hour' | 'day';

export interface StatsResponse {
  range: DashboardRange;
  window_start: string | null;
  window_end: string;
  total: number;
  open: number;
  acknowledged: number;
  resolved: number;
  avg_duration_ms: number | null;
  avg_confidence: number | null;
  total_tokens: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
}

export interface TrendBucketPoint {
  ts: string;
  total: number;
  by_category: Record<string, number>;
}

export interface TrendsResponse {
  range: DashboardRange;
  bucket: TrendBucket;
  window_start: string | null;
  window_end: string;
  series: TrendBucketPoint[];
}

export interface ByCategoryResponse {
  range: DashboardRange;
  window_start: string | null;
  window_end: string;
  counts: Record<string, number>;
  total: number;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const dashboardApi = {
  getStats: (range: DashboardRange = '24h') =>
    fetchJson<StatsResponse>(`/api/v1/incidents/stats?range=${range}`),
  getTrends: (range: DashboardRange = '7d', bucket: TrendBucket = 'day') =>
    fetchJson<TrendsResponse>(`/api/v1/incidents/trends?range=${range}&bucket=${bucket}`),
  getByCategory: (range: DashboardRange = '7d') =>
    fetchJson<ByCategoryResponse>(`/api/v1/incidents/by-category?range=${range}`),
};

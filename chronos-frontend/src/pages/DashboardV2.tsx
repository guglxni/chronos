import { useEffect, useState } from 'react';
import IncidentsTable from '../components/dashboard/IncidentsTable';
import KpiStrip from '../components/dashboard/KpiStrip';
import RangeSelector from '../components/dashboard/RangeSelector';
import RootCauseDonut from '../components/dashboard/RootCauseDonut';
import TrendsChart from '../components/dashboard/TrendsChart';
import { api } from '../lib/api';
import {
  type ByCategoryResponse,
  type DashboardRange,
  type StatsResponse,
  type TrendsResponse,
  dashboardApi,
} from '../lib/dashboardApi';
import type { IncidentReport } from '../types';

const POLL_MS = 30_000;

export default function DashboardV2() {
  const [range, setRange] = useState<DashboardRange>('30d');
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [byCategory, setByCategory] = useState<ByCategoryResponse | null>(null);
  const [incidents, setIncidents] = useState<IncidentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const loadAll = async () => {
      try {
        const [s, t, c, list] = await Promise.all([
          dashboardApi.getStats(range),
          dashboardApi.getTrends(range, 'day'),
          dashboardApi.getByCategory(range),
          api.listIncidents({ limit: 100 }),
        ]);
        if (cancelled) return;
        setStats(s);
        setTrends(t);
        setByCategory(c);
        setIncidents(list.incidents);
        setError(null);
        setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      }
      if (!cancelled) timer = setTimeout(loadAll, POLL_MS);
    };

    setLoading(true);
    loadAll();

    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [range]);

  return (
    <div
      className="min-h-screen px-6 md:px-12 py-8 pt-24"
      style={{ backgroundColor: '#F5F5F5' }}
    >
      <div className="max-w-7xl mx-auto">
        <div className="flex items-end justify-between gap-4 mb-8">
          <div>
            <p
              className="text-xs tracking-[0.3em] uppercase mb-2 font-body"
              style={{ color: '#5B8AFF' }}
            >
              Operations Dashboard
            </p>
            <h1
              className="font-heading"
              style={{ fontSize: 'clamp(28px, 4vw, 48px)', color: '#111111', lineHeight: 1.05 }}
            >
              CHRONOS · Incidents
            </h1>
          </div>
          <RangeSelector value={range} onChange={setRange} />
        </div>

        {error && (
          <div
            className="mb-4 p-3 rounded"
            style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}
          >
            <p className="font-body text-xs" style={{ color: '#b91c1c' }}>
              ⚠ {error}
            </p>
          </div>
        )}

        <div className="space-y-6">
          <KpiStrip stats={stats} loading={loading} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <TrendsChart trends={trends} loading={loading} />
            </div>
            <div>
              <RootCauseDonut data={byCategory} loading={loading} />
            </div>
          </div>

          <IncidentsTable incidents={incidents} loading={loading} />
        </div>
      </div>
    </div>
  );
}

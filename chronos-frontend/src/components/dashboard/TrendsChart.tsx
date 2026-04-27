import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TrendsResponse } from '../../lib/dashboardApi';

interface Props {
  trends: TrendsResponse | null;
  loading: boolean;
}

// Stable category → color mapping. Anything not listed falls through to GREY.
const CATEGORY_COLORS: Record<string, string> = {
  SCHEMA_CHANGE:        '#5B8AFF',
  CODE_CHANGE:          '#a855f7',
  DATA_DRIFT:           '#f59e0b',
  PIPELINE_FAILURE:     '#ef4444',
  PERMISSION_CHANGE:    '#14b8a6',
  UPSTREAM_FAILURE:     '#0ea5e9',
  CONFIGURATION_CHANGE: '#84cc16',
  UNKNOWN:              '#9A9A9C',
};

function flatten(trends: TrendsResponse | null): Array<Record<string, number | string>> {
  if (!trends) return [];
  return trends.series.map((b) => {
    const row: Record<string, number | string> = {
      ts: new Date(b.ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      total: b.total,
      ...b.by_category,
    };
    return row;
  });
}

function uniqueCategories(trends: TrendsResponse | null): string[] {
  if (!trends) return [];
  const set = new Set<string>();
  trends.series.forEach((b) => Object.keys(b.by_category).forEach((c) => set.add(c)));
  return Array.from(set);
}

export default function TrendsChart({ trends, loading }: Props) {
  const data = flatten(trends);
  const categories = uniqueCategories(trends);
  const isEmpty = !loading && data.every((d) => d.total === 0);

  return (
    <div
      className="p-6"
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '4px',
        height: '320px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <p
          className="font-body text-xs tracking-[0.15em] uppercase"
          style={{ color: '#4A4A4C' }}
        >
          Incidents Over Time
        </p>
        <p className="font-body text-xs" style={{ color: '#808082' }}>
          stacked by root cause
        </p>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="font-body text-sm" style={{ color: '#808082' }}>Loading…</p>
        </div>
      ) : isEmpty ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <p className="font-body text-sm" style={{ color: '#4A4A4C' }}>No incidents in this window</p>
          <p className="font-mono text-xs" style={{ color: '#808082' }}>
            python -m chronos.demo seed --count 30
          </p>
        </div>
      ) : (
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 10, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
              <XAxis
                dataKey="ts"
                tick={{ fontSize: 11, fill: '#4A4A4C' }}
                axisLine={{ stroke: 'rgba(0,0,0,0.1)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#4A4A4C' }}
                axisLine={{ stroke: 'rgba(0,0,0,0.1)' }}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  border: '1px solid rgba(0,0,0,0.1)',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}
              />
              {categories.map((cat) => (
                <Area
                  key={cat}
                  type="monotone"
                  dataKey={cat}
                  stackId="1"
                  stroke={CATEGORY_COLORS[cat] ?? '#9A9A9C'}
                  fill={CATEGORY_COLORS[cat] ?? '#9A9A9C'}
                  fillOpacity={0.7}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

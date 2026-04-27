import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import type { ByCategoryResponse } from '../../lib/dashboardApi';

interface Props {
  data: ByCategoryResponse | null;
  loading: boolean;
}

const CATEGORY_COLORS: Record<string, string> = {
  SCHEMA_CHANGE:        '#5B8AFF',
  CODE_CHANGE:          '#a855f7',
  DATA_DRIFT:           '#f59e0b',
  PIPELINE_FAILURE:     '#ef4444',
  PERMISSION_CHANGE:    '#14b8a6',
  UPSTREAM_FAILURE:     '#0ea5e9',
  CONFIGURATION_CHANGE: '#84cc16',
  UNKNOWN:              '#7A7A7C',
};

function prettyCategory(cat: string): string {
  return cat.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function RootCauseDonut({ data, loading }: Props) {
  const slices = data
    ? Object.entries(data.counts).map(([cat, count]) => ({
        name: prettyCategory(cat),
        rawName: cat,
        value: count,
      }))
    : [];

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
      <p
        className="font-body text-xs tracking-[0.15em] uppercase mb-4"
        style={{ color: '#4A4A4C' }}
      >
        Root Cause Distribution
      </p>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="font-body text-sm" style={{ color: '#5A5A5C' }}>Loading…</p>
        </div>
      ) : slices.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="font-body text-sm" style={{ color: '#5A5A5C' }}>No data</p>
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
          <div className="relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={slices}
                  dataKey="value"
                  innerRadius="55%"
                  outerRadius="85%"
                  paddingAngle={2}
                  stroke="none"
                >
                  {slices.map((s) => (
                    <Cell key={s.rawName} fill={CATEGORY_COLORS[s.rawName] ?? '#7A7A7C'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid rgba(0,0,0,0.1)',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div
              className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
            >
              <p className="font-heading" style={{ fontSize: '32px', color: '#111111', lineHeight: 1 }}>
                {data?.total ?? 0}
              </p>
              <p className="font-body text-xs" style={{ color: '#4A4A4C' }}>
                incidents
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-1.5 overflow-auto justify-center">
            {slices
              .sort((a, b) => b.value - a.value)
              .map((s) => (
                <div key={s.rawName} className="flex items-center gap-2 text-xs">
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: CATEGORY_COLORS[s.rawName] ?? '#7A7A7C' }}
                  />
                  <span className="font-body flex-1" style={{ color: '#111111' }}>
                    {s.name}
                  </span>
                  <span className="font-mono" style={{ color: '#4A4A4C' }}>
                    {s.value}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

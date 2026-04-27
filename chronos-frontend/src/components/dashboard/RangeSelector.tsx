import type { DashboardRange } from '../../lib/dashboardApi';

const RANGES: { value: DashboardRange; label: string }[] = [
  { value: '24h', label: '24h' },
  { value: '7d',  label: '7 days' },
  { value: '30d', label: '30 days' },
];

interface Props {
  value: DashboardRange;
  onChange: (range: DashboardRange) => void;
}

export default function RangeSelector({ value, onChange }: Props) {
  return (
    <div
      className="inline-flex items-center gap-1 p-1 rounded-full"
      style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid rgba(0,0,0,0.08)',
      }}
    >
      {RANGES.map(r => {
        const active = r.value === value;
        return (
          <button
            key={r.value}
            type="button"
            onClick={() => onChange(r.value)}
            className="font-body text-xs px-4 py-1.5 rounded-full transition-colors"
            style={{
              backgroundColor: active ? '#111111' : 'transparent',
              color: active ? '#FFFFFF' : '#4A4A4C',
              cursor: 'pointer',
              letterSpacing: '0.05em',
            }}
          >
            {r.label}
          </button>
        );
      })}
    </div>
  );
}

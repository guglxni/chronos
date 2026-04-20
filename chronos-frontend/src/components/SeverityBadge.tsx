import clsx from 'clsx';
import type { BusinessImpact } from '../types';

interface SeverityBadgeProps {
  impact: BusinessImpact;
  size?: 'sm' | 'md';
}

const CONFIG: Record<BusinessImpact, { label: string; classes: string }> = {
  critical: { label: 'CRITICAL', classes: 'bg-red-900/60 text-red-300 border border-red-700' },
  high:     { label: 'HIGH',     classes: 'bg-orange-900/60 text-orange-300 border border-orange-700' },
  medium:   { label: 'MEDIUM',   classes: 'bg-yellow-900/60 text-yellow-300 border border-yellow-700' },
  low:      { label: 'LOW',      classes: 'bg-green-900/60 text-green-300 border border-green-700' },
};

export default function SeverityBadge({ impact, size = 'sm' }: SeverityBadgeProps) {
  const cfg = CONFIG[impact] ?? CONFIG.low;
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded font-mono font-semibold tracking-wider',
        size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        cfg.classes
      )}
    >
      {cfg.label}
    </span>
  );
}

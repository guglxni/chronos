import clsx from 'clsx';
import { Layers, Users } from 'lucide-react';
import type { AffectedAsset } from '../types';
import EmptyState from './EmptyState';

interface BlastRadiusPanelProps {
  assets: AffectedAsset[];
}

const TIER_BADGE: Record<string, string> = {
  Tier1:   'bg-orange-900/60 text-orange-300 border border-orange-700',
  Tier2:   'bg-yellow-900/60 text-yellow-300 border border-yellow-700',
  Tier3:   'bg-blue-900/60 text-blue-300 border border-blue-700',
};

function getTierBadge(tier: string): string {
  return TIER_BADGE[tier] ?? 'bg-gray-700 text-gray-300 border border-gray-600';
}

type TierGroup = {
  tier: string;
  assets: AffectedAsset[];
};

export default function BlastRadiusPanel({ assets }: BlastRadiusPanelProps) {
  if (!assets || assets.length === 0) {
    return (
      <EmptyState
        title="No downstream impact"
        description="No downstream assets were identified as affected by this incident."
        icon={<Layers className="w-12 h-12" />}
      />
    );
  }

  // Group by tier
  const tierMap = new Map<string, AffectedAsset[]>();
  for (const asset of assets) {
    const tier = asset.tier || 'Untiered';
    if (!tierMap.has(tier)) tierMap.set(tier, []);
    tierMap.get(tier)!.push(asset);
  }

  const tierOrder = ['Tier1', 'Tier2', 'Tier3', 'Untiered'];
  const groups: TierGroup[] = tierOrder
    .filter((t) => tierMap.has(t))
    .map((t) => ({ tier: t, assets: tierMap.get(t)! }));

  // Add any tiers not in the predefined order
  for (const [tier, tierAssets] of tierMap) {
    if (!tierOrder.includes(tier)) {
      groups.push({ tier, assets: tierAssets });
    }
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-4 p-3 bg-gray-900 rounded-xl border border-gray-700">
        <Layers className="w-5 h-5 text-orange-400 flex-shrink-0" />
        <div>
          <p className="text-sm font-semibold text-gray-200">
            {assets.length} downstream asset{assets.length !== 1 ? 's' : ''} affected
          </p>
          <p className="text-xs text-gray-500">
            {groups.map((g) => `${g.assets.length} ${g.tier}`).join(' · ')}
          </p>
        </div>
      </div>

      {/* Tier groups */}
      {groups.map(({ tier, assets: tierAssets }) => (
        <div key={tier}>
          <div className="flex items-center gap-2 mb-2">
            <span
              className={clsx(
                'text-xs px-2 py-0.5 rounded font-semibold',
                getTierBadge(tier)
              )}
            >
              {tier}
            </span>
            <span className="text-xs text-gray-500">{tierAssets.length} asset{tierAssets.length !== 1 ? 's' : ''}</span>
          </div>

          <ul className="space-y-2">
            {tierAssets.map((asset, idx) => (
              <li key={idx} className="card border border-gray-700 py-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p
                      className="text-sm font-mono text-gray-200 truncate"
                      title={asset.fqn}
                    >
                      {asset.display_name || asset.fqn}
                    </p>
                    <p
                      className="text-xs text-gray-500 font-mono truncate mt-0.5"
                      title={asset.fqn}
                    >
                      {asset.fqn}
                    </p>
                    {asset.domain && (
                      <p className="text-xs text-gray-600 mt-0.5">
                        Domain: <span className="text-gray-500">{asset.domain}</span>
                      </p>
                    )}
                  </div>
                  {asset.owners.length > 0 && (
                    <div className="flex items-center gap-1 text-xs text-gray-500 flex-shrink-0">
                      <Users className="w-3 h-3" />
                      <span>{asset.owners.slice(0, 2).join(', ')}</span>
                      {asset.owners.length > 2 && (
                        <span className="text-gray-600">+{asset.owners.length - 2}</span>
                      )}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

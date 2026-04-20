import { useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import type { IncidentReport } from '../types';
import EmptyState from './EmptyState';
import { GitBranch } from 'lucide-react';

interface LineageFailureMapProps {
  incident: IncidentReport;
}

const TIER_COLOR: Record<string, string> = {
  Tier1: '#f97316',
  Tier2: '#eab308',
  Tier3: '#6b7280',
};

function getTierColor(tier: string): string {
  return TIER_COLOR[tier] ?? '#6b7280';
}

export default function LineageFailureMap({ incident }: LineageFailureMapProps) {
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const affectedId = 'affected';
    const affectedParts = incident.affected_entity_fqn.split('.');
    const affectedLabel = affectedParts[affectedParts.length - 1] || incident.affected_entity_fqn;

    // Affected (root) node — center
    nodes.push({
      id: affectedId,
      position: { x: 400, y: 200 },
      data: {
        label: (
          <div className="text-center">
            <div className="text-xs font-bold text-red-300 mb-0.5">AFFECTED</div>
            <div className="text-xs text-white font-mono truncate max-w-[140px]" title={incident.affected_entity_fqn}>
              {affectedLabel}
            </div>
          </div>
        ),
      },
      style: {
        background: '#450a0a',
        border: '2px solid #dc2626',
        borderRadius: 8,
        padding: 8,
        minWidth: 160,
        color: '#fff',
      },
    });

    // Upstream mock node (if we can infer from context)
    const upstreamId = 'upstream-source';
    nodes.push({
      id: upstreamId,
      position: { x: 100, y: 200 },
      data: {
        label: (
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-0.5">UPSTREAM</div>
            <div className="text-xs text-gray-300 font-mono">Source</div>
          </div>
        ),
      },
      style: {
        background: '#1f2937',
        border: '1.5px solid #4b5563',
        borderRadius: 8,
        padding: 8,
        minWidth: 120,
        color: '#fff',
      },
    });

    edges.push({
      id: `${upstreamId}->${affectedId}`,
      source: upstreamId,
      target: affectedId,
      label: 'feeds',
      markerEnd: { type: MarkerType.ArrowClosed, color: '#6b7280' },
      style: { stroke: '#6b7280' },
      labelStyle: { fill: '#9ca3af', fontSize: 10 },
      labelBgStyle: { fill: '#1f2937' },
    });

    // Downstream nodes
    const downstream = incident.affected_downstream ?? [];

    if (downstream.length === 0 && incident.evidence_chain.length === 0) {
      return { nodes: [], edges: [] };
    }

    downstream.forEach((asset, i) => {
      const nodeId = `downstream-${i}`;
      const parts = asset.fqn.split('.');
      const label = parts[parts.length - 1] || asset.display_name;
      const tier = asset.tier || 'Untiered';
      const color = getTierColor(tier);
      const row = Math.floor(i / 3);
      const col = i % 3;

      nodes.push({
        id: nodeId,
        position: { x: 680 + col * 180, y: 80 + row * 120 },
        data: {
          label: (
            <div className="text-center">
              <div className="text-xs mb-0.5" style={{ color }}>
                {tier}
              </div>
              <div
                className="text-xs text-gray-200 font-mono truncate max-w-[120px]"
                title={asset.fqn}
              >
                {label}
              </div>
              {asset.owners.length > 0 && (
                <div className="text-xs text-gray-500 mt-0.5 truncate max-w-[120px]">
                  {asset.owners[0]}
                </div>
              )}
            </div>
          ),
        },
        style: {
          background: '#1c1917',
          border: `1.5px solid ${color}`,
          borderRadius: 8,
          padding: 6,
          minWidth: 140,
          color: '#fff',
        },
      });

      edges.push({
        id: `${affectedId}->${nodeId}`,
        source: affectedId,
        target: nodeId,
        label: 'impacts',
        markerEnd: { type: MarkerType.ArrowClosed, color },
        style: { stroke: color },
        labelStyle: { fill: '#9ca3af', fontSize: 10 },
        labelBgStyle: { fill: '#1f2937' },
        animated: true,
      });
    });

    return { nodes, edges };
  }, [incident]);

  if (nodes.length === 0) {
    return (
      <EmptyState
        title="No lineage data available"
        description="Lineage information could not be constructed for this incident."
        icon={<GitBranch className="w-12 h-12" />}
      />
    );
  }

  return (
    <div className="w-full rounded-xl overflow-hidden border border-gray-700" style={{ height: 480 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: false }}
      >
        <Background color="#374151" gap={20} />
        <Controls className="bg-gray-800 border-gray-700" />
        <MiniMap
          nodeColor={(n) => (n.id === 'affected' ? '#dc2626' : '#374151')}
          maskColor="rgba(17,24,39,0.7)"
          className="bg-gray-800 border border-gray-700"
        />
      </ReactFlow>
    </div>
  );
}

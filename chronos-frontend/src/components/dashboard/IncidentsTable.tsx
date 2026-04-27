import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from '@tanstack/react-table';
import { useMemo, useState } from 'react';
import type { IncidentReport } from '../../types';

interface Props {
  incidents: IncidentReport[];
  loading: boolean;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high:     '#f59e0b',
  medium:   '#5B8AFF',
  low:      '#22c55e',
};

const STATUS_COLORS: Record<string, string> = {
  open:          '#ef4444',
  investigating: '#f59e0b',
  acknowledged:  '#5B8AFF',
  resolved:      '#22c55e',
};

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffSec = Math.floor((now - then) / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}

function prettyCategory(cat: string): string {
  return cat.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function IncidentsTable({ incidents, loading }: Props) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'detected_at', desc: true }]);
  const [filter, setFilter] = useState('');

  const columns = useMemo<ColumnDef<IncidentReport>[]>(() => [
    {
      accessorKey: 'business_impact',
      header: 'Severity',
      cell: ({ getValue }) => {
        const sev = String(getValue() ?? 'medium').toLowerCase();
        return (
          <span
            className="inline-flex items-center gap-1.5 font-body text-xs px-2 py-0.5 rounded-full uppercase"
            style={{
              backgroundColor: `${SEVERITY_COLORS[sev] ?? '#9A9A9C'}18`,
              color: SEVERITY_COLORS[sev] ?? '#4A4A4C',
              letterSpacing: '0.08em',
              fontSize: '10px',
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: SEVERITY_COLORS[sev] ?? '#9A9A9C' }}
            />
            {sev}
          </span>
        );
      },
    },
    {
      accessorKey: 'affected_entity_fqn',
      header: 'Entity',
      cell: ({ getValue }) => (
        <span className="font-mono text-xs" style={{ color: '#111111' }}>
          {String(getValue() ?? '')}
        </span>
      ),
    },
    {
      accessorKey: 'root_cause_category',
      header: 'Root Cause',
      cell: ({ getValue }) => (
        <span className="font-body text-xs" style={{ color: '#4A4A4C' }}>
          {prettyCategory(String(getValue() ?? 'UNKNOWN'))}
        </span>
      ),
    },
    {
      accessorKey: 'detected_at',
      header: 'Age',
      cell: ({ getValue }) => (
        <span className="font-body text-xs" style={{ color: '#4A4A4C' }}>
          {relativeTime(String(getValue() ?? new Date().toISOString()))}
        </span>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => {
        const st = String(getValue() ?? 'open').toLowerCase();
        return (
          <span
            className="font-body text-xs"
            style={{ color: STATUS_COLORS[st] ?? '#4A4A4C' }}
          >
            {st}
          </span>
        );
      },
    },
    {
      accessorKey: 'investigation_duration_ms',
      header: 'Duration',
      cell: ({ getValue }) => {
        const ms = Number(getValue() ?? 0);
        if (!ms) return <span style={{ color: '#9A9A9C' }}>—</span>;
        return <span className="font-mono text-xs" style={{ color: '#4A4A4C' }}>{(ms / 1000).toFixed(1)}s</span>;
      },
    },
    {
      accessorKey: 'confidence',
      header: 'Confidence',
      cell: ({ getValue }) => (
        <span className="font-mono text-xs" style={{ color: '#4A4A4C' }}>
          {Math.round(Number(getValue() ?? 0) * 100)}%
        </span>
      ),
    },
  ], []);

  const filtered = useMemo(() => {
    if (!filter.trim()) return incidents;
    const q = filter.trim().toLowerCase();
    return incidents.filter((i) =>
      i.affected_entity_fqn.toLowerCase().includes(q) ||
      i.root_cause_category.toLowerCase().includes(q) ||
      i.business_impact.toLowerCase().includes(q),
    );
  }, [incidents, filter]);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div
      className="p-6"
      style={{ backgroundColor: '#FFFFFF', borderRadius: '4px' }}
    >
      <div className="flex items-center justify-between gap-4 mb-4">
        <p
          className="font-body text-xs tracking-[0.15em] uppercase"
          style={{ color: '#4A4A4C' }}
        >
          Incidents ({filtered.length})
        </p>
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by entity, category, severity…"
          className="font-body text-xs px-3 py-1.5 rounded-full"
          style={{
            backgroundColor: '#F5F5F5',
            border: '1px solid rgba(0,0,0,0.06)',
            outline: 'none',
            minWidth: '260px',
          }}
        />
      </div>

      {loading ? (
        <p className="font-body text-sm py-8 text-center" style={{ color: '#808082' }}>Loading…</p>
      ) : filtered.length === 0 ? (
        <div className="py-12 text-center">
          <p className="font-body text-sm" style={{ color: '#4A4A4C' }}>No incidents match</p>
          <p className="font-mono text-xs mt-2" style={{ color: '#808082' }}>
            python -m chronos.demo seed --count 30
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              {table.getHeaderGroups().map((hg) => (
                <tr
                  key={hg.id}
                  style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}
                >
                  {hg.headers.map((h) => (
                    <th
                      key={h.id}
                      onClick={h.column.getToggleSortingHandler()}
                      className="font-body text-xs tracking-[0.1em] uppercase pb-2 pr-4 cursor-pointer select-none"
                      style={{ color: '#808082' }}
                    >
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      <span style={{ marginLeft: 4 }}>
                        {{ asc: '↑', desc: '↓' }[h.column.getIsSorted() as string] ?? ''}
                      </span>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-black/[0.02] transition-colors"
                  style={{ borderBottom: '1px solid rgba(0,0,0,0.04)' }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="py-3 pr-4">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

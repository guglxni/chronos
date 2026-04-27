# Unit 11 — Aggregated RCA Dashboard

> **Phase**: Construction
> **Created**: 2026-04-27
> **Status**: Functional Design Complete — In Construction
> **Owner**: Aaryan
> **Hackathon mapping**: Phase 1 of `HACKATHON_ALIGNMENT_PLAN.md` — closes the "aggregated RCA dashboard" deliverable explicitly called out in [#26659](https://github.com/open-metadata/OpenMetadata/issues/26659)
> **Depends on**: Unit 9 (production hardening — live FalkorDB + OpenMetadata)
> **Reference**: [FalkorDB docs](https://docs.falkordb.com), [browser API](https://browser.falkordb.com/docs)

---

## 1. Problem

CHRONOS produces beautiful single-incident RCA reports but has no surface that lets a data platform team see incidents *in aggregate*: how many, of what type, trending up or down, who's at risk. The hackathon issue #26659 lists "aggregated RCA dashboard" as an explicit deliverable. Without it the submission shows a tool with no operator surface.

## 2. Goals

1. **At-a-glance KPIs** — total incidents, MTTR, open incident count, LLM token spend
2. **Trend over time** — incidents per day for the last 7 / 30 days, broken down by root cause category
3. **Distribution view** — % of incidents by root cause (donut)
4. **Triage table** — sortable / filterable list of incidents with severity, entity, age, status, owner
5. **Live data** — pulls from FalkorDB (Graphiti episodes) + in-process incident store, no fixtures
6. **Demo-impressive on first load** — seeded with 30 historical incidents (Unit 9 seeder)

## 3. Non-Goals

- Real-time push updates (polling every 15s is fine)
- Multi-tenant filtering (single-org demo)
- Export-to-CSV (cute but not required)
- Mobile responsive layout (laptop demo only)

## 4. Backend Design

### 4.1 New endpoints

```
GET /api/v1/incidents/stats
  → KPIs aggregated over a window (default 24h, ?range=24h|7d|30d)
  Response: {
    total: int,
    open: int,
    acknowledged: int,
    resolved: int,
    avg_duration_ms: float | null,
    avg_confidence: float | null,
    total_tokens: int,
    range: "24h"|"7d"|"30d",
    window_start: ISO8601,
    window_end: ISO8601,
  }

GET /api/v1/incidents/trends?range=7d&bucket=day
  → Time-bucketed incident counts by root cause category
  Response: {
    range: "7d",
    bucket: "day",
    buckets: [
      { ts: "2026-04-21", total: 8, by_category: {schema_drift: 3, data_quality: 5} },
      ...
    ],
  }

GET /api/v1/incidents/by-category?range=7d
  → For the donut: {category: count} dict
  Response: { range: "7d", counts: { schema_drift: 22, data_quality: 14, ... } }
```

### 4.2 Data sources (in priority order)

1. **In-process `_incident_store`** (always available) — current open + recently-resolved incidents
2. **FalkorDB historical episodes** (when `chronos.graphiti_client._is_configured()`) — older incidents, fall back to in-process if down
3. **Graceful degradation**: when FalkorDB is down, return only in-process data with a `degraded: true` flag in the response

### 4.3 New module: `chronos/analytics/`

```
chronos/analytics/
├── __init__.py
├── stats.py          # compute_stats(range) → StatsResponse
├── trends.py         # compute_trends(range, bucket) → TrendsResponse
└── historical.py     # query_historical_incidents() — FalkorDB Cypher wrapper
```

`historical.py` uses the FalkorDB Python client per the docs:
```python
from falkordb import FalkorDB
db = FalkorDB(host=..., port=..., username='falkordb', password=...)
g = db.select_graph('chronos-historical-incidents')
result = g.query("""
    MATCH (i:Episode)
    WHERE i.created_at >= $start_ts
    RETURN i.root_cause_category AS cat, count(i) AS n
""", {'start_ts': window_start.timestamp()})
```

In-process implementation can be simpler — iterate the dict and aggregate.

### 4.4 Caching

- Each stats endpoint cached 15s in-memory (similar pattern to `chronos.health.aggregator`)
- `?force=true` bypasses cache

## 5. Frontend Design

### 5.1 New route + page

`/dashboard` — replaces the legacy `/app` Dashboard for the demo URL. Existing `/app` Dashboard stays for backwards compat.

### 5.2 Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ [Header]  CHRONOS · Dashboard           [Range: 24h 7d 30d]  ⟳    │
├────────────────────────────────────────────────────────────────────┤
│ [KPI strip — 4 cards in a row]                                      │
│  Total · Open · Avg time-to-RCA · Tokens spent                     │
├──────────────────────────────────────┬─────────────────────────────┤
│ [Trends chart — Recharts area]       │ [Root cause donut — Recharts]│
│ Incidents over time, stacked by cat  │ % distribution               │
├──────────────────────────────────────┴─────────────────────────────┤
│ [Incidents table — TanStack Table v8]                               │
│ Severity · Entity · Root cause · Age · Status · Owner · Actions    │
└────────────────────────────────────────────────────────────────────┘
```

### 5.3 Components

```
chronos-frontend/src/components/dashboard/
├── KpiStrip.tsx               # 4 stat cards w/ icon + value + delta
├── TrendsChart.tsx            # Recharts AreaChart, stacked by category
├── RootCauseDonut.tsx         # Recharts PieChart with center label
├── IncidentsTable.tsx         # TanStack Table v8 with sort/filter
├── RangeSelector.tsx          # 24h / 7d / 30d toggle pills
└── DegradedBanner.tsx         # Shown when stats response.degraded === true
```

`chronos-frontend/src/pages/DashboardV2.tsx` — top-level page composing the above.

### 5.4 Color palette (matching existing design system)

- Severity: `#ef4444` (CRITICAL), `#f59e0b` (HIGH), `#5B8AFF` (MEDIUM), `#22c55e` (LOW)
- Root cause categories: stable HSL pairs derived from category name hash (deterministic, no design tokens needed)
- Background: `#F5F5F5` page, `#FFFFFF` cards

### 5.5 FOSS dependencies

| Lib | Purpose | License | npm bundle (gzip) |
|---|---|---|---|
| `recharts` | KPI sparklines, trends area, donut | MIT | ~64KB |
| `@tanstack/react-table` v8 | Incidents table | MIT | ~14KB |

Both already industry-standard. No design system lock-in.

### 5.6 API client extensions

`chronos-frontend/src/lib/api.ts`:
- `getStats(range)` → `StatsResponse`
- `getTrends(range, bucket)` → `TrendsResponse`
- `getByCategory(range)` → `Record<string, number>`

Each respects `VITE_DEMO_MODE=true` and returns synthetic responses for offline demos.

### 5.7 Polling strategy

- Stats endpoints polled every 30s via `setInterval` in `DashboardV2.tsx` (can switch to TanStack Query later)
- Range change triggers immediate refetch
- Skeleton state on first load (shimmer)

## 6. Files to Create / Modify

### Create (Backend)
- `chronos/analytics/__init__.py`
- `chronos/analytics/stats.py`
- `chronos/analytics/trends.py`
- `chronos/analytics/historical.py`
- `chronos/api/routes/analytics.py` — new router for stats / trends / by-category
- `tests/test_analytics_stats.py`
- `tests/test_analytics_trends.py`

### Create (Frontend)
- `chronos-frontend/src/pages/DashboardV2.tsx`
- `chronos-frontend/src/components/dashboard/KpiStrip.tsx`
- `chronos-frontend/src/components/dashboard/TrendsChart.tsx`
- `chronos-frontend/src/components/dashboard/RootCauseDonut.tsx`
- `chronos-frontend/src/components/dashboard/IncidentsTable.tsx`
- `chronos-frontend/src/components/dashboard/RangeSelector.tsx`
- `chronos-frontend/src/components/dashboard/DegradedBanner.tsx`
- `chronos-frontend/src/lib/dashboardApi.ts`

### Modify
- `chronos/api/routes/__init__.py` — register analytics router
- `chronos-frontend/src/App.tsx` — add `/dashboard` route
- `chronos-frontend/src/lib/api.ts` — extend with stats/trends helpers
- `chronos-frontend/package.json` — add recharts + @tanstack/react-table
- `chronos-frontend/src/types.ts` — add StatsResponse, TrendsResponse types

## 7. Testing Strategy

- **Unit (backend)**: stats aggregation with crafted incident lists → verify counts, MTTR, deltas
- **Unit (backend)**: trends with multi-day input → verify bucket assignment + category split
- **Integration**: hit `/api/v1/incidents/stats` against running app, verify schema
- **Frontend**: render snapshot of each component with synthetic props (no MSW needed for demo)

## 8. Acceptance Criteria

- [ ] `/api/v1/incidents/stats` returns valid response from in-process store alone
- [ ] `/api/v1/incidents/stats` enriches with FalkorDB historical when configured
- [ ] `/api/v1/incidents/trends?range=7d&bucket=day` returns 7 daily buckets
- [ ] `/dashboard` route renders 4 KPI cards, trends chart, donut, table
- [ ] Range selector works (24h / 7d / 30d)
- [ ] Demo seeder populates Graphiti — dashboard reflects 30 historical incidents
- [ ] Bundle size delta < 100KB gzip (recharts + tanstack-table together)
- [ ] DegradedBanner shows when FalkorDB unreachable

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| FalkorDB Cypher query slow on first load | 15s in-memory cache; pre-warm on app startup |
| Recharts bundle pushes dist over 250KB | Lazy-import the chart components on the dashboard route |
| TanStack Table boilerplate is verbose | Stick to defaults; no custom column resizing v1 |
| Empty-state when no historical data | "Run the demo seeder" CTA banner |

## 10. Demo Talking Points

> "This is the dashboard view — 30 historical incidents, real-time KPIs. We're seeing 14 incidents in the past 7 days, average time-to-RCA is 18 seconds, and most are schema drift. The trends chart shows we had a spike on Tuesday — that was the dbt migration that broke 6 downstream tables. Dashboard pulls live from OpenMetadata + FalkorDB — see the green status badge in the nav."

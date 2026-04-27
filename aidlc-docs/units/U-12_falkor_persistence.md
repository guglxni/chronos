# Unit 12 — FalkorDB Persistence for the Incident Store

> **Phase**: Construction
> **Created**: 2026-04-27
> **Status**: Functional Design Complete — In Construction
> **Owner**: Aaryan
> **Hackathon mapping**: Production hardening — closes the volatile-store gap exposed when v33 deploy wiped 12 real investigations
> **Depends on**: Unit 9 (live FalkorDB connection)
> **Blocks**: Unit 10 (Time-Travel Lineage — requires durable historical incidents)

---

## 1. Problem

`chronos/core/incident_store.py` is in-process only. Every Heroku dyno restart (deploys, daily cycles, scaling events) wipes every stored `IncidentReport`. The dashboard, the related-past-incidents lookup, and any planned time-travel feature all break the moment a restart happens.

We already have FalkorDB live (Unit 9). This unit makes it the source of truth.

## 2. Goals

1. **Every `store()` persists to FalkorDB** — no API change for callers
2. **Startup hydration** rebuilds the in-memory store from FalkorDB
3. **Updates** (acknowledge, resolve) persist in place via `MERGE`
4. **Non-blocking** — investigation requests don't wait on FalkorDB writes
5. **Graceful degradation** — when FalkorDB is unconfigured/down, callers behave exactly like today (in-memory only)

## 3. Non-Goals

- Multi-tenant scoping (single graph for the demo)
- Pagination of hydrate() — the in-memory cap is 1000, FalkorDB write/read of <1000 nodes is sub-second
- Migration tooling — schema evolves via additive properties only

## 4. Data Model

Single node label `Incident`, keyed by `incident_id`. Critical fields are denormalized as top-level properties for indexable filtering; the full report is stored as a JSON string in `payload` so we don't lose nested structures (evidence_chain, downstream, timeline, etc.).

```cypher
CREATE INDEX FOR (i:Incident) ON (i.incident_id);
CREATE INDEX FOR (i:Incident) ON (i.detected_at);
CREATE INDEX FOR (i:Incident) ON (i.affected_entity_fqn);

(:Incident {
  incident_id: string,                    // PK — used by MERGE
  detected_at: int64,                     // ms epoch — for ORDER BY / range scans
  resolved_at: int64,                     // ms epoch (or null)
  affected_entity_fqn: string,
  root_cause_category: string,
  business_impact: string,
  status: string,
  confidence: float,
  investigation_duration_ms: int,
  total_llm_tokens: int,
  payload: string                         // full IncidentReport.model_dump_json()
})
```

Graph name: `chronos_incidents` (separate from Graphiti's episode graphs).

## 5. Module Layout

```
chronos/persistence/
├── __init__.py
├── falkor_store.py          # public API: persist, hydrate, delete, list_recent
└── _cypher.py               # parameterized Cypher templates (kept terse)
```

Public API:
```python
async def persist(report: IncidentReport) -> bool
async def hydrate(limit: int = 1000) -> list[IncidentReport]
async def delete(incident_id: str) -> bool
async def list_recent(limit: int = 50) -> list[IncidentReport]   # for paginated reads
```

Each function:
- Returns immediately when `_is_configured()` is False (no-op behavior)
- Wraps the sync FalkorDB client calls in `asyncio.to_thread` so the event loop isn't blocked
- Catches every exception and logs a WARNING — never raises into callers

## 6. Wiring Changes

### `chronos/core/incident_store.py`
- `store(report)` after committing in-memory: `asyncio.create_task(falkor_store.persist(report))`
  - Background task — caller doesn't wait for FalkorDB write
  - Tracked in a module-level `set` so tests can `await asyncio.gather(*pending)` if they need determinism
- `update_field(...)` similarly schedules a `persist()` for the updated record

### `chronos/main.py` lifespan
- After `setup_openllmetry()`, `await falkor_store.hydrate()` — populates the in-memory store from FalkorDB before any traffic arrives
- Logs hydrated count and oldest/newest timestamps for visibility

### Backward compatibility
- All existing callers (`api/routes/incidents.py`, `analytics/`) untouched — the in-memory store is still the read source for the request path

## 7. Concurrency & Failure Modes

| Scenario | Behavior |
|---|---|
| FalkorDB write times out | Logged WARNING, in-memory store still has the record. Next `store()` for same id will retry the write. |
| FalkorDB down at startup | `hydrate()` returns []; in-memory store starts empty. App still serves traffic. |
| Same incident stored twice | MERGE updates in place — no duplicates. |
| Concurrent updates to same incident | Last write wins (acceptable for hackathon; no version vector needed). |
| Background `persist()` task lost on dyno crash | At most one incident lost between in-memory store and FalkorDB write. Trade-off accepted. |

## 8. Files

### Create
- `chronos/persistence/__init__.py`
- `chronos/persistence/falkor_store.py`
- `chronos/persistence/_cypher.py`
- `tests/test_falkor_persistence.py`

### Modify
- `chronos/core/incident_store.py` — schedule persist on store/update
- `chronos/main.py` — call hydrate in lifespan
- `aidlc-docs/aidlc-state.md` — register Unit 12

## 9. Testing Strategy

- **Unit (with mocked FalkorDB)**: persist + hydrate roundtrip preserves every IncidentReport field exactly
- **Integration (live FalkorDB)**: `tests/integration/test_persistence_live.py` (skip when FALKORDB_HOST=localhost) — write 5, hydrate, assert equality
- **End-to-end (manual)**: deploy → seed 12 → trigger dyno restart → verify dashboard still shows 12 within 5 seconds of warm-up

## 10. Acceptance Criteria

- [ ] `falkor_store.persist(report)` writes a node observable in `GRAPH.QUERY chronos_incidents 'MATCH (i:Incident) RETURN i.incident_id'`
- [ ] After dyno restart, `/api/v1/incidents/stats?range=30d` returns the same total as before restart (within 5s of dyno warm-up)
- [ ] `incident_store.store()` returns in <50ms even when FalkorDB has 200ms latency (write is backgrounded)
- [ ] When `FALKORDB_HOST=localhost`, all functions no-op silently and existing tests still pass

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Background `persist()` task swallowed exception → silent data loss | Log all exceptions at WARNING + record a counter metric we can probe |
| Schema drift breaks hydrate() | Defensive: if `model_validate(payload_json)` fails, log + skip the node, don't crash startup |
| FalkorDB write storm under high load | Limit `_pending_persists` to 100 concurrent tasks; drop oldest on overflow |
| `payload` string grows unbounded with rich evidence | Hard-cap at 256KB per node; truncate `evidence_chain` if larger |

# Unit 10 — Temporal Time-Travel + Predictive Risk

> **Phase**: Construction
> **Created**: 2026-04-27
> **Status**: Functional Design Complete — Pending Implementation
> **Owner**: Aaryan
> **Hackathon mapping**: Phase 1.5 of `HACKATHON_ALIGNMENT_PLAN.md` — the **innovative twist**

---

## 1. Problem Statement

The "Back to the Metadata" / "OutaTime" hackathon theme is literally about TIME, but no project board issue exploits temporal queries on the metadata graph. CHRONOS already runs on Graphiti — a *temporal* knowledge graph where every fact is timestamped — but we surface no UI that uses this property.

Two capabilities follow naturally from the temporal graph and would differentiate us from any other team:

1. **Time-travel lineage** — scrub backward to any past time; the lineage graph reflects what existed THEN, not now
2. **Predictive risk scoring** — analyze incident history per entity to predict next-failure probability

Together they convert CHRONOS from "reactive RCA tool" to "temporal intelligence layer for data infrastructure."

## 2. Goals

1. **Time-Travel Lineage Viewer** — interactive time slider on the Investigation Cockpit; lineage graph re-renders to past state on drag
2. **Lineage Diff Mode** — side-by-side or overlay diff between any two timestamps with adds/removes color-coded
3. **Predictive Risk Scorer** — per-entity score based on past patterns; surfaces "Top 10 At-Risk Entities" widget
4. **Risk Explainer** — click an at-risk entity to see WHY it's flagged

## 3. Non-Goals

- Real ML model training (use a transparent weighted-sum heuristic; ML is overkill for hackathon)
- Predicting WHEN exactly a failure will happen (just rank likelihood)
- Cross-org risk patterns (single tenant only)
- Streaming time-travel (snapshot-based queries are sufficient)

## 4. Functional Design

### 4.1 Backend: Temporal Lineage Query

```python
# chronos/temporal/lineage_at.py
async def get_lineage_at(
    entity_fqn: str,
    valid_at: datetime,
    depth: int = 3,
) -> LineageGraph:
    """Reconstruct the lineage graph as it existed at a specific past time.
    
    Uses Graphiti's bi-temporal model: each fact has (valid_from, valid_to).
    Returns nodes and edges that were valid at `valid_at`.
    """
```

New endpoint:
```
GET /api/v1/lineage/{entity_fqn}?valid_at=2026-04-25T14:30:00Z&depth=3
```

### 4.2 Backend: Lineage Diff

```python
# chronos/temporal/lineage_diff.py
async def diff_lineage(
    entity_fqn: str,
    from_time: datetime,
    to_time: datetime,
    depth: int = 3,
) -> LineageDiff:
    """Compute structural diff between two snapshots: added_nodes, removed_nodes,
    added_edges, removed_edges, schema_changes, owner_changes."""
```

New endpoint:
```
GET /api/v1/lineage/{entity_fqn}/diff?from=...&to=...
```

### 4.3 Backend: Predictive Risk Scorer

```python
# chronos/risk/scorer.py
@dataclass(frozen=True)
class RiskFactors:
    incident_count_30d: int
    days_since_last_incident: float
    downstream_consumer_count: int
    schema_change_freq_30d: int
    upstream_failure_rate_30d: float

@dataclass(frozen=True)
class RiskScore:
    entity_fqn: str
    score: float           # 0-100
    factors: RiskFactors
    reasoning: list[str]   # human-readable why-flagged bullets

WEIGHTS = {
    "incident_count_30d":     0.30,  # primary signal
    "downstream_consumer":    0.20,  # blast radius matters
    "schema_change_freq":     0.20,  # instability
    "upstream_failure_rate":  0.20,  # dependency reliability
    "recency_decay":          0.10,  # cooldown after recent failures
}

async def compute_risk_score(entity_fqn: str) -> RiskScore: ...
async def top_at_risk(limit: int = 10) -> list[RiskScore]: ...
```

New endpoints:
```
GET /api/v1/risk/at-risk?limit=10
GET /api/v1/risk/{entity_fqn}/explain
```

### 4.4 Frontend: Time Slider Component

`chronos-frontend/src/components/cockpit/TimeSlider.tsx`:
- Horizontal slider, full width above the lineage graph
- Min: 30 days ago. Max: now.
- Default: incident time (passed from parent)
- Tick marks at each notable event (incident, schema change, classification update) — pulled from `/api/v1/timeline/{entity_fqn}`
- Drag → debounced (200ms) → triggers `getLineageAt(timestamp)` and re-renders graph
- Sticky tooltip showing the formatted timestamp + "what changed" badge

Library: **rc-slider** (MIT) for the base slider; custom render for ticks and tooltip.

### 4.5 Frontend: Lineage Diff Mode

In the Investigation Cockpit, a toggle: `[ View now ]  [ Time travel ]  [ Diff mode ]`
- Diff mode adds a SECOND time slider — pick "from" and "to" timestamps
- The lineage graph renders with edges colored:
  - GRAY = unchanged
  - GREEN = added between from→to
  - RED = removed between from→to
  - YELLOW = modified (schema/owner change)
- Side panel lists the changes textually for accessibility

### 4.6 Frontend: At-Risk Widget

`chronos-frontend/src/components/dashboard/AtRiskWidget.tsx`:
- A card on the dashboard above the trends chart
- Title: "🔮 Top 10 At-Risk Entities"
- For each entity: name | risk score (0-100) | colored bar | sparkline of incident count over 30d
- Click → drill-in modal with the `RiskScore.reasoning` bullets

### 4.7 Frontend: Risk Explainer Modal

When user clicks an at-risk entity:
- Modal shows: entity name, current score, 30-day score sparkline (Recharts)
- "Contributing factors" list: each factor with its individual contribution to the score
- "Recent incidents" timeline (last 30 days)
- CTA buttons: "View entity in OpenMetadata", "Run preventive investigation"

## 5. Files to Create / Modify

### Create (Backend)
- `chronos/temporal/__init__.py`
- `chronos/temporal/lineage_at.py`
- `chronos/temporal/lineage_diff.py`
- `chronos/temporal/timeline.py` — events on a timeline
- `chronos/risk/__init__.py`
- `chronos/risk/scorer.py`
- `chronos/risk/factors.py`
- `chronos/api/routes/lineage.py` — new sub-route for temporal lineage queries
- `chronos/api/routes/risk.py` — new sub-route for risk endpoints
- `tests/test_risk_scorer.py`
- `tests/test_temporal_lineage.py`

### Create (Frontend)
- `chronos-frontend/src/components/cockpit/TimeSlider.tsx`
- `chronos-frontend/src/components/cockpit/LineageDiffMode.tsx`
- `chronos-frontend/src/components/dashboard/AtRiskWidget.tsx`
- `chronos-frontend/src/components/dashboard/RiskExplainerModal.tsx`
- `chronos-frontend/src/lib/temporal.ts` — typed client functions
- `chronos-frontend/src/lib/risk.ts`

### Modify
- `chronos/agent/nodes/lineage_walk.py` — accept optional `valid_at` parameter
- `chronos/api/routes/__init__.py` — register new routers
- `chronos-frontend/src/pages/IncidentDetail.tsx` (or new Cockpit page) — embed TimeSlider + Diff mode
- Dashboard page — embed AtRiskWidget

## 6. Testing Strategy

- **Unit**: risk scorer with crafted incident histories — verify monotonicity (more incidents → higher score)
- **Unit**: lineage diff with paired snapshots — verify add/remove detection
- **Integration**: temporal lineage with real Graphiti episodes (depends on Unit 9 being live)
- **Frontend**: TimeSlider component test (debouncing, tooltip), AtRiskWidget render test

## 7. Acceptance Criteria

- [ ] `GET /api/v1/lineage/{fqn}?valid_at=...` returns the historical lineage subgraph
- [ ] Cockpit TimeSlider drag re-renders lineage graph for the past timestamp
- [ ] Diff mode highlights added/removed edges with color
- [ ] `GET /api/v1/risk/at-risk` returns 10 entities with scores
- [ ] AtRiskWidget renders on dashboard with sparklines
- [ ] Risk explainer modal opens with contributing factors

## 8. Demo Talking Points (For Pitch Day)

> "The hackathon is called 'Back to the Metadata.' We took that literally. Watch this slider — I'm dragging back 24 hours. The lineage graph just changed. There's an edge here that didn't exist yesterday — that's the schema migration that broke this pipeline.

> And here on the dashboard — these are the entities CHRONOS predicts will fail next, ranked by historical pattern. Last week we predicted `prod.orders.orders_daily` was 87% at risk. Yesterday morning it failed. Reactive RCA is table stakes; we're moving to predictive prevention."

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Graphiti's bi-temporal API may have edge cases | Validate with simple test cases first; fall back to "snapshot at X" if `valid_at` query is fragile |
| Risk scoring with sparse historical data | If <5 incidents exist, show "insufficient data" state instead of fake score |
| Time slider performance with large lineage | Cache snapshot results in-memory; debounce drag events to 200ms |
| FalkorDB free tier query latency | Pre-compute risk scores in background job (every 5 min); serve cached values |

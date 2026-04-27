# Unit 09 — Production Connection Layer

> **Phase**: Construction (post-Unit 8 extension)
> **Created**: 2026-04-27
> **Status**: Functional Design Complete — In Construction
> **Owner**: Aaryan
> **Hackathon mapping**: Phase 0 of `HACKATHON_ALIGNMENT_PLAN.md`

---

## 1. Problem Statement

The deployed CHRONOS API at `https://chronos-api-0e8635fe890d.herokuapp.com` runs against:
- **OpenMetadata**: not connected — agent uses `chronos/demo/fixtures.py` for the live demo
- **Graphiti / FalkorDB**: no graph database provisioned — `persist_trace` and `prior_investigations` nodes degrade gracefully (skip)
- **LiteLLM**: connected via Groq API key (✅ working)
- **Slack**: connected via webhook (✅ working when token provided)

A judge inspecting the demo at hackathon time would notice the OM tab in the cockpit shows fixture data and Graphiti's "related past incidents" panel is empty. **This undermines the technical credibility of the entire submission.**

## 2. Goals

1. **Live OpenMetadata connection** — CHRONOS hits a real OM REST API, ingests real lineage, fetches real owners + classifications
2. **Live FalkorDB connection** — Graphiti episodes persist; "related incidents" panel shows real prior data
3. **Component health observability** — endpoint + UI indicator showing per-service status (healthy / degraded / down)
4. **Graceful degradation preserved** — if FalkorDB cloud has an outage during demo, CHRONOS keeps running on fixture path with a clear UI banner
5. **Setup ergonomics** — a fresh contributor can wire production env vars in <10 minutes following `SETUP.md`

## 3. Non-Goals

- Multi-tenant OM connection (one demo OM target is enough)
- HA / failover for FalkorDB (free tier is single-node — fine for demo)
- Migrating off Heroku
- Bringing Langfuse self-hosted into Heroku (out of scope; can stay in docker-compose for local)

## 4. Key Decisions

| Question | Decision | Reason |
|---|---|---|
| OM target | **Collate Free Managed OM** (preferred) | Persistent state, real OAuth, zero infra, supports webhooks back to Heroku |
| Fallback OM target | sandbox.open-metadata.org | If Collate signup is delayed |
| Graph DB | **FalkorDB Cloud Free Tier** | Native Graphiti driver, free MVP plan, Redis-wire-compatible |
| Health check pattern | Per-component `async def probe()` returning `Status` | Parallel `asyncio.gather`, 30s in-process cache, 2s per-probe timeout |
| Fixture mode trigger | `SETTINGS.demo_mode` env var (already exists) | Preserve existing fallback path; no behavioral change when fixtures wanted |
| Status surfacing | Backend endpoint `/api/v1/health/components` + frontend nav indicator | Judges and operators both benefit |

## 5. Functional Design

### 5.1 Component Status Model

```python
# chronos/health/types.py
from enum import StrEnum
from datetime import datetime
from pydantic import BaseModel

class ComponentState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"   # reachable but slow / partial
    DOWN = "down"
    NOT_CONFIGURED = "not_configured"  # env var missing — intentional

class ComponentStatus(BaseModel):
    name: str               # "openmetadata" | "falkordb" | "litellm" | "slack"
    state: ComponentState
    latency_ms: float | None = None
    detail: str | None = None
    last_checked: datetime
```

### 5.2 Probe Functions

```python
# chronos/health/probes.py
async def probe_openmetadata(settings: Settings) -> ComponentStatus: ...
async def probe_falkordb(settings: Settings) -> ComponentStatus: ...
async def probe_litellm(settings: Settings) -> ComponentStatus: ...
async def probe_slack(settings: Settings) -> ComponentStatus: ...
```

Each probe:
- Returns within 2 seconds (uses `asyncio.wait_for`)
- Catches all exceptions and translates to `ComponentState.DOWN` with a sanitized error string
- Returns `NOT_CONFIGURED` if the env var is missing/empty (this is not a failure)

### 5.3 Health Aggregator (Cached)

```python
# chronos/health/aggregator.py
@lru_cache(maxsize=1)
def _cache(): ...  # (timestamp, list[ComponentStatus])

async def get_component_health(settings: Settings, *, force: bool = False) -> list[ComponentStatus]:
    # 30s TTL cache; force=True bypasses
```

### 5.4 New Endpoint

```
GET /api/v1/health/components
Response: { "components": [ {name, state, latency_ms, detail, last_checked}, ... ], "overall": "healthy"|"degraded"|"down" }
```

The `overall` field rolls up:
- `down` if ANY required component is down (OM, FalkorDB)
- `degraded` if any required is degraded OR any optional (Slack) is down
- `healthy` otherwise

### 5.5 Settings Validation

Extend `chronos/config/settings.py`:
- New optional fields: `falkordb_uri`, `falkordb_username`, `falkordb_password`, `openmetadata_jwt_token`
- Startup validator: log a `WARNING` for each prod var that's missing while `demo_mode=False`
- Don't BLOCK startup — keep the fixture fallback usable

### 5.6 Frontend — Status Nav Indicator

`chronos-frontend/src/components/SystemStatusBadge.tsx`:
- Polls `/api/v1/health/components` every 60s
- Renders a colored dot in the top-right of `DemoNav` and `DashboardNav`
- Click → opens a small floating panel with per-component breakdown
- Tooltip on hover: "Live • OpenMetadata: 124ms • FalkorDB: 38ms • LiteLLM: 312ms"

### 5.7 Demo Data Seeder

`chronos/demo/seeder.py`:
```python
def seed_historical_incidents(count: int = 30) -> None:
    """Populate FalkorDB with N historical incidents for dashboard demo data."""
```
- Generates plausibly-distributed incidents over the past 30 days
- Mix of root cause categories (matches existing `RootCauseCategory` enum)
- Mix of entities (uses fixture entity names so demo flow stays consistent)
- Idempotent — tagged with `demo_seed=true` for cleanup

CLI entry: `python -m chronos.demo seed --count 30 [--clear]`

## 6. Files to Create / Modify

### Create
- `chronos/health/__init__.py`
- `chronos/health/types.py`
- `chronos/health/probes.py`
- `chronos/health/aggregator.py`
- `chronos/api/routes/health_components.py` (new sub-route)
- `chronos/demo/seeder.py`
- `chronos-frontend/src/components/SystemStatusBadge.tsx`
- `SETUP.md` (root)
- `scripts/setup_production.sh`
- `tests/test_health_probes.py`

### Modify
- `chronos/config/settings.py` — add Falkor + OM JWT fields, startup warnings
- `chronos/api/routes/__init__.py` — register new health router
- `chronos/main.py` — call startup health-warmup
- `chronos-frontend/src/App.tsx` — render SystemStatusBadge in nav
- `chronos-frontend/src/lib/api.ts` — add `getComponentHealth()` helper
- `aidlc-docs/aidlc-state.md` — mark Unit 9 status

## 7. User Actions Required (Out of My Hands)

1. Sign up at https://app.falkordb.cloud/signup → create a free DB → copy the connection URL/credentials
2. Either:
   - **Option A (recommended)**: Sign up at https://www.getcollate.io → free managed OM → create a JWT token
   - **Option B**: Use https://sandbox.open-metadata.org → note: ephemeral, may reset
3. Set Heroku config vars (the setup script will guide this):
   ```bash
   heroku config:set FALKORDB_URI=falkor://...:6379 \
                     OPENMETADATA_HOST=https://your.collate.url \
                     OPENMETADATA_JWT_TOKEN=eyJ... \
                     -a chronos-api-0e8635fe890d
   ```
4. Configure OpenMetadata webhook to POST to `https://chronos-api-0e8635fe890d.herokuapp.com/api/v1/webhooks/openmetadata` (with HMAC secret)

## 8. Testing Strategy

- **Unit**: each probe with mocked underlying client (success, timeout, network error, not-configured)
- **Integration**: `tests/integration/test_health_live.py` — only runs when env vars set, hits real services
- **Frontend**: SystemStatusBadge component test with MSW mocking the endpoint

## 9. Acceptance Criteria

- [ ] `/api/v1/health/components` returns all 4 components with real states in production
- [ ] Frontend nav shows live colored status dot (green when all healthy)
- [ ] When `OPENMETADATA_HOST` is set, the live demo walks the REAL lineage graph (verified by inspecting logs)
- [ ] When `FALKORDB_URI` is set, `persist_trace` writes a real episode (verified via FalkorDB Cloud console)
- [ ] When demo seeder is run, dashboard shows 30 historical incidents
- [ ] `SETUP.md` walks a new contributor from clone → live demo in <15 minutes

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Collate Free Tier signup requires waitlist | Fall back to sandbox.open-metadata.org |
| FalkorDB Cloud free tier rate limits | Add in-process write batching; cap at 1 write/sec for demo seeder |
| Health probes add latency to cold requests | Cache aggressively (30s TTL), warm at startup |
| Heroku config var changes require dyno restart | Set during a maintenance window or use `heroku ps:restart` |

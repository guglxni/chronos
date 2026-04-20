# CHRONOS — Units Specification

**Depth Level**: Comprehensive

## Unit Dependency Graph

```
Unit 1: Core Infrastructure ──┐
                               ├── Unit 2: MCP + Ingestion ──┐
                               │                              ├── Unit 3: Investigation Agent ──┐
                               │                              │                                  ├── Unit 4: Output Layer ──┐
                               │                              │                                  │                          ├── Unit 5: REST API ──┐
                               │                              │                                  │                          │                      ├── Unit 6: Frontend
```

## Unit 1: Core Infrastructure & Configuration

**Scope**: Foundation layer — config, models, LLM client, Docker
**Python Packages**: `chronos/config/`, `chronos/models/`, `chronos/llm/`
**Project Files**: `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/config/settings.py` | Config | Pydantic BaseSettings — all env vars |
| `chronos/config/litellm_config.yaml` | Config | LiteLLM model routing (synthesis + extraction + fallback) |
| `chronos/models/incident.py` | Model | IncidentReport, EvidenceItem, AffectedAsset, RemediationStep |
| `chronos/models/events.py` | Model | OpenMetadataWebhookPayload, OpenLineageRunEvent |
| `chronos/models/graphiti_entities.py` | Model | Custom Graphiti entity types + edge types |
| `chronos/llm/client.py` | Service | LiteLLM wrapper (synthesize + extract) |
| `chronos/llm/prompts.py` | Prompt | RCA system prompt + evidence compilation |

**Tests**: `tests/test_models/`, `tests/test_llm/`

---

## Unit 2: MCP Integration Layer & Event Ingestion

**Scope**: MCP client connections + event ingestion pipelines
**Python Packages**: `chronos/mcp/`, `chronos/ingestion/`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/mcp/config.py` | Config | MCP server connection configs (3 servers) |
| `chronos/mcp/client.py` | Service | Unified MCP client wrapper (connect/call_tool) |
| `chronos/mcp/tools.py` | Helpers | Tool call convenience functions per server |
| `chronos/ingestion/graphiti_ingestor.py` | Service | OM events → Graphiti episodes |
| `chronos/ingestion/openlineage_receiver.py` | Service | OL events → OM + Graphiti |
| `chronos/ingestion/deduplicator.py` | Service | Time-window event deduplication |

**Tests**: `tests/test_mcp/`, `tests/test_ingestion/`
**Dependencies**: Unit 1

---

## Unit 3: LangGraph Investigation Agent

**Scope**: 8-node state machine + all investigation step implementations
**Python Packages**: `chronos/agent/`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/agent/state.py` | Model | InvestigationState TypedDict |
| `chronos/agent/graph.py` | Core | LangGraph StateGraph builder + conditional edges |
| `chronos/agent/nodes/scope_failure.py` | Node | Step 1 — Test + entity detail gathering |
| `chronos/agent/nodes/temporal_diff.py` | Node | Step 2 — Graphiti temporal facts + version diff |
| `chronos/agent/nodes/lineage_walk.py` | Node | Step 3 — Upstream lineage traversal |
| `chronos/agent/nodes/code_blast_radius.py` | Node | Step 4 — GitNexus code search + git log |
| `chronos/agent/nodes/downstream_impact.py` | Node | Step 5 — Downstream lineage + tier assessment |
| `chronos/agent/nodes/audit_correlation.py` | Node | Step 6 — Audit log cross-reference |
| `chronos/agent/nodes/rca_synthesis.py` | Node | Step 7 — LLM root cause synthesis |
| `chronos/agent/nodes/notify.py` | Node | Step 8 — Slack notification dispatch |

**Tests**: `tests/test_agent/`
**Dependencies**: Units 1 + 2

---

## Unit 4: Output Layer

**Scope**: Slack notifications + Graphify enrichment
**Python Packages**: `chronos/notifications/`, `chronos/enrichment/`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/notifications/slack.py` | Service | Block Kit builder + webhook sender |
| `chronos/enrichment/graphify_context.py` | Service | GRAPH_REPORT.md reader + entity context |

**Tests**: `tests/test_notifications/`
**Dependencies**: Unit 3

---

## Unit 5: FastAPI REST API & SSE Streaming

**Scope**: All HTTP endpoints + SSE + middleware
**Python Packages**: `chronos/api/`, `chronos/main.py`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/main.py` | Entrypoint | FastAPI app creation + lifespan |
| `chronos/api/routes/webhooks.py` | Route | OM + OL webhook receivers |
| `chronos/api/routes/incidents.py` | Route | Incident CRUD |
| `chronos/api/routes/investigations.py` | Route | Manual trigger + SSE stream |
| `chronos/api/routes/stats.py` | Route | Dashboard statistics |
| `chronos/api/middleware.py` | Middleware | Error handling + logging |

**Tests**: `tests/test_api/`
**Dependencies**: Units 3 + 4

---

## Unit 6: React Frontend Dashboard

**Scope**: Complete React application with React Flow
**Directory**: `chronos-frontend/`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `src/App.tsx` | Router | React Router setup |
| `src/pages/Dashboard.tsx` | Page | Incident timeline + stats |
| `src/pages/IncidentDetail.tsx` | Page | Investigation replay |
| `src/pages/Settings.tsx` | Page | Configuration |
| `src/components/LineageFailureMap.tsx` | Component | React Flow graph |
| `src/components/InvestigationReplay.tsx` | Component | Step-by-step timeline |
| `src/components/TemporalDiff.tsx` | Component | State diff view |
| `src/components/IncidentCard.tsx` | Component | Summary card |
| `src/components/EvidenceChain.tsx` | Component | Evidence items |
| `src/components/BlastRadiusPanel.tsx` | Component | Impact summary |
| `src/hooks/useWebSocket.ts` | Hook | SSE connection |
| `src/lib/api.ts` | Util | API client |
| `src/lib/types.ts` | Types | TypeScript types |

**Tests**: Vitest unit tests for components
**Dependencies**: Unit 5

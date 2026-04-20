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
                               │                              │                                  │                          │
            Unit 7: Agentic Metadata (cross-cutting) ─────────┼──────────────────────────────────┘
```

## Unit 1: Core Infrastructure & Configuration

**Scope**: Foundation layer — config, models, LLM client, Docker
**Python Packages**: `chronos/config/`, `chronos/models/`, `chronos/llm/`
**Project Files**: `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`
**Note**: v2.0 adds Langfuse env vars, OTel env vars, and version/environment tracking to settings

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

**Scope**: 10-node state machine + all investigation step implementations (v2.0: +2 new nodes)
**Python Packages**: `chronos/agent/`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/agent/state.py` | Model | InvestigationState TypedDict (v2.0: +prior_investigations, +trace_persisted) |
| `chronos/agent/graph.py` | Core | LangGraph StateGraph builder + Langfuse callback + conditional edges |
| `chronos/agent/nodes/prior_investigations.py` | Node | **Step 0** — Self-referential memory lookup (NEW v2.0) |
| `chronos/agent/nodes/scope_failure.py` | Node | Step 1 — Test + entity detail gathering |
| `chronos/agent/nodes/temporal_diff.py` | Node | Step 2 — Graphiti temporal facts + version diff |
| `chronos/agent/nodes/lineage_walk.py` | Node | Step 3 — Upstream lineage traversal |
| `chronos/agent/nodes/code_blast_radius.py` | Node | Step 4 — GitNexus code search + git log |
| `chronos/agent/nodes/downstream_impact.py` | Node | Step 5 — Downstream lineage + tier assessment |
| `chronos/agent/nodes/audit_correlation.py` | Node | Step 6 — Audit log cross-reference |
| `chronos/agent/nodes/rca_synthesis.py` | Node | Step 7 — LLM root cause synthesis |
| `chronos/agent/nodes/notify.py` | Node | Step 8 — Slack notification dispatch |
| `chronos/agent/nodes/persist_trace.py` | Node | **Step 9** — Self-referential memory persist (NEW v2.0) |

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

**Scope**: All HTTP endpoints + SSE + middleware + A2A + PROV-O routes
**Python Packages**: `chronos/api/`, `chronos/main.py`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/main.py` | Entrypoint | FastAPI app creation + lifespan + OpenLLMetry init |
| `chronos/api/routes/webhooks.py` | Route | OM + OL webhook receivers (v2.0: invokes graph with Langfuse config) |
| `chronos/api/routes/incidents.py` | Route | Incident CRUD + PROV-O export endpoints |
| `chronos/api/routes/investigations.py` | Route | Manual trigger + SSE stream |
| `chronos/api/routes/stats.py` | Route | Dashboard statistics |
| `chronos/api/routes/well_known.py` | Route | A2A Agent Card endpoint (NEW v2.0) |
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
| `src/components/ProvenanceDownload.tsx` | Component | PROV-O download button (NEW v2.0) |
| `src/hooks/useWebSocket.ts` | Hook | SSE connection |
| `src/lib/api.ts` | Util | API client |
| `src/lib/types.ts` | Types | TypeScript types |

**Tests**: Vitest unit tests for components
**Dependencies**: Unit 5

---

## Unit 7: Agentic Metadata Infrastructure (Cross-Cutting)

**Scope**: All 8 gap-closing FOSS integrations (F11-F18). Cross-cutting layer that extends Units 1, 3, 4, 5.
**Python Packages**: `chronos/compliance/`, `chronos/observability/`, `chronos/.well-known/`
**Test Packages**: `tests/evals/`
**CI**: `.github/workflows/eval.yml`

**Components**:
| File | Type | Description |
|------|------|-------------|
| `chronos/compliance/__init__.py` | Package | Compliance module |
| `chronos/compliance/prov_generator.py` | Service | W3C PROV-O document generator (F13) |
| `chronos/observability/__init__.py` | Package | Observability module |
| `chronos/observability/otel_setup.py` | Service | OpenLLMetry + OTel GenAI SemConv init (F15/F16) |
| `chronos/.well-known/agent-card.json` | Static | A2A Agent Card (F14) |
| `tests/evals/test_rca_quality.py` | Eval | DeepEval G-Eval + FaithfulnessMetric RCA tests (F17) |
| `tests/evals/test_graphiti_retrieval.py` | Eval | RAGAs retrieval quality evaluation (F18) |
| `tests/evals/fixtures/events/schema_change_webhook.json` | Fixture | Canonical test event |
| `.github/workflows/eval.yml` | CI | Quality eval workflow on PR |

**Integrates With**:
- **Unit 1**: Adds Langfuse/OTel env vars to `settings.py` + `docker-compose.yml`
- **Unit 3**: Adds `prior_investigations.py` (Step 0) + `persist_trace.py` (Step 9) + Langfuse callback in `graph.py`
- **Unit 5**: Adds PROV-O export routes to `incidents.py` + `well_known.py` for A2A + OpenLLMetry init in `main.py`
- **Unit 6**: Adds `ProvenanceDownload.tsx` component

**Tests**: `tests/evals/` (DeepEval + RAGAs)
**Dependencies**: Units 1 + 3 + 5 (cross-cutting)

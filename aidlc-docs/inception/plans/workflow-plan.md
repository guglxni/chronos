# CHRONOS — Workflow Plan

**Depth Level**: Comprehensive
**Project Type**: Greenfield — Multi-service system with 3 MCP integrations

## Execution Overview

```
INCEPTION ✅ ──→ CONSTRUCTION ⬜ ──→ OPERATIONS ⬜
(Complete)       (7 Units)          (Deploy + Demo)
```

## Unit Decomposition & Build Order

```
Unit 1: Core Infrastructure
    ↓
Unit 2: MCP + Ingestion ←── depends on Unit 1
    ↓
Unit 3: Investigation Agent ←── depends on Units 1+2
    ↓
Unit 4: Output Layer ←── depends on Unit 3
    ↓
Unit 5: REST API + SSE ←── depends on Units 3+4
    ↓
Unit 6: React Frontend ←── depends on Unit 5
    ↓
Unit 7: Agentic Metadata ←── cross-cutting (extends Units 1,3,5,6)
```

## Unit Specifications

### Unit 1: Core Infrastructure & Configuration
**Packages**: `chronos/config/`, `chronos/models/`, `chronos/llm/`
**Deliverables**:
- [ ] Pydantic Settings (env var configuration — includes Langfuse, OTel vars)
- [ ] LiteLLM config (model routing — synthesis + extraction)
- [ ] Data models (IncidentReport, EvidenceItem, AffectedAsset, RemediationStep)
- [ ] Graphiti entity types (DataAsset, DataTest, Schema, Pipeline, Incident)
- [ ] Event payload models (OpenMetadataWebhookPayload, OpenLineageRunEvent)
- [ ] LLM client wrapper (synthesize + extract functions)
- [ ] pyproject.toml with all dependencies (including langfuse, traceloop-sdk, prov, deepeval, ragas)
- [ ] Dockerfile
- [ ] docker-compose.yml (complete stack including Langfuse + Postgres)
- [ ] .env.example template (including Langfuse, OTel vars)

**Estimated Effort**: Day 1-2

### Unit 2: MCP Integration Layer & Event Ingestion
**Packages**: `chronos/mcp/`, `chronos/ingestion/`
**Deliverables**:
- [ ] MCP client configuration (3 servers: OpenMetadata, Graphiti, GitNexus)
- [ ] Unified MCP client wrapper
- [ ] MCP tool call helper functions
- [ ] Graphiti episode ingestor (OpenMetadata events → episodes)
- [ ] OpenLineage event receiver + Graphiti forwarder
- [ ] Event deduplicator (configurable window)

**Dependencies**: Unit 1 (models, config)
**Estimated Effort**: Day 2-3

### Unit 3: LangGraph Investigation Agent
**Packages**: `chronos/agent/`
**Deliverables**:
- [ ] InvestigationState TypedDict (v2.0: +prior_investigations, +trace_persisted)
- [ ] LangGraph state machine with 10 nodes + conditional edges + Langfuse callback
- [ ] Node: **prior_investigations** (Step 0 — Graphiti self-referential lookup) **(NEW v2.0)**
- [ ] Node: scope_failure (OpenMetadata MCP)
- [ ] Node: temporal_diff (Graphiti MCP + OpenMetadata MCP)
- [ ] Node: lineage_walk (OpenMetadata MCP)
- [ ] Node: code_blast_radius (GitNexus MCP + git log)
- [ ] Node: downstream_impact (OpenMetadata MCP)
- [ ] Node: audit_correlation (OpenMetadata MCP + Graphiti MCP)
- [ ] Node: rca_synthesis (LiteLLM — structured output)
- [ ] Node: notify (Slack webhook)
- [ ] Node: **persist_trace** (Step 9 — Graphiti self-referential persist) **(NEW v2.0)**
- [ ] RCA system prompt + evidence compilation

**Dependencies**: Units 1+2 (models, MCP clients, LLM client)
**Estimated Effort**: Day 3-5

### Unit 4: Output Layer
**Packages**: `chronos/notifications/`, `chronos/enrichment/`
**Deliverables**:
- [ ] Slack Block Kit message builder
- [ ] Slack webhook sender (httpx async)
- [ ] Owner-to-Slack-ID mapping
- [ ] Graphify context provider (GRAPH_REPORT.md reader)
- [ ] Severity + category emoji mappings

**Dependencies**: Unit 3 (IncidentReport output)
**Estimated Effort**: Day 5-6

### Unit 5: FastAPI REST API & SSE Streaming
**Packages**: `chronos/api/`, `chronos/main.py`
**Deliverables**:
- [ ] FastAPI application entrypoint (with OpenLLMetry init)
- [ ] Webhook routes (OpenMetadata + OpenLineage) (with Langfuse graph invocation)
- [ ] Incident CRUD routes (list, detail, acknowledge, resolve)
- [ ] PROV-O export endpoints (.jsonld, .ttl, .provn) **(NEW v2.0)**
- [ ] Investigation SSE stream endpoint
- [ ] Manual investigation trigger endpoint
- [ ] Dashboard statistics endpoint
- [ ] A2A Agent Card endpoint (`/.well-known/agent-card.json`) **(NEW v2.0)**
- [ ] Health check endpoint
- [ ] Error handling middleware

**Dependencies**: Units 3+4 (agent, notifications)
**Estimated Effort**: Day 6-7

### Unit 6: React Frontend Dashboard
**Packages**: `chronos-frontend/`
**Deliverables**:
- [ ] Vite + React + TypeScript project setup
- [ ] Tailwind CSS configuration
- [ ] React Router setup (Dashboard, IncidentDetail, Settings)
- [ ] IncidentTimeline component
- [ ] IncidentCard component
- [ ] LineageFailureMap component (React Flow)
- [ ] InvestigationReplay component
- [ ] TemporalDiff component
- [ ] EvidenceChain component
- [ ] BlastRadiusPanel component
- [ ] SeverityBadge component
- [ ] API client (fetch wrapper)
- [ ] SSE hook (useWebSocket)
- [ ] TypeScript types matching backend models

**Dependencies**: Unit 5 (API endpoints)
**Estimated Effort**: Day 7-8

### Unit 7: Agentic Metadata Infrastructure (Cross-Cutting)
**Packages**: `chronos/compliance/`, `chronos/observability/`, `chronos/.well-known/`, `tests/evals/`
**Deliverables**:
- [ ] W3C PROV-O document generator (`chronos/compliance/prov_generator.py`) **(F13)**
- [ ] OpenLLMetry + OTel GenAI SemConv init (`chronos/observability/otel_setup.py`) **(F15/F16)**
- [ ] A2A Agent Card JSON (`chronos/.well-known/agent-card.json`) **(F14)**
- [ ] DeepEval RCA quality tests (`tests/evals/test_rca_quality.py`) **(F17)**
- [ ] RAGAs retrieval quality tests (`tests/evals/test_graphiti_retrieval.py`) **(F18)**
- [ ] Test fixture: canonical demo webhook event
- [ ] GitHub Actions eval workflow (`.github/workflows/eval.yml`)

**Dependencies**: Units 1+3+5 (cross-cutting)
**Estimated Effort**: Day 8-9 (parallel with polish)

## Construction Phase Plan

For each unit, the AIDLC workflow will execute:
1. **Functional Design** — Data models, business logic, component interfaces
2. **NFR Requirements** — Performance, security, reliability constraints
3. **Code Generation** — Implementation with tests

**NFR Design** and **Infrastructure Design** are executed ONCE (Unit 1) since the infrastructure spec is defined in the tech spec.

## PRD Timeline Mapping

| PRD Phase | Days | AIDLC Units | Status |
|-----------|------|-------------|--------|
| Foundation | 1-3 | Units 1 + 2 (+ Langfuse Docker in Unit 1) | ⬜ Pending |
| Agent Core | 4-6 | Units 3 + 4 (+ Self-Referential Memory Steps 0/9) | ⬜ Pending |
| Integration & UI | 7-8 | Units 5 + 6 (+ PROV-O, A2A, OpenLLMetry, PROV-O Download) | ⬜ Pending |
| Polish & Demo | 9-10 | Unit 7 (DeepEval, RAGAs) + Operations Phase | ⬜ Pending |

## Risk Mitigation (from PRD §7.4)

| Risk | Mitigation via AIDLC |
|------|---------------------|
| MCP compatibility issues | Unit 2 tests MCP connections early; REST API fallback designed in |
| Graphiti ingestion latency | Fast extraction model via LiteLLM; batch ingestion in Unit 2 |
| Scope creep (8+ tools) | Strict unit boundaries; F7-F10 only if Units 1-6 complete |
| Demo data realism | Demo scenario script in Operations phase |
| Langfuse Docker dependency | Feature-flagged via `LANGFUSE_ENABLED=true/false`; file-based fallback |
| PROV-O complexity | Python `prov` library handles serialization; thin wrapper only |
| DeepEval/RAGAs need LLM keys | Tests skip gracefully if API keys unavailable in CI |

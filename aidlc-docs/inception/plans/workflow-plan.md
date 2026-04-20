# CHRONOS — Workflow Plan

**Depth Level**: Comprehensive
**Project Type**: Greenfield — Multi-service system with 3 MCP integrations

## Execution Overview

```
INCEPTION ✅ ──→ CONSTRUCTION ⬜ ──→ OPERATIONS ⬜
(Complete)       (6 Units)          (Deploy + Demo)
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
```

## Unit Specifications

### Unit 1: Core Infrastructure & Configuration
**Packages**: `chronos/config/`, `chronos/models/`, `chronos/llm/`
**Deliverables**:
- [ ] Pydantic Settings (env var configuration)
- [ ] LiteLLM config (model routing — synthesis + extraction)
- [ ] Data models (IncidentReport, EvidenceItem, AffectedAsset, RemediationStep)
- [ ] Graphiti entity types (DataAsset, DataTest, Schema, Pipeline, Incident)
- [ ] Event payload models (OpenMetadataWebhookPayload, OpenLineageRunEvent)
- [ ] LLM client wrapper (synthesize + extract functions)
- [ ] pyproject.toml with all dependencies
- [ ] Dockerfile
- [ ] docker-compose.yml (complete stack)
- [ ] .env.example template

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
- [ ] InvestigationState TypedDict
- [ ] LangGraph state machine with 8 nodes + conditional edges
- [ ] Node: scope_failure (OpenMetadata MCP)
- [ ] Node: temporal_diff (Graphiti MCP + OpenMetadata MCP)
- [ ] Node: lineage_walk (OpenMetadata MCP)
- [ ] Node: code_blast_radius (GitNexus MCP + git log)
- [ ] Node: downstream_impact (OpenMetadata MCP)
- [ ] Node: audit_correlation (OpenMetadata MCP + Graphiti MCP)
- [ ] Node: rca_synthesis (LiteLLM — structured output)
- [ ] Node: notify (Slack webhook)
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
- [ ] FastAPI application entrypoint
- [ ] Webhook routes (OpenMetadata + OpenLineage)
- [ ] Incident CRUD routes (list, detail, acknowledge, resolve)
- [ ] Investigation SSE stream endpoint
- [ ] Manual investigation trigger endpoint
- [ ] Dashboard statistics endpoint
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

## Construction Phase Plan

For each unit, the AIDLC workflow will execute:
1. **Functional Design** — Data models, business logic, component interfaces
2. **NFR Requirements** — Performance, security, reliability constraints
3. **Code Generation** — Implementation with tests

**NFR Design** and **Infrastructure Design** are executed ONCE (Unit 1) since the infrastructure spec is defined in the tech spec.

## PRD Timeline Mapping

| PRD Phase | Days | AIDLC Units | Status |
|-----------|------|-------------|--------|
| Foundation | 1-3 | Units 1 + 2 | ⬜ Pending |
| Agent Core | 4-6 | Units 3 + 4 | ⬜ Pending |
| Integration & UI | 7-8 | Units 5 + 6 | ⬜ Pending |
| Polish & Demo | 9-10 | Operations Phase | ⬜ Pending |

## Risk Mitigation (from PRD §7.4)

| Risk | Mitigation via AIDLC |
|------|---------------------|
| MCP compatibility issues | Unit 2 tests MCP connections early; REST API fallback designed in |
| Graphiti ingestion latency | Fast extraction model via LiteLLM; batch ingestion in Unit 2 |
| Scope creep (8+ tools) | Strict unit boundaries; F7-F10 only if Units 1-6 complete |
| Demo data realism | Demo scenario script in Operations phase |

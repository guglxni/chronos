# AI-DLC Workflow State — CHRONOS

## Project Overview
- **Project**: CHRONOS — Autonomous Data Incident Root Cause Analysis Agent
- **Version**: 2.0 — Agentic Metadata Infrastructure Edition
- **Type**: Greenfield
- **Started**: 2026-04-21
- **Hackathon**: OpenMetadata Paradox Hackathon (WeMakeDevs x OpenMetadata)
- **Deadline**: April 26, 2026

## Current Phase
**INCEPTION** — Planning & Architecture (v2.0 upgrade complete)

## Workflow Progress

### INCEPTION PHASE
- [x] Workspace Detection — Greenfield project detected
- [x] Reverse Engineering — SKIPPED (Greenfield)
- [x] Requirements Analysis — Comprehensive depth (PRD.md + spec.md pre-exist)
    - v2.0: Added FR-11 through FR-18 (8 gap-closing FOSS integrations)
- [x] User Stories — Generated (3 personas: Priya, Alex, Meera)
    - v2.0: Added Epic 7 with US-7.1 through US-7.8
- [x] Workflow Planning — Complete with unit decomposition
    - v2.0: Added Unit 7 (Agentic Metadata Infrastructure)
- [x] Application Design — Complete (triple-graph + LangGraph + FastAPI + React + Langfuse)
    - v2.0: Architecture updated with observability/compliance layers
- [x] Units Generation — 7 units identified and sequenced
    - v2.0: Unit 7 added as cross-cutting agentic metadata layer

### CONSTRUCTION PHASE
- [ ] Unit 1: Core Infrastructure & Configuration
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 2: MCP Integration Layer & Event Ingestion
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 3: LangGraph Investigation Agent (10-step pipeline: Steps 0-9)
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 4: Output Layer (Slack + Incident Reports)
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 5: FastAPI REST API & SSE Streaming (+PROV-O +A2A)
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 6: React Frontend Dashboard (+ProvenanceDownload)
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 7: Agentic Metadata Infrastructure (Cross-Cutting)
  - [ ] Functional Design
  - [ ] Code Generation
  - [ ] DeepEval / RAGAs tests
  - [ ] GitHub Actions CI
- [ ] Build and Test

### OPERATIONS PHASE
- [ ] Docker Compose orchestration
- [ ] Demo scenario scripting
- [ ] Deployment documentation

## Extension Configuration

| Extension | Enabled | Notes |
|-----------|---------|-------|
| Security Baseline | ✅ Yes | API keys via env vars, JWT auth for OpenMetadata |
| Property-Based Testing | ❌ No | Hackathon scope — unit + integration tests sufficient |
| Agentic Observability | ✅ Yes | Langfuse (feature-flagged), OpenLLMetry, OTel GenAI SemConv |
| Compliance | ✅ Yes | W3C PROV-O provenance artifacts |
| Agent Discovery | ✅ Yes | A2A Protocol Agent Card |
| Quality Evaluation | ✅ Yes | DeepEval + RAGAs |

## Technology Stack
- **Backend**: Python 3.11+, FastAPI, LangGraph, LiteLLM
- **Frontend**: React + TypeScript, React Flow, Tailwind CSS
- **Data**: Graphiti (FalkorDB), OpenMetadata MCP, GitNexus MCP
- **Observability**: Langfuse (self-hosted), OpenLLMetry (Traceloop), OTel GenAI SemConv
- **Compliance**: W3C PROV-O (prov library), A2A Agent Card
- **Quality**: DeepEval (G-Eval, Faithfulness), RAGAs (retrieval metrics)
- **Infrastructure**: Docker Compose (incl. Langfuse + Postgres)
- **LLM**: LiteLLM → Anthropic Claude / Groq Llama / OpenAI fallback

## Gap-to-Feature Mapping

| Gap | Feature | Unit | Status |
|-----|---------|------|--------|
| 1. Agentic observability | F12: Langfuse | 1+3 | ⬜ Pending |
| 2. Vendor-neutral instrumentation | F15: OpenLLMetry | 5+7 | ⬜ Pending |
| 3. Standardized telemetry | F16: OTel GenAI SemConv | 7 (free w/ F15) | ⬜ Pending |
| 4. Regression tests | F17: DeepEval | 7 | ⬜ Pending |
| 5. Retrieval evaluation | F18: RAGAs | 7 | ⬜ Pending |
| 6. Compliance provenance | F13: PROV-O | 5+7 | ⬜ Pending |
| 7. Agent discovery | F14: A2A Agent Card | 5+7 | ⬜ Pending |
| 8. Self-referential memory | F11: Graphiti loop | 3 | ⬜ Pending |

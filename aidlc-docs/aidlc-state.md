# AI-DLC Workflow State — CHRONOS

## Project Overview
- **Project**: CHRONOS — Autonomous Data Incident Root Cause Analysis Agent
- **Version**: 2.0 — Agentic Metadata Infrastructure Edition
- **Type**: Greenfield
- **Started**: 2026-04-21
- **Hackathon**: OpenMetadata Paradox Hackathon (WeMakeDevs x OpenMetadata)
- **Deadline**: April 26, 2026

## Current Phase
**CONSTRUCTION** — Post-remediation verification complete (2026-04-21)

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
- [x] Unit 1: Core Infrastructure & Configuration
  - [x] Functional Design
  - [x] Code Generation — pyproject.toml, Dockerfile, docker-compose.yml, settings.py, litellm_config.yaml, all models, LLM client + prompts
- [x] Unit 2: MCP Integration Layer & Event Ingestion
  - [x] Functional Design
  - [x] Code Generation — MCP client (JSON-RPC), 12 tool helpers, Graphiti ingestor, OpenLineage receiver, deduplicator
- [x] Unit 3: LangGraph Investigation Agent (10-step pipeline: Steps 0-9)
  - [x] Functional Design
  - [x] Code Generation — InvestigationState TypedDict, 10 node files (steps 0-9), LangGraph state machine, Langfuse callback wiring
- [x] Unit 4: Output Layer (Slack + Incident Reports)
  - [x] Functional Design
  - [x] Code Generation — Block Kit Slack notifier (severity/RCA emojis, owner mentions, action buttons), Graphify context extractor
- [x] Unit 5: FastAPI REST API & SSE Streaming (+PROV-O +A2A)
  - [x] Functional Design
  - [x] Code Generation — main.py, all 5 route groups, PROV-O 3-format export, A2A agent card, SSE streaming, webhook receivers
- [x] Unit 6: React Frontend Dashboard (+ProvenanceDownload)
  - [x] Functional Design
  - [x] Code Generation — Vite+React+TS, 10 components (React Flow lineage map, investigation replay, evidence chain, blast radius, provenance download), 3 pages (Dashboard, IncidentDetail 6-tab, Settings), TanStack Query hooks, SSE hook
- [x] Unit 7: Agentic Metadata Infrastructure (Cross-Cutting)
  - [x] Functional Design
  - [x] Code Generation — W3C PROV-O generator (JSON-LD/Turtle/PROV-N), OpenLLMetry init, A2A agent card JSON
  - [x] DeepEval / RAGAs tests — GEval + Faithfulness (F17), Context Recall/Precision (F18)
  - [x] GitHub Actions CI — eval.yml with unit tests + LLM eval stages
- [x] Security and quality remediation (internal-docs/FIX_PLAN.md)
  - [x] Secret handling hardening and startup validation
  - [x] Webhook signature auth + rate limiting + CORS hardening
  - [x] Exception narrowing and cancellation-safe async handling
  - [x] Type-safe incident access and route-level cleanup
  - [x] Lazy graph compilation to avoid import-time side effects
  - [x] Verification complete — pytest (14 passed, 3 skipped), mypy clean, targeted ruff clean
- [x] Unit 8: Local Code Intelligence Layer (2026-04-26)
  - [x] Functional Design — aidlc-docs/code_intel_design.md
  - [x] Code Generation — chronos/code_intel/{local_git,code_search,sql_parser,graphify_adapter,dbt_manifest}.py
  - [x] MCP wrappers updated — gitnexus_* now local-first; graphify_*, dbt_* added
  - [x] Pipeline integration — Step 1 community context, Step 4 dbt+graphify enrichment, Step 5 code blast paths, Step 7 live graphify rendering
  - [x] State schema — added 5 new total=False fields (no migration needed)
  - [x] Tests — 38 new (tests/test_code_intel.py + test_nodes_code_intel.py + test_graphify_context.py); 0 regressions
- [ ] Unit 9: Production Connection Layer (2026-04-27) — IN PROGRESS
  - [x] Functional Design — aidlc-docs/units/U-09_production_hardening.md
  - [ ] Code Generation — chronos/health/{types,probes,aggregator}.py + /api/v1/health/components endpoint
  - [ ] Settings extensions — Falkor + OM JWT fields, startup warnings
  - [ ] Demo seeder — chronos/demo/seeder.py + python -m chronos.demo seed CLI
  - [ ] Frontend — SystemStatusBadge component in nav
  - [ ] User runbook — SETUP.md + scripts/setup_production.sh
  - [ ] Integration — verified live against Collate Free OM + FalkorDB Cloud
- [ ] Unit 10: Temporal Innovation (Time-Travel + Predictive Risk)
  - [x] Functional Design — aidlc-docs/units/U-10_temporal_innovation.md
  - [ ] Backend — chronos/temporal/{lineage_at,lineage_diff,timeline}.py + chronos/risk/{scorer,factors}.py
  - [ ] API endpoints — GET /api/v1/lineage/{fqn}?valid_at=, /diff, /api/v1/risk/at-risk, /risk/{fqn}/explain
  - [ ] Frontend — TimeSlider, LineageDiffMode, AtRiskWidget, RiskExplainerModal
  - [ ] Tests — risk scorer monotonicity + diff detection coverage
- [ ] Build and Test (full stack integration) — Pending docker-compose up + integration verification

### OPERATIONS PHASE
- [ ] Docker Compose orchestration — docker-compose.yml ready, pending `docker compose up`
- [ ] Demo scenario scripting — schema change injection script needed
- [ ] Deployment documentation

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
- **Data**: Graphiti (FalkorDB), OpenMetadata MCP, local code_intel layer (subprocess git, ripgrep, sqlglot, dbt manifest, graphify NetworkX adapter)
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

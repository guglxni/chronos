<p align="center">
  <h1 align="center">⏳ CHRONOS</h1>
  <p align="center"><strong>Autonomous Data Incident Root Cause Analysis Agent</strong></p>
  <p align="center"><em>"Don't just detect the anomaly. Travel back through the timeline and find where it broke."</em></p>
</p>

<p align="center">
  <a href="#architecture">Architecture</a> •
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#demo">Demo</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## The Problem

When a data quality test fails, the investigation is **manual, slow, and scales poorly**:

1. 🔍 Trace lineage upstream (15-20 min for deep chains)
2. 🕐 Check for recent changes across entities (no temporal correlation tools)
3. 💻 Cross-reference code changes (metadata ↔ code is disconnected)
4. 📊 Assess downstream blast radius (manual Slack messages)
5. 🔄 Start from scratch every time (no institutional memory)

**Average MTTR: ~45 minutes per incident.**

## The Solution

CHRONOS is an autonomous agent that **investigates data quality incidents** by reasoning across three knowledge graphs simultaneously:

| Graph | What It Knows | Technology |
|-------|---------------|------------|
| **Metadata Graph** | Tables, columns, lineage, tests, ownership, tiers | OpenMetadata MCP |
| **Temporal Graph** | What changed, when, by whom — with bi-temporal facts | Graphiti + FalkorDB |
| **Code Graph** | Functions, imports, dependencies, recent commits | GitNexus MCP |

**Result: MTTR reduced from ~45 min to ~2 min.**

## Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │           EVENT INGESTION LAYER               │
                    │  OpenMetadata Webhooks │ OpenLineage Events   │
                    └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────────────┐
                    │       EVENT ROUTER & DEDUPLICATOR             │
                    └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────────────┐
                    │     INVESTIGATION ORCHESTRATOR (LangGraph)    │
                    │                                               │
                    │  PRIOR_INV → SCOPE → TEMPORAL → LINEAGE →   │
                    │  CODE → DOWNSTREAM → AUDIT → SYNTHESIS →     │
                    │  NOTIFY → PERSIST_TRACE                       │
                    │                                               │
                    │  ┌────────────┐ ┌──────────┐ ┌────────────┐ │
                    │  │ OpenMeta   │ │ Graphiti  │ │ GitNexus   │ │
                    │  │ MCP        │ │ MCP       │ │ MCP        │ │
                    │  └────────────┘ └──────────┘ └────────────┘ │
                    │                                               │
                    │  LLM: LiteLLM (Claude / Llama / GPT)         │
                    │  Traces: Langfuse │ OTel: OpenLLMetry         │
                    └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────────────┐
                    │  REST API │ Slack │ PROV-O │ A2A │ Dashboard │
                    └──────────────────────────────────────────────┘
```

## Features

### Core (Must-Have)
- **🎯 Event-Driven Detection** — Automatic webhook-triggered investigation on test failures
- **🤖 10-Step Autonomous Investigation** — LangGraph state machine reasoning across 3 MCP servers
- **💡 Self-Referential Memory** — CHRONOS learns from past investigations (Step 0: lookup, Step 9: persist)
- **🕐 Temporal Intelligence** — Graphiti bi-temporal facts answer "what was true 48 hours ago?"
- **💻 Code-Level Analysis** — GitNexus identifies implicated commits and code files
- **📊 Blast Radius Assessment** — Downstream impact with business criticality (Tier-1/2/3)
- **📋 Structured Reports** — Machine-readable incident reports with confidence scoring
- **💬 Slack Notifications** — Rich Block Kit messages with owner tags and action buttons
- **🖥️ React Dashboard** — Interactive lineage map, investigation replay, temporal diff

### Agentic Metadata Infrastructure (Gap-Closing)
- **🔭 Langfuse Observability** — Every investigation is a trace tree: replay, annotate, evaluate
- **📡 OpenLLMetry** — Vendor-neutral LLM instrumentation via OpenTelemetry GenAI SemConv
- **📄 W3C PROV-O Compliance** — One-click GDPR/SOC2-ready audit artifacts (JSON-LD/Turtle)
- **🤝 A2A Agent Card** — Agent discovery via `/.well-known/agent-card.json`
- **✅ DeepEval Quality Tests** — Pytest-compatible RCA accuracy regression detection
- **📎 RAGAs Retrieval Eval** — Graphiti retrieval quality metrics (faithfulness, precision, recall)

### Enhanced (Nice-to-Have)
- **🔗 OpenLineage Ingestion** — Richer lineage from pipeline orchestrators
- **🏗️ Graphify Architecture Context** — Multi-modal code knowledge graph
- **🔄 Pattern Recognition** — Recurring incident detection via Graphiti
- **🛡️ Prevention Mode** — Pre-merge CI/CD impact assessment

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/chronos.git
cd chronos

# Copy environment template
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY, GROQ_API_KEY, SLACK_WEBHOOK_URL)

# Start the full stack (10 containers)
docker compose up -d

# Open the dashboard
open http://localhost:3000

# Run the demo (inject a schema change failure and watch CHRONOS investigate)
python scripts/demo_inject_failure.py

# Or trigger manually via the API
curl -X POST http://localhost:8100/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{"entity_fqn": "sample_db.default.orders", "triggered_by": "manual"}'

# Check the A2A agent card
curl http://localhost:8100/.well-known/agent-card.json | jq .
```

Services started by `docker compose up`:

| Service | URL | Purpose |
|---------|-----|---------|
| CHRONOS API | http://localhost:8100 | FastAPI + LangGraph agent |
| React Dashboard | http://localhost:3000 | Investigation UI |
| OpenMetadata | http://localhost:8585 | Metadata catalog |
| Langfuse | http://localhost:3002 | Trace trees & evals |
| FalkorDB Browser | http://localhost:3001 | Temporal graph explorer |
| LiteLLM Proxy | http://localhost:4000 | LLM routing |

## Demo

### Inject a failure and watch CHRONOS investigate:

```bash
# 1. Inject a schema change (breaks downstream test)
./scripts/inject_failure.sh

# 2. Watch the dashboard for live investigation
open http://localhost:3000

# 3. Check Slack for the incident report (~90 seconds)
```

**Demo talking points:**
1. Test fails → CHRONOS checks institutional memory (Step 0 — finds 2 past incidents)
2. Graphiti finds the schema changed 2 hours ago
3. Upstream lineage walk pinpoints the source table
4. GitNexus identifies the exact commit
5. 3 Tier-1 downstream assets are at risk
6. LLM synthesizes root cause with 92% confidence (references past incident!)
7. Slack notification arrives in ~47 seconds
8. Investigation persisted to Graphiti (Step 9 — next time will be even richer)
9. Open Langfuse: full trace tree with token counts and costs
10. Download W3C PROV-O compliance artifact with one click
11. Discover CHRONOS: `curl localhost:8100/.well-known/agent-card.json`

## Tech Stack

| Layer | Technology | License |
|-------|------------|---------|
| **Metadata** | [OpenMetadata](https://open-metadata.org/) | Apache 2.0 |
| **Temporal KG** | [Graphiti](https://github.com/getzep/graphiti) + [FalkorDB](https://www.falkordb.com/) | Apache 2.0 / SSPL |
| **Code KG** | [GitNexus](https://github.com/abhigyanpatwari/GitNexus) | MIT |
| **Architecture KG** | [Graphify](https://github.com/safishamsi/graphify) | MIT |
| **Agent** | [LangGraph](https://github.com/langchain-ai/langgraph) | MIT |
| **LLM Gateway** | [LiteLLM](https://github.com/BerriAI/litellm) | MIT |
| **Observability** | [Langfuse](https://github.com/langfuse/langfuse) + [OpenLLMetry](https://github.com/traceloop/openllmetry) | MIT / Apache 2.0 |
| **Compliance** | [W3C PROV-O](https://github.com/trungdong/prov) + [A2A Protocol](https://github.com/a2aproject/A2A) | MIT / Apache 2.0 |
| **Quality** | [DeepEval](https://github.com/confident-ai/deepeval) + [RAGAs](https://github.com/explodinggradients/ragas) | Apache 2.0 |
| **Lineage Standard** | [OpenLineage](https://openlineage.io/) | Apache 2.0 |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | MIT |
| **Frontend** | React + [React Flow](https://reactflow.dev/) + Tailwind CSS | MIT |
| **Infrastructure** | Docker Compose | Apache 2.0 |

## Project Structure

```
chronos/
├── AGENTS.md                          # AIDLC workflow rules
├── PRD.md                             # Product Requirements Document (v2.0)
├── spec.md                            # Technical Specification (v2.0)
├── .env.example                       # Environment template
├── docker-compose.yml                 # Full stack (incl. Langfuse)
├── Dockerfile                         # CHRONOS server image
├── pyproject.toml                     # Python dependencies
│
├── chronos/                           # Python backend
│   ├── main.py                        # FastAPI + OpenLLMetry init
│   ├── config/                        # Settings + LiteLLM config
│   ├── api/                           # REST routes + SSE + A2A
│   ├── agent/                         # LangGraph investigation
│   │   └── nodes/                     # 10 steps (0-9)
│   ├── mcp/                           # MCP client connections
│   ├── ingestion/                     # Event pipelines
│   ├── compliance/                    # W3C PROV-O generator
│   ├── observability/                 # OpenLLMetry + OTel setup
│   ├── notifications/                 # Slack integration
│   ├── enrichment/                    # Graphify context
│   ├── models/                        # Pydantic data models
│   ├── llm/                           # LiteLLM wrapper
│   └── .well-known/                   # A2A Agent Card
│
├── chronos-frontend/                  # React dashboard
│   └── src/
│       ├── pages/                     # Dashboard, IncidentDetail
│       ├── components/                # LineageMap, Timeline, PROV-O DL
│       └── hooks/                     # SSE, API hooks
│
├── tests/
│   ├── test_agent/                    # Agent unit tests
│   └── evals/                         # DeepEval + RAGAs quality tests
│
├── aidlc-docs/                        # AIDLC workflow documentation
├── scripts/                           # Setup & demo scripts
├── sample-dbt-project/                # Demo dbt project
└── .github/workflows/eval.yml         # Quality eval CI
```

## Hackathon

**Event**: [Back to the Metadata Hackathon](https://wemakedevs.org/) — organized by WeMakeDevs x OpenMetadata
**Theme**: "Back to the Metadata" — temporal intelligence in the data pipeline
**Tracks**: T-01 (MCP & AI Agents), T-02 (Data Observability), T-05 (Community), T-06 (Governance)
**Dates**: April 17-26, 2026

## Development Workflow

This project uses the [AI-DLC (AI-Driven Development Life Cycle)](https://github.com/awslabs/aidlc-workflows) methodology:

- **Inception Phase** ✅ — Requirements, user stories, architecture, unit planning
- **Construction Phase** 🔄 — Per-unit functional design + code generation
- **Operations Phase** ⬜ — Deployment, demo scripting, documentation

See [`aidlc-docs/aidlc-state.md`](./aidlc-docs/aidlc-state.md) for current workflow progress.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>Built with ⏳ temporal intelligence for the Back to the Metadata Hackathon — WeMakeDevs x OpenMetadata</strong>
</p>

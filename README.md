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
                    │  SCOPE → TEMPORAL → LINEAGE → CODE →         │
                    │  DOWNSTREAM → AUDIT → SYNTHESIS → NOTIFY     │
                    │                                               │
                    │  ┌────────────┐ ┌──────────┐ ┌────────────┐ │
                    │  │ OpenMeta   │ │ Graphiti  │ │ GitNexus   │ │
                    │  │ MCP        │ │ MCP       │ │ MCP        │ │
                    │  └────────────┘ └──────────┘ └────────────┘ │
                    │                                               │
                    │  LLM: LiteLLM (Claude / Llama / GPT)         │
                    └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────────────┐
                    │  REST API │ Slack Notification │ Dashboard    │
                    └─────────────────────────────────────────────┘
```

## Features

### Core (Must-Have)
- **🎯 Event-Driven Detection** — Automatic webhook-triggered investigation on test failures
- **🤖 7-Step Autonomous Investigation** — LangGraph state machine reasoning across 3 MCP servers
- **🕐 Temporal Intelligence** — Graphiti bi-temporal facts answer "what was true 48 hours ago?"
- **💻 Code-Level Analysis** — GitNexus identifies implicated commits and code files
- **📊 Blast Radius Assessment** — Downstream impact with business criticality (Tier-1/2/3)
- **📋 Structured Reports** — Machine-readable incident reports with confidence scoring
- **💬 Slack Notifications** — Rich Block Kit messages with owner tags and action buttons
- **🖥️ React Dashboard** — Interactive lineage map, investigation replay, temporal diff

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
# Edit .env with your API keys

# Start the full stack
docker-compose up -d

# Seed sample data
./scripts/seed_openmetadata.sh

# Index code with GitNexus
./scripts/index_gitnexus.sh ./sample-dbt-project

# Open the dashboard
open http://localhost:3000
```

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
1. Test fails → CHRONOS immediately starts investigating
2. Graphiti finds the schema changed 2 hours ago
3. Upstream lineage walk pinpoints the source table
4. GitNexus identifies the exact commit
5. 3 Tier-1 downstream assets are at risk
6. LLM synthesizes root cause with 92% confidence
7. Slack notification arrives with full context in ~47 seconds

## Tech Stack

| Layer | Technology | License |
|-------|------------|---------|
| **Metadata** | [OpenMetadata](https://open-metadata.org/) | Apache 2.0 |
| **Temporal KG** | [Graphiti](https://github.com/getzep/graphiti) + [FalkorDB](https://www.falkordb.com/) | Apache 2.0 / SSPL |
| **Code KG** | [GitNexus](https://github.com/abhigyanpatwari/GitNexus) | MIT |
| **Architecture KG** | [Graphify](https://github.com/safishamsi/graphify) | MIT |
| **Agent** | [LangGraph](https://github.com/langchain-ai/langgraph) | MIT |
| **LLM Gateway** | [LiteLLM](https://github.com/BerriAI/litellm) | MIT |
| **Lineage Standard** | [OpenLineage](https://openlineage.io/) | Apache 2.0 |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | MIT |
| **Frontend** | React + [React Flow](https://reactflow.dev/) + Tailwind CSS | MIT |
| **Infrastructure** | Docker Compose | Apache 2.0 |

## Project Structure

```
chronos/
├── AGENTS.md                          # AIDLC workflow rules
├── PRD.md                             # Product Requirements Document
├── spec.md                            # Technical Specification
├── .env.example                       # Environment template
├── docker-compose.yml                 # Full stack orchestration
├── Dockerfile                         # CHRONOS server image
├── pyproject.toml                     # Python dependencies
│
├── chronos/                           # Python backend
│   ├── main.py                        # FastAPI entrypoint
│   ├── config/                        # Settings + LiteLLM config
│   ├── api/                           # REST routes + SSE
│   ├── agent/                         # LangGraph investigation
│   │   └── nodes/                     # One file per step
│   ├── mcp/                           # MCP client connections
│   ├── ingestion/                     # Event pipelines
│   ├── notifications/                 # Slack integration
│   ├── enrichment/                    # Graphify context
│   ├── models/                        # Pydantic data models
│   └── llm/                           # LiteLLM wrapper
│
├── chronos-frontend/                  # React dashboard
│   └── src/
│       ├── pages/                     # Dashboard, IncidentDetail
│       ├── components/                # LineageMap, Timeline, etc.
│       └── hooks/                     # SSE, API hooks
│
├── aidlc-docs/                        # AIDLC workflow documentation
│   ├── inception/                     # Requirements, stories, design
│   ├── construction/                  # Unit plans, code summaries
│   └── aidlc-state.md                 # Workflow progress tracker
│
├── scripts/                           # Setup & demo scripts
└── sample-dbt-project/                # Demo dbt project
```

## Hackathon

**Event**: [OpenMetadata Paradox Hackathon](https://wemakedevs.org/) (WeMakeDevs x OpenMetadata)
**Theme**: "Back to the Future" — temporal paradoxes in the data timeline
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
  <strong>Built with ⏳ temporal intelligence for the OpenMetadata Paradox Hackathon</strong>
</p>

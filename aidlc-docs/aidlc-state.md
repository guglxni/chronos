# AI-DLC Workflow State — CHRONOS

## Project Overview
- **Project**: CHRONOS — Autonomous Data Incident Root Cause Analysis Agent
- **Type**: Greenfield
- **Started**: 2026-04-21
- **Hackathon**: OpenMetadata Paradox Hackathon (WeMakeDevs x OpenMetadata)
- **Deadline**: April 26, 2026

## Current Phase
**INCEPTION** — Planning & Architecture

## Workflow Progress

### INCEPTION PHASE
- [x] Workspace Detection — Greenfield project detected
- [x] Reverse Engineering — SKIPPED (Greenfield)
- [x] Requirements Analysis — Comprehensive depth (PRD.md + spec.md pre-exist)
- [x] User Stories — Generated (3 personas: Priya, Alex, Meera)
- [x] Workflow Planning — Complete with unit decomposition
- [x] Application Design — Complete (triple-graph + LangGraph + FastAPI + React)
- [x] Units Generation — 6 units identified and sequenced

### CONSTRUCTION PHASE
- [ ] Unit 1: Core Infrastructure & Configuration
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 2: MCP Integration Layer & Event Ingestion
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 3: LangGraph Investigation Agent (7-step pipeline)
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 4: Output Layer (Slack + Incident Reports)
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 5: FastAPI REST API & SSE Streaming
  - [ ] Functional Design
  - [ ] Code Generation
- [ ] Unit 6: React Frontend Dashboard
  - [ ] Functional Design
  - [ ] Code Generation
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

## Technology Stack
- **Backend**: Python 3.11+, FastAPI, LangGraph, LiteLLM
- **Frontend**: React + TypeScript, React Flow, Tailwind CSS
- **Data**: Graphiti (FalkorDB), OpenMetadata MCP, GitNexus MCP
- **Infrastructure**: Docker Compose
- **LLM**: LiteLLM → Anthropic Claude / Groq Llama / OpenAI fallback

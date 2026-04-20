# CHRONOS — Application Design

**Depth Level**: Comprehensive

## 1. Architecture Pattern

**Triple-Graph + Event-Driven Agent Architecture with Agentic Observability**

```
┌─────────────────────────────────────────────────┐
│              EVENT INGESTION LAYER               │
│   OpenMetadata Webhooks │ OpenLineage Receiver   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         EVENT ROUTER & DEDUPLICATOR              │
│   Classifies │ Deduplicates │ Queues │ Ingests   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│   INVESTIGATION ORCHESTRATOR (LangGraph)         │
│                                                  │
│  PRIOR_INV → SCOPE → TEMPORAL → LINEAGE →       │
│  CODE → DOWNSTREAM → AUDIT → SYNTHESIS →        │
│  NOTIFY → PERSIST_TRACE                          │
│                                                  │
│  MCP Clients:                                    │
│  ├── OpenMetadata MCP (metadata layer)           │
│  ├── Graphiti MCP (temporal layer)               │
│  └── GitNexus MCP (code layer)                   │
│                                                  │
│  LLM: LiteLLM (synthesis + extraction)           │
│  Callbacks: Langfuse (trace trees)               │
│  Telemetry: OpenLLMetry (OTel GenAI SemConv)     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              OUTPUT LAYER                        │
│  REST API │ Slack │ Graphiti Persist │ PROV-O    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         OBSERVABILITY & COMPLIANCE               │
│  Langfuse Traces │ A2A Agent Card │ DeepEval CI │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              REACT FRONTEND                      │
│  Timeline │ Lineage Map │ Replay │ PROV-O DL    │
└─────────────────────────────────────────────────┘
```

## 2. Component Inventory

| Component | Language | Framework | Port | Purpose |
|-----------|----------|-----------|------|---------|
| chronos-server | Python 3.11+ | FastAPI | 8100 | Core API + agent orchestrator |
| chronos-frontend | TypeScript | React + React Flow | 3000 | Dashboard UI |
| openmetadata | Java | Dropwizard | 8585 | Metadata platform (Docker) |
| graphiti-mcp | Python | Graphiti MCP | 8200 | Temporal KG MCP server |
| falkordb | C | FalkorDB | 6379 | Graph DB (Graphiti backend) |
| gitnexus-mcp | Node.js | GitNexus MCP | stdio | Code graph MCP |
| litellm-proxy | Python | LiteLLM | 4000 | LLM gateway |
| langfuse | TypeScript | Next.js | 3001 | Agentic observability (self-hosted) |
| langfuse-db | — | PostgreSQL 16 | 5433 | Langfuse persistence |

## 3. Data Flow

### Investigation Flow (10 Steps)
1. OpenMetadata fires webhook → FastAPI `/api/v1/webhooks/openmetadata`
2. Event Router classifies event type, deduplicates within window
3. Investigation queued → LangGraph state machine initialized with Langfuse callback
4. **Step 0: Prior Investigations** — query Graphiti for past incidents on same entity
5. Steps 1-7: 7-step investigation pipeline (MCP tool calls + LLM)
6. **Step 8: Notify** — Slack notification sent → SSE broadcast to frontend
7. **Step 9: Persist Trace** — investigation trace persisted as Graphiti episode
8. IncidentReport available via REST API + PROV-O export endpoint

### Ingestion Flow
1. OpenMetadata change events → FastAPI webhook endpoint
2. Events mapped to Graphiti episodes (natural language + JSON)
3. Graphiti extracts entities/facts with bi-temporal metadata
4. Future queries leverage temporal fact history

## 4. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| LangGraph over raw LangChain | Explicit state machine with conditional edges; debuggable investigation flows |
| MCP over direct REST APIs | Protocol standardization; tool-calling pattern matches LangGraph nodes |
| LiteLLM over direct SDK | Multi-provider fallback; cost tracking; model swapping without code changes |
| Graphiti over raw FalkorDB | Bi-temporal fact management; automatic invalidation; episode-based ingestion |
| React Flow over D3 | Purpose-built for node graphs; built-in interactions; React integration |
| FastAPI over Flask | Async Python required for concurrent MCP calls; auto-generated OpenAPI |
| Langfuse over custom observability | Deepest LangGraph integration; self-hostable; combines tracing + eval + prompt mgmt |
| OpenLLMetry over manual OTel | Pure OTel-based; single-line init; leads GenAI SemConv working group |
| PROV-O over custom audit format | W3C Recommendation since 2013; universally understood; JSON-LD interop |
| A2A over custom discovery | Linux Foundation standard; Agent Card spec; future-proof interoperability |
| DeepEval over manual evals | Pytest-compatible; 50+ metrics; G-Eval for custom criteria |
| Self-referential Graphiti over external DB | Zero new infra; uses existing Graphiti; cheapest path to institutional memory |

## 5. Security Model

- **Auth**: OpenMetadata JWT token stored in env vars
- **Internal comms**: LiteLLM master key for proxy auth
- **External**: Slack incoming webhook URL (no tokens exposed)
- **Secrets**: Never in source code; .env template with empty values
- **PROV-O**: Compliance artifacts contain no PII; entity FQNs only
- **A2A**: Agent Card is public; no auth required for discovery
- **Langfuse**: Self-hosted; no data leaves infrastructure; feature-flagged

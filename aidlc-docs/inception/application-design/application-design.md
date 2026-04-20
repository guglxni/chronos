# CHRONOS — Application Design

**Depth Level**: Comprehensive

## 1. Architecture Pattern

**Triple-Graph + Event-Driven Agent Architecture**

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
│        INVESTIGATION ORCHESTRATOR (LangGraph)    │
│                                                  │
│  SCOPE ─> TEMPORAL ─> LINEAGE ─> CODE ─>        │
│  DOWNSTREAM ─> AUDIT ─> SYNTHESIS ─> NOTIFY     │
│                                                  │
│  MCP Clients:                                    │
│  ├── OpenMetadata MCP (metadata layer)           │
│  ├── Graphiti MCP (temporal layer)               │
│  └── GitNexus MCP (code layer)                   │
│                                                  │
│  LLM: LiteLLM (synthesis + extraction)           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              OUTPUT LAYER                        │
│  REST API │ Slack Webhook │ Graphiti Persist     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              REACT FRONTEND                      │
│  Timeline │ Lineage Map │ Investigation Replay   │
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

## 3. Data Flow

### Investigation Flow
1. OpenMetadata fires webhook → FastAPI `/api/v1/webhooks/openmetadata`
2. Event Router classifies event type, deduplicates within window
3. Investigation queued → LangGraph state machine initialized
4. 7-step investigation pipeline executes (MCP tool calls + LLM)
5. IncidentReport produced → persisted to Graphiti as episode
6. Slack notification sent → REST API updated → SSE broadcast to frontend

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

## 5. Security Model

- **Auth**: OpenMetadata JWT token stored in env vars
- **Internal comms**: LiteLLM master key for proxy auth
- **External**: Slack incoming webhook URL (no tokens exposed)
- **Secrets**: Never in source code; .env template with empty values

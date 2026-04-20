# CHRONOS — Technical Specification

**Autonomous Data Incident Root Cause Analysis Agent**
**Version:** 2.0 — Agentic Metadata Infrastructure Edition
**Changelog:** v2.0 adds technical specs for 8 FOSS gap-closing integrations (Langfuse, OpenLLMetry, OTel GenAI, DeepEval, RAGAs, W3C PROV-O, A2A, self-referential memory)

---

## 1. System Architecture Overview

CHRONOS is a Python-based autonomous agent system built as an **agentic metadata infrastructure layer**. It integrates with OpenMetadata, Graphiti, GitNexus, and Graphify via MCP (Model Context Protocol) to perform event-driven root cause analysis of data quality incidents. The system is orchestrated via LangGraph, uses LiteLLM as a unified LLM gateway, emits OpenTelemetry GenAI SemConv traces observable in Langfuse, generates W3C PROV-O compliance artifacts, and learns from its own past investigations via self-referential Graphiti memory.

### 1.1 High-Level Architecture

```
                    ┌──────────────────────────────────────────────────┐
                    │              EVENT INGESTION LAYER                │
                    │                                                  │
                    │  ┌───────────────────┐  ┌─────────────────────┐  │
                    │  │ OpenMetadata       │  │ OpenLineage         │  │
                    │  │ Webhook Listener   │  │ Event Receiver      │  │
                    │  │ (FastAPI endpoint) │  │ (FastAPI endpoint)  │  │
                    │  └────────┬──────────┘  └──────────┬──────────┘  │
                    │           │                        │              │
                    └───────────┼────────────────────────┼──────────────┘
                                │                        │
                    ┌───────────▼────────────────────────▼──────────────┐
                    │           EVENT ROUTER & DEDUPLICATOR              │
                    │   - Event type classification                      │
                    │   - Dedup window (configurable, default 5 min)     │
                    │   - Priority queue for investigation requests      │
                    │   - Episode ingestion into Graphiti                │
                    └───────────────────────┬───────────────────────────┘
                                            │
                    ┌───────────────────────▼───────────────────────────┐
                    │            INVESTIGATION ORCHESTRATOR              │
                    │                  (LangGraph)                       │
                    │                                                    │
                    │   ┌─────────────────────────────────────────┐     │
                    │   │            Agent State Machine           │     │
                    │   │                                         │     │
                    │   │  ┌──────────┐    ┌──────────────────┐  │     │
                    │   │  │  SCOPE   │───▶│  TEMPORAL_DIFF   │  │     │
                    │   │  └──────────┘    └───────┬──────────┘  │     │
                    │   │                          │              │     │
                    │   │                 ┌────────▼─────────┐   │     │
                    │   │                 │  LINEAGE_WALK    │   │     │
                    │   │                 └────────┬─────────┘   │     │
                    │   │                          │              │     │
                    │   │              ┌───────────▼──────────┐  │     │
                    │   │              │  CODE_BLAST_RADIUS   │  │     │
                    │   │              └───────────┬──────────┘  │     │
                    │   │                          │              │     │
                    │   │             ┌────────────▼───────────┐ │     │
                    │   │             │  DOWNSTREAM_IMPACT     │ │     │
                    │   │             └────────────┬───────────┘ │     │
                    │   │                          │              │     │
                    │   │              ┌───────────▼──────────┐  │     │
                    │   │              │  AUDIT_CORRELATION   │  │     │
                    │   │              └───────────┬──────────┘  │     │
                    │   │                          │              │     │
                    │   │               ┌──────────▼─────────┐   │     │
                    │   │               │  RCA_SYNTHESIS     │   │     │
                    │   │               └──────────┬─────────┘   │     │
                    │   │                          │              │     │
                    │   │                ┌─────────▼────────┐    │     │
                    │   │                │     NOTIFY        │    │     │
                    │   │                └──────────────────┘    │     │
                    │   └─────────────────────────────────────────┘     │
                    │                                                    │
                    │   MCP Client Connections:                          │
                    │   ├── OpenMetadata MCP (metadata, lineage, tests)  │
                    │   ├── Graphiti MCP (temporal facts, episodes)      │
                    │   └── GitNexus MCP (code graph, dependencies)      │
                    │                                                    │
                    │   LLM Gateway:                                     │
                    │   └── LiteLLM (model routing, fallback, cost)      │
                    └───────────────────────┬───────────────────────────┘
                                            │
                    ┌───────────────────────▼───────────────────────────┐
                    │              OUTPUT LAYER                          │
                    │                                                    │
                    │  ┌──────────────┐ ┌────────────┐ ┌─────────────┐ │
                    │  │ FastAPI      │ │ Slack      │ │ Graphiti    │ │
                    │  │ REST API     │ │ Webhook    │ │ Episode     │ │
                    │  │ (dashboard)  │ │ (notify)   │ │ (persist)   │ │
                    │  └──────────────┘ └────────────┘ └─────────────┘ │
                    └───────────────────────────────────────────────────┘
                                            │
                    ┌───────────────────────▼───────────────────────────┐
                    │              FRONTEND                              │
                    │                                                    │
                    │  React + React Flow + Tailwind CSS                 │
                    │  ├── Incident Timeline                             │
                    │  ├── Investigation Replay                          │
                    │  ├── Lineage Failure Map (React Flow)              │
                    │  └── Temporal State Diff                           │
                    └───────────────────────────────────────────────────┘
```

### 1.2 Component Inventory

| Component | Language | Framework | Port | Description |
|---|---|---|---|---|
| `chronos-server` | Python 3.11+ | FastAPI | 8100 | Core API server, webhook receiver, investigation orchestrator |
| `chronos-frontend` | TypeScript | React + React Flow | 3000 | Dashboard UI |
| `openmetadata` | Java | Dropwizard | 8585/8586 | OpenMetadata platform (Docker) |
| `graphiti-mcp` | Python | Graphiti MCP Server | 8200 | Temporal KG MCP server |
| `falkordb` | C | FalkorDB | 6379 | Graph database for Graphiti |
| `gitnexus-mcp` | Node.js | GitNexus MCP | stdio | Code knowledge graph MCP |
| `litellm-proxy` | Python | LiteLLM Proxy | 4000 | LLM gateway proxy |
| `langfuse` | TypeScript | Next.js | 3001 | Agentic observability platform (self-hosted) |
| `langfuse-db` | — | PostgreSQL 16 | 5433 | Langfuse persistence layer |

---

## 2. Data Models

### 2.1 Investigation State (LangGraph)

```python
from typing import TypedDict, Optional, Literal
from datetime import datetime
from pydantic import BaseModel

class InvestigationState(TypedDict):
    # Trigger
    incident_id: str
    trigger_event: dict                    # Raw OpenMetadata webhook payload
    triggered_at: datetime

    # Step 0: Prior Investigations (NEW — self-referential memory)
    prior_investigations: Optional[list[dict]]  # Past investigations of same entity
    recurrence_patterns: Optional[list[dict]]   # Pattern matches from Graphiti

    # Step 1: Scope
    failed_test: Optional[dict]            # Test case details from OpenMetadata
    affected_entity_fqn: Optional[str]     # Fully qualified name of affected entity
    affected_columns: Optional[list[str]]  # Specific columns if column-level test
    last_passed_at: Optional[datetime]     # When the test last passed
    failure_history: Optional[list[dict]]  # Recent pass/fail pattern

    # Step 2: Temporal Diff
    temporal_changes: Optional[list[dict]] # Changes from Graphiti within time window
    schema_changes: Optional[list[dict]]   # Filtered schema-specific changes
    entity_version_diff: Optional[dict]    # OpenMetadata version history diff

    # Step 3: Lineage Walk
    upstream_lineage: Optional[list[dict]] # Upstream assets with status
    upstream_failures: Optional[list[dict]]# Upstream tests that also failed
    upstream_changes: Optional[list[dict]] # Upstream entities that changed recently

    # Step 4: Code Blast Radius
    related_code_files: Optional[list[dict]]  # Code files touching this entity
    recent_commits: Optional[list[dict]]      # Git commits on related files
    code_dependencies: Optional[list[dict]]   # GitNexus dependency graph

    # Step 5: Downstream Impact
    downstream_assets: Optional[list[dict]]   # Downstream with tier + ownership
    business_impact_score: Optional[float]     # 0-1 based on tier weights
    affected_owners: Optional[list[dict]]      # Owners to notify

    # Step 6: Audit Correlation
    audit_events: Optional[list[dict]]    # Relevant audit log entries
    suspicious_actions: Optional[list[dict]]  # Flagged unusual actions

    # Step 7: Synthesis
    incident_report: Optional[dict]       # Final structured report
    confidence: Optional[float]           # 0-1 confidence in root cause

    # Step 8: Notify (unchanged)

    # Step 9: Persist Trace (NEW — self-referential memory)
    trace_persisted: Optional[bool]        # Whether investigation was persisted to Graphiti

    # Metadata
    current_step: str                      # Current step name
    step_results: list[dict]               # Log of step outcomes
    errors: list[str]                      # Errors encountered during investigation
    investigation_duration_ms: Optional[int]
```

### 2.2 Incident Report Schema

```python
class EvidenceItem(BaseModel):
    source: Literal["openmetadata", "graphiti", "gitnexus", "graphify", "audit_log"]
    description: str
    raw_data: Optional[dict] = None
    timestamp: Optional[datetime] = None
    confidence: float  # 0-1

class AffectedAsset(BaseModel):
    fqn: str
    asset_type: str                        # table, dashboard, pipeline, ml_model
    tier: Optional[str]                    # Tier1, Tier2, etc.
    owner: Optional[str]
    owner_slack_id: Optional[str]
    relationship: str                      # "direct_downstream", "transitive_downstream"
    hops_from_failure: int

class RemediationStep(BaseModel):
    action: str
    priority: Literal["immediate", "short_term", "long_term"]
    description: str
    assignee_suggestion: Optional[str] = None

class IncidentReport(BaseModel):
    incident_id: str
    detected_at: datetime
    investigation_completed_at: datetime
    investigation_duration_ms: int

    # Failure Details
    affected_entity_fqn: str
    test_name: str
    test_type: str
    failure_message: Optional[str]

    # Root Cause
    probable_root_cause: str               # Natural language description
    root_cause_category: Literal[
        "SCHEMA_CHANGE",
        "CODE_CHANGE",
        "DATA_DRIFT",
        "PIPELINE_FAILURE",
        "PERMISSION_CHANGE",
        "UPSTREAM_FAILURE",
        "CONFIGURATION_CHANGE",
        "UNKNOWN"
    ]
    confidence: float                      # 0-1
    evidence_chain: list[EvidenceItem]

    # Impact
    affected_downstream: list[AffectedAsset]
    business_impact: Literal["critical", "high", "medium", "low"]
    business_impact_reasoning: str

    # Remediation
    recommended_actions: list[RemediationStep]

    # Context
    investigation_timeline: list[dict]     # Step-by-step agent trace
    related_past_incidents: Optional[list[str]]  # From Graphiti pattern matching
    graphify_context: Optional[str]        # Architectural context from Graphify

    # Metadata
    agent_version: str
    llm_model_used: str
    total_mcp_calls: int
    total_llm_tokens: int
```

### 2.3 Graphiti Entity Types (Custom Ontology)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Custom entity types for Graphiti
# These extend Graphiti's built-in entity extraction

class DataAssetEntity(BaseModel):
    """A data asset tracked in OpenMetadata (table, topic, dashboard, etc.)"""
    fqn: str = Field(description="Fully qualified name in OpenMetadata")
    asset_type: str = Field(description="table, topic, dashboard, pipeline, ml_model")
    tier: Optional[str] = Field(default=None, description="Tier classification")
    domain: Optional[str] = Field(default=None, description="Data domain")
    service: Optional[str] = Field(default=None, description="Service name")

class DataTestEntity(BaseModel):
    """A data quality test definition and its results"""
    test_name: str
    test_type: str                         # columnValuesToBeBetween, etc.
    target_entity_fqn: str
    target_column: Optional[str] = None
    last_status: str                       # Passed, Failed, Aborted
    last_run_at: Optional[datetime] = None

class SchemaStateEntity(BaseModel):
    """Snapshot of a table's schema at a point in time"""
    entity_fqn: str
    column_count: int
    column_names: list[str]
    column_types: dict[str, str]           # column_name -> data_type
    captured_at: datetime

class PipelineRunEntity(BaseModel):
    """A pipeline execution event"""
    pipeline_fqn: str
    run_id: str
    status: str                            # Success, Failed, Running
    started_at: datetime
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None

class IncidentEntity(BaseModel):
    """A CHRONOS investigation result"""
    incident_id: str
    root_cause_category: str
    confidence: float
    affected_entity_fqn: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None

# Custom edge types
CHRONOS_EDGE_TYPES = [
    "PRODUCES",          # CodeFile -> DataAsset
    "CONSUMES",          # DataAsset -> DataAsset (lineage)
    "TESTS",             # DataTest -> DataAsset
    "OWNS",              # User -> DataAsset
    "MODIFIED_BY",       # DataAsset -> User (schema change)
    "CAUSED_FAILURE",    # SchemaState/PipelineRun -> Incident
    "DOWNSTREAM_OF",     # DataAsset -> DataAsset
    "SAME_INCIDENT",     # Incident -> Incident (related)
    "RECURRENCE_OF",     # Incident -> Incident (pattern)
]
```

### 2.4 OpenMetadata Webhook Event Schema (Inbound)

```python
# Relevant event types from OpenMetadata webhooks
# Reference: OpenMetadata Event Subscription API

class OpenMetadataWebhookPayload(BaseModel):
    """Simplified representation of OM webhook payload"""
    event_type: str                        # entityCreated, entityUpdated, entityDeleted,
                                           # testCaseResultUpdated, etc.
    entity_type: str                       # table, testCase, pipeline, etc.
    entity_fqn: str                        # Fully qualified name
    entity_id: str                         # UUID
    timestamp: int                         # Unix epoch ms
    change_description: Optional[dict]     # Fields changed
    previous_version: Optional[float]      # Version before change
    current_version: Optional[float]       # Version after change
    user_name: Optional[str]               # Who made the change
```

---

## 3. MCP Integration Layer

### 3.1 MCP Client Configuration

CHRONOS acts as an MCP client connecting to three MCP servers simultaneously. Each server exposes different tools.

```python
# chronos/mcp/config.py

MCP_SERVERS = {
    "openmetadata": {
        "transport": "http",
        "url": "http://localhost:8585/api/v1/mcp",
        "auth": {
            "type": "jwt",
            "token_env": "OPENMETADATA_JWT_TOKEN"
        },
        "tools_used": [
            "search_entities",
            "get_entity_by_fqn",
            "get_lineage",
            "get_entity_version_history",
            "get_test_case_results",
            "get_audit_logs",
            "search_query",
        ]
    },
    "graphiti": {
        "transport": "http",
        "url": "http://localhost:8200/mcp/",
        "tools_used": [
            "add_episode",
            "search_facts",
            "search_nodes",
            "get_episodes",
            "delete_entity_edge",
        ]
    },
    "gitnexus": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "gitnexus@latest", "mcp"],
        "env": {},
        "tools_used": [
            "query_graph",       # Cypher queries on code graph
            "get_node",          # Get specific code entity
            "get_neighbors",     # Get connected code entities
            "shortest_path",     # Find connection between code entities
            "search",            # Semantic search over code graph
        ]
    }
}
```

### 3.2 MCP Tool Call Patterns Per Investigation Step

**Step 1 — SCOPE_FAILURE:**
```python
# OpenMetadata MCP calls
om.get_entity_by_fqn(fqn=affected_entity_fqn, entity_type="table")
om.get_test_case_results(test_case_fqn=test_fqn, limit=20)
```

**Step 2 — TEMPORAL_DIFF:**
```python
# Graphiti MCP calls
graphiti.search_facts(
    query=f"changes to {affected_entity_fqn}",
    group_id="openmetadata-events",
    # Graphiti handles temporal filtering via its bi-temporal model
)

# OpenMetadata MCP calls
om.get_entity_version_history(entity_id=entity_id, entity_type="table")
```

**Step 3 — LINEAGE_WALK:**
```python
# OpenMetadata MCP calls
om.get_lineage(
    fqn=affected_entity_fqn,
    entity_type="table",
    direction="upstream",
    depth=5
)
# For each upstream entity:
om.get_test_case_results(entity_fqn=upstream_fqn)
om.get_entity_version_history(entity_id=upstream_id)
```

**Step 4 — CODE_BLAST_RADIUS:**
```python
# GitNexus MCP calls
gitnexus.search(query=f"references to {table_name}")
gitnexus.get_neighbors(node_id=code_file_id)
gitnexus.query_graph(
    cypher="MATCH (f:File)-[:CALLS|IMPORTS*1..3]->(t) "
           "WHERE f.name CONTAINS $table_name "
           "RETURN f, t",
    params={"table_name": table_name}
)
```

**Step 5 — DOWNSTREAM_IMPACT:**
```python
# OpenMetadata MCP calls
om.get_lineage(
    fqn=affected_entity_fqn,
    entity_type="table",
    direction="downstream",
    depth=3
)
# For each downstream entity:
om.get_entity_by_fqn(fqn=downstream_fqn)  # Get tier + ownership
```

**Step 6 — AUDIT_CORRELATION:**
```python
# OpenMetadata MCP calls
om.get_audit_logs(
    entity_fqn=affected_entity_fqn,
    start_time=investigation_window_start,
    end_time=investigation_window_end
)

# Graphiti MCP calls (cross-reference)
graphiti.search_facts(
    query=f"user actions on {affected_entity_fqn} lineage path"
)
```

**Step 7 — RCA_SYNTHESIS:**
```python
# LiteLLM call (not MCP)
litellm.completion(
    model="anthropic/claude-sonnet-4-20250514",  # or configured model
    messages=[
        {"role": "system", "content": RCA_SYSTEM_PROMPT},
        {"role": "user", "content": synthesis_prompt_with_all_evidence}
    ],
    response_format=IncidentReport  # Structured output
)
```

---

## 4. LangGraph Agent Implementation

### 4.1 State Machine Definition

```python
# chronos/agent/graph.py

from langgraph.graph import StateGraph, END
from langfuse.callback import CallbackHandler
from chronos.agent.state import InvestigationState
from chronos.agent.nodes import (
    check_prior_investigations,   # NEW — Step 0 (self-referential memory)
    scope_failure,
    temporal_diff,
    lineage_walk,
    code_blast_radius,
    downstream_impact,
    audit_correlation,
    rca_synthesis,
    notify,
    persist_investigation_trace,  # NEW — Step 9 (self-referential memory)
)
from chronos.config import settings

def build_investigation_graph(incident_id: str) -> tuple[StateGraph, dict]:
    """Build the LangGraph investigation state machine with Langfuse tracing."""

    graph = StateGraph(InvestigationState)

    # Add nodes (10 total: Step 0 + Steps 1-7 + Step 8 + Step 9)
    graph.add_node("check_prior_investigations", check_prior_investigations)  # Step 0
    graph.add_node("scope_failure", scope_failure)                            # Step 1
    graph.add_node("temporal_diff", temporal_diff)                            # Step 2
    graph.add_node("lineage_walk", lineage_walk)                              # Step 3
    graph.add_node("code_blast_radius", code_blast_radius)                    # Step 4
    graph.add_node("downstream_impact", downstream_impact)                    # Step 5
    graph.add_node("audit_correlation", audit_correlation)                     # Step 6
    graph.add_node("rca_synthesis", rca_synthesis)                             # Step 7
    graph.add_node("notify", notify)                                          # Step 8
    graph.add_node("persist_investigation_trace", persist_investigation_trace) # Step 9

    # Define edges (entry -> Step 0 -> Steps 1-8 -> Step 9 -> END)
    graph.set_entry_point("check_prior_investigations")

    graph.add_edge("check_prior_investigations", "scope_failure")
    graph.add_edge("scope_failure", "temporal_diff")
    graph.add_edge("temporal_diff", "lineage_walk")
    graph.add_edge("lineage_walk", "code_blast_radius")
    graph.add_conditional_edges(
        "code_blast_radius",
        should_check_code,
        {
            True: "downstream_impact",
            False: "downstream_impact",   # Always proceed but may skip code analysis
        }
    )
    graph.add_edge("downstream_impact", "audit_correlation")
    graph.add_edge("audit_correlation", "rca_synthesis")
    graph.add_edge("rca_synthesis", "notify")
    graph.add_edge("notify", "persist_investigation_trace")
    graph.add_edge("persist_investigation_trace", END)

    compiled = graph.compile()

    # Langfuse callback for automatic trace capture (optional — feature-flagged)
    config = {}
    if settings.LANGFUSE_ENABLED:
        langfuse_handler = CallbackHandler(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
            session_id=incident_id,
            user_id="chronos-agent",
            tags=["chronos", "rca", settings.ENVIRONMENT],
            metadata={
                "agent_version": settings.VERSION,
                "trigger": "openmetadata_webhook",
            },
        )
        config = {"callbacks": [langfuse_handler]}

    return compiled, config


def should_check_code(state: InvestigationState) -> bool:
    """Determine if code blast radius analysis found relevant results."""
    return len(state.get("related_code_files", [])) > 0
```

### 4.2 Node Implementations (Pseudocode)

```python
# chronos/agent/nodes/scope_failure.py

async def scope_failure(state: InvestigationState) -> dict:
    """Step 1: Scope the failure — gather test and entity details."""

    mcp = get_openmetadata_mcp_client()

    # Get failed test details
    test_event = state["trigger_event"]
    test_fqn = test_event["entity_fqn"]

    test_details = await mcp.call_tool(
        "get_entity_by_fqn",
        {"fqn": test_fqn, "entity_type": "testCase"}
    )

    # Get recent test results (last 20 runs)
    test_results = await mcp.call_tool(
        "get_test_case_results",
        {"test_case_fqn": test_fqn, "limit": 20}
    )

    # Extract affected entity
    affected_entity_fqn = test_details["entityLink"]
    affected_columns = extract_columns_from_test(test_details)

    # Find last passing result
    last_passed = find_last_passed(test_results)

    return {
        "failed_test": test_details,
        "affected_entity_fqn": affected_entity_fqn,
        "affected_columns": affected_columns,
        "last_passed_at": last_passed["timestamp"] if last_passed else None,
        "failure_history": test_results,
        "current_step": "scope_failure",
        "step_results": state["step_results"] + [{
            "step": "scope_failure",
            "completed_at": datetime.utcnow().isoformat(),
            "summary": f"Test {test_fqn} failed on {affected_entity_fqn}. "
                       f"Last passed: {last_passed['timestamp'] if last_passed else 'never'}"
        }]
    }
```

```python
# chronos/agent/nodes/temporal_diff.py

async def temporal_diff(state: InvestigationState) -> dict:
    """Step 2: Query Graphiti for temporal changes in the investigation window."""

    graphiti_mcp = get_graphiti_mcp_client()
    om_mcp = get_openmetadata_mcp_client()

    entity_fqn = state["affected_entity_fqn"]
    window_start = state["last_passed_at"] or (
        datetime.utcnow() - timedelta(hours=72)
    )

    # Query Graphiti for all facts about this entity that changed
    temporal_facts = await graphiti_mcp.call_tool(
        "search_facts",
        {
            "query": f"changes modifications schema updates on {entity_fqn}",
            "group_id": "chronos-metadata-events",
        }
    )

    # Also get OpenMetadata version history for structured diff
    entity_details = await om_mcp.call_tool(
        "get_entity_by_fqn",
        {"fqn": entity_fqn, "entity_type": "table", "fields": "all"}
    )

    version_history = await om_mcp.call_tool(
        "get_entity_version_history",
        {"entity_id": entity_details["id"], "entity_type": "table"}
    )

    # Diff versions within the investigation window
    version_diff = compute_version_diff(
        version_history,
        since=window_start
    )

    # Filter for schema-specific changes
    schema_changes = [
        change for change in version_diff
        if change["field_name"] in (
            "columns", "dataModel", "tableConstraints", "tableType"
        )
    ]

    return {
        "temporal_changes": temporal_facts,
        "schema_changes": schema_changes,
        "entity_version_diff": version_diff,
        "current_step": "temporal_diff",
        "step_results": state["step_results"] + [{
            "step": "temporal_diff",
            "completed_at": datetime.utcnow().isoformat(),
            "summary": f"Found {len(temporal_facts)} temporal changes. "
                       f"{len(schema_changes)} schema changes in window."
        }]
    }
```

### 4.3 RCA Synthesis Prompt

```python
# chronos/agent/nodes/rca_synthesis.py

RCA_SYSTEM_PROMPT = """You are CHRONOS, an autonomous data incident root cause analysis agent.
You have investigated a data quality test failure by examining three knowledge graphs:
1. OpenMetadata (metadata, lineage, test results, ownership)
2. Graphiti (temporal changes, fact history with validity windows)
3. GitNexus (code structure, file dependencies, recent commits)

Based on ALL the evidence gathered, produce a structured root cause analysis.

RULES:
- Be specific. Cite exact entity FQNs, column names, timestamps, commit hashes.
- State confidence honestly. If evidence is inconclusive, say so.
- Distinguish correlation from causation. A change happening before a failure
  does not prove it caused the failure.
- Rank remediation actions by priority: immediate (stop the bleeding),
  short_term (fix the root cause), long_term (prevent recurrence).
- Include all affected downstream assets with their tier classification.
- If you detect a pattern matching previous incidents (from Graphiti),
  mention it explicitly.

OUTPUT FORMAT: Respond with valid JSON matching the IncidentReport schema.
Do not include markdown formatting, backticks, or preamble."""

async def rca_synthesis(state: InvestigationState) -> dict:
    """Step 7: Synthesize all evidence into a root cause analysis."""

    synthesis_context = compile_evidence(state)

    response = await litellm.acompletion(
        model=config.SYNTHESIS_MODEL,     # e.g. "anthropic/claude-sonnet-4-20250514"
        messages=[
            {"role": "system", "content": RCA_SYSTEM_PROMPT},
            {"role": "user", "content": synthesis_context}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,                  # Low temperature for factual synthesis
        max_tokens=4000,
    )

    report_data = json.loads(response.choices[0].message.content)
    report = IncidentReport(**report_data)

    # Persist incident to Graphiti as an episode for future pattern matching
    graphiti_mcp = get_graphiti_mcp_client()
    await graphiti_mcp.call_tool(
        "add_episode",
        {
            "name": f"incident-{report.incident_id}",
            "episode_body": json.dumps(report.model_dump(), default=str),
            "source_description": "CHRONOS RCA Agent",
            "group_id": "chronos-incidents",
        }
    )

    return {
        "incident_report": report.model_dump(),
        "confidence": report.confidence,
        "current_step": "rca_synthesis",
        "step_results": state["step_results"] + [{
            "step": "rca_synthesis",
            "completed_at": datetime.utcnow().isoformat(),
            "summary": f"Root cause: {report.root_cause_category} "
                       f"(confidence: {report.confidence:.0%}). "
                       f"{len(report.affected_downstream)} downstream assets affected."
        }]
    }
```

---

## 5. LiteLLM Configuration

### 5.1 Model Routing Strategy

```yaml
# chronos/config/litellm_config.yaml

model_list:
  # Primary synthesis model (strong reasoning)
  - model_name: "chronos-synthesis"
    litellm_params:
      model: "anthropic/claude-sonnet-4-20250514"
      api_key: "os.environ/ANTHROPIC_API_KEY"
      max_tokens: 4000
      temperature: 0.1

  # Fast extraction model (entity extraction for Graphiti, code analysis)
  - model_name: "chronos-extraction"
    litellm_params:
      model: "groq/llama-3.3-70b-versatile"
      api_key: "os.environ/GROQ_API_KEY"
      max_tokens: 2000
      temperature: 0.0

  # Fallback model
  - model_name: "chronos-synthesis"
    litellm_params:
      model: "openai/gpt-4.1-mini"
      api_key: "os.environ/OPENAI_API_KEY"
      max_tokens: 4000
      temperature: 0.1

router_settings:
  routing_strategy: "simple-shuffle"     # Try primary first, fallback on failure
  num_retries: 2
  timeout: 60
  allowed_fails: 1

litellm_settings:
  drop_params: true
  set_verbose: false
  cache: true
  cache_params:
    type: "local"
    ttl: 300                             # Cache LLM responses for 5 min (dedup)

general_settings:
  master_key: "os.environ/LITELLM_MASTER_KEY"
```

### 5.2 LiteLLM Integration in CHRONOS

```python
# chronos/llm/client.py

import litellm
from chronos.config import settings

# Configure LiteLLM
litellm.set_verbose = settings.DEBUG
litellm.drop_params = True

# Model aliases
SYNTHESIS_MODEL = "chronos-synthesis"     # Strong reasoning for RCA
EXTRACTION_MODEL = "chronos-extraction"   # Fast extraction for Graphiti episodes

async def synthesize(prompt: str, system_prompt: str) -> str:
    """Use the synthesis model for root cause analysis."""
    response = await litellm.acompletion(
        model=SYNTHESIS_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return response.choices[0].message.content

async def extract(prompt: str) -> str:
    """Use the fast extraction model for entity/fact extraction."""
    response = await litellm.acompletion(
        model=EXTRACTION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return response.choices[0].message.content

def get_cost_tracker() -> dict:
    """Return LiteLLM cost tracking data for the incident report."""
    return {
        "total_tokens": litellm._current_cost.get("total_tokens", 0),
        "total_cost_usd": litellm._current_cost.get("total_cost", 0.0),
    }
```

---

## 6. Graphiti Integration

### 6.1 Episode Ingestion Pipeline

```python
# chronos/ingestion/graphiti_ingestor.py

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

class OpenMetadataEventIngestor:
    """Ingests OpenMetadata events into Graphiti as episodes."""

    def __init__(self, graphiti_client: Graphiti):
        self.graphiti = graphiti_client
        self.group_id = "chronos-metadata-events"

    async def ingest_event(self, event: OpenMetadataWebhookPayload):
        """Convert an OpenMetadata webhook event to a Graphiti episode."""

        episode_body = self._format_episode_body(event)

        await self.graphiti.add_episode(
            name=f"om-{event.event_type}-{event.entity_fqn}-{event.timestamp}",
            episode_body=episode_body,
            source=EpisodeType.json,
            source_description=f"OpenMetadata {event.event_type}",
            group_id=self.group_id,
            reference_time=datetime.fromtimestamp(event.timestamp / 1000),
        )

    def _format_episode_body(self, event: OpenMetadataWebhookPayload) -> str:
        """Structure the event as a natural language + JSON episode."""

        # Graphiti's LLM extraction works better with natural language
        nl_description = (
            f"At {datetime.fromtimestamp(event.timestamp / 1000).isoformat()}, "
            f"user '{event.user_name or 'system'}' performed '{event.event_type}' "
            f"on {event.entity_type} '{event.entity_fqn}'. "
        )

        if event.change_description:
            fields_changed = event.change_description.get("fieldsChanged", [])
            fields_added = event.change_description.get("fieldsAdded", [])
            fields_deleted = event.change_description.get("fieldsDeleted", [])

            if fields_changed:
                names = [f["name"] for f in fields_changed]
                nl_description += f"Fields changed: {', '.join(names)}. "
            if fields_added:
                names = [f["name"] for f in fields_added]
                nl_description += f"Fields added: {', '.join(names)}. "
            if fields_deleted:
                names = [f["name"] for f in fields_deleted]
                nl_description += f"Fields deleted: {', '.join(names)}. "

        return json.dumps({
            "description": nl_description,
            "event": event.model_dump(),
        })
```

### 6.2 Graphiti MCP Server Docker Configuration

```yaml
# Part of docker-compose.yml

  graphiti-mcp:
    build:
      context: ./graphiti/mcp_server
      dockerfile: Dockerfile
    ports:
      - "8200:8000"
    environment:
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}     # For entity extraction
      - MODEL_NAME=gpt-4.1-mini             # Fast model for extraction
      - TRANSPORT=http
    depends_on:
      - falkordb

  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
      - "3000:3000"                          # FalkorDB browser UI
    volumes:
      - falkordb_data:/data
```

---

## 7. GitNexus Integration

### 7.1 Repository Indexing

```bash
#!/bin/bash
# chronos/scripts/index_codebase.sh

# Index the dbt project / data platform repo
# Run once during setup, then incrementally on git hooks

REPO_PATH="${1:-./sample-dbt-project}"

echo "Indexing repository at $REPO_PATH with GitNexus..."

# Install GitNexus globally if not present
npm install -g gitnexus@latest 2>/dev/null || true

# Index the repository
cd "$REPO_PATH"
npx gitnexus@latest index .

echo "GitNexus index stored at $REPO_PATH/.gitnexus/"
echo "Graph available for MCP queries."
```

### 7.2 GitNexus MCP Tool Usage

```python
# chronos/agent/nodes/code_blast_radius.py

async def code_blast_radius(state: InvestigationState) -> dict:
    """Step 4: Query GitNexus for code-level dependencies and recent changes."""

    gitnexus_mcp = get_gitnexus_mcp_client()
    entity_fqn = state["affected_entity_fqn"]

    # Extract table name from FQN for code search
    table_name = entity_fqn.split(".")[-1]  # e.g., "orders" from "db.schema.orders"

    # Search code graph for references to this table
    code_refs = await gitnexus_mcp.call_tool(
        "search",
        {"query": f"references to {table_name} table model"}
    )

    related_files = []
    recent_commits = []

    for ref in code_refs.get("results", []):
        file_path = ref.get("file_path", "")
        related_files.append(ref)

        # Get neighbors (other files that depend on or are depended by this file)
        neighbors = await gitnexus_mcp.call_tool(
            "get_neighbors",
            {"node_id": ref.get("node_id")}
        )
        related_files.extend(neighbors.get("results", []))

    # Cross-reference with git log for recent changes
    # (This uses subprocess, not MCP — GitNexus doesn't expose git history)
    if related_files:
        file_paths = [f["file_path"] for f in related_files if "file_path" in f]
        recent_commits = await get_recent_git_commits(
            file_paths=file_paths,
            since=state.get("last_passed_at"),
        )

    # Deduplicate files
    seen = set()
    unique_files = []
    for f in related_files:
        key = f.get("file_path", f.get("node_id", ""))
        if key not in seen:
            seen.add(key)
            unique_files.append(f)

    return {
        "related_code_files": unique_files,
        "recent_commits": recent_commits,
        "code_dependencies": code_refs.get("results", []),
        "current_step": "code_blast_radius",
        "step_results": state["step_results"] + [{
            "step": "code_blast_radius",
            "completed_at": datetime.utcnow().isoformat(),
            "summary": f"Found {len(unique_files)} related code files. "
                       f"{len(recent_commits)} recent commits in investigation window."
        }]
    }


async def get_recent_git_commits(
    file_paths: list[str],
    since: Optional[datetime] = None,
    repo_path: str = "./sample-dbt-project",
) -> list[dict]:
    """Get recent git commits for specific files."""

    since_str = since.strftime("%Y-%m-%d") if since else "7 days ago"

    cmd = [
        "git", "-C", repo_path, "log",
        f"--since={since_str}",
        "--pretty=format:%H|%an|%ae|%aI|%s",
        "--", *file_paths
    ]

    result = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await result.communicate()

    commits = []
    for line in stdout.decode().strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) == 5:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })

    return commits
```

---

## 8. Graphify Integration

### 8.1 Architecture Context Enrichment

```python
# chronos/enrichment/graphify_context.py

import json
from pathlib import Path

class GraphifyContextProvider:
    """Provides architectural context from Graphify's knowledge graph."""

    def __init__(self, graphify_output_dir: str = "./graphify-out"):
        self.output_dir = Path(graphify_output_dir)
        self.graph_report = self._load_report()
        self.graph_data = self._load_graph()

    def _load_report(self) -> Optional[str]:
        report_path = self.output_dir / "GRAPH_REPORT.md"
        if report_path.exists():
            return report_path.read_text()
        return None

    def _load_graph(self) -> Optional[dict]:
        graph_path = self.output_dir / "graph.json"
        if graph_path.exists():
            return json.loads(graph_path.read_text())
        return None

    def get_context_for_entity(self, entity_name: str) -> Optional[str]:
        """Find architectural context for a given entity in the Graphify graph."""
        if not self.graph_data:
            return None

        # Search nodes for references to the entity
        relevant_nodes = []
        for node in self.graph_data.get("nodes", []):
            if entity_name.lower() in node.get("label", "").lower():
                relevant_nodes.append(node)
                # Get community membership
                community_id = node.get("community")
                if community_id is not None:
                    community_nodes = [
                        n for n in self.graph_data["nodes"]
                        if n.get("community") == community_id
                    ]
                    node["community_context"] = {
                        "community_id": community_id,
                        "community_size": len(community_nodes),
                        "community_members": [
                            n["label"] for n in community_nodes[:10]
                        ]
                    }

        if not relevant_nodes:
            return None

        context = f"Graphify architectural context for '{entity_name}':\n"
        for node in relevant_nodes:
            context += f"- File: {node.get('label', 'unknown')}\n"
            context += f"  Provenance: {node.get('provenance', 'unknown')}\n"
            if "community_context" in node:
                cc = node["community_context"]
                context += f"  Community: #{cc['community_id']} ({cc['community_size']} members)\n"
                context += f"  Related: {', '.join(cc['community_members'][:5])}\n"

        return context

    def get_report_summary(self) -> Optional[str]:
        """Return a compressed version of GRAPH_REPORT.md for LLM context."""
        if not self.graph_report:
            return None
        # Truncate to first 2000 chars to fit in synthesis prompt
        return self.graph_report[:2000]
```

### 8.2 Graphify Indexing (Setup Script)

```bash
#!/bin/bash
# chronos/scripts/index_graphify.sh

REPO_PATH="${1:-./sample-dbt-project}"

echo "Building Graphify knowledge graph for $REPO_PATH..."

pip install graphifyy --break-system-packages 2>/dev/null || true

cd "$REPO_PATH"

# Run Graphify in standard mode
graphify . --no-viz

echo "Graphify output at $REPO_PATH/graphify-out/"
echo "  - graph.json: Structural graph"
echo "  - GRAPH_REPORT.md: Architecture report"
echo "  - graph.html: Interactive visualization"
```

---

## 9. OpenLineage Integration

### 9.1 Event Receiver

```python
# chronos/ingestion/openlineage_receiver.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/lineage", tags=["openlineage"])

class OpenLineageRunEvent(BaseModel):
    """Simplified OpenLineage RunEvent schema."""
    eventType: str            # START, RUNNING, COMPLETE, FAIL, ABORT
    eventTime: str            # ISO 8601
    run: dict                 # {runId, facets}
    job: dict                 # {namespace, name, facets}
    inputs: list[dict]        # [{namespace, name, facets}]
    outputs: list[dict]       # [{namespace, name, facets}]
    producer: Optional[str] = None

@router.post("/events")
async def receive_openlineage_event(event: OpenLineageRunEvent):
    """Receive OpenLineage events from pipeline orchestrators.

    These events are:
    1. Forwarded to OpenMetadata's OpenLineage ingestion endpoint
    2. Ingested into Graphiti as episodes for temporal tracking
    """

    # Forward to OpenMetadata (which natively accepts OpenLineage as of 1.12)
    await forward_to_openmetadata(event)

    # Also ingest into Graphiti for temporal correlation
    await ingest_openlineage_to_graphiti(event)

    return {"status": "accepted", "event_type": event.eventType}


async def ingest_openlineage_to_graphiti(event: OpenLineageRunEvent):
    """Convert OpenLineage event to Graphiti episode."""

    description = (
        f"Pipeline '{event.job['name']}' in namespace '{event.job['namespace']}' "
        f"{event.eventType.lower()} at {event.eventTime}. "
    )

    if event.eventType == "FAIL":
        error_facet = event.run.get("facets", {}).get("errorMessage", {})
        if error_facet:
            description += f"Error: {error_facet.get('message', 'unknown')}. "

    if event.inputs:
        input_names = [i["name"] for i in event.inputs]
        description += f"Inputs: {', '.join(input_names)}. "

    if event.outputs:
        output_names = [o["name"] for o in event.outputs]
        description += f"Outputs: {', '.join(output_names)}. "

    graphiti_mcp = get_graphiti_mcp_client()
    await graphiti_mcp.call_tool(
        "add_episode",
        {
            "name": f"ol-{event.job['name']}-{event.eventType}-{event.eventTime}",
            "episode_body": json.dumps({
                "description": description,
                "event": event.model_dump(),
            }),
            "source_description": f"OpenLineage {event.producer or 'unknown'}",
            "group_id": "chronos-pipeline-events",
        }
    )
```

---

## 10. Slack Notification

### 10.1 Block Kit Message Builder

```python
# chronos/notifications/slack.py

import httpx
from chronos.models import IncidentReport

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

CATEGORY_EMOJI = {
    "SCHEMA_CHANGE": "🔧",
    "CODE_CHANGE": "💻",
    "DATA_DRIFT": "📊",
    "PIPELINE_FAILURE": "⚙️",
    "PERMISSION_CHANGE": "🔐",
    "UPSTREAM_FAILURE": "⬆️",
    "CONFIGURATION_CHANGE": "⚙️",
    "UNKNOWN": "❓",
}

def build_slack_blocks(report: IncidentReport) -> list[dict]:
    """Build Slack Block Kit message from incident report."""

    severity_emoji = SEVERITY_EMOJI.get(report.business_impact, "⚪")
    category_emoji = CATEGORY_EMOJI.get(report.root_cause_category, "❓")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji} CHRONOS Incident Report"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Incident:*\n`{report.incident_id}`"},
                {"type": "mrkdwn", "text": f"*Detected:*\n{report.detected_at.strftime('%H:%M UTC %b %d')}"},
                {"type": "mrkdwn", "text": f"*Severity:*\n{report.business_impact.upper()}"},
                {"type": "mrkdwn", "text": f"*Confidence:*\n{report.confidence:.0%}"},
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{category_emoji} Root Cause: {report.root_cause_category}*\n"
                    f"{report.probable_root_cause}"
                )
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Failed Test:* `{report.test_name}` on `{report.affected_entity_fqn}`\n"
                    f"*Investigation Duration:* {report.investigation_duration_ms}ms"
                )
            }
        },
    ]

    # Affected downstream assets
    if report.affected_downstream:
        tier1_assets = [a for a in report.affected_downstream if a.tier == "Tier1"]
        total = len(report.affected_downstream)

        downstream_text = f"*Blast Radius:* {total} downstream assets affected"
        if tier1_assets:
            downstream_text += f" ({len(tier1_assets)} Tier-1 critical)"
            for asset in tier1_assets[:3]:
                downstream_text += f"\n  • `{asset.fqn}` (owner: {asset.owner or 'unassigned'})"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": downstream_text}
        })

    # Remediation actions
    if report.recommended_actions:
        immediate = [a for a in report.recommended_actions if a.priority == "immediate"]
        if immediate:
            actions_text = "*Recommended Actions:*\n"
            for action in immediate[:3]:
                actions_text += f"  → {action.description}\n"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": actions_text}
            })

    # Action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View in CHRONOS"},
                "url": f"http://localhost:3000/incidents/{report.incident_id}",
                "style": "primary"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View in OpenMetadata"},
                "url": f"http://localhost:8585/table/{report.affected_entity_fqn}",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Acknowledge"},
                "action_id": f"ack_{report.incident_id}",
            }
        ]
    })

    return blocks


async def send_slack_notification(
    report: IncidentReport,
    webhook_url: str,
    channel: Optional[str] = None,
):
    """Send incident report to Slack via webhook."""

    blocks = build_slack_blocks(report)

    # Build owner mention string
    owner_mentions = []
    for asset in report.affected_downstream:
        if asset.owner_slack_id:
            owner_mentions.append(f"<@{asset.owner_slack_id}>")
    owner_mentions = list(set(owner_mentions))

    fallback_text = (
        f"CHRONOS: {report.root_cause_category} detected on "
        f"{report.affected_entity_fqn} "
        f"({report.business_impact.upper()} severity, "
        f"{report.confidence:.0%} confidence)"
    )

    if owner_mentions:
        fallback_text += f"\ncc: {' '.join(owner_mentions[:5])}"

    payload = {
        "text": fallback_text,
        "blocks": blocks,
    }
    if channel:
        payload["channel"] = channel

    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()
```

---

## 11. Frontend Specification

### 11.1 Pages & Components

```
chronos-frontend/
├── src/
│   ├── App.tsx                     # Router setup
│   ├── pages/
│   │   ├── Dashboard.tsx           # Incident timeline + summary stats
│   │   ├── IncidentDetail.tsx      # Single incident investigation replay
│   │   └── Settings.tsx            # Configuration (Slack, LLM, thresholds)
│   ├── components/
│   │   ├── IncidentTimeline.tsx     # Chronological incident list
│   │   ├── IncidentCard.tsx         # Summary card per incident
│   │   ├── LineageFailureMap.tsx    # React Flow lineage visualization
│   │   ├── InvestigationReplay.tsx  # Step-by-step investigation timeline
│   │   ├── TemporalDiff.tsx         # Side-by-side state comparison
│   │   ├── EvidenceChain.tsx        # Evidence items with source attribution
│   │   ├── BlastRadiusPanel.tsx     # Downstream impact summary
│   │   └── SeverityBadge.tsx        # Severity indicator component
│   ├── hooks/
│   │   ├── useIncidents.ts          # Fetch incidents from CHRONOS API
│   │   ├── useIncidentDetail.ts     # Fetch single incident
│   │   └── useWebSocket.ts          # Live investigation updates
│   └── lib/
│       ├── api.ts                   # API client
│       └── types.ts                 # TypeScript types matching backend models
```

### 11.2 Lineage Failure Map (React Flow)

```typescript
// chronos-frontend/src/components/LineageFailureMap.tsx

import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
} from 'reactflow';

type AssetStatus = 'failing' | 'at_risk' | 'healthy' | 'unknown';

interface LineageNode {
  fqn: string;
  name: string;
  type: string;          // table, dashboard, pipeline, ml_model
  tier?: string;
  owner?: string;
  status: AssetStatus;
  testResults?: { passed: number; failed: number; };
}

const STATUS_COLORS: Record<AssetStatus, string> = {
  failing:  '#EF4444',   // red-500
  at_risk:  '#F59E0B',   // amber-500
  healthy:  '#10B981',   // emerald-500
  unknown:  '#6B7280',   // gray-500
};

function buildReactFlowGraph(
  upstream: LineageNode[],
  affected: LineageNode,
  downstream: LineageNode[],
  rootCauseEntityFqn?: string,
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Position upstream nodes on the left
  upstream.forEach((asset, i) => {
    const isRootCause = asset.fqn === rootCauseEntityFqn;
    nodes.push({
      id: asset.fqn,
      position: { x: 100, y: i * 120 },
      data: {
        label: asset.name,
        tier: asset.tier,
        status: asset.status,
        isRootCause,
      },
      style: {
        border: `3px solid ${STATUS_COLORS[asset.status]}`,
        borderRadius: '12px',
        padding: '16px',
        background: isRootCause ? '#FEF3C7' : '#1F2937',
        color: isRootCause ? '#1F2937' : '#F9FAFB',
        fontWeight: isRootCause ? 'bold' : 'normal',
      },
    });
  });

  // Affected node in the center
  nodes.push({
    id: affected.fqn,
    position: { x: 400, y: (upstream.length * 120) / 2 },
    data: { label: `⚠️ ${affected.name}`, status: 'failing' },
    style: {
      border: `4px solid ${STATUS_COLORS.failing}`,
      borderRadius: '12px',
      padding: '16px',
      background: '#7F1D1D',
      color: '#FCA5A5',
      fontWeight: 'bold',
      fontSize: '14px',
    },
  });

  // Downstream nodes on the right
  downstream.forEach((asset, i) => {
    nodes.push({
      id: asset.fqn,
      position: { x: 700, y: i * 120 },
      data: { label: asset.name, tier: asset.tier, status: asset.status },
      style: {
        border: `3px solid ${STATUS_COLORS[asset.status]}`,
        borderRadius: '12px',
        padding: '16px',
        background: '#1F2937',
        color: '#F9FAFB',
      },
    });
  });

  // Build edges (simplified; real implementation uses lineage data)
  upstream.forEach((asset) => {
    edges.push({
      id: `${asset.fqn}->${affected.fqn}`,
      source: asset.fqn,
      target: affected.fqn,
      animated: asset.status === 'failing',
      style: {
        stroke: asset.fqn === rootCauseEntityFqn ? '#EF4444' : '#6B7280',
        strokeWidth: asset.fqn === rootCauseEntityFqn ? 3 : 1,
      },
    });
  });

  downstream.forEach((asset) => {
    edges.push({
      id: `${affected.fqn}->${asset.fqn}`,
      source: affected.fqn,
      target: asset.fqn,
      animated: true,
      style: { stroke: '#F59E0B', strokeWidth: 2 },
    });
  });

  return { nodes, edges };
}
```

---

## 12. Docker Compose (Full Stack)

```yaml
# docker-compose.yml

version: "3.9"

services:
  # ─── OpenMetadata ───
  openmetadata-server:
    image: openmetadata/server:1.12.4
    ports:
      - "8585:8585"
      - "8586:8586"
    environment:
      - OPENMETADATA_CLUSTER_NAME=chronos-demo
      - SERVER_HOST_API_URL=http://localhost:8585/api
      - DB_HOST=openmetadata-db
      - DB_PORT=3306
      - DB_USER=openmetadata_user
      - DB_USER_PASSWORD=openmetadata_password
      - DB_SCHEME=mysql
      - SEARCH_TYPE=elasticsearch
      - ELASTICSEARCH_HOST=elasticsearch
    depends_on:
      openmetadata-db:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy

  openmetadata-db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=openmetadata_db
      - MYSQL_USER=openmetadata_user
      - MYSQL_PASSWORD=openmetadata_password
    volumes:
      - om_mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    volumes:
      - om_es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Graphiti + FalkorDB ───
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
      - "3001:3000"          # FalkorDB browser (avoid conflict with frontend)
    volumes:
      - falkordb_data:/data

  graphiti-mcp:
    build:
      context: ./services/graphiti-mcp
      dockerfile: Dockerfile
    ports:
      - "8200:8000"
    environment:
      - DATABASE_PROVIDER=falkordb
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MODEL_NAME=gpt-4.1-mini
      - TRANSPORT=http
    depends_on:
      - falkordb

  # ─── LiteLLM Proxy ───
  litellm-proxy:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "4000:4000"
    volumes:
      - ./config/litellm_config.yaml:/app/config.yaml
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    command: ["--config", "/app/config.yaml", "--port", "4000"]

  # ─── CHRONOS Core ───
  chronos-server:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8100:8100"
    environment:
      - OPENMETADATA_HOST=http://openmetadata-server:8585
      - OPENMETADATA_JWT_TOKEN=${OPENMETADATA_JWT_TOKEN}
      - GRAPHITI_MCP_URL=http://graphiti-mcp:8000/mcp/
      - LITELLM_BASE_URL=http://litellm-proxy:4000
      - LITELLM_API_KEY=${LITELLM_MASTER_KEY}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - GITNEXUS_REPO_PATH=/data/sample-dbt-project
      - GRAPHIFY_OUTPUT_DIR=/data/sample-dbt-project/graphify-out
    volumes:
      - ./sample-dbt-project:/data/sample-dbt-project
    depends_on:
      - openmetadata-server
      - graphiti-mcp
      - litellm-proxy

  # ─── CHRONOS Frontend ───
  chronos-frontend:
    build:
      context: ./chronos-frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8100
    depends_on:
      - chronos-server

volumes:
  om_mysql_data:
  om_es_data:
  falkordb_data:
```

---

## 13. API Specification (CHRONOS Server)

### 13.1 REST Endpoints

```
POST   /api/v1/webhooks/openmetadata     # Receive OM webhook events
POST   /api/v1/webhooks/openlineage      # Receive OpenLineage events

GET    /api/v1/incidents                  # List incidents (paginated, filterable)
GET    /api/v1/incidents/{id}             # Get incident detail + investigation trace
POST   /api/v1/incidents/{id}/acknowledge # Acknowledge incident
POST   /api/v1/incidents/{id}/resolve     # Mark incident resolved

GET    /api/v1/incidents/{id}/provenance.jsonld    # W3C PROV-O export (JSON-LD)
GET    /api/v1/incidents/{id}/provenance.ttl       # W3C PROV-O export (Turtle)
GET    /api/v1/incidents/{id}/provenance.provn     # W3C PROV-O export (PROV-N)

GET    /api/v1/investigations/{id}/stream # SSE stream for live investigation updates

POST   /api/v1/investigate               # Manually trigger investigation
       Body: {"entity_fqn": "...", "test_name": "..."}

GET    /api/v1/stats                     # Dashboard stats (incident count, MTTR, etc.)
GET    /api/v1/stats/patterns            # Recurring incident patterns from Graphiti

GET    /api/v1/health                    # Health check (all service dependencies)
GET    /.well-known/agent-card.json      # A2A Agent Card (agent discovery)
```

### 13.2 WebSocket / SSE for Live Investigation

```python
# chronos/api/routes/investigations.py

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/investigations")

@router.get("/{investigation_id}/stream")
async def stream_investigation(investigation_id: str):
    """Server-Sent Events stream for live investigation progress."""

    async def event_generator():
        investigation = get_investigation(investigation_id)

        async for step_update in investigation.subscribe():
            yield {
                "event": "step_update",
                "data": json.dumps({
                    "step": step_update["current_step"],
                    "status": step_update["status"],  # running, completed, error
                    "summary": step_update.get("summary", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                })
            }

        # Final event
        yield {
            "event": "investigation_complete",
            "data": json.dumps({
                "incident_id": investigation.incident_id,
                "report_available": True,
            })
        }

    return EventSourceResponse(event_generator())
```

---

## 14. Project Structure

```
chronos/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── PRD.md
├── spec.md
│
├── chronos/                           # Python package
│   ├── __init__.py
│   ├── main.py                        # FastAPI app entrypoint + OpenLLMetry init
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                # Pydantic Settings (env vars)
│   │   └── litellm_config.yaml        # LiteLLM model routing config
│   │
│   ├── api/                           # FastAPI routes
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── webhooks.py            # OM + OpenLineage webhook receivers
│   │   │   ├── incidents.py           # Incident CRUD + PROV-O export
│   │   │   ├── investigations.py      # Manual trigger + live stream
│   │   │   ├── stats.py               # Dashboard statistics
│   │   │   └── well_known.py          # A2A Agent Card endpoint
│   │   └── middleware.py              # Error handling, logging
│   │
│   ├── agent/                         # LangGraph investigation agent
│   │   ├── __init__.py
│   │   ├── graph.py                   # State machine + Langfuse callback
│   │   ├── state.py                   # InvestigationState TypedDict
│   │   └── nodes/                     # One file per investigation step
│   │       ├── __init__.py
│   │       ├── prior_investigations.py # Step 0: Self-referential memory lookup
│   │       ├── scope_failure.py
│   │       ├── temporal_diff.py
│   │       ├── lineage_walk.py
│   │       ├── code_blast_radius.py
│   │       ├── downstream_impact.py
│   │       ├── audit_correlation.py
│   │       ├── rca_synthesis.py
│   │       ├── notify.py
│   │       └── persist_trace.py       # Step 9: Self-referential memory persist
│   │
│   ├── mcp/                           # MCP client connections
│   │   ├── __init__.py
│   │   ├── config.py                  # MCP server configurations
│   │   ├── client.py                  # Unified MCP client wrapper
│   │   └── tools.py                   # Tool call helpers
│   │
│   ├── ingestion/                     # Event ingestion pipelines
│   │   ├── __init__.py
│   │   ├── graphiti_ingestor.py       # OM events -> Graphiti episodes
│   │   ├── openlineage_receiver.py    # OpenLineage -> OM + Graphiti
│   │   └── deduplicator.py            # Event deduplication logic
│   │
│   ├── compliance/                    # Compliance & provenance (NEW)
│   │   ├── __init__.py
│   │   └── prov_generator.py          # W3C PROV-O document generator
│   │
│   ├── observability/                 # Telemetry & tracing (NEW)
│   │   ├── __init__.py
│   │   └── otel_setup.py             # OpenLLMetry + OTel GenAI SemConv init
│   │
│   ├── enrichment/                    # Context enrichment
│   │   ├── __init__.py
│   │   └── graphify_context.py        # Graphify graph report reader
│   │
│   ├── notifications/                 # Output channels
│   │   ├── __init__.py
│   │   └── slack.py                   # Slack Block Kit builder + sender
│   │
│   ├── models/                        # Pydantic data models
│   │   ├── __init__.py
│   │   ├── incident.py                # IncidentReport, EvidenceItem, etc.
│   │   ├── events.py                  # Webhook payload models
│   │   └── graphiti_entities.py       # Custom Graphiti entity types
│   │
│   ├── llm/                           # LLM abstraction via LiteLLM
│   │   ├── __init__.py
│   │   ├── client.py                  # Synthesis + extraction wrappers
│   │   └── prompts.py                 # System prompts for RCA
│   │
│   └── .well-known/                   # A2A Protocol (NEW)
│       └── agent-card.json            # Agent capability descriptor
│
├── chronos-frontend/                  # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── Dockerfile
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── IncidentDetail.tsx
│       │   └── Settings.tsx
│       ├── components/
│       │   ├── IncidentTimeline.tsx
│       │   ├── IncidentCard.tsx
│       │   ├── LineageFailureMap.tsx
│       │   ├── InvestigationReplay.tsx
│       │   ├── TemporalDiff.tsx
│       │   ├── EvidenceChain.tsx
│       │   ├── BlastRadiusPanel.tsx
│       │   └── ProvenanceDownload.tsx  # PROV-O download button (NEW)
│       ├── hooks/
│       │   ├── useIncidents.ts
│       │   ├── useIncidentDetail.ts
│       │   └── useWebSocket.ts
│       └── lib/
│           ├── api.ts
│           └── types.ts
│
├── services/                          # Service-specific configs
│   └── graphiti-mcp/
│       ├── Dockerfile
│       ├── config.yaml
│       └── requirements.txt
│
├── scripts/                           # Setup & utility scripts
│   ├── setup.sh                       # One-command full setup
│   ├── index_gitnexus.sh              # Index code repo with GitNexus
│   ├── index_graphify.sh              # Index code repo with Graphify
│   ├── seed_openmetadata.sh           # Seed sample data + tests
│   └── inject_failure.sh              # Inject a schema change to trigger demo
│
├── sample-dbt-project/                # Demo dbt project for GitNexus/Graphify
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_payments.sql
│   │   │   ├── stg_orders.sql
│   │   │   └── stg_customers.sql
│   │   └── marts/
│   │       ├── orders.sql
│   │       └── customer_metrics.sql
│   └── tests/
│       └── assert_total_amount_positive.sql
│
├── tests/                             # Python tests
│   ├── test_agent/
│   │   ├── test_graph.py
│   │   └── test_nodes.py
│   ├── test_ingestion/
│   │   └── test_graphiti_ingestor.py
│   ├── test_notifications/
│   │   └── test_slack.py
│   └── evals/                         # Quality evaluation tests (NEW)
│       ├── test_rca_quality.py         # DeepEval RCA accuracy tests
│       ├── test_graphiti_retrieval.py  # RAGAs retrieval quality tests
│       └── fixtures/                  # Test event fixtures
│           └── events/
│               └── schema_change_webhook.json
│
└── .github/                           # CI/CD
    └── workflows/
        └── eval.yml                   # CHRONOS Quality Eval workflow
```

---

## 15. Environment Variables

```bash
# .env (template)

# ─── OpenMetadata ───
OPENMETADATA_HOST=http://localhost:8585
OPENMETADATA_JWT_TOKEN=              # Generated via OM admin UI

# ─── Graphiti / FalkorDB ───
FALKORDB_HOST=localhost
FALKORDB_PORT=6379

# ─── LLM Providers (via LiteLLM) ───
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
LITELLM_MASTER_KEY=sk-chronos-local  # Local LiteLLM proxy key

# ─── Slack ───
SLACK_WEBHOOK_URL=                   # Incoming webhook URL
SLACK_CHANNEL=#data-incidents

# ─── Langfuse (Agentic Observability) ───
LANGFUSE_ENABLED=true                # Feature flag — set false for Langfuse-free mode
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=pk-lf-chronos-demo
LANGFUSE_SECRET_KEY=sk-lf-chronos-demo

# ─── OpenLLMetry / OTel ───
OTEL_EXPORTER_OTLP_ENDPOINT=http://langfuse:4318  # OTLP endpoint (Langfuse or Jaeger)
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental

# ─── CHRONOS Config ───
CHRONOS_PORT=8100
CHRONOS_DEBUG=true
CHRONOS_VERSION=0.1.0
ENVIRONMENT=development
INVESTIGATION_WINDOW_HOURS=72       # How far back to look
LINEAGE_DEPTH_UPSTREAM=5
LINEAGE_DEPTH_DOWNSTREAM=3
DEDUP_WINDOW_SECONDS=300             # 5 min dedup window
SYNTHESIS_MODEL=chronos-synthesis    # LiteLLM model alias
EXTRACTION_MODEL=chronos-extraction  # LiteLLM model alias
```

---

## 16. Demo Scenario Script

### 16.1 Setup Phase

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for OpenMetadata to be healthy
./scripts/wait_for_om.sh

# 3. Seed OpenMetadata with sample data
./scripts/seed_openmetadata.sh
# This creates:
#   - A PostgreSQL database service
#   - Tables: raw.stripe.payments, staging.stg_payments,
#             warehouse.orders, warehouse.customer_metrics
#   - Column-level lineage between all tables
#   - Data quality tests on warehouse.orders.total_amount
#   - Tier-1 classification on warehouse.orders
#   - Ownership assigned to demo users

# 4. Index code with GitNexus + Graphify
./scripts/index_gitnexus.sh ./sample-dbt-project
./scripts/index_graphify.sh ./sample-dbt-project

# 5. Let Graphiti ingest initial metadata events (~2 min)
sleep 120
```

### 16.2 Demo Execution

```bash
# 6. Inject the failure: change column type in source
./scripts/inject_failure.sh
# This script:
#   a. Modifies stg_payments.sql to cast total_amount as VARCHAR
#   b. Commits the change to git (so GitNexus can find it)
#   c. Updates the table schema in OpenMetadata via API
#   d. Triggers the data quality test, which now fails
#   e. OpenMetadata fires webhook -> CHRONOS investigation begins

# 7. Watch CHRONOS investigate in real time
open http://localhost:3000
# The dashboard shows the investigation steps in real time via SSE

# 8. Slack notification arrives within ~90 seconds of failure
```

### 16.3 Demo Talking Points

1. "Watch: the test just failed. CHRONOS is already investigating."
2. "Step 0: It checked institutional memory — found 2 related past incidents on this entity."
3. "Step 1: Scoped the failure — identified the exact column and test."
4. "Step 2: Graphiti tells us this table's schema changed 2 hours ago."
5. "Step 3: Upstream lineage walk found the schema change in `raw.stripe.payments`."
6. "Step 4: GitNexus identified the commit in `stg_payments.sql`."
7. "Step 5: 3 Tier-1 downstream assets at risk."
8. "Step 6: Audit log shows the change was made by user `alex` at 23:12 UTC."
9. "Step 7: LLM synthesized a root cause report with 92% confidence. It references the past incident!"
10. "Step 8: Slack notification fired with owner tags and remediation steps."
11. "Step 9: This entire investigation is now persisted in Graphiti — next time it happens, CHRONOS will know."
12. "Total time: 47 seconds. Now let me show you the Langfuse trace tree..."
13. *(Switch to Langfuse UI)* "Every step is a span in this trace tree. You can see token counts, costs, and timing."
14. *(Click Download)* "One-click W3C PROV-O compliance artifact for GDPR auditors."
15. "And any other agent can discover CHRONOS via: `curl localhost:8100/.well-known/agent-card.json`"

---

## 17. Self-Referential Investigation Memory (F11)

### 17.1 Step 0: Check Prior Investigations

```python
# chronos/agent/nodes/prior_investigations.py

async def check_prior_investigations(state: InvestigationState) -> dict:
    """
    Step 0: Query Graphiti for past investigations of the same entity
    or pattern. Include findings as context for the current investigation.
    """
    graphiti_mcp = get_graphiti_mcp_client()
    entity_fqn = extract_entity_from_trigger(state["trigger_event"])

    prior_investigations = await graphiti_mcp.call_tool(
        "search_facts",
        {
            "query": f"past incidents on {entity_fqn}",
            "group_id": "chronos-investigation-traces",
        }
    )

    patterns = await graphiti_mcp.call_tool(
        "search_nodes",
        {
            "query": f"recurrence patterns for {entity_fqn} or similar assets",
            "group_id": "chronos-investigation-traces",
        }
    )

    return {
        "prior_investigations": prior_investigations,
        "recurrence_patterns": patterns,
        "step_results": state["step_results"] + [{
            "step": "check_prior_investigations",
            "completed_at": datetime.utcnow().isoformat(),
            "summary": f"Found {len(prior_investigations)} related past incidents"
        }]
    }
```

### 17.2 Step 9: Persist Investigation Trace

```python
# chronos/agent/nodes/persist_trace.py

async def persist_investigation_trace(state: InvestigationState) -> dict:
    """
    Step 9 (post-notify): Persist the investigation trace as a
    Graphiti episode. Creates self-improving memory over time.
    """
    graphiti_mcp = get_graphiti_mcp_client()
    report = state["incident_report"]

    trace_narrative = _format_investigation_as_episode(state)

    await graphiti_mcp.call_tool(
        "add_episode",
        {
            "name": f"chronos-investigation-{report['incident_id']}",
            "episode_body": trace_narrative,
            "source": "json",
            "source_description": "CHRONOS investigation trace",
            "group_id": "chronos-investigation-traces",
            "reference_time": datetime.utcnow().isoformat(),
        }
    )

    # Per-step telemetry for cost/latency analysis
    for step_result in state["step_results"]:
        await graphiti_mcp.call_tool(
            "add_episode",
            {
                "name": f"step-{report['incident_id']}-{step_result['step']}",
                "episode_body": json.dumps({
                    "incident_id": report["incident_id"],
                    "step": step_result["step"],
                    "duration_ms": step_result.get("duration_ms"),
                    "mcp_calls": step_result.get("mcp_calls", 0),
                    "llm_tokens": step_result.get("llm_tokens", 0),
                    "summary": step_result["summary"],
                }),
                "source": "json",
                "source_description": "CHRONOS step telemetry",
                "group_id": "chronos-step-telemetry",
            }
        )

    return {"trace_persisted": True}

def _format_investigation_as_episode(state) -> str:
    report = state["incident_report"]
    return (
        f"CHRONOS investigation {report['incident_id']} completed on "
        f"{report['investigation_completed_at']}. "
        f"Investigated failure of test '{report['test_name']}' on entity "
        f"'{report['affected_entity_fqn']}'. "
        f"Root cause identified as {report['root_cause_category']} "
        f"with {report['confidence']:.0%} confidence. "
        f"Probable cause: {report['probable_root_cause']}. "
        f"Business impact: {report['business_impact']}. "
        f"Affected {len(report['affected_downstream'])} downstream assets. "
        f"Investigation took {report['investigation_duration_ms']}ms and "
        f"used {report['total_llm_tokens']} tokens across "
        f"{report['total_mcp_calls']} MCP tool calls."
    )
```

---

## 18. Langfuse Integration (F12)

### 18.1 Docker Compose Additions

```yaml
  langfuse-db:
    image: postgres:16
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    ports:
      - "5433:5432"
    volumes:
      - langfuse_db_data:/var/lib/postgresql/data

  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3001:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
      NEXTAUTH_URL: http://localhost:3001
      NEXTAUTH_SECRET: chronos-hackathon-secret-change-me
      SALT: chronos-salt-change-me
      TELEMETRY_ENABLED: "false"
      LANGFUSE_INIT_ORG_ID: chronos-org
      LANGFUSE_INIT_PROJECT_ID: chronos
      LANGFUSE_INIT_PROJECT_PUBLIC_KEY: pk-lf-chronos-demo
      LANGFUSE_INIT_PROJECT_SECRET_KEY: sk-lf-chronos-demo
    depends_on:
      - langfuse-db
```

### 18.2 Invocation with Callback

```python
# chronos/api/routes/webhooks.py (updated invocation)

graph, config = build_investigation_graph(incident_id=generated_id)
result = await graph.ainvoke(initial_state, config=config)
```

---

## 19. OpenLLMetry + OTel GenAI SemConv (F15/F16)

### 19.1 Initialization

```python
# chronos/observability/otel_setup.py

import os
os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = "gen_ai_latest_experimental"

from traceloop.sdk import Traceloop
from opentelemetry import trace
from opentelemetry.trace import SpanKind

def init_observability(settings):
    """Initialize OpenLLMetry for vendor-neutral LLM instrumentation."""
    Traceloop.init(
        app_name="chronos",
        api_endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        disable_batch=False,
        resource_attributes={
            "service.name": "chronos-agent",
            "service.version": settings.VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        },
    )

tracer = trace.get_tracer("chronos.agent")
```

### 19.2 App Startup Integration

```python
# chronos/main.py (additions)

from chronos.observability.otel_setup import init_observability

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_observability(settings)
    yield
```

---

## 20. W3C PROV-O Compliance (F13)

### 20.1 Provenance Document Generator

```python
# chronos/compliance/prov_generator.py

from prov.model import ProvDocument
from chronos.models import IncidentReport

CHRONOS_NS = "http://chronos.dev/ns/"
OM_NS = "http://openmetadata.org/ns/"

def generate_prov_document(report: IncidentReport) -> ProvDocument:
    doc = ProvDocument()
    doc.add_namespace("chronos", CHRONOS_NS)
    doc.add_namespace("om", OM_NS)
    doc.add_namespace("prov", "http://www.w3.org/ns/prov#")

    # AGENT: CHRONOS itself
    chronos_agent = doc.agent(
        f"chronos:agent/{report.agent_version}",
        {"prov:type": "prov:SoftwareAgent", "chronos:version": report.agent_version},
    )

    # ACTIVITY: the investigation
    investigation = doc.activity(
        f"chronos:investigation/{report.incident_id}",
        startTime=report.detected_at,
        endTime=report.investigation_completed_at,
        other_attributes={
            "chronos:root_cause_category": report.root_cause_category,
            "chronos:confidence": report.confidence,
        },
    )
    doc.wasAssociatedWith(investigation, chronos_agent)

    # ENTITY: affected data asset
    affected = doc.entity(f"om:table/{report.affected_entity_fqn}")
    doc.used(investigation, affected)

    # ENTITY: incident report output
    report_ent = doc.entity(f"chronos:incident/{report.incident_id}")
    doc.wasGeneratedBy(report_ent, investigation)

    # Evidence items
    for i, ev in enumerate(report.evidence_chain):
        ev_ent = doc.entity(f"chronos:evidence/{report.incident_id}/{i}")
        doc.used(investigation, ev_ent)
        doc.wasDerivedFrom(report_ent, ev_ent)

    # Downstream blast radius
    for asset in report.affected_downstream:
        ds = doc.entity(f"om:asset/{asset.fqn}", {"om:tier": asset.tier})
        doc.wasInfluencedBy(ds, affected)

    return doc

def export_prov_jsonld(report): return generate_prov_document(report).serialize(format="json")
def export_prov_turtle(report): return generate_prov_document(report).serialize(format="rdf", rdf_format="turtle")
```

### 20.2 API Endpoints

```python
# chronos/api/routes/incidents.py (additions)

@router.get("/incidents/{incident_id}/provenance.jsonld")
async def get_provenance_jsonld(incident_id: str):
    report = await get_incident_report(incident_id)
    return Response(content=export_prov_jsonld(report), media_type="application/ld+json")

@router.get("/incidents/{incident_id}/provenance.ttl")
async def get_provenance_turtle(incident_id: str):
    report = await get_incident_report(incident_id)
    return Response(content=export_prov_turtle(report), media_type="text/turtle")
```

---

## 21. A2A Agent Card (F14)

### 21.1 Agent Card Definition

```json
// chronos/.well-known/agent-card.json
{
  "name": "CHRONOS",
  "description": "Autonomous data incident root cause analysis agent.",
  "url": "http://localhost:8100",
  "version": "0.1.0",
  "provider": { "organization": "chronos-hackathon", "url": "https://github.com/guglxni/chronos" },
  "capabilities": { "streaming": true, "pushNotifications": true, "stateTransitionHistory": true },
  "authentication": { "schemes": ["Bearer"] },
  "defaultInputModes": ["application/json"],
  "defaultOutputModes": ["application/json", "application/ld+json"],
  "skills": [
    {
      "id": "investigate_data_incident",
      "name": "Investigate Data Quality Incident",
      "description": "Given a failed test, autonomously investigate root cause across metadata, temporal, and code graphs.",
      "tags": ["data-quality", "root-cause-analysis", "openmetadata"]
    },
    {
      "id": "assess_blast_radius",
      "name": "Assess Blast Radius",
      "description": "Compute downstream blast radius for a data asset.",
      "tags": ["impact-analysis", "lineage"]
    },
    {
      "id": "generate_compliance_report",
      "name": "Generate W3C PROV-O Compliance Artifact",
      "description": "Export investigation as W3C PROV-O provenance document.",
      "tags": ["compliance", "provenance", "gdpr"]
    }
  ]
}
```

### 21.2 FastAPI Route

```python
# chronos/api/routes/well_known.py

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/.well-known/agent-card.json")
async def get_agent_card():
    return FileResponse("chronos/.well-known/agent-card.json", media_type="application/json")
```

---

## 22. DeepEval Quality Tests (F17)

```python
# tests/evals/test_rca_quality.py

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval, FaithfulnessMetric

rca_accuracy = GEval(
    name="RCA Accuracy",
    criteria=(
        "Determine if the root cause correctly identifies the injected failure. "
        "Check entity, category, and blast radius match."
    ),
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    threshold=0.8,
)

evidence_faithfulness = FaithfulnessMetric(threshold=0.85, model="gpt-4.1-mini", include_reason=True)

@pytest.mark.asyncio
async def test_chronos_detects_schema_change(schema_change_scenario):
    incident = await run_investigation(schema_change_scenario["trigger_event"])
    test_case = LLMTestCase(
        input=str(schema_change_scenario["trigger_event"]),
        actual_output=incident.model_dump_json(),
        expected_output=str(schema_change_scenario["expected_output"]),
        retrieval_context=[str(e.raw_data) for e in incident.evidence_chain],
    )
    assert_test(test_case, [rca_accuracy, evidence_faithfulness])
```

---

## 23. RAGAs Retrieval Evaluation (F18)

```python
# tests/evals/test_graphiti_retrieval.py

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

async def test_graphiti_temporal_diff_retrieval():
    entity_fqn = "raw.stripe.payments"
    seeded_fact = "Column total_amount type changed from DECIMAL to VARCHAR"

    state = await temporal_diff({"affected_entity_fqn": entity_fqn, ...})
    retrieved_facts = [f["fact"] for f in state["temporal_changes"]]

    dataset = Dataset.from_dict({
        "question": [f"What recently changed about {entity_fqn}?"],
        "answer": [state.get("temporal_summary", "")],
        "contexts": [retrieved_facts],
        "ground_truth": [seeded_fact],
    })

    result = evaluate(dataset=dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
    assert result["context_recall"] > 0.8
    assert result["context_precision"] > 0.6
```

---

## 24. GitHub Actions CI for Evaluations (F17)

```yaml
# .github/workflows/eval.yml

name: CHRONOS Quality Eval
on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start Docker stack
        run: docker-compose up -d openmetadata falkordb graphiti-mcp
      - name: Seed demo data
        run: ./scripts/seed_openmetadata.sh
      - name: Run CHRONOS evals
        run: pytest tests/evals/ -v
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

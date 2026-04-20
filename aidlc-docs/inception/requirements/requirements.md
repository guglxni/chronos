# CHRONOS — Requirements Document

**Depth Level**: Comprehensive
**Source**: PRD.md + spec.md (pre-existing)

## 1. Functional Requirements

### FR-01: Event-Driven Trigger (F1)
- **Priority**: Must-Have
- **Description**: Subscribe to OpenMetadata webhooks for `testCaseResult` events with status `Failed` or `Aborted`
- **Acceptance Criteria**:
  - FastAPI endpoint receives and validates OpenMetadata webhook payloads
  - Event deduplication within configurable window (default: 5 min)
  - Events queued for sequential investigation processing
  - Supported event types: testCaseResultUpdated, entityCreated, entityUpdated, entityDeleted

### FR-02: Autonomous Investigation Agent (F2)
- **Priority**: Must-Have
- **Description**: LangGraph state machine executing 7-step investigation protocol across 3 MCP servers
- **Steps**:
  1. Scope Failure — query test + entity details from OpenMetadata
  2. Temporal Diff — query Graphiti for changes in investigation window
  3. Lineage Walk — trace upstream lineage (configurable depth, default: 5 hops)
  4. Code Blast Radius — query GitNexus for code references + recent commits
  5. Downstream Impact — trace downstream lineage, assess business criticality via tier tags
  6. Audit Correlation — cross-reference audit logs and temporal facts
  7. RCA Synthesis — LLM produces structured IncidentReport via LiteLLM

### FR-03: Temporal Knowledge Graph Ingestion (F3)
- **Priority**: Must-Have
- **Description**: Continuous ingestion of OpenMetadata events into Graphiti as episodes
- **Custom Entity Types**: DataAsset, DataTest, Pipeline, Schema, Owner, CodeFile, Incident
- **Custom Edge Types**: PRODUCES, CONSUMES, TESTS, OWNS, MODIFIED_BY, CAUSED_FAILURE, DOWNSTREAM_OF, SAME_INCIDENT, RECURRENCE_OF

### FR-04: Structured Incident Report (F4)
- **Priority**: Must-Have
- **Description**: Machine-readable + human-readable incident report with Pydantic schema
- **Fields**: incident_id, detected_at, affected_entity_fqn, test_name, probable_root_cause, root_cause_category (8 categories), confidence (0-1), evidence_chain, affected_downstream, business_impact, recommended_actions, investigation_timeline

### FR-05: Slack Notification (F5)
- **Priority**: Must-Have
- **Description**: Slack Block Kit messages with owner tagging, action buttons
- **Features**: Severity-based emoji, blast radius summary, remediation steps, "View in CHRONOS" / "View in OpenMetadata" / "Acknowledge" buttons

### FR-06: React Frontend Dashboard (F6)
- **Priority**: Must-Have
- **Description**: Web dashboard with 4 views
- **Views**: Incident Timeline, Investigation Replay (step-by-step), Lineage Failure Map (React Flow), Temporal State Diff

### FR-07: OpenLineage Event Ingestion (F7)
- **Priority**: Nice-to-Have
- **Description**: Accept OpenLineage events, forward to OpenMetadata + Graphiti

### FR-08: Graphify Architecture Context (F8)
- **Priority**: Nice-to-Have
- **Description**: Multi-modal code knowledge graph via Graphify for architectural context enrichment

### FR-09: Incident Pattern Recognition (F9)
- **Priority**: Nice-to-Have
- **Description**: Use Graphiti search to identify recurring patterns across incidents

### FR-10: Prevention Mode (F10)
- **Priority**: Stretch Goal
- **Description**: CI/CD integration for pre-merge impact assessment

## 2. Non-Functional Requirements

### NFR-01: Performance
- Investigation completion: < 120 seconds end-to-end
- Webhook event processing: < 500ms acknowledgment
- Dashboard page load: < 2 seconds
- Slack notification: < 30 seconds after investigation completes

### NFR-02: Reliability
- Event deduplication prevents redundant investigations
- LiteLLM fallback routing ensures LLM availability
- Graceful degradation if any single MCP server is unavailable

### NFR-03: Security
- API keys via environment variables only
- JWT auth for OpenMetadata access
- No secrets in source code or Docker images
- LiteLLM proxy key for internal service communication

### NFR-04: Operability
- Single `docker-compose up` to start entire stack
- Health check endpoint with dependency status
- Environment variable template (.env.example)

### NFR-05: Observability
- Investigation step timing in incident reports
- LLM token usage and cost tracking via LiteLLM
- Total MCP call count per investigation

## 3. Constraints
- Python 3.11+ for backend
- React + TypeScript for frontend
- Docker Compose for orchestration
- OpenMetadata 1.12+ required (MCP server, audit log retention)
- 10-day hackathon timeline (Apr 17-26, 2026)

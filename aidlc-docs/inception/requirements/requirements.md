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

### FR-11: Self-Referential Investigation Memory (F11 — Gap 8)
- **Priority**: Must-Have (HIGHEST)
- **Description**: CHRONOS persists investigation traces as Graphiti episodes and queries them before new investigations
- **Acceptance Criteria**:
  - Step 0 (new): Queries `chronos-investigation-traces` group for past incidents on same entity
  - Step 9 (new): Persists full investigation trace as Graphiti episode after notification
  - "Related Past Incidents" section in incident report
  - Per-step telemetry persisted in `chronos-step-telemetry` group

### FR-12: Agentic Observability via Langfuse (F12 — Gap 1)
- **Priority**: Must-Have (HIGH)
- **Description**: Every investigation becomes a trace tree in Langfuse
- **Acceptance Criteria**:
  - Self-hosted Langfuse in Docker Compose (Postgres-backed)
  - LangChain callback handler wired into LangGraph
  - Session ID = incident ID (groups all steps)
  - Cost per investigation tracked automatically
  - Feature-flagged: `LANGFUSE_ENABLED=true|false`

### FR-13: Compliance-Grade Provenance via W3C PROV-O (F13 — Gap 6)
- **Priority**: Must-Have (MEDIUM-HIGH)
- **Description**: Generate GDPR/SOC2-ready audit artifacts from investigation traces
- **Acceptance Criteria**:
  - `GET /api/v1/incidents/{id}/provenance.jsonld` endpoint
  - Serializes to JSON-LD, RDF/Turtle, PROV-N
  - Maps CHRONOS concepts to PROV-O: Agent, Activity, Entity

### FR-14: A2A Agent Card for Discovery (F14 — Gap 7)
- **Priority**: Should-Have (MEDIUM)
- **Description**: Self-describing agent card at `/.well-known/agent-card.json`
- **Acceptance Criteria**:
  - JSON agent card following A2A Protocol spec
  - Describes 3 skills: investigate, blast radius, compliance report
  - Served by FastAPI

### FR-15: Vendor-Neutral LLM Instrumentation via OpenLLMetry (F15 — Gap 2)
- **Priority**: Should-Have (MEDIUM)
- **Description**: OTel-based instrumentation via Traceloop SDK
- **Acceptance Criteria**:
  - Single-line init at app startup
  - `gen_ai.*` span attributes emitted

### FR-16: OTel GenAI Semantic Conventions (F16 — Gap 3)
- **Priority**: Nice-to-Have (LOW)
- **Description**: Standardized telemetry schema (emerges free from FR-15)

### FR-17: Continuous Quality Evaluation via DeepEval (F17 — Gap 4)
- **Priority**: Should-Have (MEDIUM)
- **Description**: Pytest-compatible RCA quality regression tests
- **Acceptance Criteria**:
  - G-Eval metric for RCA accuracy
  - FaithfulnessMetric for evidence chain
  - 2-3 tests on canonical demo scenario
  - GitHub Actions workflow

### FR-18: Retrieval Quality Evaluation via RAGAs (F18 — Gap 5)
- **Priority**: Nice-to-Have (LOW-MEDIUM)
- **Description**: Evaluate Graphiti's retrieval quality per investigation step

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
- Langfuse optional — feature-flagged for Langfuse-free deployments

### NFR-03: Security
- API keys via environment variables only
- JWT auth for OpenMetadata access
- No secrets in source code or Docker images
- LiteLLM proxy key for internal service communication
- PROV-O compliance artifacts contain no PII

### NFR-04: Operability
- Single `docker-compose up` to start entire stack (including Langfuse)
- Health check endpoint with dependency status
- Environment variable template (.env.example)
- A2A Agent Card discoverable at `/.well-known/agent-card.json`

### NFR-05: Observability
- Investigation step timing in incident reports
- LLM token usage and cost tracking via LiteLLM + Langfuse
- Total MCP call count per investigation
- OpenTelemetry GenAI SemConv v1.37+ `gen_ai.*` spans via OpenLLMetry
- Langfuse trace trees for investigation replay + annotation
- Investigation traces persisted as Graphiti episodes for self-referential learning

## 3. Constraints
- Python 3.11+ for backend
- React + TypeScript for frontend
- Docker Compose for orchestration (now includes Langfuse + Postgres)
- OpenMetadata 1.12+ required (MCP server, audit log retention)
- 10-day hackathon timeline (Apr 17-26, 2026)
- New dependencies: langfuse, traceloop-sdk, prov, deepeval, ragas

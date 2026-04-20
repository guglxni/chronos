# CHRONOS — Product Requirements Document

**Autonomous Data Incident Root Cause Analysis Agent**
*"Don't just detect the anomaly. Travel back through the timeline and find where it broke."*

**Hackathon:** OpenMetadata Paradox Hackathon (WeMakeDevs x OpenMetadata)
**Dates:** April 17 - April 26, 2026
**Track Coverage:** T-01 (MCP & AI Agents), T-02 (Data Observability), T-05 (Community & Comms), T-06 (Governance & Classification)
**Version:** 2.0 — Agentic Metadata Infrastructure Edition
**Author:** Aaryan
**Changelog:** v2.0 adds 8 FOSS integrations closing gaps from *Is Agentic Metadata the Next Infrastructure Layer?* (The New Stack, Jan 2026): Langfuse, OpenLLMetry, OTel GenAI SemConv, DeepEval, RAGAs, W3C PROV-O, A2A Protocol, self-referential investigation memory.

---

## 1. Problem Statement

When a data quality test fails in a modern data stack, the investigation workflow is almost entirely manual. A data engineer receives an alert, then spends 30-60 minutes executing a predictable sequence of steps: trace lineage upstream, check for recent schema changes, cross-reference audit logs, identify whether related tests also failed, assess the downstream blast radius, and notify affected asset owners.

This process is slow, repetitive, error-prone, and scales poorly. As data platforms grow, the metadata graph becomes too large for any single engineer to hold in their head. The information needed to diagnose a root cause is scattered across metadata catalogs, version histories, audit logs, code repositories, and communication channels.

OpenMetadata already stores all the raw ingredients for automated root cause analysis: entity version history, column-level lineage, test suite results, audit logs (with 6-month retention as of v1.12), ownership metadata, tier classifications, and an MCP server that exposes all of this programmatically. What's missing is an autonomous agent that connects these dots without human intervention.

### 1.1 Current Pain Points

**Manual lineage tracing.** When a test on `warehouse.orders.total_amount` fails, an engineer manually clicks through upstream lineage in the OpenMetadata UI, checking each node for anomalies. For deep lineage chains (5+ hops), this alone takes 15-20 minutes.

**No temporal correlation.** OpenMetadata tracks version history per entity, but there's no tool that correlates changes across multiple entities in a shared time window. "Did anything upstream change in the last 48 hours?" requires checking each entity individually.

**Siloed code context.** Data quality failures often originate in code changes (dbt model edits, ETL script modifications, Airflow DAG updates) that are invisible to metadata-only tools. The code layer and the metadata layer are disconnected.

**Delayed blast radius assessment.** Determining which dashboards, ML models, and downstream consumers are affected requires tracing lineage downstream, pulling tier tags and ownership, and manually composing a Slack message. This delays communication to stakeholders.

**No institutional memory.** Each investigation starts from scratch. There's no persistent memory of past incidents, their root causes, or the resolution paths that worked. Recurring failure patterns are re-investigated every time.

### 1.2 Who Experiences This Pain

**Data engineers** who are on-call and responsible for triaging data quality incidents. They spend disproportionate time on investigation vs. remediation.

**Analytics engineers** whose dbt models may be implicated in failures and need to understand the blast radius of their changes before and after merge.

**Data consumers** (analysts, data scientists, business users) who need to know whether the data they're using is reliable and when it will be fixed. They currently wait for manual Slack messages from the on-call engineer.

**Platform teams** who need incident metrics (MTTR, failure frequency by domain, recurring root causes) to prioritize infrastructure investments.

---

## 2. Product Vision

CHRONOS is an autonomous data incident investigation agent built as an **agentic metadata infrastructure layer**. It operates across three knowledge graphs simultaneously to identify root causes, assess blast radius, and communicate findings — reducing mean time to resolution (MTTR) from ~45 minutes to ~2 minutes.

CHRONOS embodies the vision from *Is Agentic Metadata the Next Infrastructure Layer?* (The New Stack): treating what's happening under the hood of AI agents as first-class metadata, producing compliance-grade provenance, emitting standardized telemetry, self-describing via agent discovery protocols, and improving over time from its own investigation traces.

When a data quality test fails, CHRONOS autonomously:

1. **Checks institutional memory** — queries past investigations of the same entity/pattern via Graphiti
2. **Detects** the failure via OpenMetadata webhooks
3. **Investigates** the root cause by reasoning across metadata, temporal state, and code structure
4. **Assesses** downstream impact by tracing lineage and evaluating business criticality
5. **Produces** a structured incident report with probable cause, confidence level, and remediation guidance
6. **Generates** W3C PROV-O compliance artifacts for audit trails (GDPR/SOC2-ready)
7. **Notifies** affected stakeholders via Slack with contextual, role-appropriate information
8. **Remembers** the incident in a temporal knowledge graph for pattern recognition over time
9. **Emits** OpenTelemetry GenAI SemConv traces observable in Langfuse
10. **Describes itself** via A2A Agent Card for agent-to-agent discovery

### 2.1 The Triple-Graph Architecture

CHRONOS differentiates itself by reasoning across three complementary knowledge graphs:

**Graph 1 — OpenMetadata's Unified Knowledge Graph (Metadata Layer)**
The canonical source for data asset metadata: tables, columns, lineage, test results, ownership, tier classifications, glossary terms, and governance policies. Accessed via OpenMetadata's native MCP server.

**Graph 2 — Graphiti's Temporal Context Graph (Time Layer)**
A temporally-aware knowledge graph built on FalkorDB that ingests OpenMetadata events as episodes. Every schema change, test result, ownership transfer, and tag modification is stored with bi-temporal metadata (`valid_from`, `valid_until`). This enables point-in-time queries like "what was true about this table 48 hours ago?" and automatic fact invalidation when state changes.

**Graph 3 — GitNexus Code Knowledge Graph (Code Layer)**
A knowledge graph of the data platform's codebase (dbt models, ETL scripts, pipeline definitions) built via static analysis with AST parsing. Maps functions, imports, call chains, and file dependencies. Enables the agent to answer "which code files produce data for this table, and did any of them change recently?"

### 2.2 Hackathon Theme Alignment

The hackathon theme is "Back to the Future" — temporal paradoxes in the data timeline. CHRONOS literally travels through metadata time:

- Graphiti's temporal knowledge graph preserves the full history of metadata state changes
- The agent reconstructs "what was true" at any point in time
- Investigation reports show a timeline of cascading changes that led to the failure
- The name CHRONOS (Greek Titan of Time) reinforces the temporal investigation metaphor

---

## 3. Target Users & Personas

### 3.1 Primary: On-Call Data Engineer (Priya)

Priya is a data engineer at a mid-size company using dbt + Snowflake + Airflow. She's on PagerDuty rotation and gets woken up at 2 AM when a data quality test fails. She needs to figure out what happened, how bad it is, and who to tell — as fast as possible.

**CHRONOS value for Priya:** She wakes up to a Slack message from CHRONOS that says: "Test `column_values_not_null` failed on `warehouse.orders.total_amount` at 01:47 UTC. Probable root cause: Column `total_amount` type changed from DECIMAL(10,2) to VARCHAR in upstream source `raw.stripe.payments` at 23:12 UTC yesterday (commit `a3f7b2c` by @alex in `models/staging/stg_payments.sql`). 3 Tier-1 dashboards affected. Recommended: Revert commit or add explicit cast in staging model." She can act immediately instead of investigating.

### 3.2 Secondary: Analytics Engineer (Alex)

Alex maintains dbt models and wants to understand the downstream impact of his changes before they cause problems. He also needs to know when his changes have caused failures after deployment.

**CHRONOS value for Alex:** When his commit causes a downstream test failure, CHRONOS tags him in the incident report with the specific commit, file, and line range that's implicated. He doesn't have to guess whether the alert is related to his change.

### 3.3 Tertiary: Data Platform Lead (Meera)

Meera runs the data platform team and needs aggregate incident intelligence: which data domains have the most failures, what are recurring root cause patterns, and where should the team invest in prevention.

**CHRONOS value for Meera:** Graphiti's temporal knowledge graph accumulates incident history over time. Meera can query it for patterns: "Show me all incidents in the payments domain in the last 30 days" or "What are the most common root cause categories?"

---

## 4. Feature Requirements

### 4.1 Core Features (Must-Have for Hackathon)

**F1: Event-Driven Trigger**
CHRONOS subscribes to OpenMetadata's webhook system. When a `testCaseResult` event fires with status `Failed` or `Aborted`, the investigation pipeline is triggered automatically. No manual invocation required.

- Subscribe to OpenMetadata event subscription API
- Filter for relevant event types (test failures, anomaly detections)
- Deduplicate rapid-fire events on the same entity within a configurable window (default: 5 minutes)
- Queue investigation requests for sequential processing

**F2: Autonomous Investigation Agent**
A LangGraph-based state machine that chains MCP tool calls across OpenMetadata and Graphiti to investigate root causes. The agent follows a structured investigation protocol but can adapt its path based on intermediate findings.

Investigation steps:

- **Step 1 — Scope the Failure:** Query OpenMetadata MCP for failed test details: which entity, which column, what test type, current status, when it last passed, historical pass/fail pattern
- **Step 2 — Temporal Diff:** Query Graphiti for all facts about the affected entity that changed in a configurable time window (default: 72 hours). Surface schema changes, description changes, tag additions/removals, ownership transfers
- **Step 3 — Upstream Lineage Walk:** Query OpenMetadata MCP for column-level lineage. For each upstream asset (up to configurable depth, default: 5 hops), check: recent schema changes, recent test failures, pipeline run status
- **Step 4 — Code Blast Radius:** Query GitNexus MCP for code files that reference the affected table/model. Cross-reference with git log to identify recent commits on those files
- **Step 5 — Downstream Impact Assessment:** Query OpenMetadata MCP for downstream lineage. For each downstream asset, retrieve tier classification and ownership. Rank by business criticality
- **Step 6 — Audit Log Correlation:** Query OpenMetadata audit logs (or Graphiti episodes) for all user and agent actions on the affected lineage path in the investigation time window
- **Step 7 — Root Cause Synthesis:** Feed all gathered context into LLM (via LiteLLM) that produces a structured incident report

**F3: Temporal Knowledge Graph Ingestion**
Continuous ingestion of OpenMetadata events into Graphiti's temporal knowledge graph.

- Subscribe to OpenMetadata's change event feed
- Map events to Graphiti episodes with appropriate metadata (entity type, entity FQN, event type, timestamp, user/agent who made the change)
- Define custom Graphiti entity types: `DataAsset`, `DataTest`, `Pipeline`, `Schema`, `Owner`, `CodeFile`
- Define custom edge types: `PRODUCES`, `CONSUMES`, `TESTS`, `OWNS`, `MODIFIED_BY`, `CAUSED_FAILURE`
- Graphiti handles temporal fact management: new facts automatically invalidate contradictory old facts

**F4: Structured Incident Report**
The investigation produces a machine-readable and human-readable incident report.

Report schema:

- `incident_id`: Unique identifier
- `detected_at`: Timestamp of test failure
- `affected_entity`: FQN of the entity where the test failed
- `test_name`: Name of the failed test
- `probable_root_cause`: Natural language description of the most likely cause
- `root_cause_category`: Enum — `SCHEMA_CHANGE`, `CODE_CHANGE`, `DATA_DRIFT`, `PIPELINE_FAILURE`, `PERMISSION_CHANGE`, `UNKNOWN`
- `confidence`: Float 0-1 indicating confidence in the root cause assessment
- `evidence_chain`: Ordered list of evidence items with source attribution (which graph, which query)
- `affected_downstream`: List of downstream assets with tier and ownership
- `business_impact`: Severity assessment based on tier classifications of affected assets
- `recommended_actions`: List of suggested remediation steps
- `investigation_timeline`: Sequence of agent steps with timestamps

**F5: Slack Notification**
Post the incident report to a configured Slack channel with rich formatting.

- Use Slack Block Kit for structured message layout
- Tag affected asset owners using OpenMetadata ownership -> Slack user mapping
- Include a link to the full incident report in the CHRONOS dashboard
- Support configurable notification routing: different channels for different data domains
- Include quick-action buttons: "Acknowledge", "Assign to me", "View in OpenMetadata"

**F6: React Frontend Dashboard**
A web dashboard showing investigation results and incident history.

- **Incident Timeline View:** Chronological list of incidents with status, severity, and root cause category
- **Investigation Detail View:** Step-by-step investigation replay showing what the agent found at each step
- **Lineage Failure Map:** Interactive React Flow graph showing the affected lineage path, with nodes colored by status (red = failing, yellow = at risk, green = healthy)
- **Temporal State Diff:** Side-by-side comparison of entity state at "last known good" vs. "failure detected"

### 4.2 Enhanced Features (Nice-to-Have)

**F7: OpenLineage Event Ingestion**
Accept OpenLineage events from pipeline orchestrators (Airflow, dbt) and ingest them into both OpenMetadata and Graphiti. This provides richer lineage data with actual runtime information (dataset facets, run facets, job facets).

**F8: Graphify Architecture Context**
Run Graphify on the data platform repository to build a multi-modal knowledge graph of code + documentation + architecture decisions. Use the `GRAPH_REPORT.md` to give the LLM architectural context during root cause synthesis.

- Index dbt project, ETL scripts, and pipeline definitions
- Generate community clusters and god-node identification
- Feed compressed architectural context into the synthesis prompt

**F9: Incident Pattern Recognition**
Use Graphiti's search capabilities to identify recurring incident patterns.

- "This is the 3rd time a test on `orders.total_amount` has failed this month"
- "Schema changes in the `raw.stripe` schema have caused 7 downstream failures in the last quarter"
- Surface these patterns in the incident report and dashboard

**F10: Prevention Mode (Grai-Inspired)**
A CI/CD integration that runs a lightweight CHRONOS check before code merges.

- When a PR modifies a dbt model or ETL script, query GitNexus and OpenMetadata to identify all downstream data quality tests
- Warn the developer about potential impact: "This change affects 3 Tier-1 tables with 12 active data quality tests"
- This is a stretch goal but would be extremely impressive for the hackathon demo

### 4.3 Agentic Metadata Infrastructure Features (Gap-Closing)

These features close the seven architectural gaps identified in *Is Agentic Metadata the Next Infrastructure Layer?* (The New Stack, Jan 2026) and transform CHRONOS from an "automated investigator" into a self-improving agentic metadata layer.

**F11: Self-Referential Investigation Memory (Gap 8)**
CHRONOS persists its own investigation traces as Graphiti episodes and queries them before new investigations. This is the single most important architectural upgrade.

- **Step 0 (new):** Before investigating, query `chronos-investigation-traces` group for past incidents on the same entity or matching pattern
- **Step 9 (new):** After notification, persist the full investigation trace (root cause, evidence, timing, cost) as a Graphiti episode
- "Related Past Incidents" section in the incident report with linkbacks
- Per-step telemetry episodes persisted in `chronos-step-telemetry` group
- Enables pattern recognition: "5 incidents in payments domain this month, 4 were SCHEMA_CHANGE"
- **Priority: HIGHEST** — cheapest change with biggest conceptual payoff (uses existing infrastructure)

**F12: Agentic Observability via Langfuse (Gap 1)**
Every CHRONOS investigation becomes a trace tree in Langfuse — persistent, replayable, annotatable, queryable.

- Self-hosted Langfuse via Docker Compose (Postgres-backed)
- LangChain callback handler wired into LangGraph for automatic trace capture
- Zero changes to agent logic — callback-based instrumentation
- Session ID = incident ID (groups all steps of one investigation)
- Cost per investigation automatically tracked with model/provider breakdown
- Failed investigations replayable + annotatable via Annotation Queues
- Production traces promotable into evaluation datasets (regression testing)
- **Priority: HIGH** — 1-day integration, massive observability depth

**F13: Compliance-Grade Provenance via W3C PROV-O (Gap 6)**
Generate GDPR/SOC2-ready audit artifacts from investigation traces using the W3C PROV-O standard.

- Python `prov` library generates ProvDocuments from IncidentReports
- Maps CHRONOS concepts to PROV-O: Agent (CHRONOS), Activity (investigation), Entity (data assets, evidence)
- Serializes to JSON-LD, RDF/Turtle, PROV-N formats
- New API endpoint: `GET /api/v1/incidents/{id}/provenance.jsonld`
- Aligns with OpenMetadata Standards' own use of PROV-O
- "Download as W3C PROV-O compliance artifact" button in dashboard
- **Priority: MEDIUM-HIGH** — stealth differentiator for enterprise judges

**F14: A2A Agent Card for Discovery (Gap 7)**
CHRONOS describes itself via the A2A Protocol Agent Card — making it discoverable by other agents.

- JSON agent card served at `/.well-known/agent-card.json`
- Describes capabilities (investigate, assess blast radius, generate compliance report)
- Follows Google/LF AI & Data A2A specification
- Demoable via `curl http://localhost:8100/.well-known/agent-card.json | jq`
- **Priority: MEDIUM** — 30 minutes, high conceptual payoff

**F15: Vendor-Neutral LLM Instrumentation via OpenLLMetry (Gap 2)**
Pure OpenTelemetry-based instrumentation so telemetry is portable to any backend.

- Traceloop SDK auto-instruments LiteLLM + LangGraph via OTel GenAI SemConv
- Single-line initialization at app startup
- `gen_ai.*` span attributes for model, provider, tokens, cost, finish reason
- Traces dual-routable: Langfuse for agent UI, Jaeger/SigNoz for infrastructure correlation
- **Priority: MEDIUM** — shows architectural sophistication

**F16: OTel GenAI Semantic Conventions (Gap 3)**
Standardized telemetry schema following OpenTelemetry GenAI SemConv v1.37+.

- `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.agent.id` attributes
- Custom `chronos.*` namespace for investigation-specific attributes
- Emerges mostly free from OpenLLMetry integration
- README compliance posture: "CHRONOS emits OpenTelemetry GenAI SemConv spans"
- **Priority: LOW** — free with F15

**F17: Continuous Quality Evaluation via DeepEval (Gap 4)**
Pytest-compatible evaluation tests for RCA quality regression detection.

- Custom G-Eval metric: does the root cause match the injected failure?
- FaithfulnessMetric: is the evidence chain faithful to gathered facts?
- 2-3 tests on the canonical demo scenario
- CI/CD integration via GitHub Actions
- Production traces → evaluation datasets (feedback loop)
- **Priority: MEDIUM** — engineering maturity signal

**F18: Retrieval Quality Evaluation via RAGAs (Gap 5)**
Evaluate Graphiti's retrieval quality per investigation step.

- Faithfulness, Answer Relevancy, Context Precision, Context Recall metrics
- Validates that Graphiti returns the right temporal facts
- Test: "Did Graphiti surface the schema change fact when queried?"
- **Priority: LOW-MEDIUM** — nice-to-have quality gate

---

## 5. Success Metrics

### 5.1 Hackathon Judging Criteria Mapping

| Criteria | How CHRONOS Addresses It |
|---|---|
| **Potential Impact** | Directly reduces data incident MTTR from ~45 min to ~2 min. Every data team has this pain. |
| **Creativity & Innovation** | Triple-graph architecture (metadata + temporal + code) is novel. Autonomous investigation vs. passive chatbot. |
| **Technical Excellence** | LangGraph state machine, 3 MCP servers, Graphiti temporal KG, LiteLLM routing, React Flow visualization |
| **Best Use of OpenMetadata** | Deep integration: MCP server, webhooks, lineage API, version history, audit logs, test results, tier classification, ownership |
| **User Experience** | Polished React dashboard with interactive lineage graph. Slack notifications with actionable context. Zero-config investigation. |
| **Presentation Quality** | Time-travel narrative fits hackathon theme. Triple-graph story is demo-friendly. Before/after MTTR comparison is quantifiable. |

### 5.2 Demo Success Criteria

- [ ] Live demo: Intentionally introduce a schema change in a dbt model
- [ ] CHRONOS detects the resulting test failure within 30 seconds
- [ ] Agent autonomously investigates and produces root cause report within 60 seconds
- [ ] Report correctly identifies the schema change as root cause with high confidence
- [ ] Downstream blast radius accurately shows all affected dashboards/tables
- [ ] Slack notification fires with owner tags and remediation guidance
- [ ] Dashboard shows interactive lineage graph with failure path highlighted
- [ ] Temporal diff view shows entity state before and after the breaking change

---

## 6. FOSS Tooling Stack

### 6.1 Core Platform

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **OpenMetadata** | Central metadata platform, MCP server, webhooks, lineage, governance | Apache 2.0 | Hackathon requirement. 70+ connectors, native MCP, comprehensive API |
| **Graphiti** (getzep/graphiti) | Temporal knowledge graph engine + self-referential investigation memory | Apache 2.0 | Bi-temporal model, episode-based ingestion, automatic fact invalidation, native MCP server, FalkorDB backend |
| **GitNexus** (abhigyanpatwari/GitNexus) | Code knowledge graph | MIT | AST-based code analysis, Cypher queries, KuzuDB embedded, MCP server, blast radius detection |
| **Graphify** (safishamsi/graphify) | Multi-modal knowledge graph for docs/architecture | MIT | Tree-sitter 25-language support, Leiden clustering, GRAPH_REPORT.md, multi-modal ingestion |

### 6.2 Agent & AI Layer

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **LangGraph** (langchain-ai/langgraph) | Agent orchestration as state machine | MIT | Explicit state management, conditional edges, built-in Graphiti integration, debuggable investigation flows |
| **LiteLLM** (BerriAI/litellm) | Unified LLM provider gateway | MIT | 100+ LLM providers through one API, fallback routing, cost tracking, rate limiting. Swap models without code changes |

### 6.3 Agentic Observability & Compliance Layer (NEW)

| Tool | Role | License | Why This Tool | Gap Addressed |
|---|---|---|---|---|
| **Langfuse** (langfuse/langfuse) | Agentic observability — trace trees, annotation, evaluation | MIT | Deepest LangGraph integration, self-hostable Docker, 21k+ stars, combines observability + prompt mgmt + eval | Gap 1 |
| **OpenLLMetry** (traceloop/openllmetry) | Vendor-neutral LLM instrumentation via OTel | Apache 2.0 | Pure OpenTelemetry-based, leads GenAI SemConv working group, single-line setup | Gap 2 |
| **OTel GenAI SemConv** (open-telemetry/semantic-conventions) | Standardized telemetry schema | Apache 2.0 | `gen_ai.*` span attributes, portable to any OTLP backend, industry convergence | Gap 3 |
| **DeepEval** (confident-ai/deepeval) | Continuous RCA quality evaluation | Apache 2.0 | Pytest-compatible, 50+ metrics, G-Eval for custom criteria, CI/CD native | Gap 4 |
| **RAGAs** (explodinggradients/ragas) | Retrieval quality evaluation for Graphiti | Apache 2.0 | Faithfulness, Relevancy, Precision, Recall metrics for RAG evaluation | Gap 5 |
| **W3C PROV-O** via `prov` (trungdong/prov) | Compliance-grade provenance | MIT | W3C Recommendation since 2013, JSON-LD/RDF/Turtle, GDPR/SOC2-ready | Gap 6 |
| **A2A Protocol** (a2aproject/A2A) | Agent discovery & self-description | Apache 2.0 | Linux Foundation project (Google-contributed), Agent Card spec, emerging standard | Gap 7 |

### 6.4 Data & Lineage

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **OpenLineage** (OpenLineage/OpenLineage) | Lineage event standard | Apache 2.0 | Native OpenMetadata 1.12 integration, vendor-neutral lineage events, Airflow/dbt/Spark integrations |
| **FalkorDB** | Graph database (Graphiti backend) | Server Side Public License | Redis-based, lightweight, Docker-ready, default Graphiti backend, low latency |

### 6.5 Frontend & Visualization

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **React Flow** (xyflow/xyflow) | Interactive lineage graph visualization | MIT | De facto standard for node-based UIs in React, handles large graphs, extensive customization |
| **React** + **Tailwind CSS** | Frontend framework + styling | MIT | Standard modern stack, fast prototyping |

### 6.6 Infrastructure

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **Docker Compose** | Local orchestration | Apache 2.0 | Single `docker-compose up` to run OpenMetadata + FalkorDB + Langfuse + CHRONOS |
| **FastAPI** | CHRONOS API server | MIT | Async Python, auto-generated OpenAPI docs, webhook endpoints |

---

## 7. Scope & Constraints

### 7.1 In Scope

- Event-driven investigation triggered by OpenMetadata test failures
- Multi-step autonomous investigation using LangGraph + 3 MCP servers
- Temporal knowledge graph construction and querying via Graphiti
- Self-referential investigation memory: CHRONOS learns from its own past investigations (F11)
- Code-level blast radius analysis via GitNexus
- Architecture context enrichment via Graphify
- Structured incident reports with confidence scoring
- W3C PROV-O compliance artifact generation for GDPR/SOC2 audits (F13)
- Slack notification with owner tagging and remediation guidance
- React dashboard with interactive lineage visualization
- OpenLineage event ingestion for richer lineage data
- LiteLLM for model-agnostic LLM inference
- Agentic observability via Langfuse trace trees (F12)
- Vendor-neutral instrumentation via OpenLLMetry + OTel GenAI SemConv (F15/F16)
- A2A Agent Card for agent discovery (F14)
- RCA quality evaluation via DeepEval (F17)

### 7.2 Out of Scope

- Production-grade auth/RBAC (will use OpenMetadata's built-in bot auth for the demo)
- Multi-tenant isolation (single-tenant demo)
- Custom alerting rules engine (will use OpenMetadata's native alerting as the trigger)
- Mobile UI
- Real-time streaming investigation (batch investigation per event is sufficient)
- Integration with PagerDuty, Opsgenie, or other incident management platforms (Slack only for hackathon)

### 7.3 Assumptions

- OpenMetadata is deployed locally via Docker with sample metadata ingested
- At least one data source is configured with active data quality tests
- A dbt project or SQL transformation repository is available for GitNexus indexing
- LLM API access is available (via LiteLLM — any provider: OpenAI, Anthropic, Groq, etc.)
- Slack workspace is available for notification testing

### 7.4 Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **MCP server compatibility issues** between OpenMetadata, Graphiti, and GitNexus | Agent can't query all three graphs | Medium | Test MCP connections early (Day 1-2). Fall back to direct REST API calls if MCP fails for any tool |
| **Graphiti ingestion latency** — LLM calls for entity extraction may be slow | Investigation delayed | Medium | Use fast models via LiteLLM (Groq/Llama for extraction). Batch ingest during off-peak. Cache extracted entities |
| **GitNexus indexing scope** — may not support all file types in the data platform repo | Incomplete code blast radius | Low | GitNexus supports Python, SQL, TypeScript. dbt models are SQL. If gaps exist, supplement with git log analysis |
| **Demo data realism** — canned data may not produce convincing investigation results | Weak demo | Medium | Create a realistic multi-hop lineage scenario with intentional failure injection. Script the demo flow |
| **Scope creep across 8+ tools** | Can't finish in 10 days | High | Strict priority tiers. Core (F1-F6) must ship. Enhanced (F7-F10) only if time permits. Cut Graphify before GitNexus before Graphiti |

---

## 8. Timeline

| Phase | Days | Deliverables |
|---|---|---|
| **Foundation** | 1-3 | OpenMetadata Docker running with sample data. Graphiti + FalkorDB running with test episodes. GitNexus indexed on sample dbt repo. All 3 MCP servers verified. LiteLLM configured. **Langfuse Docker deployed.** |
| **Agent Core** | 4-6 | LangGraph investigation state machine with all 9 steps (including Step 0: prior_investigations and Step 9: persist_trace). End-to-end investigation with **self-referential memory loop (F11)**. Graphiti episode ingestion pipeline. **Langfuse callback wired in (F12).** |
| **Integration & UI** | 7-8 | React Flow dashboard with lineage failure map. Slack notification integration. **W3C PROV-O endpoint (F13). A2A Agent Card (F14). OpenLLMetry (F15).** OpenLineage event ingestion (if time). |
| **Polish & Demo** | 9-10 | Demo scenario scripted and tested. **DeepEval tests on canonical scenario (F17).** README with architecture diagrams. Video recording. Edge case handling. |

---

## 9. Competitive Differentiation

### 9.1 What Other Hackathon Teams Will Build

Based on the six tracks and the obvious interpretations:

- **T-01 chatbots:** "Ask questions about your metadata in natural language" using OpenMetadata MCP. This is the default, low-differentiation play.
- **T-02 dashboards:** Static monitoring dashboards that display test results. No investigation, no automation.
- **T-03 connectors:** New data source connectors. Useful but narrow.
- **T-06 taggers:** PII detection or auto-classification tools. OpenMetadata already ships this natively.

### 9.2 Why CHRONOS Stands Apart

- **Autonomous vs. reactive.** Other MCP projects wait for user queries. CHRONOS acts on events.
- **Multi-graph reasoning.** Nobody else will combine metadata + temporal + code graphs.
- **Temporal intelligence.** Graphiti's bi-temporal model is architecturally novel for metadata use cases.
- **Actionable output.** Not just "here's what I found" but "here's the probable cause, the blast radius, the affected stakeholders, and the recommended fix."
- **Self-improving over time.** CHRONOS learns from its own investigation traces — second-time incidents include past context automatically.
- **Compliance-ready.** W3C PROV-O audit artifacts position CHRONOS for enterprise adoption beyond the hackathon.
- **Standards-aligned.** OpenTelemetry GenAI SemConv, A2A Agent Card, W3C PROV-O — every choice maps to an industry standard.
- **Observable from day one.** Langfuse trace trees show every investigation step, LLM call, and cost — production-grade from the start.
- **Cross-track coverage.** Touching T-01 + T-02 + T-05 + T-06 demonstrates breadth and depth.

---

## 10. Open Questions

1. ~~**LLM model selection:**~~ **RESOLVED.** Claude Sonnet for synthesis, Groq Llama 3.3 70B for extraction, GPT-4.1 Mini as fallback. Configured via LiteLLM model routing.

2. ~~**Graphiti entity ontology:**~~ **RESOLVED.** `DataAsset`, `DataTest`, `Pipeline`, `Schema`, `Owner`, `CodeFile`, `Incident` validated. New groups: `chronos-investigation-traces` and `chronos-step-telemetry` for self-referential memory.

3. ~~**Investigation depth limits:**~~ **RESOLVED.** Configurable with sensible defaults (5 hops up, 3 down). Environment variables: `LINEAGE_DEPTH_UPSTREAM`, `LINEAGE_DEPTH_DOWNSTREAM`.

4. ~~**Demo scenario design:**~~ **RESOLVED.** Schema change in stg_payments.sql cascading to executive dashboard. With v2.0 upgrades, demo also shows: (a) Langfuse trace tree, (b) PROV-O download, (c) second investigation referencing "this happened before" via self-referential memory.

5. ~~**GitNexus vs. Graphify priority:**~~ **RESOLVED.** GitNexus first, Graphify if time permits.

6. **Langfuse vs. inline observability:** Langfuse adds a Docker dependency (Postgres + app). For minimal deployments, should we support a "Langfuse-free" mode with file-based trace export? **Decision: Yes — make Langfuse optional via feature flag.**

7. **PROV-O serialization format:** JSON-LD is most interoperable, Turtle is most human-readable, PROV-N is most compact. **Decision: Default to JSON-LD, support all three as query parameter.**

---

## 11. Gap-to-Feature Mapping (Reference)

| Agentic Metadata Gap (The New Stack, Jan 2026) | CHRONOS Feature | Priority | Effort |
|---|---|---|---|
| 1. Agentic observability & tracing | F12: Langfuse | HIGH | 1 day |
| 2. Vendor-neutral LLM instrumentation | F15: OpenLLMetry | MEDIUM | 0.5 day |
| 3. Standardized telemetry schema | F16: OTel GenAI SemConv | LOW | Free w/ F15 |
| 4. Continuous improvement / regression tests | F17: DeepEval | MEDIUM | 0.5 day |
| 5. Retrieval quality evaluation | F18: RAGAs | LOW-MEDIUM | 1 day |
| 6. Compliance-grade provenance | F13: W3C PROV-O | MEDIUM-HIGH | 0.5 day |
| 7. Agent discovery & self-description | F14: A2A Agent Card | MEDIUM | 30 min |
| 8. Self-referential metadata loop | F11: Graphiti self-memory | HIGHEST | 0.5 day |

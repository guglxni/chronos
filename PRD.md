# CHRONOS — Product Requirements Document

**Autonomous Data Incident Root Cause Analysis Agent**
*"Don't just detect the anomaly. Travel back through the timeline and find where it broke."*

**Hackathon:** OpenMetadata Paradox Hackathon (WeMakeDevs x OpenMetadata)
**Dates:** April 17 - April 26, 2026
**Track Coverage:** T-01 (MCP & AI Agents), T-02 (Data Observability), T-05 (Community & Comms), T-06 (Governance & Classification)
**Version:** 1.0
**Author:** Aaryan

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

CHRONOS is an autonomous data incident investigation agent that operates across three knowledge graphs simultaneously to identify root causes, assess blast radius, and communicate findings — reducing mean time to resolution (MTTR) from ~45 minutes to ~2 minutes.

When a data quality test fails, CHRONOS autonomously:

1. Detects the failure via OpenMetadata webhooks
2. Investigates the root cause by reasoning across metadata, temporal state, and code structure
3. Assesses downstream impact by tracing lineage and evaluating business criticality
4. Produces a structured incident report with probable cause, confidence level, and remediation guidance
5. Notifies affected stakeholders via Slack with contextual, role-appropriate information
6. Remembers the incident in a temporal knowledge graph for pattern recognition over time

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
| **Graphiti** (getzep/graphiti) | Temporal knowledge graph engine | Apache 2.0 | Bi-temporal model, episode-based ingestion, automatic fact invalidation, native MCP server, FalkorDB backend |
| **GitNexus** (abhigyanpatwari/GitNexus) | Code knowledge graph | MIT | AST-based code analysis, Cypher queries, KuzuDB embedded, MCP server, blast radius detection |
| **Graphify** (safishamsi/graphify) | Multi-modal knowledge graph for docs/architecture | MIT | Tree-sitter 25-language support, Leiden clustering, GRAPH_REPORT.md, multi-modal ingestion |

### 6.2 Agent & AI Layer

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **LangGraph** (langchain-ai/langgraph) | Agent orchestration as state machine | MIT | Explicit state management, conditional edges, built-in Graphiti integration, debuggable investigation flows |
| **LiteLLM** (BerriAI/litellm) | Unified LLM provider gateway | MIT | 100+ LLM providers through one API, fallback routing, cost tracking, rate limiting. Swap models without code changes |

### 6.3 Data & Lineage

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **OpenLineage** (OpenLineage/OpenLineage) | Lineage event standard | Apache 2.0 | Native OpenMetadata 1.12 integration, vendor-neutral lineage events, Airflow/dbt/Spark integrations |
| **FalkorDB** | Graph database (Graphiti backend) | Server Side Public License | Redis-based, lightweight, Docker-ready, default Graphiti backend, low latency |

### 6.4 Frontend & Visualization

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **React Flow** (xyflow/xyflow) | Interactive lineage graph visualization | MIT | De facto standard for node-based UIs in React, handles large graphs, extensive customization |
| **React** + **Tailwind CSS** | Frontend framework + styling | MIT | Standard modern stack, fast prototyping |

### 6.5 Infrastructure

| Tool | Role | License | Why This Tool |
|---|---|---|---|
| **Docker Compose** | Local orchestration | Apache 2.0 | Single `docker-compose up` to run OpenMetadata + FalkorDB + CHRONOS |
| **FastAPI** | CHRONOS API server | MIT | Async Python, auto-generated OpenAPI docs, webhook endpoints |

---

## 7. Scope & Constraints

### 7.1 In Scope

- Event-driven investigation triggered by OpenMetadata test failures
- Multi-step autonomous investigation using LangGraph + 3 MCP servers
- Temporal knowledge graph construction and querying via Graphiti
- Code-level blast radius analysis via GitNexus
- Architecture context enrichment via Graphify
- Structured incident reports with confidence scoring
- Slack notification with owner tagging and remediation guidance
- React dashboard with interactive lineage visualization
- OpenLineage event ingestion for richer lineage data
- LiteLLM for model-agnostic LLM inference

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
| **Foundation** | 1-3 | OpenMetadata Docker running with sample data. Graphiti + FalkorDB running with test episodes. GitNexus indexed on sample dbt repo. All 3 MCP servers verified. LiteLLM configured with at least one provider. |
| **Agent Core** | 4-6 | LangGraph investigation state machine with all 7 steps implemented. End-to-end investigation from test failure to structured report. Graphiti episode ingestion pipeline from OpenMetadata webhooks. |
| **Integration & UI** | 7-8 | React Flow dashboard with lineage failure map. Slack notification integration. OpenLineage event ingestion (if time). Graphify architecture context (if time). |
| **Polish & Demo** | 9-10 | Demo scenario scripted and tested. README with architecture diagrams. Video recording. Edge case handling. Performance optimization. |

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
- **Cross-track coverage.** Touching T-01 + T-02 + T-05 + T-06 demonstrates breadth and depth.

---

## 10. Open Questions

1. **LLM model selection:** What's the optimal model for root cause synthesis via LiteLLM? Strong reasoning (Claude Sonnet, GPT-4.1) vs. fast/cheap (Groq Llama, Gemini Flash)? Consider using fast models for entity extraction and strong models for synthesis.

2. **Graphiti entity ontology:** What custom entity types best represent metadata concepts? Proposed: `DataAsset`, `DataTest`, `Pipeline`, `Schema`, `Owner`, `CodeFile`, `Incident`. Needs validation against actual OpenMetadata event payloads.

3. **Investigation depth limits:** How deep should lineage walking go before the agent stops? Configurable with a sensible default (5 hops upstream, 3 downstream). Need to prevent infinite loops on circular lineage.

4. **Demo scenario design:** What's the most compelling failure scenario to demonstrate? Proposed: Schema change in a source table cascading through a dbt model to break a dashboard used by executives. This hits all the emotional notes.

5. **GitNexus vs. Graphify priority:** If time is tight, which code analysis tool adds more value? GitNexus provides direct code-level blast radius (higher impact). Graphify provides architectural context (nice for enrichment). Recommendation: GitNexus first, Graphify if time permits.

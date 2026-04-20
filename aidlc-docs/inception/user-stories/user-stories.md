# CHRONOS — User Stories

## Personas

### Persona 1: Priya — On-Call Data Engineer
- **Role**: Data Engineer on PagerDuty rotation
- **Context**: Mid-size company using dbt + Snowflake + Airflow
- **Pain**: Spends 30-60 min per incident on manual investigation
- **Goal**: Get actionable root cause analysis in < 2 minutes

### Persona 2: Alex — Analytics Engineer  
- **Role**: dbt model maintainer
- **Context**: Pushes schema/model changes that may break downstream tests
- **Pain**: Doesn't know when his changes cause failures until manual triage
- **Goal**: Be immediately tagged with specific commit + file when his change causes issues

### Persona 3: Meera — Data Platform Lead
- **Role**: Platform team leader
- **Context**: Needs aggregate incident intelligence for prioritization
- **Pain**: No persistent memory of past incidents or recurring patterns
- **Goal**: Query incident patterns across time for strategic decisions

---

## User Stories

### Epic 1: Automated Incident Detection (F1)

**US-1.1**: As Priya, I want CHRONOS to automatically detect test failures via OpenMetadata webhooks, so that investigation starts without manual intervention.
- **Acceptance**: Webhook endpoint receives events, deduplicates within 5-min window, queues for investigation
- **Priority**: Must-Have

**US-1.2**: As Priya, I want duplicate alerts for the same entity to be suppressed within a configurable window, so that I don't get spammed during cascading failures.
- **Acceptance**: Events on same entity_fqn within dedup window are collapsed into single investigation
- **Priority**: Must-Have

### Epic 2: Autonomous Investigation (F2)

**US-2.1**: As Priya, I want CHRONOS to scope the failure by gathering test details and failure history, so that the investigation starts with the right context.
- **Acceptance**: Step 1 retrieves test details, affected entity, affected columns, last passed timestamp, failure history (20 recent results)
- **Priority**: Must-Have

**US-2.2**: As Priya, I want CHRONOS to check what changed temporally in the investigation window, so that I can see schema changes, description changes, tag modifications.
- **Acceptance**: Graphiti temporal facts + OpenMetadata version history diff within configurable window (default: 72h)
- **Priority**: Must-Have

**US-2.3**: As Priya, I want CHRONOS to walk upstream lineage and check each node, so that I don't have to manually trace the data pipeline.
- **Acceptance**: Upstream lineage traversal to configurable depth (default: 5 hops), checks test results + version history at each node
- **Priority**: Must-Have

**US-2.4**: As Alex, I want CHRONOS to identify which code files are implicated and check recent commits, so that I know exactly where to look.
- **Acceptance**: GitNexus code search for table references, neighbor traversal, git log cross-reference for recent commits
- **Priority**: Must-Have

**US-2.5**: As Priya, I want CHRONOS to assess downstream blast radius with business criticality, so that I know how urgent the fix is.
- **Acceptance**: Downstream lineage to configurable depth (default: 3 hops), retrieves tier classification + ownership for each downstream asset
- **Priority**: Must-Have

**US-2.6**: As Priya, I want CHRONOS to cross-reference audit logs for suspicious actions, so that human error or malicious changes are surfaced.
- **Acceptance**: Audit log query within investigation window, Graphiti fact cross-reference
- **Priority**: Must-Have

**US-2.7**: As Priya, I want CHRONOS to synthesize evidence into a structured root cause report, so that I get an actionable, confidence-scored diagnosis.
- **Acceptance**: LLM-powered synthesis via LiteLLM, IncidentReport Pydantic schema output, confidence 0-1, root_cause_category enum
- **Priority**: Must-Have

### Epic 3: Temporal Knowledge (F3)

**US-3.1**: As Meera, I want all OpenMetadata events ingested into Graphiti as temporal episodes, so that we build institutional memory over time.
- **Acceptance**: OpenMetadata events mapped to Graphiti episodes with bi-temporal metadata, custom entity types defined
- **Priority**: Must-Have

**US-3.2**: As Meera, I want to query historical state at any point in time, so that I can reconstruct "what was true" during a past incident.
- **Acceptance**: Graphiti search_facts returns temporally-filtered results with valid_from/valid_until windows
- **Priority**: Must-Have

### Epic 4: Communication (F5)

**US-4.1**: As Priya, I want a Slack notification with severity, root cause, blast radius, and remediation steps, so that I can act immediately from Slack.
- **Acceptance**: Slack Block Kit message with severity emoji, root cause section, affected downstream (with Tier-1 highlighted), remediation actions, action buttons
- **Priority**: Must-Have

**US-4.2**: As Alex, I want to be tagged in Slack when my code change causes a failure, so that I'm immediately aware.
- **Acceptance**: Owner-to-Slack-ID mapping, @-mentions in notification for affected asset owners
- **Priority**: Must-Have

### Epic 5: Dashboard (F6)

**US-5.1**: As Priya, I want a dashboard showing incident timeline with severity and category, so that I can see all recent incidents at a glance.
- **Acceptance**: Chronological list with status, severity badge, root cause category icon, investigation duration
- **Priority**: Must-Have

**US-5.2**: As Priya, I want to replay an investigation step-by-step, so that I can verify the agent's reasoning.
- **Acceptance**: Step-by-step timeline showing what was found at each investigation step with timestamps
- **Priority**: Must-Have

**US-5.3**: As Priya, I want an interactive lineage map with failure path highlighted, so that I can visually see the blast radius.
- **Acceptance**: React Flow graph with colored nodes (red=failing, yellow=at_risk, green=healthy), animated edges for failure path
- **Priority**: Must-Have

**US-5.4**: As Priya, I want a temporal diff view showing entity state before/after the breaking change, so that I can see exactly what changed.
- **Acceptance**: Side-by-side comparison of entity state at "last known good" vs "failure detected"
- **Priority**: Must-Have

### Epic 6: Patterns (F9 — Nice-to-Have)

**US-6.1**: As Meera, I want CHRONOS to identify recurring incident patterns, so that we can invest in prevention for the most impactful areas.
- **Acceptance**: Graphiti pattern search surfaces "3rd time this month" style insights in reports
- **Priority**: Nice-to-Have

### Epic 7: Agentic Metadata Infrastructure (F11-F18 — Gap-Closing)

**US-7.1**: As Priya, I want CHRONOS to check past investigations of the same entity before starting a new one, so that I get richer context like "this happened before; last time the root cause was X."
- **Acceptance**: Step 0 queries `chronos-investigation-traces` Graphiti group; "Related Past Incidents" section appears in report when matches exist
- **Priority**: Must-Have
- **Feature**: F11 (Self-Referential Memory — Gap 8)

**US-7.2**: As Priya, I want each completed investigation to be persisted as a Graphiti episode, so that CHRONOS builds institutional memory over time.
- **Acceptance**: Step 9 persists full investigation trace + per-step telemetry to Graphiti; episodes searchable by entity FQN or root cause category
- **Priority**: Must-Have
- **Feature**: F11 (Self-Referential Memory — Gap 8)

**US-7.3**: As Meera, I want every investigation visible as a trace tree in Langfuse, so that I can replay steps, see token/cost breakdowns, and annotate failures.
- **Acceptance**: Langfuse UI shows trace per incident (session_id = incident_id); each step is a span with duration + token count; cost per investigation computed
- **Priority**: Must-Have
- **Feature**: F12 (Langfuse — Gap 1)

**US-7.4**: As Meera, I want to download a W3C PROV-O compliance artifact for any incident, so that our legal team has GDPR/SOC2-ready audit trails.
- **Acceptance**: `GET /api/v1/incidents/{id}/provenance.jsonld` returns valid PROV-O JSON-LD; also supports `.ttl` (Turtle) format; maps CHRONOS Agent→Activity→Entity
- **Priority**: Should-Have
- **Feature**: F13 (W3C PROV-O — Gap 6)

**US-7.5**: As Alex, I want other agents in our infrastructure to discover CHRONOS's capabilities programmatically, so that I can build orchestration workflows.
- **Acceptance**: `GET /.well-known/agent-card.json` returns valid A2A Agent Card with 3 skills (investigate, blast radius, compliance report)
- **Priority**: Should-Have
- **Feature**: F14 (A2A Agent Card — Gap 7)

**US-7.6**: As Meera, I want CHRONOS's LLM telemetry to follow OpenTelemetry GenAI SemConv, so that our existing monitoring infrastructure can ingest it.
- **Acceptance**: OpenLLMetry Traceloop SDK initialized at app startup; `gen_ai.*` span attributes emitted for all LiteLLM calls
- **Priority**: Nice-to-Have
- **Feature**: F15/F16 (OpenLLMetry + OTel GenAI SemConv — Gaps 2/3)

**US-7.7**: As Alex, I want CI to catch RCA quality regressions when prompts or models change, so that we don't ship worse root cause analysis silently.
- **Acceptance**: `pytest tests/evals/` runs DeepEval G-Eval + FaithfulnessMetric on canonical demo scenario; GitHub Actions workflow on PR
- **Priority**: Should-Have
- **Feature**: F17 (DeepEval — Gap 4)

**US-7.8**: As Meera, I want to validate that Graphiti returns the right temporal facts during investigation, so that retrieval quality is measured.
- **Acceptance**: RAGAs context_recall > 0.8 and context_precision > 0.6 on seeded schema change scenario
- **Priority**: Nice-to-Have
- **Feature**: F18 (RAGAs — Gap 5)

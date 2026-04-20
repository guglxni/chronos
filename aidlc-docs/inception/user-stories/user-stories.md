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

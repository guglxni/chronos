# Graph Report - .  (2026-04-24)

## Corpus Check
- 125 files · ~79,840 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 769 nodes · 1549 edges · 46 communities detected
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 503 edges (avg confidence: 0.63)
- Token cost: 18,500 input · 5,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Data Models & RCA Schemas|Data Models & RCA Schemas]]
- [[_COMMUNITY_AIDLC Development Methodology|AIDLC Development Methodology]]
- [[_COMMUNITY_LangGraph Investigation Pipeline|LangGraph Investigation Pipeline]]
- [[_COMMUNITY_Incident Store & Stats API|Incident Store & Stats API]]
- [[_COMMUNITY_Webhook & Investigation Runner|Webhook & Investigation Runner]]
- [[_COMMUNITY_MCP Client Layer|MCP Client Layer]]
- [[_COMMUNITY_Incidents API & PROV-O|Incidents API & PROV-O]]
- [[_COMMUNITY_FastAPI Middleware & HTTP|FastAPI Middleware & HTTP]]
- [[_COMMUNITY_Settings & Configuration|Settings & Configuration]]
- [[_COMMUNITY_Audit Correlation Node|Audit Correlation Node]]
- [[_COMMUNITY_Event Deduplication|Event Deduplication]]
- [[_COMMUNITY_Security & Auth Dependencies|Security & Auth Dependencies]]
- [[_COMMUNITY_Slack Notifications|Slack Notifications]]
- [[_COMMUNITY_LLM Client & Synthesis|LLM Client & Synthesis]]
- [[_COMMUNITY_Audit Findings & Security|Audit Findings & Security]]
- [[_COMMUNITY_Webhook Test Helpers|Webhook Test Helpers]]
- [[_COMMUNITY_Frontend Animation|Frontend Animation]]
- [[_COMMUNITY_React Error Boundary|React Error Boundary]]
- [[_COMMUNITY_Dashboard View|Dashboard View]]
- [[_COMMUNITY_Rate Limiting|Rate Limiting]]
- [[_COMMUNITY_Incident Detail View|Incident Detail View]]
- [[_COMMUNITY_Incident Model Tests|Incident Model Tests]]
- [[_COMMUNITY_Graphify Context Enrichment|Graphify Context Enrichment]]
- [[_COMMUNITY_Investigation Replay UI|Investigation Replay UI]]
- [[_COMMUNITY_Demo Inject Script|Demo Inject Script]]
- [[_COMMUNITY_Lineage Failure Map|Lineage Failure Map]]
- [[_COMMUNITY_SSE Real-Time Hook|SSE Real-Time Hook]]
- [[_COMMUNITY_Frontend API Client|Frontend API Client]]
- [[_COMMUNITY_Import Integrity Tests|Import Integrity Tests]]
- [[_COMMUNITY_LLM Prompt Templates|LLM Prompt Templates]]
- [[_COMMUNITY_Core Runtime Init|Core Runtime Init]]
- [[_COMMUNITY_Evidence Chain UI|Evidence Chain UI]]
- [[_COMMUNITY_Temporal Diff UI|Temporal Diff UI]]
- [[_COMMUNITY_Severity Badge|Severity Badge]]
- [[_COMMUNITY_Provenance Download|Provenance Download]]
- [[_COMMUNITY_Loading Spinner|Loading Spinner]]
- [[_COMMUNITY_Blast Radius Panel|Blast Radius Panel]]
- [[_COMMUNITY_Incident Card|Incident Card]]
- [[_COMMUNITY_Empty State|Empty State]]
- [[_COMMUNITY_Truncated Text|Truncated Text]]
- [[_COMMUNITY_Demo Fixtures|Demo Fixtures]]
- [[_COMMUNITY_CORS Origins Helper|CORS Origins Helper]]
- [[_COMMUNITY_Startup Validation|Startup Validation]]
- [[_COMMUNITY_Webhook Signing Property|Webhook Signing Property]]
- [[_COMMUNITY_Project Directory Structure|Project Directory Structure]]
- [[_COMMUNITY_Wave 7 Audit Summary|Wave 7 Audit Summary]]

## God Nodes (most connected - your core abstractions)
1. `get()` - 64 edges
2. `IncidentReport` - 59 edges
3. `InvestigationState` - 38 edges
4. `RootCauseCategory` - 33 edges
5. `MCPServerType` - 24 edges
6. `store()` - 22 edges
7. `IncidentStatus` - 20 edges
8. `generate_provenance()` - 19 edges
9. `CHRONOS Product Requirements Document` - 18 edges
10. `_base_state()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `10-Step Investigation Pipeline (LangGraph)` --semantically_similar_to--> `F2: Autonomous Investigation Agent (10-Step LangGraph Pipeline)`  [INFERRED] [semantically similar]
  README.md → PRD.md
- `Vercel AI Gateway Replacing LiteLLM Proxy` --semantically_similar_to--> `LiteLLM — Unified LLM Provider Gateway`  [INFERRED] [semantically similar]
  VERCEL_DEPLOYMENT_PLAN.md → PRD.md
- `Vercel Workflow DevKit (WDK) — Post-Hackathon Consideration` --conceptually_related_to--> `F2: Autonomous Investigation Agent (10-Step LangGraph Pipeline)`  [INFERRED]
  VERCEL_DEPLOYMENT_PLAN.md → PRD.md
- `AIDLC State: Construction Phase Complete, Build/Test Pending` --references--> `AGENTS.md — AIDLC Adaptive Software Development Workflow`  [INFERRED]
  aidlc-docs/aidlc-state.md → AGENTS.md
- `Persist a completed incident report.      Accepts either a typed ``IncidentRepor` --uses--> `IncidentReport`  [INFERRED]
  /Volumes/MacExt/chronos/chronos/core/incident_store.py → /Volumes/MacExt/chronos/chronos/models/incident.py

## Hyperedges (group relationships)
- **Triple-Graph MCP Investigation: OpenMetadata + Graphiti + GitNexus power the 10-step autonomous pipeline** — prd_metadata_graph, prd_temporal_graph, prd_code_graph, prd_f2_investigation_agent, readme_investigation_pipeline [EXTRACTED 0.95]
- **Agentic Metadata Gap-Closing Features: F11-F18 collectively close 8 gaps from The New Stack article** — prd_f11_self_referential_memory, prd_f12_langfuse_observability, prd_f13_prov_o, prd_f14_a2a_agent_card, prd_f15_openllmetry, prd_f16_otel_semconv, prd_f17_deepeval, prd_f18_ragas [EXTRACTED 0.93]
- **Hybrid Deployment: Vercel Static Frontend + Fly.io Always-On Backend + Neon Postgres + Langfuse Cloud** — vercel_plan_frontend_only, vercel_plan_flyio_backend, vercel_plan_neon_postgres, vercel_plan_langfuse_cloud [EXTRACTED 0.90]

## Communities

### Community 0 - "Data Models & RCA Schemas"
Cohesion: 0.11
Nodes (62): BaseModel, DataAssetEntity, DataTestEntity, GraphitiEdge, IncidentEntity, PipelineRunEntity, SchemaStateEntity, AffectedAsset (+54 more)

### Community 1 - "AIDLC Development Methodology"
Cohesion: 0.03
Nodes (72): AIDLC Mandatory Audit Log (audit.md) — Complete Raw Input Capture, AIDLC Construction Phase (Per-Unit Loop: Design, NFR, Code Gen), AIDLC Inception Phase (Requirements, Stories, Design, Units), AGENTS.md — AIDLC Adaptive Software Development Workflow, AIDLC Audit Log (audit.md) — Timestamped Interaction Record, 7 Construction Units (Core Infra, MCP, Agent, Output, API, Frontend, Agentic Metadata), AIDLC State: Construction Phase Complete, Build/Test Pending, Application Design — Triple-Graph + Event-Driven Agent Architecture (+64 more)

### Community 2 - "LangGraph Investigation Pipeline"
Cohesion: 0.06
Nodes (49): code_blast_radius_node(), Step 4 — Code Blast Radius  Uses GitNexus to find code files (SQL, Python, dbt m, Search GitNexus for code files referencing the affected entity., build_investigation_graph(), get_investigation_graph(), get_langfuse_callback(), LangGraph investigation state machine.  Wires all 10 nodes in a linear pipeline, Construct and compile the 10-step investigation graph. (+41 more)

### Community 3 - "Incident Store & Stats API"
Cohesion: 0.09
Nodes (52): get(), get_or_raise(), list_all(), In-memory incident store — a single source of truth for all completed investigat, Persist a completed incident report.      Accepts either a typed ``IncidentRepor, Return the incident or None if not found., Return the incident or raise ``KeyError``.      Route handlers should catch this, Return all stored incidents (insertion order preserved — Python 3.7+). (+44 more)

### Community 4 - "Webhook & Investigation Runner"
Cohesion: 0.06
Nodes (40): InvestigationTrigger, OpenLineageDataset, OpenLineageFacet, OpenLineageRunEvent, OpenMetadataTestCase, OpenMetadataTestResult, OpenMetadataWebhookPayload, ingest_om_event() (+32 more)

### Community 5 - "MCP Client Layer"
Cohesion: 0.09
Nodes (39): MCPClient, _next_rpc_id(), Unified async MCP client for CHRONOS.  Maintains persistent httpx sessions for H, Close all open HTTP sessions., Singleton async MCP client.      Usage:         result = await mcp_client.call_t, Return (or lazily create) a persistent httpx session for a server., Call a named tool on the specified MCP server.          Sends a JSON-RPC 2.0 ``t, get_mcp_configs() (+31 more)

### Community 6 - "Incidents API & PROV-O"
Cohesion: 0.13
Nodes (29): acknowledge_incident(), get_incident(), _get_incident_or_404(), get_provenance_jsonld(), get_provenance_provn(), get_provenance_turtle(), list_incidents(), resolve_incident() (+21 more)

### Community 7 - "FastAPI Middleware & HTTP"
Cohesion: 0.08
Nodes (22): errorResponse(), jsonResponse(), enforce_body_size(), _handle_rate_limit(), health(), lifespan(), CHRONOS FastAPI application entry point.  Mounts all route groups, registers mid, Application lifespan — runs setup before first request, teardown on shutdown. (+14 more)

### Community 8 - "Settings & Configuration"
Cohesion: 0.16
Nodes (27): BaseSettings, loadSettings(), maskSecret(), Settings(), _dev(), _prod(), Unit tests for chronos.config.settings.Settings model_validator.  All tests cons, Create a minimal valid development Settings without loading .env. (+19 more)

### Community 9 - "Audit Correlation Node"
Cohesion: 0.13
Nodes (19): audit_correlation_node(), Step 6 — Audit Correlation  Fetches OpenMetadata audit logs for the affected ent, Fetch audit logs and cross-reference with Graphiti user-action facts., downstream_impact_node(), Step 5 — Downstream Impact  Walks downstream lineage to identify all assets that, Walk downstream lineage and classify business impact by tier., Step 1 — Scope Failure  Fetches the failing test case and affected entity detail, Fetch test details and entity info; extract affected columns. (+11 more)

### Community 10 - "Event Deduplication"
Cohesion: 0.14
Nodes (15): EventDeduplicator, In-memory event deduplicator with a sliding TTL window.  Prevents the same entit, Thread-safe-ish (single-process async) deduplicator backed by a plain dict., Return True if ``event_key`` was already seen within the dedup window.         R, Remove entries older than the dedup window., Clear all seen events (useful for testing)., RAGAs Graphiti retrieval quality tests (F18).  Evaluates whether Graphiti's sema, Unit test — InvestigationState accepts partial dicts (total=False). (+7 more)

### Community 11 - "Security & Auth Dependencies"
Cohesion: 0.17
Nodes (15): _compute_hmac(), FastAPI dependencies for CHRONOS API security.  Provides HMAC-SHA256 signature v, Dependency: validate OpenMetadata webhook HMAC signature (with optional replay g, Dependency: validate OpenLineage webhook HMAC signature (with optional replay gu, Return a 'sha256=<hex>' HMAC digest.      When ``timestamp`` is provided the sig, Validate the HMAC-SHA256 signature header against the raw request body.      Whe, verify_openlineage_signature(), verify_openmetadata_signature() (+7 more)

### Community 12 - "Slack Notifications"
Cohesion: 0.21
Nodes (14): _load_slack_user_map(), Slack Block Kit notification sender for CHRONOS incident reports.  Sends a rich,, Parse config/slack_users.yaml once at import time.      We parse manually (``key, Render an owner name as a Slack mention using the YAML map., Send a rich Block Kit Slack notification for a completed investigation.      Ret, _render_owner_mention(), send_incident_notification(), _make_report() (+6 more)

### Community 13 - "LLM Client & Synthesis"
Cohesion: 0.23
Nodes (15): _call_litellm(), extract_structured(), _litellm_headers(), _parse_json_response(), Attempt to parse JSON from a raw LLM response.     Handles markdown code fences, Return a safe degraded RCA result when LLM synthesis fails., Call LiteLLM proxy (chronos-synthesis model group) to synthesize a root cause, Call LiteLLM proxy (chronos-extraction model — fast Groq model) to extract     s (+7 more)

### Community 14 - "Audit Findings & Security"
Cohesion: 0.25
Nodes (11): Wave 7 Audit: Hackathon Demo READY — 97 Python + 15 Frontend Tests Green, Wave 7: 3 Production Blockers (Plaintext Creds, SSE No Auth, No Investigation Timeout), Python Anti-Pattern: Broad Exception Handling (no-generic-except), Python Anti-Pattern: Inline/Deferred Imports (Circular Dependencies), OWASP Critical: Hardcoded Secrets in settings.py, OWASP High: Unauthenticated Webhook Endpoints, Demo Blockers: Graphiti-MCP Dockerfile Phantom Package, Seed Script Compat, New Findings (Wave 6): Incident Store Race Condition, Prompt Injection, Rate-Limit Spoofing (+3 more)

### Community 15 - "Webhook Test Helpers"
Cohesion: 0.47
Nodes (8): _payload_bytes(), _restore_webhook_settings(), _sign(), _stub_webhook_background_tasks(), test_invalid_signature_rejected(), test_missing_signature_rejected_when_required(), test_unsigned_accepted_in_dev_mode(), test_valid_signature_accepted()

### Community 16 - "Frontend Animation"
Cohesion: 0.61
Nodes (6): attachPowerOn(), countUp(), crossfadeIn(), fillBar(), prefersReducedMotion(), staggerFadeIn()

### Community 17 - "React Error Boundary"
Cohesion: 0.29
Nodes (1): ErrorBoundary

### Community 18 - "Dashboard View"
Cohesion: 0.33
Nodes (3): Dashboard(), StatCard(), useIncidents()

### Community 19 - "Rate Limiting"
Cohesion: 0.47
Nodes (4): _parse_trusted_proxies(), _rate_limit_key(), Centralized SlowAPI limiter configuration for CHRONOS.  The key function resolve, Derive the rate-limit key from the request.      Security: in direct mode, the k

### Community 20 - "Incident Detail View"
Cohesion: 0.33
Nodes (2): IncidentDetail(), useIncidentDetail()

### Community 21 - "Incident Model Tests"
Cohesion: 0.6
Nodes (4): _clear_store(), test_incident_report_rejects_missing_required_fields(), test_store_accepts_dict_and_model(), _valid_report_dict()

### Community 22 - "Graphify Context Enrichment"
Cohesion: 0.5
Nodes (3): get_graphify_context(), Graphify context enrichment.  Reads GRAPH_REPORT.md generated by the Graphify to, Read GRAPH_REPORT.md and return relevant context.      If ``entity_name`` is pro

### Community 23 - "Investigation Replay UI"
Cohesion: 0.6
Nodes (3): formatDuration(), formatStep(), toLocaleTimeString()

### Community 24 - "Demo Inject Script"
Cohesion: 0.6
Nodes (3): main(), Return sha256=<hmac> over f'{timestamp}.{body}', matching _compute_hmac in depen, _sign_payload()

### Community 25 - "Lineage Failure Map"
Cohesion: 0.67
Nodes (2): getTierColor(), shortLabel()

### Community 26 - "SSE Real-Time Hook"
Cohesion: 0.67
Nodes (2): parseEventData(), useSSE()

### Community 27 - "Frontend API Client"
Cohesion: 0.67
Nodes (2): delay(), throwApiError()

### Community 28 - "Import Integrity Tests"
Cohesion: 0.67
Nodes (2): test_graph_compilation_deferred_until_runtime(), test_no_circular_imports()

### Community 29 - "LLM Prompt Templates"
Cohesion: 0.67
Nodes (1): LLM prompts for CHRONOS RCA synthesis and structured extraction.

### Community 30 - "Core Runtime Init"
Cohesion: 0.67
Nodes (1): Core runtime services for CHRONOS.

### Community 31 - "Evidence Chain UI"
Cohesion: 0.67
Nodes (1): clsx()

### Community 32 - "Temporal Diff UI"
Cohesion: 0.67
Nodes (1): renderValue()

### Community 33 - "Severity Badge"
Cohesion: 0.67
Nodes (1): SeverityBadge()

### Community 34 - "Provenance Download"
Cohesion: 0.67
Nodes (1): ProvenanceDownload()

### Community 35 - "Loading Spinner"
Cohesion: 0.67
Nodes (1): LoadingSpinner()

### Community 36 - "Blast Radius Panel"
Cohesion: 0.67
Nodes (1): getTierBadge()

### Community 37 - "Incident Card"
Cohesion: 0.67
Nodes (1): IncidentCard()

### Community 38 - "Empty State"
Cohesion: 0.67
Nodes (1): EmptyState()

### Community 39 - "Truncated Text"
Cohesion: 0.67
Nodes (1): TruncatedText()

### Community 40 - "Demo Fixtures"
Cohesion: 0.67
Nodes (1): minutes()

### Community 45 - "CORS Origins Helper"
Cohesion: 1.0
Nodes (1): Return CORS origins as a trimmed list from a comma-separated string.

### Community 46 - "Startup Validation"
Cohesion: 1.0
Nodes (1): Fail at startup — not deep in a request handler — when required secrets

### Community 47 - "Webhook Signing Property"
Cohesion: 1.0
Nodes (1): Webhook signing is mandatory in production regardless of the field value.

### Community 98 - "Project Directory Structure"
Cohesion: 1.0
Nodes (1): CHRONOS Project Directory Structure

### Community 99 - "Wave 7 Audit Summary"
Cohesion: 1.0
Nodes (1): Wave 7 Grade Summary (Architecture A, Code A-, Security B+, Frontend B+)

## Knowledge Gaps
- **70 isolated node(s):** `Thread-safe-ish (single-process async) deduplicator backed by a plain dict.`, `Return True if ``event_key`` was already seen within the dedup window.         R`, `Remove entries older than the dedup window.`, `Clear all seen events (useful for testing).`, `Recursively clip long strings and escape prompt-breaking sequences.      - Strin` (+65 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `React Error Boundary`** (7 nodes): `ErrorBoundary.tsx`, `ErrorBoundary`, `.componentDidCatch()`, `.constructor()`, `.getDerivedStateFromError()`, `.render()`, `ErrorBoundary.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Incident Detail View`** (6 nodes): `useIncidentDetail.ts`, `IncidentDetail.tsx`, `IncidentDetail()`, `useIncidentDetail()`, `useIncidentDetail.ts`, `IncidentDetail.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Lineage Failure Map`** (4 nodes): `LineageFailureMap.tsx`, `getTierColor()`, `shortLabel()`, `LineageFailureMap.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SSE Real-Time Hook`** (4 nodes): `useSSE.ts`, `parseEventData()`, `useSSE()`, `useSSE.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Frontend API Client`** (4 nodes): `delay()`, `throwApiError()`, `api.ts`, `api.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Import Integrity Tests`** (4 nodes): `test_graph_compilation_deferred_until_runtime()`, `test_no_circular_imports()`, `test_imports.py`, `test_imports.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `LLM Prompt Templates`** (3 nodes): `prompts.py`, `LLM prompts for CHRONOS RCA synthesis and structured extraction.`, `prompts.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Core Runtime Init`** (3 nodes): `__init__.py`, `Core runtime services for CHRONOS.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Evidence Chain UI`** (3 nodes): `EvidenceChain.tsx`, `clsx()`, `EvidenceChain.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Temporal Diff UI`** (3 nodes): `TemporalDiff.tsx`, `renderValue()`, `TemporalDiff.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Severity Badge`** (3 nodes): `SeverityBadge.tsx`, `SeverityBadge()`, `SeverityBadge.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Provenance Download`** (3 nodes): `ProvenanceDownload.tsx`, `ProvenanceDownload()`, `ProvenanceDownload.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Loading Spinner`** (3 nodes): `LoadingSpinner.tsx`, `LoadingSpinner()`, `LoadingSpinner.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Blast Radius Panel`** (3 nodes): `getTierBadge()`, `BlastRadiusPanel.tsx`, `BlastRadiusPanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Incident Card`** (3 nodes): `IncidentCard.tsx`, `IncidentCard()`, `IncidentCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Empty State`** (3 nodes): `EmptyState.tsx`, `EmptyState()`, `EmptyState.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Truncated Text`** (3 nodes): `TruncatedText.tsx`, `TruncatedText()`, `TruncatedText.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Demo Fixtures`** (3 nodes): `demoFixtures.ts`, `minutes()`, `demoFixtures.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `CORS Origins Helper`** (1 nodes): `Return CORS origins as a trimmed list from a comma-separated string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Startup Validation`** (1 nodes): `Fail at startup — not deep in a request handler — when required secrets`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Webhook Signing Property`** (1 nodes): `Webhook signing is mandatory in production regardless of the field value.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Directory Structure`** (1 nodes): `CHRONOS Project Directory Structure`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Wave 7 Audit Summary`** (1 nodes): `Wave 7 Grade Summary (Architecture A, Code A-, Security B+, Frontend B+)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get()` connect `Incident Store & Stats API` to `Data Models & RCA Schemas`, `LangGraph Investigation Pipeline`, `Webhook & Investigation Runner`, `MCP Client Layer`, `Incidents API & PROV-O`, `FastAPI Middleware & HTTP`, `Audit Correlation Node`, `Slack Notifications`, `LLM Client & Synthesis`, `Rate Limiting`, `Demo Inject Script`?**
  _High betweenness centrality (0.259) - this node is a cross-community bridge._
- **Why does `IncidentReport` connect `Data Models & RCA Schemas` to `LangGraph Investigation Pipeline`, `Incident Store & Stats API`, `Webhook & Investigation Runner`, `FastAPI Middleware & HTTP`, `Slack Notifications`, `Incident Model Tests`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `secret_or_none()` connect `Security & Auth Dependencies` to `LangGraph Investigation Pipeline`, `MCP Client Layer`, `Slack Notifications`, `LLM Client & Synthesis`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 60 inferred relationships involving `get()` (e.g. with `enforce_body_size()` and `receive_openlineage_event()`) actually correct?**
  _`get()` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 56 inferred relationships involving `IncidentReport` (e.g. with `Investigation orchestration runner.  This is the single place that knows how to:` and `Return the compiled investigation graph and Langfuse callback factory.      Impo`) actually correct?**
  _`IncidentReport` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `InvestigationState` (e.g. with `LangGraph investigation state machine.  Wires all 10 nodes in a linear pipeline` and `Construct and compile the 10-step investigation graph.`) actually correct?**
  _`InvestigationState` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `RootCauseCategory` (e.g. with `Investigation orchestration runner.  This is the single place that knows how to:` and `Return the compiled investigation graph and Langfuse callback factory.      Impo`) actually correct?**
  _`RootCauseCategory` has 30 INFERRED edges - model-reasoned connections that need verification._
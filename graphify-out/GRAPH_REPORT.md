# Graph Report - chronos  (2026-04-26)

## Corpus Check
- 129 files · ~119,818 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1146 nodes · 2255 edges · 64 communities detected
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 1043 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 108|Community 108]]
- [[_COMMUNITY_Community 109|Community 109]]
- [[_COMMUNITY_Community 110|Community 110]]
- [[_COMMUNITY_Community 111|Community 111]]
- [[_COMMUNITY_Community 112|Community 112]]
- [[_COMMUNITY_Community 113|Community 113]]
- [[_COMMUNITY_Community 114|Community 114]]

## God Nodes (most connected - your core abstractions)
1. `IncidentReport` - 107 edges
2. `MCPServerType` - 82 edges
3. `RootCauseCategory` - 80 edges
4. `IncidentStatus` - 66 edges
5. `get()` - 63 edges
6. `InvestigationTrigger` - 44 edges
7. `Settings()` - 42 edges
8. `InvestigationState` - 42 edges
9. `store()` - 28 edges
10. `BusinessImpact` - 21 edges

## Surprising Connections (you probably didn't know these)
- `F2: Autonomous Investigation Agent (10-Step LangGraph Pipeline)` --semantically_similar_to--> `10-Step Investigation Pipeline (LangGraph)`  [INFERRED] [semantically similar]
  PRD.md → README.md
- `Settings()` --uses--> `Unit tests for chronos.config.settings.Settings model_validator.  All tests cons`  [INFERRED]
  chronos-frontend/src/pages/Settings.tsx → tests/test_settings.py
- `Settings()` --uses--> `Create a minimal valid development Settings without loading .env.`  [INFERRED]
  chronos-frontend/src/pages/Settings.tsx → tests/test_settings.py
- `Settings()` --uses--> `Create a minimal valid production Settings without loading .env.`  [INFERRED]
  chronos-frontend/src/pages/Settings.tsx → tests/test_settings.py
- `Settings()` --uses--> `Production should always require signed webhooks, regardless of the raw field.`  [INFERRED]
  chronos-frontend/src/pages/Settings.tsx → tests/test_settings.py

## Hyperedges (group relationships)
- **Triple-Graph MCP Investigation: OpenMetadata + Graphiti + GitNexus power the 10-step autonomous pipeline** — prd_metadata_graph, prd_temporal_graph, prd_code_graph, prd_f2_investigation_agent, readme_investigation_pipeline [EXTRACTED 0.95]
- **Agentic Metadata Gap-Closing Features: F11-F18 collectively close 8 gaps from The New Stack article** — prd_f11_self_referential_memory, prd_f12_langfuse_observability, prd_f13_prov_o, prd_f14_a2a_agent_card, prd_f15_openllmetry, prd_f16_otel_semconv, prd_f17_deepeval, prd_f18_ragas [EXTRACTED 0.93]
- **Hybrid Deployment: Vercel Static Frontend + Fly.io Always-On Backend + Neon Postgres + Langfuse Cloud** — vercel_plan_frontend_only, vercel_plan_flyio_backend, vercel_plan_neon_postgres, vercel_plan_langfuse_cloud [EXTRACTED 0.90]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (104): BaseSettings, DemoRunRequest, list_scenarios(), _push(), Demo investigation endpoint — pre-seeded scenarios for the CHRONOS live demo., Run a pre-seeded demo investigation with real LLM synthesis and SSE streaming., Run a pre-seeded demo investigation with real LLM synthesis and SSE streaming., List available demo scenarios. (+96 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (107): audit_correlation_node(), Return a safe degraded RCA result when LLM synthesis fails., _synthesis_fallback(), _gather_file_references(), main(), Return sha256=<hmac> over f'{timestamp}.{body}', matching _compute_hmac in depen, _sign_payload(), downstream_impact_node() (+99 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (67): Step 6 — Audit Correlation  Fetches OpenMetadata audit logs for the affected ent, Fetch audit logs and cross-reference with Graphiti user-action facts., code_blast_radius_node(), _normalise_table_candidates(), Step 4 — Code Blast Radius  Uses GitNexus to find code files (SQL, Python, dbt m, Search GitNexus for code files referencing the affected entity., Return a ranked list of search terms for a data-entity FQN.      Most data wareh, Run gitnexus search across all candidate names, de-duplicated by path. (+59 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (70): MCPClient, _next_rpc_id(), Unified async MCP client for CHRONOS.  Maintains persistent httpx sessions for H, Close all open HTTP sessions., Singleton async MCP client.      Usage:         result = await mcp_client.call_t, Return (or lazily create) a persistent httpx session for a server., Call a named tool on the specified MCP server.          Sends a JSON-RPC 2.0 ``t, get_mcp_configs() (+62 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (68): asearch_entity_references(), _ext_to_language(), Codebase scanner that finds files referencing a data entity.  Replaces the ``git, Pure-Python fallback scanner. Slow but works without ripgrep., Find files in ``repo_path`` whose contents reference ``query``.      Tries ripgr, Async wrapper — runs the blocking scanner in a thread pool., Return True iff the ripgrep binary is on PATH. Cached for the process., Return the query iff it matches the safe charset, else None. (+60 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (72): AIDLC Mandatory Audit Log (audit.md) — Complete Raw Input Capture, AIDLC Construction Phase (Per-Unit Loop: Design, NFR, Code Gen), AIDLC Inception Phase (Requirements, Stories, Design, Units), AGENTS.md — AIDLC Adaptive Software Development Workflow, AIDLC Audit Log (audit.md) — Timestamped Interaction Record, 7 Construction Units (Core Infra, MCP, Agent, Output, API, Frontend, Agentic Metadata), AIDLC State: Construction Phase Complete, Build/Test Pending, Application Design — Triple-Graph + Event-Driven Agent Architecture (+64 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (66): _find_best_node(), get_community(), get_neighbors(), get_node(), god_nodes(), _graph(), graph_stats(), _GraphCache (+58 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (58): InvestigationTrigger, list_all(), Return all stored incidents (insertion order preserved — Python 3.7+)., _evict_orphan_queue(), _on_investigation_done(), Manual investigation trigger and SSE streaming endpoints.  Allows external syste, Manually trigger a CHRONOS investigation.      Returns immediately with an incid, Stream investigation progress via Server-Sent Events.      Events carry a ``data (+50 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (50): _entity_matches_node(), get_children(), get_node_by_entity(), get_node_files(), get_parents(), is_available(), _load(), _manifest() (+42 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (33): BaseModel, _normalize_aliases(), OpenLineageDataset, OpenLineageFacet, OpenLineageRunEvent, OpenMetadataTestCase, OpenMetadataTestResult, OpenMetadataWebhookPayload (+25 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (33): _get_incident_or_404(), get_provenance_jsonld(), get_provenance_provn(), get_provenance_turtle(), generate_provenance(), _parse_iso_dt(), W3C PROV-O provenance document generator.  Produces a structured PROV document t, Return a minimal valid PROV-O document when full generation fails. (+25 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (25): jsonResponse(), _cli_main(), enforce_body_size(), health(), lifespan(), CHRONOS FastAPI application entry point.  Mounts all route groups, registers mid, Entry point for the ``chronos-server`` console script., Application lifespan — runs setup before first request, teardown on shutdown. (+17 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (16): _call_litellm(), extract_structured(), _litellm_headers(), _parse_json_response(), POST to LiteLLM proxy /chat/completions and return the assistant message content, Attempt to parse JSON from a raw LLM response.     Handles markdown code fences, Call LiteLLM proxy (chronos-synthesis model group) to synthesize a root cause, Call LiteLLM proxy (chronos-extraction model — fast Groq model) to extract     s (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (27): _dev(), _prod(), Unit tests for chronos.config.settings.Settings model_validator.  All tests cons, Create a minimal valid development Settings without loading .env., Create a minimal valid production Settings without loading .env., Production should always require signed webhooks, regardless of the raw field., test_cors_origins_splits_comma_separated(), test_cors_origins_trims_whitespace() (+19 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (21): notify_node(), Step 8 — Notify  Sends a Slack Block Kit notification with the investigation res, Send Slack notification for the completed investigation., _base_state(), Unit tests for the 7 CHRONOS LangGraph nodes not covered in test_nodes.py.  All, A Graphiti failure must NOT raise — trace persistence is best-effort., test_code_blast_radius_empty_entity_skips_search(), test_code_blast_radius_populates_files_and_commits() (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (15): add_episode(), config, get_episodes(), _get_graphiti(), _HashEmbedder, _is_configured(), In-process Graphiti client.  Replaces the graphiti-mcp sidecar with direct graph, Add an episode to the knowledge graph. (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.21
Nodes (11): _compute_hmac(), FastAPI dependencies for CHRONOS API security.  Provides HMAC-SHA256 signature v, Validate the HMAC-SHA256 signature header against the raw request body.      In, Dependency: validate OpenMetadata webhook HMAC signature., Dependency: validate OpenLineage webhook HMAC signature., Require a valid Bearer token on mutation endpoints (acknowledge, resolve)., Return a 'sha256=<hex>' HMAC digest.      When ``timestamp`` is provided the sig, verify_bearer_token() (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.25
Nodes (11): Wave 7 Audit: Hackathon Demo READY — 97 Python + 15 Frontend Tests Green, Wave 7: 3 Production Blockers (Plaintext Creds, SSE No Auth, No Investigation Timeout), Python Anti-Pattern: Broad Exception Handling (no-generic-except), Python Anti-Pattern: Inline/Deferred Imports (Circular Dependencies), OWASP Critical: Hardcoded Secrets in settings.py, OWASP High: Unauthenticated Webhook Endpoints, Demo Blockers: Graphiti-MCP Dockerfile Phantom Package, Seed Script Compat, New Findings (Wave 6): Incident Store Race Condition, Prompt Injection, Rate-Limit Spoofing (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.36
Nodes (6): _payload_bytes(), _sign(), test_invalid_signature_rejected(), test_missing_signature_rejected_when_required(), test_unsigned_accepted_in_dev_mode(), test_valid_signature_accepted()

### Community 19 - "Community 19"
Cohesion: 0.25
Nodes (8): _load_slack_user_map(), Parse config/slack_users.yaml once at import time.      We parse manually (``key, _make_report(), test_render_owner_mention_direct_user(), test_render_owner_mention_fallback_for_unmapped(), test_render_owner_mention_usergroup(), test_send_notification_returns_false_without_webhook(), test_slack_user_map_file_is_optional()

### Community 20 - "Community 20"
Cohesion: 0.52
Nodes (6): attachPowerOn(), countUp(), crossfadeIn(), fillBar(), prefersReducedMotion(), staggerFadeIn()

### Community 21 - "Community 21"
Cohesion: 0.33
Nodes (1): ErrorBoundary

### Community 22 - "Community 22"
Cohesion: 0.4
Nodes (1): CHRONOS application settings.  All secrets are typed as ``SecretStr | None`` so

### Community 23 - "Community 23"
Cohesion: 0.4
Nodes (2): Dashboard(), useIncidents()

### Community 24 - "Community 24"
Cohesion: 0.5
Nodes (1): Pre-seeded investigation scenarios for the CHRONOS live demo.

### Community 26 - "Community 26"
Cohesion: 0.5
Nodes (2): IncidentDetail(), useIncidentDetail()

### Community 27 - "Community 27"
Cohesion: 0.67
Nodes (1): Core runtime services for CHRONOS.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): LLM prompts for CHRONOS RCA synthesis and structured extraction.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Return CORS origins as a trimmed list from a comma-separated string.

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): Fail at startup — not deep in a request handler — when required secrets

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Webhook signing is mandatory in production regardless of the field value.

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Tolerant fallback that captures FROM/JOIN/INTO/UPDATE identifiers.

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): Return the de-duplicated, lowercased list of table refs in the input.      Args:

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (1): Return a ``{matched, tables, match_kind}`` summary for one file.      ``match_ki

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): Return the CHRONOS A2A Agent Card.

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): Fail at startup — not deep in a request handler — when required secrets

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): Fail at startup — not deep in a request handler — when required secrets

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): Webhook signing is mandatory in production regardless of the field value.

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): Safely unwrap a SecretStr.  Returns None when the field is unset so callers

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (1): Return CORS origins as a trimmed list from a comma-separated string.

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (1): Webhook signing is mandatory in production regardless of the field value.

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (1): Safely unwrap a SecretStr.  Returns None when the field is unset so callers

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (1): Return a 'sha256=<hex>' HMAC digest.      When ``timestamp`` is provided the sig

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (1): Validate the HMAC-SHA256 signature header against the raw request body.      In

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (1): Dependency: validate OpenMetadata webhook HMAC signature.

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (1): Dependency: validate OpenLineage webhook HMAC signature.

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (1): json.dumps with evidence sanitisation + default=str for tricky types.

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (1): POST to LiteLLM proxy /chat/completions and return the assistant message content

### Community 99 - "Community 99"
Cohesion: 1.0
Nodes (1): Attempt to parse JSON from a raw LLM response.     Handles markdown code fences

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (1): Return a safe degraded RCA result when LLM synthesis fails.

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (1): Call LiteLLM proxy (chronos-synthesis model group) to synthesize a root cause

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (1): Call LiteLLM proxy (chronos-extraction model — fast Groq model) to extract     s

### Community 103 - "Community 103"
Cohesion: 1.0
Nodes (1): Return CORS origins as a trimmed list from a comma-separated string.

### Community 104 - "Community 104"
Cohesion: 1.0
Nodes (1): Fail at startup — not deep in a request handler — when required secrets

### Community 105 - "Community 105"
Cohesion: 1.0
Nodes (1): Webhook signing is mandatory in production regardless of the field value.

### Community 106 - "Community 106"
Cohesion: 1.0
Nodes (1): Safely unwrap a SecretStr.  Returns None when the field is unset so callers

### Community 107 - "Community 107"
Cohesion: 1.0
Nodes (1): Full investigation state — required inputs plus optional accumulated outputs.

### Community 108 - "Community 108"
Cohesion: 1.0
Nodes (1): Return a 'sha256=<hex>' HMAC digest.      When ``timestamp`` is provided the sig

### Community 109 - "Community 109"
Cohesion: 1.0
Nodes (1): Validate the HMAC-SHA256 signature header against the raw request body.      Whe

### Community 110 - "Community 110"
Cohesion: 1.0
Nodes (1): Dependency: validate OpenMetadata webhook HMAC signature (with optional replay g

### Community 111 - "Community 111"
Cohesion: 1.0
Nodes (1): Dependency: validate OpenLineage webhook HMAC signature (with optional replay gu

### Community 112 - "Community 112"
Cohesion: 1.0
Nodes (1): Read GRAPH_REPORT.md and return relevant context.      If ``entity_name`` is pro

### Community 113 - "Community 113"
Cohesion: 1.0
Nodes (1): CHRONOS Project Directory Structure

### Community 114 - "Community 114"
Cohesion: 1.0
Nodes (1): Wave 7 Grade Summary (Architecture A, Code A-, Security B+, Frontend B+)

## Knowledge Gaps
- **249 isolated node(s):** `config`, `In-process Graphiti client.  Replaces the graphiti-mcp sidecar with direct graph`, `Deterministic SHA-256-seeded unit-vector embedder — no external API.`, `Return True only when a non-local FalkorDB host is set.`, `Add an episode to the knowledge graph.` (+244 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 21`** (6 nodes): `ErrorBoundary.tsx`, `ErrorBoundary`, `.componentDidCatch()`, `.constructor()`, `.getDerivedStateFromError()`, `.render()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (5 nodes): `settings.py`, `cors_origins()`, `effective_webhook_signature_required()`, `CHRONOS application settings.  All secrets are typed as ``SecretStr | None`` so`, `_validate_secrets_for_enabled_features()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (5 nodes): `useIncidents.ts`, `Dashboard.tsx`, `Dashboard()`, `StatCard()`, `useIncidents()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (4 nodes): `scenarios.py`, `_days_ago()`, `_hours_ago()`, `Pre-seeded investigation scenarios for the CHRONOS live demo.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (4 nodes): `useIncidentDetail.ts`, `IncidentDetail.tsx`, `IncidentDetail()`, `useIncidentDetail()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (3 nodes): `__init__.py`, `__init__.py`, `Core runtime services for CHRONOS.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `prompts.py`, `LLM prompts for CHRONOS RCA synthesis and structured extraction.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Return CORS origins as a trimmed list from a comma-separated string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Fail at startup — not deep in a request handler — when required secrets`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Webhook signing is mandatory in production regardless of the field value.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Tolerant fallback that captures FROM/JOIN/INTO/UPDATE identifiers.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `Return the de-duplicated, lowercased list of table refs in the input.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `Return a ``{matched, tables, match_kind}`` summary for one file.      ``match_ki`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `Return the CHRONOS A2A Agent Card.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `Fail at startup — not deep in a request handler — when required secrets`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `Fail at startup — not deep in a request handler — when required secrets`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `Webhook signing is mandatory in production regardless of the field value.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `Safely unwrap a SecretStr.  Returns None when the field is unset so callers`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `Return CORS origins as a trimmed list from a comma-separated string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `Webhook signing is mandatory in production regardless of the field value.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `Safely unwrap a SecretStr.  Returns None when the field is unset so callers`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `Return a 'sha256=<hex>' HMAC digest.      When ``timestamp`` is provided the sig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `Validate the HMAC-SHA256 signature header against the raw request body.      In`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `Dependency: validate OpenMetadata webhook HMAC signature.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (1 nodes): `Dependency: validate OpenLineage webhook HMAC signature.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `json.dumps with evidence sanitisation + default=str for tricky types.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `POST to LiteLLM proxy /chat/completions and return the assistant message content`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 99`** (1 nodes): `Attempt to parse JSON from a raw LLM response.     Handles markdown code fences`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (1 nodes): `Return a safe degraded RCA result when LLM synthesis fails.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (1 nodes): `Call LiteLLM proxy (chronos-synthesis model group) to synthesize a root cause`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (1 nodes): `Call LiteLLM proxy (chronos-extraction model — fast Groq model) to extract     s`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 103`** (1 nodes): `Return CORS origins as a trimmed list from a comma-separated string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 104`** (1 nodes): `Fail at startup — not deep in a request handler — when required secrets`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 105`** (1 nodes): `Webhook signing is mandatory in production regardless of the field value.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 106`** (1 nodes): `Safely unwrap a SecretStr.  Returns None when the field is unset so callers`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 107`** (1 nodes): `Full investigation state — required inputs plus optional accumulated outputs.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 108`** (1 nodes): `Return a 'sha256=<hex>' HMAC digest.      When ``timestamp`` is provided the sig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 109`** (1 nodes): `Validate the HMAC-SHA256 signature header against the raw request body.      Whe`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 110`** (1 nodes): `Dependency: validate OpenMetadata webhook HMAC signature (with optional replay g`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 111`** (1 nodes): `Dependency: validate OpenLineage webhook HMAC signature (with optional replay gu`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 112`** (1 nodes): `Read GRAPH_REPORT.md and return relevant context.      If ``entity_name`` is pro`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 113`** (1 nodes): `CHRONOS Project Directory Structure`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 114`** (1 nodes): `Wave 7 Grade Summary (Architecture A, Code A-, Security B+, Frontend B+)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentReport` connect `Community 0` to `Community 1`, `Community 7`, `Community 9`, `Community 11`, `Community 12`, `Community 14`, `Community 19`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `get()` connect `Community 1` to `Community 0`, `Community 2`, `Community 10`, `Community 11`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `MCPServerType` connect `Community 3` to `Community 0`, `Community 8`, `Community 6`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 105 inferred relationships involving `IncidentReport` (e.g. with `Investigation orchestration runner.  This is the single place that knows how to:` and `Return the compiled investigation graph and Langfuse callback factory.      Impo`) actually correct?**
  _`IncidentReport` has 105 INFERRED edges - model-reasoned connections that need verification._
- **Are the 80 inferred relationships involving `MCPServerType` (e.g. with `MCPClient` and `Unified async MCP client for CHRONOS.  Maintains persistent httpx sessions for H`) actually correct?**
  _`MCPServerType` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 78 inferred relationships involving `RootCauseCategory` (e.g. with `Investigation orchestration runner.  This is the single place that knows how to:` and `Return the compiled investigation graph and Langfuse callback factory.      Impo`) actually correct?**
  _`RootCauseCategory` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Are the 64 inferred relationships involving `IncidentStatus` (e.g. with `Investigation orchestration runner.  This is the single place that knows how to:` and `Return the compiled investigation graph and Langfuse callback factory.      Impo`) actually correct?**
  _`IncidentStatus` has 64 INFERRED edges - model-reasoned connections that need verification._
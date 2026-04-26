/**
 * Demo-mode fixtures — realistic incident data used when `VITE_DEMO_MODE=true`.
 *
 * Purpose: the deployed Vercel URL should show a representative CHRONOS
 * experience (stats, incident list, full detail pages, PROV-O downloads)
 * without requiring a publicly-hosted backend.  This module lets the API
 * layer return these fixtures instead of hitting the network.
 *
 * Three incidents are modelled:
 *   1. A high-impact SCHEMA_CHANGE that the agent resolved with 92% confidence.
 *   2. A medium-impact UPSTREAM_FAILURE currently open.
 *   3. A resolved CODE_CHANGE with a recurring pattern callout.
 */
import type { DashboardStats, IncidentReport } from '../types';

const now = Date.now();
const minutes = (m: number) => new Date(now - m * 60_000).toISOString();

export const DEMO_INCIDENTS: IncidentReport[] = [
  {
    incident_id: 'inc-demo-001',
    detected_at: minutes(42),
    investigation_completed_at: minutes(40),
    investigation_duration_ms: 87_430,
    affected_entity_fqn:
      'analytics_warehouse.analytics_db.public.orders',
    test_name: 'column_values_to_be_not_null',
    test_type: 'columnValuesToBeNotNull',
    failure_message:
      "Found 1523 null values in order_id column. Expected 0 nulls.",
    probable_root_cause:
      "The upstream `order_items` table had its `order_id` column renamed to `order_ref_id` in commit abc123 (2h ago). The dbt model for `orders` still references the old column name, producing nulls on every refresh. The rename is consistent with the 'column standardisation' PR merged yesterday.",
    root_cause_category: 'SCHEMA_CHANGE',
    confidence: 0.92,
    evidence_chain: [
      {
        source: 'openmetadata',
        description:
          "Column `order_items.order_id` was removed from the schema at 2026-04-23T06:14:00Z. Version history shows it was renamed to `order_ref_id`.",
        raw_data: {},
        timestamp: minutes(134),
        confidence: 0.95,
      },
      {
        source: 'gitnexus',
        description:
          "Commit abc123 by alice@team.com: 'rename order_id -> order_ref_id for consistency'. Touches 3 dbt models.",
        raw_data: {},
        timestamp: minutes(128),
        confidence: 0.9,
      },
      {
        source: 'graphiti',
        description:
          "Similar schema-rename incident occurred on `products.product_id` in Jan 2026 — resolved by rolling back the rename and creating a deprecation alias.",
        raw_data: {},
        timestamp: minutes(42),
        confidence: 0.72,
      },
    ],
    affected_downstream: [
      {
        fqn: 'analytics_warehouse.analytics_db.public.daily_revenue',
        display_name: 'Daily Revenue',
        tier: 'Tier1',
        owners: ['data-engineering-team'],
        domain: 'finance',
      },
      {
        fqn: 'analytics_warehouse.analytics_db.public.executive_dashboard',
        display_name: 'Executive Dashboard',
        tier: 'Tier1',
        owners: ['data-engineering-team', 'executive-reporting'],
        domain: 'finance',
      },
    ],
    upstream_assets: [
      {
        fqn: 'analytics_warehouse.analytics_db.public.order_items',
        display_name: 'Order Items',
        tier: 'Tier1',
        owners: ['data-engineering-team'],
        domain: 'commerce',
      },
      {
        fqn: 'analytics_warehouse.analytics_db.public.dim_products',
        display_name: 'Dim Products',
        tier: 'Tier2',
        owners: ['analytics-engineering'],
        domain: 'commerce',
      },
    ],
    business_impact: 'high',
    business_impact_reasoning:
      'Two Tier1 downstream assets feed the executive dashboard read by the CFO. Without mitigation, morning revenue reports will show incorrect zeros.',
    recommended_actions: [
      {
        description:
          'Restore the `order_id` column on `order_items` as an alias view to `order_ref_id`. This preserves downstream compatibility while the team migrates.',
        priority: 'immediate',
        owner: 'data-engineering-team',
      },
      {
        description:
          'Open a PR to update the dbt model for `orders` to use `order_ref_id` directly.',
        priority: 'short_term',
        owner: 'alice',
      },
      {
        description:
          'Establish a schema-change review checklist that flags renames of columns referenced by downstream models.',
        priority: 'long_term',
        owner: 'data-engineering-team',
      },
    ],
    investigation_timeline: [
      { step: 0, name: 'prior_investigations', started_at: minutes(42), completed_at: minutes(42), duration_ms: 1203, summary: 'Found 1 related incident in the last 30 days.' },
      { step: 1, name: 'scope_failure', started_at: minutes(42), completed_at: minutes(42), duration_ms: 842, summary: 'Scoped to test orders_not_null_order_id on table orders.' },
      { step: 2, name: 'temporal_diff', started_at: minutes(42), completed_at: minutes(42), duration_ms: 2414, summary: 'Schema change detected 2h ago on upstream table order_items.' },
      { step: 3, name: 'lineage_walk', started_at: minutes(42), completed_at: minutes(42), duration_ms: 5120, summary: 'Walked 5 upstream + 3 downstream nodes.' },
      { step: 4, name: 'code_blast_radius', started_at: minutes(42), completed_at: minutes(42), duration_ms: 3891, summary: 'Found commit abc123 matching schema change timing.' },
      { step: 5, name: 'downstream_impact', started_at: minutes(42), completed_at: minutes(42), duration_ms: 1502, summary: 'Identified 2 Tier1 downstream assets at risk.' },
      { step: 6, name: 'audit_correlation', started_at: minutes(42), completed_at: minutes(41), duration_ms: 2033, summary: 'No suspicious audit events in window.' },
      { step: 7, name: 'rca_synthesis', started_at: minutes(41), completed_at: minutes(40), duration_ms: 14_822, summary: 'RCA: SCHEMA_CHANGE, confidence=0.92, evidence=3, actions=3, downstream=2' },
      { step: 8, name: 'persist_trace', started_at: minutes(40), completed_at: minutes(40), duration_ms: 421, summary: 'Trace persisted to Graphiti.' },
      { step: 9, name: 'notify', started_at: minutes(40), completed_at: minutes(40), duration_ms: 1012, summary: 'Slack notification sent to #data-incidents.' },
    ],
    related_past_incidents: [
      {
        incident_id: 'inc-hist-2026-01-15',
        root_cause_category: 'SCHEMA_CHANGE',
        affected_entity_fqn: 'analytics_warehouse.analytics_db.public.products',
        detected_at: '2026-01-15T14:20:00Z',
        confidence: 0.88,
      },
    ],
    graphify_context:
      'Entity `orders` is a Tier1 asset with 5 upstream dependencies and 3 downstream consumers. Historically, incidents on this entity have been concentrated around schema evolution (last 6 months: 3 SCHEMA_CHANGE, 1 CODE_CHANGE).',
    agent_version: '2.0.0',
    llm_model_used: 'claude-sonnet-4-6',
    total_mcp_calls: 18,
    total_llm_tokens: 4231,
    status: 'acknowledged',
    acknowledged_by: 'alice',
    resolved_by: null,
    resolved_at: null,
  },
  {
    incident_id: 'inc-demo-002',
    detected_at: minutes(12),
    investigation_completed_at: minutes(10),
    investigation_duration_ms: 92_150,
    affected_entity_fqn:
      'analytics_warehouse.analytics_db.public.daily_revenue',
    test_name: 'table_row_count_to_be_between',
    test_type: 'tableRowCountToBeBetween',
    failure_message:
      'Row count 0 below minimum threshold 1000. Table appears empty.',
    probable_root_cause:
      'The upstream `orders` table failed its own null-check test 42 minutes ago (SCHEMA_CHANGE, inc-demo-001). The scheduled dbt run for `daily_revenue` filtered out all rows due to the upstream nulls, producing an empty result set. This is a cascading failure.',
    root_cause_category: 'UPSTREAM_FAILURE',
    confidence: 0.87,
    evidence_chain: [
      {
        source: 'graphiti',
        description:
          'Related incident inc-demo-001 on upstream table `orders` is currently acknowledged.',
        raw_data: {},
        timestamp: minutes(12),
        confidence: 0.9,
      },
      {
        source: 'openmetadata',
        description:
          'The last successful run of the `daily_revenue` dbt model produced 1,482 rows. The latest run produced 0.',
        raw_data: {},
        timestamp: minutes(11),
        confidence: 0.85,
      },
    ],
    affected_downstream: [
      {
        fqn: 'analytics_warehouse.analytics_db.public.executive_dashboard',
        display_name: 'Executive Dashboard',
        tier: 'Tier1',
        owners: ['data-engineering-team', 'executive-reporting'],
        domain: 'finance',
      },
    ],
    upstream_assets: [
      {
        fqn: 'analytics_warehouse.analytics_db.public.orders',
        display_name: 'Orders',
        tier: 'Tier1',
        owners: ['data-engineering-team'],
        domain: 'commerce',
      },
    ],
    business_impact: 'critical',
    business_impact_reasoning:
      'Downstream executive dashboard feeds the CFO morning briefing. A zero-row daily_revenue feeds a $0 revenue number into the C-suite report.',
    recommended_actions: [
      {
        description:
          'Wait for incident inc-demo-001 resolution, then re-run the daily_revenue dbt model.',
        priority: 'immediate',
        owner: 'data-engineering-team',
      },
      {
        description:
          'Add a row-count floor check to the dbt model that aborts rather than writing zero rows.',
        priority: 'short_term',
        owner: 'analytics-engineering',
      },
    ],
    investigation_timeline: [
      { step: 0, name: 'prior_investigations', started_at: minutes(12), completed_at: minutes(12), duration_ms: 984, summary: 'Found 1 cascading incident on upstream `orders`.' },
      { step: 1, name: 'scope_failure', started_at: minutes(12), completed_at: minutes(12), duration_ms: 671, summary: 'Scoped to daily_revenue row-count test.' },
      { step: 3, name: 'lineage_walk', started_at: minutes(12), completed_at: minutes(11), duration_ms: 4892, summary: 'Upstream `orders` is currently incident-flagged.' },
      { step: 7, name: 'rca_synthesis', started_at: minutes(11), completed_at: minutes(10), duration_ms: 13_021, summary: 'RCA: UPSTREAM_FAILURE, confidence=0.87' },
    ],
    related_past_incidents: [
      {
        incident_id: 'inc-demo-001',
        root_cause_category: 'SCHEMA_CHANGE',
        affected_entity_fqn: 'analytics_warehouse.analytics_db.public.orders',
        detected_at: minutes(42),
        confidence: 0.92,
      },
    ],
    graphify_context:
      'Entity `daily_revenue` has a hard dependency on `orders`. 73% of historical daily_revenue incidents have been UPSTREAM_FAILURE cascades.',
    agent_version: '2.0.0',
    llm_model_used: 'claude-sonnet-4-6',
    total_mcp_calls: 9,
    total_llm_tokens: 2891,
    status: 'open',
    acknowledged_by: null,
    resolved_by: null,
    resolved_at: null,
  },
  {
    incident_id: 'inc-demo-003',
    detected_at: minutes(1440),
    investigation_completed_at: minutes(1438),
    investigation_duration_ms: 74_200,
    affected_entity_fqn:
      'analytics_warehouse.analytics_db.public.dim_customers',
    test_name: 'column_values_to_be_unique',
    test_type: 'columnValuesToBeUnique',
    failure_message:
      'Found 12 duplicate values in customer_id column.',
    probable_root_cause:
      'A deduplication step in the upstream ETL pipeline was removed in commit def456 last week. The author intended to consolidate two duplicate steps but accidentally deleted the unique-constraint check instead of consolidating it.',
    root_cause_category: 'CODE_CHANGE',
    confidence: 0.81,
    evidence_chain: [
      {
        source: 'gitnexus',
        description:
          "Commit def456 by bob@team.com removed the `.drop_duplicates(['customer_id'])` call from the etl_customers.py script.",
        raw_data: {},
        timestamp: minutes(1450),
        confidence: 0.88,
      },
    ],
    affected_downstream: [],
    upstream_assets: [],
    business_impact: 'medium',
    business_impact_reasoning:
      'Duplicate customer_ids cause duplicate rows in segmentation analyses but do not directly feed external reports.',
    recommended_actions: [
      {
        description: 'Revert the .drop_duplicates() removal in commit def456.',
        priority: 'immediate',
        owner: 'bob',
      },
      {
        description:
          'Add a CI check that forbids removing constraint enforcement without an explicit approval label.',
        priority: 'long_term',
        owner: 'data-engineering-team',
      },
    ],
    investigation_timeline: [],
    related_past_incidents: [],
    graphify_context: '',
    agent_version: '2.0.0',
    llm_model_used: 'claude-sonnet-4-6',
    total_mcp_calls: 7,
    total_llm_tokens: 1820,
    status: 'resolved',
    acknowledged_by: 'bob',
    resolved_by: 'bob',
    resolved_at: minutes(1200),
  },
];

export const DEMO_STATS: DashboardStats = {
  total_incidents: DEMO_INCIDENTS.length,
  by_root_cause: {
    SCHEMA_CHANGE: 1,
    UPSTREAM_FAILURE: 1,
    CODE_CHANGE: 1,
  },
  by_impact: { critical: 1, high: 1, medium: 1, low: 0 },
  by_status: { open: 1, acknowledged: 1, resolved: 1, investigating: 0 },
  avg_confidence:
    DEMO_INCIDENTS.reduce((sum, i) => sum + i.confidence, 0) /
    DEMO_INCIDENTS.length,
  open_count: 1,
  critical_count: 1,
};

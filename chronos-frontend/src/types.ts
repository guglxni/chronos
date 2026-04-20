export type RootCauseCategory =
  | 'SCHEMA_CHANGE'
  | 'CODE_CHANGE'
  | 'DATA_DRIFT'
  | 'PIPELINE_FAILURE'
  | 'PERMISSION_CHANGE'
  | 'UPSTREAM_FAILURE'
  | 'CONFIGURATION_CHANGE'
  | 'UNKNOWN';

export type BusinessImpact = 'critical' | 'high' | 'medium' | 'low';
export type IncidentStatus = 'open' | 'investigating' | 'resolved' | 'acknowledged';
export type EvidenceSource = 'openmetadata' | 'graphiti' | 'gitnexus' | 'graphify' | 'audit_log';

export interface EvidenceItem {
  source: EvidenceSource;
  description: string;
  raw_data: Record<string, unknown>;
  timestamp: string | null;
  confidence: number;
}

export interface AffectedAsset {
  fqn: string;
  display_name: string;
  tier: string;
  owners: string[];
  domain: string;
}

export interface RemediationStep {
  description: string;
  priority: 'immediate' | 'short_term' | 'long_term';
  owner: string;
}

export interface InvestigationTimelineEntry {
  step: number;
  name: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  summary: string;
}

export interface IncidentReport {
  incident_id: string;
  detected_at: string;
  investigation_completed_at: string | null;
  investigation_duration_ms: number | null;
  affected_entity_fqn: string;
  test_name: string;
  test_type: string;
  failure_message: string;
  probable_root_cause: string;
  root_cause_category: RootCauseCategory;
  confidence: number;
  evidence_chain: EvidenceItem[];
  affected_downstream: AffectedAsset[];
  business_impact: BusinessImpact;
  recommended_actions: RemediationStep[];
  investigation_timeline: InvestigationTimelineEntry[];
  related_past_incidents: unknown[];
  graphify_context: string;
  status: IncidentStatus;
  acknowledged_by: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
}

export interface DashboardStats {
  total_incidents: number;
  by_root_cause: Record<string, number>;
  by_impact: Record<string, number>;
  by_status: Record<string, number>;
  avg_confidence: number;
  open_count: number;
  critical_count: number;
}

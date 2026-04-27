"""Parameterized Cypher templates for the chronos_incidents graph.

Kept terse and explicit — easier to audit than a query builder.
All param names are ``$snake_case`` to match the FalkorDB Python client.
"""

GRAPH_NAME = "chronos_incidents"

# MERGE on incident_id so re-stores update in place (no duplicates).
# The ON CREATE / ON MATCH split lets us avoid clobbering ``detected_at`` on
# update — that field is immutable once set.
PERSIST = """
MERGE (i:Incident {incident_id: $incident_id})
ON CREATE SET
  i.detected_at = $detected_at,
  i.affected_entity_fqn = $affected_entity_fqn,
  i.root_cause_category = $root_cause_category,
  i.business_impact = $business_impact,
  i.confidence = $confidence,
  i.investigation_duration_ms = $investigation_duration_ms,
  i.total_llm_tokens = $total_llm_tokens,
  i.payload = $payload,
  i.status = $status,
  i.resolved_at = $resolved_at
ON MATCH SET
  i.status = $status,
  i.resolved_at = $resolved_at,
  i.business_impact = $business_impact,
  i.confidence = $confidence,
  i.investigation_duration_ms = $investigation_duration_ms,
  i.total_llm_tokens = $total_llm_tokens,
  i.payload = $payload
RETURN i.incident_id AS id
"""

# Hydrate ordered by detected_at DESC so we get newest first.
HYDRATE = """
MATCH (i:Incident)
RETURN i.incident_id AS incident_id, i.payload AS payload
ORDER BY i.detected_at DESC
LIMIT $limit
"""

LIST_RECENT = HYDRATE  # same shape — kept separate for future divergence

DELETE = """
MATCH (i:Incident {incident_id: $incident_id})
DELETE i
RETURN count(i) AS deleted
"""

# Index creation runs once at startup; FalkorDB ignores duplicate CREATE INDEX.
INDEXES: tuple[str, ...] = (
    "CREATE INDEX FOR (i:Incident) ON (i.incident_id)",
    "CREATE INDEX FOR (i:Incident) ON (i.detected_at)",
    "CREATE INDEX FOR (i:Incident) ON (i.affected_entity_fqn)",
)

"""Aggregate analytics over the in-process incident store.

These functions power the dashboard's KPI strip, trends chart, and
root-cause distribution. They read from ``chronos.core.incident_store``
and apply pure-Python aggregation — no DB queries, microsecond-fast.

When Graphiti / FalkorDB is configured, the demo seeder mirrors
historical episodes into the in-process store as well, so the dashboard
shows them without needing a separate query path.
"""

from chronos.analytics.stats import compute_stats
from chronos.analytics.trends import compute_by_category, compute_trends

__all__ = ["compute_by_category", "compute_stats", "compute_trends"]

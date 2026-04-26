"""
Step 4 — Code Blast Radius

Uses GitNexus to find code files (SQL, Python, dbt models, Airflow DAGs) that
reference the failing entity. Surfaces potential CODE_CHANGE root cause.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import gitnexus_get_commits, gitnexus_search_files


async def code_blast_radius_node(state: InvestigationState) -> InvestigationState:
    """Search GitNexus for code files referencing the affected entity."""
    entity_fqn = state.get("entity_fqn", "")
    start_time = datetime.now(tz=UTC)

    # Use the table-name component (most specific without service prefix)
    parts = entity_fqn.split(".")
    table_name = parts[-1] if parts else ""
    # Also try the schema.table form for more precision
    schema_table = ".".join(parts[-2:]) if len(parts) >= 2 else table_name

    related_code_files: list[dict[str, Any]] = []
    recent_commits: list[dict[str, Any]] = []
    code_dependencies: list[str] = []

    if table_name:
        # Broad search by table name
        files = await gitnexus_search_files(table_name)
        related_code_files = files[:20]

        # If we got few results, also try schema.table form
        if len(related_code_files) < 5 and schema_table != table_name:
            extra = await gitnexus_search_files(schema_table)
            # Merge, de-duplicate by path
            seen_paths = {f.get("path", "") for f in related_code_files}
            for f in extra:
                if f.get("path", "") not in seen_paths:
                    related_code_files.append(f)
                    if len(related_code_files) >= 20:
                        break

        # Fetch recent commits referencing this entity
        recent_commits = await gitnexus_get_commits(table_name, limit=10)

        code_dependencies = [
            f.get("path", "") for f in related_code_files if f.get("path")
        ]

    step_result = {
        "step": 4,
        "name": "code_blast_radius",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": (
            f"Found {len(related_code_files)} related code files "
            f"for entity '{table_name}'"
        ),
    }

    return {
        **state,
        "related_code_files": related_code_files,
        "recent_commits": recent_commits,
        "code_dependencies": code_dependencies,
        "step_results": [*state.get("step_results", []), step_result],
    }

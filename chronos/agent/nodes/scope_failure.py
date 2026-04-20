"""
Step 1 — Scope Failure

Fetches the failing test case and affected entity details from OpenMetadata.
Extracts column information from the test entity link.
"""

from __future__ import annotations

from datetime import datetime

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import om_get_entity, om_get_test_results


async def scope_failure_node(state: InvestigationState) -> InvestigationState:
    """Fetch test details and entity info; extract affected columns."""
    entity_fqn = state.get("entity_fqn", "")
    test_name = state.get("test_name", "")
    start_time = datetime.utcnow()

    entity = await om_get_entity(entity_fqn)
    test_results = await om_get_test_results(entity_fqn, limit=10)

    failed_test: dict = {}
    last_passed_at = None
    affected_columns: list[str] = []

    # Find the failed test by name, or fall back to the first failed result
    for tr in test_results:
        tc_name = tr.get("name", "") or tr.get("testCaseFQN", "")
        tc_status = (
            tr.get("testCaseResult", {}).get("testCaseStatus")
            or tr.get("testCaseStatus", "")
        )
        if tc_status == "Failed":
            if not test_name or tc_name == test_name or test_name in tc_name:
                failed_test = tr
                break

    # Extract column from entityLink: <#E::table::fqn::columns::col_name>
    entity_link = failed_test.get("entityLink", "")
    if "::" in entity_link:
        parts = [p.strip("<>#") for p in entity_link.split("::")]
        # Last segment after "columns" is the column name
        try:
            col_idx = next(
                i for i, p in enumerate(parts) if p.lower() == "columns"
            )
            col_name = parts[col_idx + 1] if col_idx + 1 < len(parts) else ""
            if col_name:
                affected_columns.append(col_name)
        except StopIteration:
            pass

    step_result = {
        "step": 1,
        "name": "scope_failure",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "summary": (
            f"Scoped failure: entity={entity_fqn}, "
            f"test={test_name or '(first failed)'}, "
            f"columns={affected_columns}"
        ),
    }

    return {
        **state,
        "failed_test": failed_test,
        "affected_entity": entity,
        "affected_columns": affected_columns,
        "last_passed_at": last_passed_at,
        "step_results": state.get("step_results", []) + [step_result],
    }

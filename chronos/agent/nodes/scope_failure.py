"""
Step 1 — Scope Failure

Fetches the failing test case and affected entity details from OpenMetadata.
Extracts column information from the test entity link.
"""

from __future__ import annotations

from datetime import UTC, datetime

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import om_get_entity, om_get_test_results


async def scope_failure_node(state: InvestigationState) -> InvestigationState:
    """Fetch test details and entity info; extract affected columns."""
    entity_fqn = state.get("entity_fqn", "")
    test_name = state.get("test_name", "")
    start_time = datetime.now(tz=UTC)

    entity = await om_get_entity(entity_fqn)
    test_results = await om_get_test_results(entity_fqn, limit=10)

    failed_test: dict = {}
    last_passed_at: datetime | None = None
    affected_columns: list[str] = []

    # Find the failed test by name, or fall back to the first failed result.
    # Also track the most recent "Success" run to surface time-since-last-pass.
    for tr in test_results:
        tc_name = tr.get("name", "") or tr.get("testCaseFQN", "")
        tc_result = tr.get("testCaseResult", {})
        tc_status = tc_result.get("testCaseStatus") or tr.get("testCaseStatus", "")

        if tc_status == "Failed" and not failed_test and (
            not test_name or tc_name == test_name or test_name in tc_name
        ):
            failed_test = tr

        if tc_status == "Success":
            raw_ts = tc_result.get("timestamp") or tr.get("timestamp")
            if raw_ts is not None:
                try:
                    if isinstance(raw_ts, (int, float)):
                        ts = datetime.fromtimestamp(raw_ts / 1000, tz=UTC)
                    else:
                        ts = datetime.fromisoformat(str(raw_ts))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                    if last_passed_at is None or ts > last_passed_at:
                        last_passed_at = ts
                except (ValueError, OSError, OverflowError):
                    pass

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
        "completed_at": datetime.now(tz=UTC).isoformat(),
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
        "step_results": [*state.get("step_results", []), step_result],
    }

"""
Step 1 — Scope Failure

Fetches the failing test case and affected entity details from OpenMetadata.
Extracts column information from the test entity link.

In addition to the OpenMetadata calls, this step now consults the graphify
adapter for the entity's *architectural community* — the louvain cluster of
code modules that implement or consume the entity. Surfacing this early in
the pipeline means later steps (and the LLM RCA prompt) have a clear
ownership / module hint without an extra MCP roundtrip.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from chronos.agent.state import InvestigationState
from chronos.mcp.tools import (
    graphify_get_community,
    om_get_entity,
    om_get_test_results,
)

logger = logging.getLogger("chronos.agent.scope_failure")


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

        if (
            tc_status == "Failed"
            and not failed_test
            and (not test_name or tc_name == test_name or test_name in tc_name)
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
            col_idx = next(i for i, p in enumerate(parts) if p.lower() == "columns")
            col_name = parts[col_idx + 1] if col_idx + 1 < len(parts) else ""
            if col_name:
                affected_columns.append(col_name)
        except StopIteration:
            pass

    # Architectural context — non-fatal best effort. The graphify graph may
    # not contain the data entity (it indexes the CHRONOS codebase, not the
    # data warehouse) but for code-shaped entity names it returns the
    # community membership which is useful as an ownership hint.
    architectural_community: dict = {}
    if entity_fqn:
        # Try the most specific name first; fall back to the bare table name.
        candidates = [entity_fqn]
        last_segment = entity_fqn.rsplit(".", 1)[-1]
        if last_segment and last_segment != entity_fqn:
            candidates.append(last_segment)
        for candidate in candidates:
            try:
                community = await graphify_get_community(candidate, limit=20)
            except Exception as exc:
                logger.debug("graphify_get_community(%s) failed: %s", candidate, exc)
                community = {}
            if community:
                architectural_community = community
                break

    step_result = {
        "step": 1,
        "name": "scope_failure",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.now(tz=UTC).isoformat(),
        "summary": (
            f"Scoped failure: entity={entity_fqn}, "
            f"test={test_name or '(first failed)'}, "
            f"columns={affected_columns}, "
            f"community={architectural_community.get('community_id', 'n/a')}"
        ),
    }

    return {
        **state,
        "failed_test": failed_test,
        "affected_entity": entity,
        "affected_columns": affected_columns,
        "last_passed_at": last_passed_at,
        "architectural_community": architectural_community,
        "step_results": [*state.get("step_results", []), step_result],
    }

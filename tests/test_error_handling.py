from __future__ import annotations

import asyncio

import httpx
import pytest

from chronos.core.investigation_runner import run_investigation
from chronos.llm.client import synthesize_rca
from chronos.models.events import InvestigationTrigger


@pytest.mark.asyncio
async def test_synthesize_rca_returns_fallback_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _mock_call(*_args, **_kwargs):
        request = httpx.Request("POST", "http://litellm.local/chat/completions")
        response = httpx.Response(status_code=503, request=request, text="unavailable")
        raise httpx.HTTPStatusError("upstream failed", request=request, response=response)

    monkeypatch.setattr("chronos.llm.client._call_litellm", _mock_call)

    result = await synthesize_rca({"failed_test": {"name": "not_null"}})
    assert result["root_cause_category"] == "UNKNOWN"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_run_investigation_reraises_cancelled_error(
    monkeypatch: pytest.MonkeyPatch,
):
    class _CancelledGraph:
        async def ainvoke(self, *_args, **_kwargs):
            raise asyncio.CancelledError()

    monkeypatch.setattr(
        "chronos.core.investigation_runner._get_graph",
        lambda: (_CancelledGraph(), lambda _incident_id: None),
    )

    trigger = InvestigationTrigger(
        entity_fqn="sample_db.default.orders",
        test_name="column_values_to_be_not_null",
        failure_message="nulls found",
    )

    with pytest.raises(asyncio.CancelledError):
        await run_investigation(trigger, incident_id="incident-cancelled")

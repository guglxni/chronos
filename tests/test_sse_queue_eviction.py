"""
Tests for the SSE queue orphan-eviction logic in chronos.api.routes.investigations.

When /investigate is triggered but nobody ever connects to /stream, the queue
must be evicted after _SSE_ORPHAN_TTL seconds to avoid an unbounded memory leak.
Tests patch the TTL constant so they complete in milliseconds.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from chronos.api.routes import investigations


@pytest.fixture(autouse=True)
def _clear_queues():
    investigations._sse_queues.clear()
    investigations._active_tasks.clear()
    yield
    investigations._sse_queues.clear()
    investigations._active_tasks.clear()


@pytest.mark.asyncio
async def test_evict_orphan_queue_removes_entry():
    """Queue should be removed after the TTL when nobody drained it."""
    investigations._sse_queues["test-1"] = asyncio.Queue(maxsize=10)

    with patch.object(investigations, "_SSE_ORPHAN_TTL", 0.01):
        await investigations._evict_orphan_queue("test-1")

    assert "test-1" not in investigations._sse_queues


@pytest.mark.asyncio
async def test_evict_orphan_queue_is_noop_when_already_gone():
    """If the stream consumer already removed the queue, eviction must not raise."""
    # Not adding anything to _sse_queues — simulates consumer-already-popped
    with patch.object(investigations, "_SSE_ORPHAN_TTL", 0.01):
        await investigations._evict_orphan_queue("missing-id")  # must not raise

    assert "missing-id" not in investigations._sse_queues


@pytest.mark.asyncio
async def test_on_investigation_done_schedules_cleanup():
    """Done-callback should create a cleanup task when the investigation finishes."""
    investigations._sse_queues["test-2"] = asyncio.Queue(maxsize=10)

    async def _dummy():
        return None

    task = asyncio.create_task(_dummy())
    await task

    callback = investigations._on_investigation_done("test-2")

    with patch.object(investigations, "_SSE_ORPHAN_TTL", 0.01):
        callback(task)
        # Yield control so the created cleanup task runs
        await asyncio.sleep(0.05)

    assert "test-2" not in investigations._sse_queues

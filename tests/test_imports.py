from __future__ import annotations

import importlib
import time


def test_no_circular_imports():
    import chronos.api.routes.incidents
    import chronos.api.routes.investigations
    import chronos.api.routes.webhooks
    import chronos.core.investigation_runner


def test_graph_compilation_deferred_until_runtime():
    started = time.perf_counter()
    module = importlib.reload(importlib.import_module("chronos.core.investigation_runner"))
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
    assert module._graph_cache is None  # graph should not compile on module import

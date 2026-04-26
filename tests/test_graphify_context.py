"""Tests for the graphify_context enrichment renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from chronos.code_intel import graphify_adapter
from chronos.enrichment import graphify_context

GRAPH_PATH = Path(__file__).resolve().parent.parent / "graphify-out" / "graph.json"


@pytest.fixture(autouse=True)
def _point_at_real_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the in-tree graph artifact for these tests."""
    monkeypatch.setattr(graphify_context, "GRAPH_PATH", GRAPH_PATH)


@pytest.mark.skipif(
    not GRAPH_PATH.exists(),
    reason="graph.json missing — run /graphify . to generate it",
)
def test_get_graphify_context_returns_markdown_block() -> None:
    rendered = graphify_context.get_graphify_context("IncidentReport")
    assert rendered, "expected non-empty context for a known node"
    assert "###" in rendered  # at least one markdown heading present
    assert len(rendered) <= graphify_context._MAX_CHARS


@pytest.mark.skipif(
    not GRAPH_PATH.exists(),
    reason="graph.json missing — run /graphify . to generate it",
)
def test_get_graphify_context_global_god_nodes_when_entity_unknown() -> None:
    # Unknown entity → no community/neighbours, but god nodes still render.
    rendered = graphify_context.get_graphify_context("definitely_not_a_real_node_xyz")
    assert "god nodes" in rendered.lower()


def test_get_graphify_context_returns_empty_when_artifact_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "no_graph.json"
    monkeypatch.setattr(graphify_context, "GRAPH_PATH", missing)
    assert graphify_context.get_graphify_context("anything") == ""


def test_render_block_handles_empty_payload() -> None:
    assert graphify_context._render_block({}) == ""


def test_render_block_truncates_oversized_input() -> None:
    payload = {
        "neighbors": [
            {
                "node": {"id": f"n{i}", "label": "X" * 200},
                "relation": "calls",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            }
            for i in range(50)
        ],
        "god_nodes": [{"id": f"g{i}", "label": "G" * 200, "degree": 99} for i in range(50)],
    }
    out = graphify_context._render_block(payload)
    assert len(out) <= graphify_context._MAX_CHARS


def test_adapter_cache_reloads_on_mtime_change(tmp_path: Path) -> None:
    """Touching the file invalidates the cache so the next call reloads."""
    import json

    from chronos.code_intel.graphify_adapter import _GraphCache

    cache = _GraphCache()
    path = tmp_path / "graph.json"
    path.write_text(
        json.dumps(
            {
                "directed": False,
                "multigraph": False,
                "graph": {},
                "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
                "links": [{"source": "a", "target": "b"}],
            }
        )
    )
    g1 = cache.get(path)
    assert g1 is not None and g1.number_of_nodes() == 2

    # Bump mtime + content. Sleep for at least 1ns is implicit in the rewrite.
    path.write_text(
        json.dumps(
            {
                "directed": False,
                "multigraph": False,
                "graph": {},
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                    {"id": "c", "label": "C"},
                ],
                "links": [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}],
            }
        )
    )
    g2 = cache.get(path)
    assert g2 is not None and g2.number_of_nodes() == 3

    # Confirm graphify_adapter helpers honour the new graph.
    node = graphify_adapter.get_node("C", graph_path=path)
    assert node.get("label") == "C"

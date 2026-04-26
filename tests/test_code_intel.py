"""
Tests for the chronos.code_intel layer.

Covers:
* ``local_git`` — subprocess git ops against a temp repo.
* ``code_search`` — ripgrep + pure-Python file scan against a temp tree.
* ``sql_parser`` — sqlglot AST + regex fallback.
* ``graphify_adapter`` — live queries against the in-tree graph.json.
* ``dbt_manifest`` — manifest parser against a synthetic manifest.

Each test is hermetic: nothing reaches out to the network and the only
filesystem state is in pytest's ``tmp_path`` fixture (except the graphify
adapter test which intentionally exercises the real
``graphify-out/graph.json`` artifact that ships with this repo).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from chronos.code_intel import (
    code_search,
    dbt_manifest,
    graphify_adapter,
    local_git,
    sql_parser,
)

# ─── helpers ──────────────────────────────────────────────────────────────────

def _run(args: list[str], cwd: Path) -> None:
    """Run a subprocess command in ``cwd`` and assert success.

    We strip the user's global git signing config (``commit.gpgsign=true``,
    ``gpg.format=ssh``) by setting ``GIT_CONFIG_GLOBAL`` to ``/dev/null`` —
    otherwise local commits would block on the user's SSH passphrase.
    """
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@t",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }
    subprocess.run(args, cwd=cwd, env=env, check=True,  # noqa: S603
                   capture_output=True)


def _make_repo(root: Path) -> Path:
    """Create a tiny git repo with three commits and return its path."""
    repo = root / "repo"
    repo.mkdir()
    _run(["git", "init", "-q", "-b", "main"], repo)
    # Belt-and-braces: disable signing locally too in case the env var path
    # changes between git versions.
    _run(["git", "config", "commit.gpgsign", "false"], repo)
    _run(["git", "config", "tag.gpgsign", "false"], repo)
    (repo / "model.sql").write_text("SELECT * FROM analytics.orders\n")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-q", "-m", "initial orders model"], repo)
    (repo / "etl.py").write_text(
        "import pandas as pd\nDF = pd.read_sql('SELECT id FROM orders', None)\n"
    )
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-q", "-m", "etl reading orders table"], repo)
    (repo / "unrelated.py").write_text("print('hello')\n")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-q", "-m", "noise commit unrelated"], repo)
    return repo


# ─── local_git ────────────────────────────────────────────────────────────────

def test_local_git_finds_only_orders_commits(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    commits = local_git.get_commits_for_entity("orders", repo, limit=5)
    assert len(commits) == 2  # the two commits whose diffs touch "orders"
    sample = commits[0]
    for key in ("sha", "author", "date", "message", "files_changed"):
        assert key in sample
    assert all(isinstance(c["files_changed"], list) for c in commits)


def test_local_git_rejects_unsafe_entity(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    # Shell-meta and overlong inputs return [] without invoking git.
    assert local_git.get_commits_for_entity("orders; rm -rf /", repo) == []
    assert local_git.get_commits_for_entity("", repo) == []


def test_local_git_returns_empty_for_non_repo(tmp_path: Path) -> None:
    plain = tmp_path / "not_a_repo"
    plain.mkdir()
    assert local_git.get_commits_for_entity("orders", plain) == []


def test_local_git_file_history(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    history = local_git.get_file_history("model.sql", repo, limit=5)
    assert len(history) == 1
    assert history[0]["message"].startswith("initial orders")


@pytest.mark.asyncio
async def test_local_git_async_wrapper_runs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    commits = await local_git.aget_commits_for_entity("orders", repo, limit=5)
    assert len(commits) == 2


# ─── code_search ──────────────────────────────────────────────────────────────

def test_code_search_finds_files_referencing_orders(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    hits = code_search.search_entity_references("orders", repo, limit=10)
    paths = {h["path"] for h in hits}
    assert "model.sql" in paths
    assert "etl.py" in paths
    assert "unrelated.py" not in paths
    for hit in hits:
        assert "snippet" in hit
        assert "language" in hit


def test_code_search_rejects_unsafe_query(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    assert code_search.search_entity_references("o;rm -rf /", repo) == []
    assert code_search.search_entity_references("", repo) == []


def test_code_search_returns_empty_when_path_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir"
    assert code_search.search_entity_references("orders", missing) == []


@pytest.mark.asyncio
async def test_code_search_async_wrapper_runs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    hits = await code_search.asearch_entity_references("orders", repo, limit=10)
    assert any(h["path"] == "model.sql" for h in hits)


# ─── sql_parser ───────────────────────────────────────────────────────────────

def test_sql_parser_extracts_basic_tables() -> None:
    sql = "SELECT * FROM analytics.orders JOIN raw.users u ON u.id = orders.user_id"
    tables = sql_parser.extract_table_references(sql)
    assert "analytics.orders" in tables
    assert "raw.users" in tables


def test_sql_parser_handles_quoted_identifiers() -> None:
    sql = 'SELECT * FROM "Analytics"."Orders" JOIN `raw`.`users`'
    tables = sql_parser.extract_table_references(sql)
    # Quoting is normalised away and identifiers are lowercased.
    assert "analytics.orders" in tables
    assert "raw.users" in tables


def test_sql_parser_returns_empty_for_garbage_input() -> None:
    assert sql_parser.extract_table_references("") == []
    assert sql_parser.extract_table_references("not sql at all") == []


def test_file_references_entity_matches_trailing_segment() -> None:
    sql = "SELECT * FROM analytics.orders"
    result = sql_parser.file_references_entity(sql, "orders")
    assert result["matched"] is True
    assert "analytics.orders" in result["tables"]


def test_file_references_entity_text_fallback() -> None:
    text = "# orders runbook\nthis file just mentions orders in prose"
    result = sql_parser.file_references_entity(text, "orders")
    assert result["matched"] is True
    assert result["match_kind"] == "text"


# ─── graphify_adapter ─────────────────────────────────────────────────────────
# These exercise the real graphify-out/graph.json shipped with this repo.

GRAPH_PATH = (
    Path(__file__).resolve().parent.parent / "graphify-out" / "graph.json"
)
_GRAPH_AVAILABLE = GRAPH_PATH.exists()


@pytest.mark.skipif(
    not _GRAPH_AVAILABLE, reason="graph.json missing — skipping live adapter tests",
)
def test_graphify_loads_and_reports_stats() -> None:
    stats = graphify_adapter.graph_stats(GRAPH_PATH)
    assert stats["available"] is True
    assert stats["nodes"] > 0
    assert stats["edges"] > 0


@pytest.mark.skipif(not _GRAPH_AVAILABLE, reason="graph.json missing")
def test_graphify_get_node_for_known_label() -> None:
    node = graphify_adapter.get_node("IncidentReport", graph_path=GRAPH_PATH)
    assert node, "expected to find IncidentReport node"
    assert "label" in node and "id" in node


@pytest.mark.skipif(not _GRAPH_AVAILABLE, reason="graph.json missing")
def test_graphify_get_neighbors_returns_edges_with_metadata() -> None:
    neighbours = graphify_adapter.get_neighbors(
        "IncidentReport", limit=5, graph_path=GRAPH_PATH
    )
    assert neighbours
    sample = neighbours[0]
    assert "node" in sample and "relation" in sample and "confidence" in sample


@pytest.mark.skipif(not _GRAPH_AVAILABLE, reason="graph.json missing")
def test_graphify_god_nodes_includes_known_hub() -> None:
    gods = graphify_adapter.god_nodes(limit=10, graph_path=GRAPH_PATH)
    labels = {g["label"] for g in gods}
    # IncidentReport is consistently in the top 5 in the in-tree graph.
    assert any("IncidentReport" in lbl for lbl in labels)


@pytest.mark.skipif(not _GRAPH_AVAILABLE, reason="graph.json missing")
def test_graphify_returns_empty_for_unknown_query() -> None:
    assert graphify_adapter.get_node(
        "definitely_not_a_real_node_xyz", graph_path=GRAPH_PATH
    ) == {}
    assert graphify_adapter.get_neighbors(
        "definitely_not_a_real_node_xyz", graph_path=GRAPH_PATH
    ) == []


def test_graphify_handles_missing_artifact(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    assert graphify_adapter.is_available(missing) is False
    assert graphify_adapter.graph_stats(missing) == {
        "available": False, "nodes": 0, "edges": 0, "communities": 0,
    }
    assert graphify_adapter.get_node("anything", graph_path=missing) == {}


# ─── dbt_manifest ─────────────────────────────────────────────────────────────

@pytest.fixture()
def synthetic_manifest(tmp_path: Path) -> Path:
    """Write a minimal dbt manifest covering one source + two models."""
    manifest = {
        "metadata": {"dbt_version": "1.7.0"},
        "nodes": {
            "model.shop.dim_orders": {
                "name": "dim_orders",
                "resource_type": "model",
                "database": "analytics",
                "schema": "marts",
                "alias": "dim_orders",
                "package_name": "shop",
                "original_file_path": "models/marts/dim_orders.sql",
                "patch_path": "shop://models/marts/schema.yml",
                "tags": ["tier1"],
                "depends_on": {"nodes": ["source.shop.raw.orders"]},
            },
            "model.shop.fact_revenue": {
                "name": "fact_revenue",
                "resource_type": "model",
                "database": "analytics",
                "schema": "marts",
                "alias": "fact_revenue",
                "package_name": "shop",
                "original_file_path": "models/marts/fact_revenue.sql",
                "patch_path": "",
                "tags": [],
                "depends_on": {"nodes": ["model.shop.dim_orders"]},
            },
        },
        "sources": {
            "source.shop.raw.orders": {
                "name": "orders",
                "resource_type": "source",
                "database": "raw",
                "schema": "raw",
                "alias": "orders",
                "package_name": "shop",
                "original_file_path": "models/sources.yml",
                "patch_path": "",
                "tags": [],
                "depends_on": {"nodes": []},
            },
        },
        "child_map": {
            "source.shop.raw.orders": ["model.shop.dim_orders"],
            "model.shop.dim_orders": ["model.shop.fact_revenue"],
            "model.shop.fact_revenue": [],
        },
    }
    target = tmp_path / "manifest.json"
    target.write_text(json.dumps(manifest))
    return target


def test_dbt_manifest_resolves_node_by_table_name(synthetic_manifest: Path) -> None:
    node = dbt_manifest.get_node_by_entity("orders", synthetic_manifest)
    assert node["resource_type"] == "source"
    assert node["name"] == "orders"


def test_dbt_manifest_returns_parents_and_children(synthetic_manifest: Path) -> None:
    parents = dbt_manifest.get_parents("dim_orders", synthetic_manifest)
    children = dbt_manifest.get_children("dim_orders", synthetic_manifest)
    assert any(p["name"] == "orders" for p in parents)
    assert any(c["name"] == "fact_revenue" for c in children)


def test_dbt_manifest_walk_downstream_two_levels(synthetic_manifest: Path) -> None:
    walk = dbt_manifest.walk_downstream("orders", depth=3,
                                        manifest_path=synthetic_manifest)
    names = [n["name"] for n in walk]
    assert "dim_orders" in names
    assert "fact_revenue" in names


def test_dbt_manifest_get_node_files_returns_sql_and_yaml(
    synthetic_manifest: Path,
) -> None:
    files = dbt_manifest.get_node_files("dim_orders", synthetic_manifest)
    paths = {f["path"] for f in files}
    assert "models/marts/dim_orders.sql" in paths
    # patch_path was given as ``shop://models/marts/schema.yml`` — prefix stripped.
    assert "models/marts/schema.yml" in paths


def test_dbt_manifest_handles_missing_artifact(tmp_path: Path) -> None:
    missing = tmp_path / "no_manifest.json"
    assert dbt_manifest.is_available(missing) is False
    assert dbt_manifest.get_node_by_entity("orders", missing) == {}
    assert dbt_manifest.get_parents("orders", missing) == []
    assert dbt_manifest.get_children("orders", missing) == []

"""
dbt ``target/manifest.json`` parser — exact lineage for dbt projects.

dbt-core writes ``manifest.json`` after every ``dbt parse``/``dbt run``. The
file contains the full project DAG: ``parent_map`` (upstream dependencies)
and ``child_map`` (downstream dependents) keyed by node id. This module
loads the manifest and exposes the queries the CHRONOS pipeline cares about:

* ``get_node_by_entity`` — locate the dbt node id for a table FQN.
* ``get_parents`` / ``get_children`` — direct DAG neighbours.
* ``get_node_files`` — the source files defining a dbt node (model SQL,
  schema YAML, snapshot SQL, etc.).
* ``walk_upstream`` / ``walk_downstream`` — depth-limited DAG traversal.

Returns are JSON-serialisable so the result drops directly into the
``InvestigationState`` and the IncidentReport.

Why this matters: for dbt projects, this gives **structural ground truth**
(no LLM, no regex) about which models read/write a table, which is far more
reliable than the substring-based file scan in ``code_search``. The two
backends are complementary — manifest answers "which dbt models?", code
search answers "which Python/SQL outside dbt?".
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger("chronos.code_intel.dbt_manifest")

# Conventional location of the manifest relative to the dbt project root.
_DEFAULT_MANIFEST_REL_PATH = Path("target") / "manifest.json"

# Walk depth caps — protect against pathological dbt graphs.
_MAX_DEPTH = 8
_MAX_RESULTS = 100


class _ManifestCache:
    """Process-wide manifest cache keyed by ``(path, mtime_ns)``."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._path: Path | None = None
        self._mtime_ns: int | None = None
        self._manifest: dict[str, Any] | None = None

    def get(self, path: Path) -> dict[str, Any] | None:
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            return None
        with self._lock:
            if (
                self._manifest is not None
                and self._path == path
                and self._mtime_ns == mtime_ns
            ):
                return self._manifest
            data = self._load(path)
            if data is None:
                return None
            self._path = path
            self._mtime_ns = mtime_ns
            self._manifest = data
            return data

    @staticmethod
    def _load(path: Path) -> dict[str, Any] | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("dbt: failed to read %s: %s", path, exc)
            return None
        if not isinstance(data, dict) or "nodes" not in data:
            logger.warning("dbt: manifest at %s missing required keys", path)
            return None
        logger.info(
            "dbt: loaded manifest with %d nodes / %d sources from %s",
            len(data.get("nodes", {})), len(data.get("sources", {})), path,
        )
        return data


_CACHE = _ManifestCache()


def _resolve_path(manifest_path: Path | str | None) -> Path:
    """Coerce the manifest path arg to ``Path``, defaulting to ``target/manifest.json``."""
    if manifest_path is None:
        # Search upward from CWD for a ``target/manifest.json`` so this
        # works whether CHRONOS runs from the dbt project root or a sibling.
        cwd = Path.cwd()
        for parent in (cwd, *cwd.parents):
            candidate = parent / _DEFAULT_MANIFEST_REL_PATH
            if candidate.exists():
                return candidate
        return cwd / _DEFAULT_MANIFEST_REL_PATH
    return Path(manifest_path) if isinstance(manifest_path, str) else manifest_path


def _manifest(manifest_path: Path | str | None = None) -> dict[str, Any] | None:
    """Return the loaded manifest or ``None`` if unavailable."""
    return _CACHE.get(_resolve_path(manifest_path))


def is_available(manifest_path: Path | str | None = None) -> bool:
    """Return True iff a dbt manifest can be loaded."""
    return _manifest(manifest_path) is not None


def manifest_stats(manifest_path: Path | str | None = None) -> dict[str, Any]:
    """Compact summary suitable for ``/healthz`` readiness checks."""
    data = _manifest(manifest_path)
    if data is None:
        return {"available": False, "models": 0, "sources": 0}
    return {
        "available": True,
        "models": sum(
            1 for v in data.get("nodes", {}).values()
            if isinstance(v, dict) and v.get("resource_type") == "model"
        ),
        "sources": len(data.get("sources", {})),
        "exposures": len(data.get("exposures", {})),
        "tests": sum(
            1 for v in data.get("nodes", {}).values()
            if isinstance(v, dict) and v.get("resource_type") == "test"
        ),
        "path": str(_resolve_path(manifest_path)),
    }


def _entity_matches_node(entity_name: str, node: dict[str, Any]) -> bool:
    """Check whether a manifest node represents the given table FQN."""
    if not isinstance(node, dict):
        return False
    target = entity_name.strip().lower()
    if not target:
        return False
    # Compare against database.schema.name and the table alias the user sees.
    db = str(node.get("database") or "").lower()
    schema = str(node.get("schema") or "").lower()
    name = str(node.get("name") or node.get("alias") or "").lower()
    candidates = {
        name,
        f"{schema}.{name}" if schema else "",
        f"{db}.{schema}.{name}" if db and schema else "",
        str(node.get("identifier") or "").lower(),
        str(node.get("relation_name") or "").strip('"`').lower(),
    }
    candidates.discard("")
    if target in candidates:
        return True
    # Allow a trailing-segment match for ``service.db.schema.table`` FQNs
    # where ``service`` is the OpenMetadata service prefix that dbt does not
    # know about.
    parts = target.split(".")
    if len(parts) >= 2 and parts[-1] == name:
        return True
    return bool(len(parts) >= 3 and parts[-1] == name and parts[-2] == schema)


def get_node_by_entity(
    entity_name: str,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Locate the dbt node id and metadata for a given table FQN."""
    data = _manifest(manifest_path)
    if data is None:
        return {}
    # Prefer real nodes (models/snapshots) over sources/seeds when both exist.
    for collection_key in ("nodes", "sources", "exposures", "metrics"):
        collection = data.get(collection_key, {})
        if not isinstance(collection, dict):
            continue
        for node_id, node in collection.items():
            if _entity_matches_node(entity_name, node):
                return _summarise_node(node_id, node)
    return {}


def _summarise_node(node_id: str, node: dict[str, Any]) -> dict[str, Any]:
    """Project a manifest node onto a stable, JSON-friendly summary."""
    return {
        "node_id": node_id,
        "name": str(node.get("name", "")),
        "resource_type": str(node.get("resource_type", "")),
        "database": str(node.get("database", "") or ""),
        "schema": str(node.get("schema", "") or ""),
        "alias": str(node.get("alias", "") or ""),
        "package_name": str(node.get("package_name", "") or ""),
        "original_file_path": str(node.get("original_file_path", "") or ""),
        "patch_path": str(node.get("patch_path", "") or ""),
        "tags": [str(t) for t in (node.get("tags") or [])],
        "depends_on_nodes": [
            str(n) for n in ((node.get("depends_on") or {}).get("nodes") or [])
        ],
    }


def _resolve_node(
    data: dict[str, Any],
    node_id: str,
) -> dict[str, Any] | None:
    """Find a node by id across all manifest collections."""
    for collection_key in ("nodes", "sources", "exposures", "metrics"):
        collection = data.get(collection_key, {})
        if isinstance(collection, dict) and node_id in collection:
            entry = collection[node_id]
            return entry if isinstance(entry, dict) else None
    return None


def get_parents(
    entity_name: str,
    manifest_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return the direct upstream dbt nodes for a table FQN."""
    data = _manifest(manifest_path)
    if data is None:
        return []
    summary = get_node_by_entity(entity_name, manifest_path)
    if not summary:
        return []
    parents: list[dict[str, Any]] = []
    for parent_id in summary.get("depends_on_nodes", []):
        node = _resolve_node(data, parent_id)
        if node is not None:
            parents.append(_summarise_node(parent_id, node))
    return parents


def get_children(
    entity_name: str,
    manifest_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return the direct downstream dbt nodes for a table FQN.

    Uses ``child_map`` when present (modern dbt manifests) and falls back to
    inverting ``depends_on`` across all nodes for older formats.
    """
    data = _manifest(manifest_path)
    if data is None:
        return []
    summary = get_node_by_entity(entity_name, manifest_path)
    if not summary:
        return []
    node_id = summary["node_id"]
    child_map = data.get("child_map")
    if isinstance(child_map, dict) and node_id in child_map:
        child_ids = list(child_map.get(node_id) or [])
    else:
        child_ids = []
        for cid, node in (data.get("nodes") or {}).items():
            deps = ((node or {}).get("depends_on") or {}).get("nodes") or []
            if node_id in deps:
                child_ids.append(cid)
    children: list[dict[str, Any]] = []
    for cid in child_ids:
        node = _resolve_node(data, cid)
        if node is not None:
            children.append(_summarise_node(cid, node))
    return children


def get_node_files(
    entity_name: str,
    manifest_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return the dbt source files defining a node (SQL + YAML).

    Result format matches ``code_search.search_entity_references`` so the
    pipeline's existing ``related_code_files`` field accepts it directly:
    ``[{path, line, snippet, language, source}]``.
    """
    summary = get_node_by_entity(entity_name, manifest_path)
    if not summary:
        return []
    files: list[dict[str, Any]] = []
    for path_field, language in (
        ("original_file_path", "sql"),
        ("patch_path", "yaml"),
    ):
        path_value = summary.get(path_field, "")
        if not path_value:
            continue
        # ``patch_path`` may include a ``package://`` prefix used by dbt to
        # disambiguate cross-project schema yml files. Strip it for display.
        cleaned = str(path_value).split("://", 1)[-1]
        files.append(
            {
                "path": cleaned,
                "line": 0,
                "snippet": (
                    f"dbt {summary['resource_type']} '{summary['name']}' "
                    f"defined here"
                )[:200],
                "language": language,
                "source": "dbt_manifest",
            }
        )
    return files


def walk_upstream(
    entity_name: str,
    depth: int = 3,
    manifest_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Breadth-first walk upstream from ``entity_name``."""
    return _walk(entity_name, depth, "parents", manifest_path)


def walk_downstream(
    entity_name: str,
    depth: int = 3,
    manifest_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Breadth-first walk downstream from ``entity_name``."""
    return _walk(entity_name, depth, "children", manifest_path)


def _walk(
    entity_name: str,
    depth: int,
    direction: str,
    manifest_path: Path | str | None,
) -> list[dict[str, Any]]:
    data = _manifest(manifest_path)
    if data is None:
        return []
    seed = get_node_by_entity(entity_name, manifest_path)
    if not seed:
        return []
    visited: set[str] = {seed["node_id"]}
    frontier: list[dict[str, Any]] = [seed]
    out: list[dict[str, Any]] = []
    levels = max(1, min(depth, _MAX_DEPTH))
    for level in range(1, levels + 1):
        next_frontier: list[dict[str, Any]] = []
        for current in frontier:
            neighbour_summaries = (
                get_parents(current["name"], manifest_path)
                if direction == "parents"
                else get_children(current["name"], manifest_path)
            )
            for neighbour in neighbour_summaries:
                if neighbour["node_id"] in visited:
                    continue
                visited.add(neighbour["node_id"])
                neighbour_with_level = {**neighbour, "depth": level}
                out.append(neighbour_with_level)
                next_frontier.append(neighbour)
                if len(out) >= _MAX_RESULTS:
                    return out
        frontier = next_frontier
        if not frontier:
            break
    return out

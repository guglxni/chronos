"""
Live in-process adapter over a graphify ``graph.json`` artifact.

Replaces ``chronos.enrichment.graphify_context.get_graphify_context`` —
which was a naive markdown grep — with a NetworkX-backed loader that
exposes the queries the LangGraph pipeline actually needs:

* ``get_node`` — fetch full attributes for one node.
* ``get_neighbors`` — adjacent nodes with edge metadata (calls / imports /
  semantically_similar_to).
* ``get_community`` — every node in the failing entity's louvain community,
  plus the community label and cohesion score.
* ``shortest_path`` — code-level path between two nodes (blast radius).
* ``query_graph`` — BFS bag-of-context for an entity name + depth budget.
* ``god_nodes`` — most-connected nodes (architectural risk surface).

Design notes:

* The graph is loaded **once per process**, lazily, behind a lock. Reloads
  happen only when ``graph.json`` mtime changes — the post-commit hook /
  ``graphify --update`` rewrites the file, so a long-running CHRONOS
  process picks up the new graph automatically without a restart.
* Every public function returns plain ``dict`` / ``list[dict]`` so the
  result is JSON-serialisable and can be embedded directly in the
  ``InvestigationState`` TypedDict and the IncidentReport's
  ``graphify_context`` field.
* All functions fail soft: missing artifact → ``{}`` or ``[]``; missing
  node → ``{}``. The investigation pipeline should never crash because of
  a stale graph.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

import networkx as nx
from networkx.readwrite import json_graph

logger = logging.getLogger("chronos.code_intel.graphify_adapter")

# Default location of the graphify-out artifact relative to the repo root.
_DEFAULT_GRAPH_PATH = (
    Path(__file__).resolve().parent.parent.parent / "graphify-out" / "graph.json"
)

# How many neighbours / community members / path nodes to return at most.
_DEFAULT_NEIGHBOR_LIMIT = 25
_DEFAULT_COMMUNITY_LIMIT = 50
_DEFAULT_QUERY_DEPTH = 2
_DEFAULT_QUERY_LIMIT = 30
_DEFAULT_GOD_LIMIT = 10


class _GraphCache:
    """Process-wide cache keyed by ``(path, mtime_ns)``."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._path: Path | None = None
        self._mtime_ns: int | None = None
        self._graph: nx.Graph | None = None

    def get(self, path: Path) -> nx.Graph | None:
        """Return the cached graph, reloading if the file has changed."""
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            return None
        with self._lock:
            if (
                self._graph is not None
                and self._path == path
                and self._mtime_ns == mtime_ns
            ):
                return self._graph
            graph = self._load(path)
            if graph is None:
                return None
            self._path = path
            self._mtime_ns = mtime_ns
            self._graph = graph
            return graph

    @staticmethod
    def _load(path: Path) -> nx.Graph | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("graphify: failed to read %s: %s", path, exc)
            return None
        try:
            # NetworkX' node-link format uses ``links`` for edges by default
            # (the format graphify writes). The ``edges='links'`` kwarg is
            # the modern, deprecation-safe spelling.
            graph = json_graph.node_link_graph(data, edges="links")
        except (TypeError, KeyError, nx.NetworkXError) as exc:
            logger.warning("graphify: invalid graph payload in %s: %s", path, exc)
            return None
        logger.info(
            "graphify: loaded %d nodes / %d edges from %s",
            graph.number_of_nodes(), graph.number_of_edges(), path,
        )
        return graph


_CACHE = _GraphCache()


def _resolve_path(graph_path: Path | str | None) -> Path:
    """Coerce the path arg to ``Path``, defaulting to ``graphify-out/graph.json``."""
    if graph_path is None:
        return _DEFAULT_GRAPH_PATH
    return Path(graph_path) if isinstance(graph_path, str) else graph_path


def _graph(graph_path: Path | str | None = None) -> nx.Graph | None:
    """Return the loaded graph or ``None`` if the artifact is unavailable."""
    return _CACHE.get(_resolve_path(graph_path))


def _node_attrs(graph: nx.Graph, node_id: str) -> dict[str, Any]:
    """Return a node's attribute dict with ``id`` injected, or ``{}``."""
    if node_id not in graph.nodes:
        return {}
    attrs = dict(graph.nodes[node_id])
    attrs["id"] = node_id
    return attrs


def _find_best_node(graph: nx.Graph, query: str) -> str | None:
    """Find the node whose label or id best matches ``query``.

    Scoring:
        * Exact id match → highest priority.
        * Exact lowercased label match → next.
        * Substring match in label → fallback, ranked by label brevity
          (shorter labels are usually better hits).
    """
    if not query:
        return None
    query_lower = query.strip().lower()
    if not query_lower:
        return None
    if query in graph.nodes:
        return str(query)
    # Walk all nodes once, recording the strongest hit so far.
    best_id: str | None = None
    best_score: tuple[int, int] = (-1, 0)  # (rank, -len(label))
    for node_id, data in graph.nodes(data=True):
        label = str(data.get("label", "")).lower()
        norm = str(data.get("norm_label", "")).lower()
        node_lower = node_id.lower()
        if query_lower == node_lower:
            return str(node_id)
        if query_lower in (label, norm):
            rank = 3
        elif label.endswith("." + query_lower) or label.endswith("/" + query_lower):
            rank = 2
        elif query_lower in label or query_lower in norm or query_lower in node_lower:
            rank = 1
        else:
            continue
        score = (rank, -len(label))
        if score > best_score:
            best_score = score
            best_id = node_id
    return best_id


def is_available(graph_path: Path | str | None = None) -> bool:
    """Return True iff the graphify artifact loads cleanly."""
    return _graph(graph_path) is not None


def graph_stats(graph_path: Path | str | None = None) -> dict[str, Any]:
    """Return a compact summary of the loaded graph for the API ``/healthz``."""
    graph = _graph(graph_path)
    if graph is None:
        return {"available": False, "nodes": 0, "edges": 0, "communities": 0}
    communities = {
        data.get("community")
        for _, data in graph.nodes(data=True)
        if data.get("community") is not None
    }
    return {
        "available": True,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "communities": len(communities),
        "path": str(_resolve_path(graph_path)),
    }


def get_node(
    query: str,
    graph_path: Path | str | None = None,
) -> dict[str, Any]:
    """Look up a node by id or label and return its attributes."""
    graph = _graph(graph_path)
    if graph is None:
        return {}
    node_id = _find_best_node(graph, query)
    if node_id is None:
        return {}
    return _node_attrs(graph, node_id)


def get_neighbors(
    query: str,
    limit: int = _DEFAULT_NEIGHBOR_LIMIT,
    graph_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return the directly-connected nodes with edge metadata."""
    graph = _graph(graph_path)
    if graph is None:
        return []
    node_id = _find_best_node(graph, query)
    if node_id is None:
        return []
    results: list[dict[str, Any]] = []
    for neighbour in graph.neighbors(node_id):
        edge = graph.get_edge_data(node_id, neighbour) or {}
        attrs = _node_attrs(graph, neighbour)
        if not attrs:
            continue
        results.append(
            {
                "node": attrs,
                "relation": str(edge.get("relation", "")),
                "confidence": str(edge.get("confidence", "")),
                "confidence_score": float(edge.get("confidence_score", 0.0) or 0.0),
                "source_file": str(edge.get("source_file", "")),
                "source_location": str(edge.get("source_location", "") or ""),
            }
        )
        if len(results) >= max(1, min(limit, 200)):
            break
    return results


def get_community(
    query: str,
    limit: int = _DEFAULT_COMMUNITY_LIMIT,
    graph_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return all nodes in the same louvain community as ``query``.

    Result shape::

        {
            "community_id": 5,
            "size": 38,
            "members": [{id, label, file_type, source_file}, ...],
            "node_id": "matched_node_id"
        }

    ``members`` is capped at ``limit`` (most-connected first) so the LLM
    prompt does not blow the context window for very large communities.
    """
    graph = _graph(graph_path)
    if graph is None:
        return {}
    node_id = _find_best_node(graph, query)
    if node_id is None:
        return {}
    community_id = graph.nodes[node_id].get("community")
    if community_id is None:
        return {"community_id": None, "size": 0, "members": [], "node_id": node_id}

    members_raw = [
        nid for nid, data in graph.nodes(data=True)
        if data.get("community") == community_id
    ]
    # Rank by degree desc so the most central members come first.
    members_raw.sort(key=lambda nid: graph.degree(nid), reverse=True)
    members = [
        {
            "id": nid,
            "label": str(graph.nodes[nid].get("label", nid))[:200],
            "file_type": str(graph.nodes[nid].get("file_type", "")),
            "source_file": str(graph.nodes[nid].get("source_file", "")),
            "degree": int(graph.degree(nid)),
        }
        for nid in members_raw[: max(1, min(limit, 500))]
    ]
    return {
        "community_id": int(community_id) if isinstance(community_id, int) else community_id,
        "size": len(members_raw),
        "members": members,
        "node_id": node_id,
    }


def shortest_path(
    source: str,
    target: str,
    graph_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Find the shortest code-level path between two nodes.

    Returns a list of ``{id, label, edge_to_next}`` dicts representing the
    hops. Empty list when either endpoint is missing or no path exists.
    """
    graph = _graph(graph_path)
    if graph is None:
        return []
    src_id = _find_best_node(graph, source)
    tgt_id = _find_best_node(graph, target)
    if src_id is None or tgt_id is None or src_id == tgt_id:
        return []
    try:
        path = nx.shortest_path(graph, src_id, tgt_id)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
    hops: list[dict[str, Any]] = []
    for i, nid in enumerate(path):
        edge_to_next: dict[str, Any] = {}
        if i + 1 < len(path):
            edge = graph.get_edge_data(nid, path[i + 1]) or {}
            edge_to_next = {
                "relation": str(edge.get("relation", "")),
                "confidence": str(edge.get("confidence", "")),
            }
        hops.append(
            {
                "id": nid,
                "label": str(graph.nodes[nid].get("label", nid))[:200],
                "source_file": str(graph.nodes[nid].get("source_file", "")),
                "edge_to_next": edge_to_next,
            }
        )
    return hops


def query_graph(
    question: str,
    depth: int = _DEFAULT_QUERY_DEPTH,
    limit: int = _DEFAULT_QUERY_LIMIT,
    graph_path: Path | str | None = None,
) -> dict[str, Any]:
    """BFS the graph from terms in ``question`` and return a context bundle.

    This is the replacement for the prior ``get_graphify_context``: callers
    receive a structured payload of nodes + edges that the LLM prompt can
    embed directly. The format is intentionally compact (labels, no full
    attributes) to fit in a small context window.
    """
    graph = _graph(graph_path)
    if graph is None:
        return {"start_nodes": [], "nodes": [], "edges": []}
    terms = [t for t in question.split() if len(t) >= 3]
    seeds: list[str] = []
    seen_seeds: set[str] = set()
    for term in terms:
        nid = _find_best_node(graph, term)
        if nid and nid not in seen_seeds:
            seeds.append(nid)
            seen_seeds.add(nid)
        if len(seeds) >= 3:
            break
    if not seeds:
        return {"start_nodes": [], "nodes": [], "edges": []}

    visited: set[str] = set(seeds)
    frontier: set[str] = set(seeds)
    edges: list[dict[str, Any]] = []
    for _ in range(max(1, min(depth, 4))):
        next_frontier: set[str] = set()
        for node in frontier:
            for neighbour in graph.neighbors(node):
                if neighbour in visited:
                    continue
                next_frontier.add(neighbour)
                edge = graph.get_edge_data(node, neighbour) or {}
                edges.append(
                    {
                        "source": node,
                        "target": neighbour,
                        "relation": str(edge.get("relation", "")),
                        "confidence": str(edge.get("confidence", "")),
                    }
                )
                if len(visited) + len(next_frontier) >= max(1, min(limit, 200)):
                    break
            if len(visited) + len(next_frontier) >= max(1, min(limit, 200)):
                break
        visited.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break

    nodes_payload = [
        {
            "id": nid,
            "label": str(graph.nodes[nid].get("label", nid))[:200],
            "file_type": str(graph.nodes[nid].get("file_type", "")),
            "source_file": str(graph.nodes[nid].get("source_file", "")),
            "community": graph.nodes[nid].get("community"),
        }
        for nid in list(visited)[: max(1, min(limit, 200))]
    ]
    return {
        "start_nodes": [
            {"id": s, "label": str(graph.nodes[s].get("label", s))[:200]}
            for s in seeds
        ],
        "nodes": nodes_payload,
        "edges": edges[: max(1, min(limit * 2, 400))],
    }


def god_nodes(
    limit: int = _DEFAULT_GOD_LIMIT,
    graph_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return the most-connected nodes in the graph (architectural risk)."""
    graph = _graph(graph_path)
    if graph is None:
        return []
    ranked = sorted(graph.degree(), key=lambda kv: kv[1], reverse=True)
    return [
        {
            "id": nid,
            "label": str(graph.nodes[nid].get("label", nid))[:200],
            "degree": int(degree),
            "source_file": str(graph.nodes[nid].get("source_file", "")),
            "community": graph.nodes[nid].get("community"),
        }
        for nid, degree in ranked[: max(1, min(limit, 50))]
    ]

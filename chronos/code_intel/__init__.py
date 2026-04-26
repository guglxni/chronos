"""
CHRONOS local code intelligence layer.

Replaces the GitNexus stub (which is browser-only and non-commercial) with
real, FOSS-backed implementations:

- ``local_git``: subprocess wrappers around ``git log``, ``git show``,
  ``git diff`` for commit history and file change attribution.
- ``code_search``: pure-Python codebase scanner with optional ripgrep
  acceleration for finding files referencing a data entity.
- ``sql_parser``: sqlglot-backed SQL table/column extractor with a regex
  fallback when sqlglot is unavailable.
- ``graphify_adapter``: NetworkX-backed loader for graphify-out/graph.json
  exposing live graph queries (community, neighbours, shortest path, god
  nodes) — replaces the prior naive markdown grep.

All modules are designed to fail soft: a missing git repo, missing graph
artifact, or missing optional dependency degrades gracefully to an empty
result rather than crashing the investigation pipeline.
"""

from __future__ import annotations

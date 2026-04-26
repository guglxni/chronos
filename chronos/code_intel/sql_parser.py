"""
SQL entity extractor — finds table and column references in SQL strings.

Used by Step 4 to lift entity references out of ``.sql`` files and inline SQL
embedded in Python (e.g. ``cursor.execute("SELECT ... FROM orders")``).

Implementation strategy:

1. If ``sqlglot`` is installed, parse the SQL with the requested dialect and
   walk the AST. This is dialect-aware and handles aliases, CTEs, and quoted
   identifiers correctly across BigQuery / Snowflake / Postgres / dbt SQL.
2. If ``sqlglot`` is not available, fall back to a tolerant regex that
   captures ``FROM <ident>`` and ``JOIN <ident>`` patterns. The regex is
   intentionally permissive — false positives are filtered by callers via
   the entity match check.

Both modes accept arbitrary text (not just clean SQL) so the same function
can scan inline SQL strings inside Python source.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("chronos.code_intel.sql_parser")

try:
    import sqlglot
    from sqlglot import exp

    _SQLGLOT_AVAILABLE = True
except ImportError:
    sqlglot = None  # type: ignore[assignment]
    exp = None  # type: ignore[assignment]
    _SQLGLOT_AVAILABLE = False

# Regex fallback — matches identifiers after FROM/JOIN/INTO/UPDATE keywords.
# Captures schema-qualified names like ``analytics.orders`` or
# ``"my_db"."public"."orders"``. Intentionally tolerant; downstream code
# normalises and de-duplicates the results.
_TABLE_REGEX = re.compile(
    r"""(?ix)                              # case-insensitive, verbose
    \b(?:from|join|into|update|table)\s+
    (                                    # capture the qualified identifier
        (?:\"[\w.\-]+\"|`[\w.\-]+`|\[[\w.\-]+\]|[\w]+)
        (?:\s*\.\s*
            (?:\"[\w.\-]+\"|`[\w.\-]+`|\[[\w.\-]+\]|[\w]+)
        ){0,3}
    )
    """,
)


def _normalise_identifier(raw: str) -> str:
    """Strip quoting characters and lowercase a SQL identifier path."""
    cleaned_parts: list[str] = []
    for part in re.split(r"\s*\.\s*", raw):
        cleaned = part.strip().strip('"').strip("`").strip("[").strip("]")
        if cleaned:
            cleaned_parts.append(cleaned)
    return ".".join(cleaned_parts).lower()


def _extract_with_sqlglot(sql: str, dialect: str | None) -> list[str]:
    """Walk a sqlglot AST and pull out every Table reference."""
    if not _SQLGLOT_AVAILABLE:
        return []
    tables: set[str] = set()
    try:
        parsed_list = sqlglot.parse(sql, read=dialect or None)  # type: ignore[union-attr,unused-ignore]
    except Exception as parse_err:
        logger.debug("sqlglot parse failed (%s); falling back to regex", parse_err)
        return []
    for parsed in parsed_list:
        if parsed is None:
            continue
        for table in parsed.find_all(exp.Table):  # type: ignore[union-attr,unused-ignore]
            try:
                # Build the qualified name from structured AST attributes
                # (catalog, db, name) instead of table.sql() which includes
                # aliases like "raw.users AS u" and breaks normalisation.
                parts = [
                    p.strip('"').strip("`").lower()
                    for p in [table.catalog, table.db, table.name]
                    if p
                ]
                qualified = ".".join(parts)
            except Exception:
                qualified = getattr(table, "name", "") or ""
            normalised = qualified.strip()
            if normalised:
                tables.add(normalised)
    return sorted(tables)


def _extract_with_regex(sql: str) -> list[str]:
    """Tolerant fallback that captures FROM/JOIN/INTO/UPDATE identifiers."""
    tables: set[str] = set()
    for match in _TABLE_REGEX.finditer(sql):
        normalised = _normalise_identifier(match.group(1))
        if normalised and not normalised.isdigit():
            tables.add(normalised)
    return sorted(tables)


def extract_table_references(
    sql_or_text: str,
    dialect: str | None = None,
) -> list[str]:
    """Return the de-duplicated, lowercased list of table refs in the input.

    Args:
        sql_or_text: Raw SQL or arbitrary text containing inline SQL.
        dialect: Optional sqlglot dialect (``snowflake``, ``bigquery``,
            ``postgres``, ``mysql``, etc.). ``None`` lets sqlglot guess.

    Returns:
        List of qualified identifiers like ``["analytics.orders",
        "raw.users"]``. Empty list when the input is empty or unparseable.
    """
    if not sql_or_text or not isinstance(sql_or_text, str):
        return []
    text = sql_or_text.strip()
    if not text:
        return []
    if _SQLGLOT_AVAILABLE:
        result = _extract_with_sqlglot(text, dialect)
        if result:
            return result
    return _extract_with_regex(text)


def file_references_entity(
    file_text: str,
    entity_name: str,
    dialect: str | None = None,
) -> dict[str, Any]:
    """Return a ``{matched, tables, match_kind}`` summary for one file.

    ``match_kind`` is ``"sql_ast"`` when sqlglot found the entity in a
    structural reference, ``"sql_regex"`` when only the regex fallback hit,
    and ``"text"`` when neither matched but the entity name appears as a
    plain substring (covers Python config files, YAML, etc.).
    """
    target = entity_name.strip().lower()
    if not target:
        return {"matched": False, "tables": [], "match_kind": "none"}
    tables = extract_table_references(file_text, dialect)
    # Match if any extracted identifier ends with the entity name. Handles the
    # common case where the entity FQN includes a service or database prefix
    # that the SQL omits.
    for table in tables:
        if table == target or table.endswith("." + target) or table.split(".")[-1] == target:
            kind = "sql_ast" if _SQLGLOT_AVAILABLE else "sql_regex"
            return {"matched": True, "tables": tables, "match_kind": kind}
    if target in file_text.lower():
        return {"matched": True, "tables": tables, "match_kind": "text"}
    return {"matched": False, "tables": tables, "match_kind": "none"}

"""
Approximate row counts from **catalog statistics only** (no COUNT(*) on heap).

Used to drive ``TableSamplingMetadata.estimated_row_count`` for sampling strategy
without scanning large append-only / audit tables.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text


def _positive_row_estimate(row: Any, idx: int = 0) -> int | None:
    if row is None:
        return None
    v = int(row[idx] or 0)
    return v if v > 0 else None


def _estimate_postgresql(connection: Any, schema: str, table: str) -> int | None:
    row = connection.execute(
        text(
            """
            SELECT COALESCE(c.reltuples::bigint, 0) AS est
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname = :schema
              AND c.relname = :table
            """
        ),
        {"schema": schema, "table": table},
    ).fetchone()
    return _positive_row_estimate(row)


def _estimate_mssql(connection: Any, schema: str, table: str) -> int | None:
    row = connection.execute(
        text(
            """
            SELECT COALESCE(SUM(p.rows), 0) AS est
            FROM sys.partitions AS p
            INNER JOIN sys.tables AS t ON p.object_id = t.object_id
            INNER JOIN sys.schemas AS s ON t.schema_id = s.schema_id
            WHERE s.name = :schema AND t.name = :table
              AND p.index_id IN (0, 1)
            """
        ),
        {"schema": schema, "table": table},
    ).fetchone()
    return _positive_row_estimate(row)


def _estimate_oracle(connection: Any, schema: str, table: str) -> int | None:
    row = connection.execute(
        text(
            """
            SELECT num_rows FROM all_tables
            WHERE owner = :schema AND table_name = :table
            """
        ),
        {"schema": schema.upper(), "table": table.upper()},
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return _positive_row_estimate(row)


def _estimate_mysql(connection: Any, schema: str, table: str) -> int | None:
    row = connection.execute(
        text(
            """
            SELECT COALESCE(table_rows, 0) AS est
            FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
            """
        ),
        {"schema": schema, "table": table},
    ).fetchone()
    return _positive_row_estimate(row)


_ESTIMATORS: dict[str, Callable[[Any, str, str], int | None]] = {
    "postgresql": _estimate_postgresql,
    "postgres": _estimate_postgresql,
    "mssql": _estimate_mssql,
    "microsoft sql server": _estimate_mssql,
    "oracle": _estimate_oracle,
    "mysql": _estimate_mysql,
    "mariadb": _estimate_mysql,
}


def estimate_table_rows(
    connection: Any,
    dialect: str,
    schema: str,
    table: str,
) -> int | None:
    """
    Return an approximate row count from the engine data dictionary, or ``None``.

    Identifiers are bound as parameters (not identifier-quoted inside dynamic SQL
    beyond the fixed catalog queries below).
    """
    tbl = table or ""
    if not tbl:
        return None
    d = (dialect or "").lower()
    est = _ESTIMATORS.get(d)
    if est is None:
        return None
    try:
        return est(connection, schema or "", tbl)
    except Exception:
        return None

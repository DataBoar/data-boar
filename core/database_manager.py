"""
Data discovery helper for SQL-backed targets (SQLAlchemy).

Purpose: provide a small, testable layer for the next iteration where Data Boar
actively samples real tables before detector analysis.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData, Table, asc, create_engine, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class DataDiscoveryEngine:
    """Thin SQLAlchemy wrapper for schema discovery and safe sample fetch."""

    def __init__(self, connection_string: str) -> None:
        """
        Initialize SQLAlchemy engine and inspector.

        Examples
        --------
        - ``sqlite:///lab_database.db``
        - ``postgresql://user:password@localhost/dbname``
        """
        self.engine: Engine = create_engine(connection_string)
        self.session_factory = sessionmaker(bind=self.engine)
        self.inspector = inspect(self.engine)

    def open_session(self) -> Session:
        """Return a bound ORM session (caller closes)."""
        return self.session_factory()

    def get_all_tables(self, *, include_schema: bool = False) -> dict[str, list[str]]:
        """
        Return table->columns map discovered by SQLAlchemy inspector.

        When ``include_schema=True``, keys are ``schema.table`` for non-default schemas.
        """
        schema_map: dict[str, list[str]] = {}
        schema_names = self._schema_names_or_default()
        for schema in schema_names:
            for table_name in self.inspector.get_table_names(schema=schema):
                columns = [
                    str(col["name"])
                    for col in self.inspector.get_columns(table_name, schema=schema)
                    if isinstance(col, dict) and "name" in col
                ]
                key = self._table_key(table_name, schema, include_schema=include_schema)
                schema_map[key] = columns
        return schema_map

    def fetch_sample_data(
        self,
        table_name: str,
        *,
        schema: str | None = None,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Fetch ``limit`` sample rows using SQLAlchemy ``select`` (no string SQL concat).

        Raises
        ------
        ValueError
            If table is not found in inspector metadata.
        """
        safe_limit = max(1, int(limit))
        if safe_limit > 10_000:
            safe_limit = 10_000

        table = self._load_table(table_name, schema=schema)
        stmt = select(table).limit(safe_limit)

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            columns = list(result.keys())
            rows = [dict(r._mapping) for r in result.fetchall()]
        return rows, columns

    def fetch_after_id(
        self,
        table_name: str,
        *,
        last_id: int = 0,
        id_column: str = "id",
        schema: str | None = None,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Fetch rows with ``id_column > last_id`` ordered ascending for checkpoint resume.
        """
        safe_limit = max(1, int(limit))
        if safe_limit > 10_000:
            safe_limit = 10_000

        table = self._load_table(table_name, schema=schema)
        if id_column not in table.c:
            raise ValueError(f"Column not found for checkpointing: {id_column}")

        stmt = (
            select(table)
            .where(table.c[id_column] > int(last_id))
            .order_by(asc(table.c[id_column]))
            .limit(safe_limit)
        )

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            columns = list(result.keys())
            rows = [dict(r._mapping) for r in result.fetchall()]
        return rows, columns

    def _schema_names_or_default(self) -> list[str | None]:
        """Return discoverable schemas, or [None] for engines like SQLite."""
        names = list(self.inspector.get_schema_names() or [])
        if not names:
            return [None]
        default = self.inspector.default_schema_name
        ordered: list[str | None] = []
        if default in names:
            ordered.append(default)
        for name in names:
            if name != default:
                ordered.append(name)
        return ordered or [None]

    @staticmethod
    def _table_key(table_name: str, schema: str | None, *, include_schema: bool) -> str:
        if include_schema and schema:
            return f"{schema}.{table_name}"
        return table_name

    def _load_table(self, table_name: str, *, schema: str | None = None) -> Table:
        if not self.inspector.has_table(table_name, schema=schema):
            target = f"{schema}.{table_name}" if schema else table_name
            raise ValueError(f"Table not found: {target}")
        md = MetaData()
        return Table(table_name, md, autoload_with=self.engine, schema=schema)

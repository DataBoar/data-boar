"""Tests for ``core.database_manager.DataDiscoveryEngine`` using SQLite fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from core.database_manager import DataDiscoveryEngine


def _build_sqlite_fixture(path: Path) -> None:
    eng = create_engine(f"sqlite:///{path}")
    with eng.begin() as conn:
        conn.execute(
            text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        )
        conn.execute(
            text(
                "INSERT INTO users (name, email) VALUES "
                "('Ana', 'ana@example.test'), ('Bruno', 'bruno@example.test')"
            )
        )
    eng.dispose()


def test_get_all_tables_and_columns(tmp_path: Path) -> None:
    db = tmp_path / "lab.db"
    _build_sqlite_fixture(db)
    dd = DataDiscoveryEngine(f"sqlite:///{db}")
    try:
        schema_map = dd.get_all_tables()
        assert "users" in schema_map
        assert schema_map["users"] == ["id", "name", "email"]
    finally:
        dd.engine.dispose()


def test_fetch_sample_data_returns_rows_and_columns(tmp_path: Path) -> None:
    db = tmp_path / "lab.db"
    _build_sqlite_fixture(db)
    dd = DataDiscoveryEngine(f"sqlite:///{db}")
    try:
        rows, cols = dd.fetch_sample_data("users", limit=1)
        assert cols == ["id", "name", "email"]
        assert len(rows) == 1
        assert rows[0]["name"] in {"Ana", "Bruno"}
    finally:
        dd.engine.dispose()


def test_fetch_sample_data_caps_and_missing_table(tmp_path: Path) -> None:
    db = tmp_path / "lab.db"
    _build_sqlite_fixture(db)
    dd = DataDiscoveryEngine(f"sqlite:///{db}")
    try:
        rows, _cols = dd.fetch_sample_data("users", limit=99_999)
        assert len(rows) == 2

        with pytest.raises(ValueError, match="Table not found"):
            dd.fetch_sample_data("missing_table")
    finally:
        dd.engine.dispose()


def test_fetch_after_id_returns_incremental_rows(tmp_path: Path) -> None:
    db = tmp_path / "lab.db"
    _build_sqlite_fixture(db)
    dd = DataDiscoveryEngine(f"sqlite:///{db}")
    try:
        rows, cols = dd.fetch_after_id("users", last_id=1, limit=10)
        assert cols == ["id", "name", "email"]
        assert len(rows) == 1
        assert rows[0]["id"] == 2
    finally:
        dd.engine.dispose()


def test_fetch_after_id_requires_checkpoint_column(tmp_path: Path) -> None:
    db = tmp_path / "lab.db"
    _build_sqlite_fixture(db)
    dd = DataDiscoveryEngine(f"sqlite:///{db}")
    try:
        with pytest.raises(ValueError, match="Column not found for checkpointing"):
            dd.fetch_after_id("users", id_column="missing_id")
    finally:
        dd.engine.dispose()

"""Dictionary-only row estimates (no COUNT(*))."""

from pathlib import Path

from sqlalchemy import create_engine, text

from connectors.sql_table_row_estimate import estimate_table_rows


def test_estimate_table_rows_sqlite_returns_none(tmp_path: Path) -> None:
    db = tmp_path / "e.db"
    eng = create_engine(f"sqlite:///{db}")
    try:
        with eng.connect() as conn:
            conn.execute(text("CREATE TABLE t (id INTEGER)"))
            conn.commit()
        with eng.connect() as conn:
            assert estimate_table_rows(conn, "sqlite", "", "t") is None
    finally:
        eng.dispose()

"""Tests for ``scripts.setup_lab_db`` synthetic database bootstrap."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from scripts.setup_lab_db import create_mock_db


def test_create_mock_db_creates_expected_tables_and_rows(tmp_path: Path) -> None:
    db = tmp_path / "lab.db"
    out = create_mock_db(db)
    assert out == db
    assert db.is_file()

    with closing(sqlite3.connect(str(db))) as conn:
        cur = conn.cursor()
        users_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        cfg_count = cur.execute("SELECT COUNT(*) FROM system_config").fetchone()[0]
        cards_count = cur.execute("SELECT COUNT(*) FROM payment_cards").fetchone()[0]
        cpfs = [
            r[0] for r in cur.execute("SELECT cpf FROM users ORDER BY id").fetchall()
        ]
        cards = cur.execute(
            "SELECT card_number, expected_luhn_valid FROM payment_cards ORDER BY id"
        ).fetchall()

    assert users_count == 2
    assert cfg_count == 1
    assert cards_count == 2
    assert cpfs == ["390.533.447-05", "39053344705"]
    assert cards == [("4111 1111 1111 1111", 1), ("4111 1111 1111 1112", 0)]

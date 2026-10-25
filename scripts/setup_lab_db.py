#!/usr/bin/env python3
"""
Create a synthetic SQLite lab database for discovery smoke tests.

Default output: ``data/lab_completao.db`` (under repository root).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def create_mock_db(db_path: Path) -> Path:
    """
    Build/refresh a small dataset with one table containing synthetic PII-like fields.

    The values are placeholders for scanner validation only (no real identities).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER, nome TEXT, cpf TEXT, email TEXT)"
        )
        cursor.execute("DELETE FROM users")
        cursor.executemany(
            "INSERT INTO users (id, nome, cpf, email) VALUES (?, ?, ?, ?)",
            [
                (1, "User Alpha", "390.533.447-05", "alpha@example.test"),
                (2, "User Beta", "39053344705", "beta@example.test"),
            ],
        )

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS payment_cards ("
            "id INTEGER, owner TEXT, card_number TEXT, expected_luhn_valid INTEGER)"
        )
        cursor.execute("DELETE FROM payment_cards")
        cursor.executemany(
            "INSERT INTO payment_cards (id, owner, card_number, expected_luhn_valid) "
            "VALUES (?, ?, ?, ?)",
            [
                (1, "User Alpha", "4111 1111 1111 1111", 1),
                (2, "User Beta", "4111 1111 1111 1112", 0),
            ],
        )

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS system_config (key TEXT, value TEXT)"
        )
        cursor.execute("DELETE FROM system_config")
        cursor.execute(
            "INSERT INTO system_config (key, value) VALUES (?, ?)",
            ("port", "8080"),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create synthetic SQLite DB for lab discovery scan."
    )
    parser.add_argument(
        "--output",
        default="data/lab_completao.db",
        help="Output SQLite path (default: data/lab_completao.db).",
    )
    args = parser.parse_args(argv)

    out = Path(args.output).expanduser()
    created = create_mock_db(out)
    print(f"[OK] Mock database created: {created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

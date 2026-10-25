"""Legacy: prefer core.database.LocalDBManager and report.generator for new code."""

import sqlite3
from typing import List, Dict


def create_sqlite_report(data: List[Dict]) -> None:
    """Cria banco SQLite com dados levantados."""
    conn = sqlite3.connect("auditoria_dados.sqlite")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dados_sensiveis (
            id INTEGER PRIMARY KEY,
            table TEXT,
            column TEXT,
            data_type TEXT,
            sensitivity TEXT,
            ip TEXT,
            db_name TEXT,
            file_path TEXT
        )
    """)

    for item in data:
        cursor.execute(
            "INSERT INTO dados_sensiveis VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None,
                item.get("table", ""),
                item.get("column", ""),
                item.get("data_type", ""),
                item.get("sensitivity", ""),
                item.get("ip", ""),
                item.get("db_name", ""),
                item.get("file_path", ""),
            ),
        )
    conn.commit()
    conn.close()

"""Legacy: prefer core.engine + connectors.sql_connector for new code."""

from sqlalchemy import inspect
from typing import Any, Dict, List


def scan_database_tables(
    engine: Any, db_name: str, metadata: Dict[str, str] | None = None
) -> List[Dict]:
    """Scan tables and columns. metadata optional (e.g. {'ip': host}) for backward compat."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    results = []
    meta = metadata or {}
    for table in tables:
        try:
            columns = inspector.get_columns(table)
        except Exception:
            columns = []
        results.append(
            {
                "table": table,
                "columns": [
                    {"name": col["name"], "type": str(col["type"])} for col in columns
                ],
                "metadata": {"db": db_name, **meta},
            }
        )
    return results

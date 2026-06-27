"""Optional SQL driver extras — probe before connect (#1047)."""

from __future__ import annotations

import importlib.util

# Engine key (config driver, before '+') -> (extra name, modules that satisfy the driver)
_SQL_DRIVER_EXTRAS: dict[str, tuple[str, tuple[str, ...]]] = {
    "postgresql": ("postgres", ("psycopg2",)),
    "mysql": ("mysql", ("pymysql",)),
    "mariadb": ("mariadb", ("mariadb",)),
    "mssql": ("mssql", ("pyodbc",)),
    "oracle": ("oracle", ("oracledb",)),
}


def required_extra_for_driver(driver: str) -> str | None:
    """Return the optional-extra name for a SQL engine, or None for sqlite / unknown."""
    key = (driver or "postgresql").split("+")[0].lower()
    if key == "sqlite":
        return None
    spec = _SQL_DRIVER_EXTRAS.get(key)
    return spec[0] if spec else None


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def ensure_sql_driver_available(driver: str) -> None:
    """Raise ImportError with an install hint when the driver extra is not installed."""
    key = (driver or "postgresql").split("+")[0].lower()
    if key == "sqlite":
        return
    spec = _SQL_DRIVER_EXTRAS.get(key)
    if not spec:
        return
    extra, modules = spec
    if any(_module_available(name) for name in modules):
        return
    raise ImportError(
        f"SQL connector '{key}' requires optional dependencies. "
        f"Install with: pip install 'data-boar[{extra}]' "
        f'(or: uv pip install -e ".[{extra}]").'
    )

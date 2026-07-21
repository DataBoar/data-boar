"""Optional SQL driver extras — probe before connect (#1047)."""

from __future__ import annotations

import importlib.util

# Engine key (bare config driver) -> (extra name, modules that satisfy the driver)
_SQL_DRIVER_EXTRAS: dict[str, tuple[str, tuple[str, ...]]] = {
    "postgresql": ("postgres", ("psycopg2",)),
    "mysql": ("mysql", ("pymysql",)),
    "mariadb": ("mariadb", ("mariadb",)),
    "mssql": ("mssql-pymssql", ("pymssql",)),
    "oracle": ("oracle", ("oracledb",)),
}

# Explicit dialect+driver strings that differ from the bare-engine default extra.
_EXPLICIT_DRIVER_EXTRAS: dict[str, tuple[str, tuple[str, ...]]] = {
    "mssql+pyodbc": ("mssql", ("pyodbc",)),
    "mssql+pymssql": ("mssql-pymssql", ("pymssql",)),
}


def _driver_spec(driver: str) -> tuple[str, tuple[str, ...]] | None:
    raw = (driver or "postgresql").strip()
    if "+" in raw:
        return _EXPLICIT_DRIVER_EXTRAS.get(raw.lower()) or _SQL_DRIVER_EXTRAS.get(
            raw.split("+", 1)[0].lower()
        )
    return _SQL_DRIVER_EXTRAS.get(raw.lower())


def required_extra_for_driver(driver: str) -> str | None:
    """Return the optional-extra name for a SQL engine, or None for sqlite / unknown."""
    key = (driver or "postgresql").strip().lower()
    if key == "sqlite" or key.startswith("sqlite+"):
        return None
    spec = _driver_spec(driver)
    return spec[0] if spec else None


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def ensure_sql_driver_available(driver: str) -> None:
    """Raise ImportError with an install hint when the driver extra is not installed."""
    raw = (driver or "postgresql").strip()
    key = raw.lower()
    if key == "sqlite" or key.startswith("sqlite+"):
        return
    spec = _driver_spec(driver)
    if not spec:
        return
    extra, modules = spec
    if any(_module_available(name) for name in modules):
        return
    label = raw.split("+", 1)[0].lower() if "+" in raw else key
    raise ImportError(
        f"SQL connector '{label}' requires optional dependencies. "
        f"Install with: pip install 'data-boar[{extra}]' "
        f'(or: uv pip install -e ".[{extra}]").'
    )

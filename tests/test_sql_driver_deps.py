"""SQL optional-extra install hints (#1047)."""

from __future__ import annotations

import pytest

from connectors.sql_driver_deps import (
    ensure_sql_driver_available,
    required_extra_for_driver,
)


def test_required_extra_for_sqlite_is_none() -> None:
    assert required_extra_for_driver("sqlite") is None


def test_required_extra_for_postgresql() -> None:
    assert required_extra_for_driver("postgresql+psycopg2") == "postgres"


def test_required_extra_for_bare_mssql_defaults_to_pymssql_extra() -> None:
    assert required_extra_for_driver("mssql") == "mssql-pymssql"


def test_required_extra_for_explicit_mssql_pyodbc() -> None:
    assert required_extra_for_driver("mssql+pyodbc") == "mssql"


def test_required_extra_for_explicit_mssql_pymssql() -> None:
    assert required_extra_for_driver("mssql+pymssql") == "mssql-pymssql"


def test_ensure_sql_driver_missing_mssql_pymssql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "connectors.sql_driver_deps._module_available",
        lambda _name: False,
    )
    with pytest.raises(ImportError, match=r"data-boar\[mssql-pymssql\]"):
        ensure_sql_driver_available("mssql")


def test_ensure_sql_driver_missing_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "connectors.sql_driver_deps._module_available",
        lambda _name: False,
    )
    with pytest.raises(ImportError, match=r"data-boar\[postgres\]"):
        ensure_sql_driver_available("postgresql")


def test_ensure_sql_driver_sqlite_never_raises() -> None:
    ensure_sql_driver_available("sqlite")

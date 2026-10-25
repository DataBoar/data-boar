"""Guards that the dedicated extras CI job actually imports optional connectors (#1638).

The default matrix job only ``uv sync --extra shares``. Mongo/Redis/archive/SQL
driver tests then skip. When ``DATA_BOAR_CI_EXTRAS=1`` (extras job), those
packages must be importable so ``tests/test_connector_timeouts.py`` Mongo/Redis
cases run instead of skip. The 3.13 extras job omits ``mariadb`` (upstream
1.1.14 ``SyntaxError``).
"""

from __future__ import annotations

import importlib
import os

import pytest

_EXTRAS_JOB = os.environ.get("DATA_BOAR_CI_EXTRAS") == "1"

# Packages installed by the 3.13 extras job (sql-all minus mariadb).
# mariadb 1.1.14 (latest stable) raises SyntaxError on CPython 3.13
# (non-raw docstring in connectionpool.py). Restore ``mariadb`` here when a
# stable connector imports on 3.13 — see PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md.
_REQUIRED_WHEN_EXTRAS_JOB = (
    "pymongo",
    "redis",
    "py7zr",
    "pyarrow",
    "psycopg2",
    "pymysql",
    "pymssql",
    "pyodbc",
    "oracledb",
)


@pytest.mark.skipif(not _EXTRAS_JOB, reason="DATA_BOAR_CI_EXTRAS job only")
def test_extras_job_imports_optional_connector_packages() -> None:
    missing: list[str] = []
    for name in _REQUIRED_WHEN_EXTRAS_JOB:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    assert missing == [], (
        "extras CI job must install these packages so optional tests run: "
        + ", ".join(missing)
    )

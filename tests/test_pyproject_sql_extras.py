"""Guards: SQL C-extension drivers are optional extras, not core (#1047)."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"

_FORBIDDEN_IN_CORE = frozenset(
    {
        "mariadb",
        "mysqlclient",
        "mysql",  # placeholder package on PyPI, not a connector
        "psycopg2-binary",
        "pymysql",
        "pyodbc",
        "oracledb",
    }
)

_EXPECTED_SQL_EXTRAS = frozenset(
    {"postgres", "mysql", "mariadb", "mssql", "oracle", "sql-all"}
)


def _load_pyproject() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


def _core_dependency_names() -> set[str]:
    data = _load_pyproject()
    deps = data.get("project", {}).get("dependencies", [])
    names: set[str] = set()
    for dep in deps:
        if not isinstance(dep, str):
            continue
        name = (
            dep.split("[")[0].strip().split(">")[0].split("<")[0].split("=")[0].strip()
        )
        names.add(name.lower())
    return names


def test_core_dependencies_exclude_sql_c_ext_drivers() -> None:
    core = _core_dependency_names()
    overlap = sorted(core & _FORBIDDEN_IN_CORE)
    assert not overlap, (
        "SQL drivers must be optional extras, not [project].dependencies: "
        + ", ".join(overlap)
    )


def test_sql_optional_extras_present() -> None:
    data = _load_pyproject()
    optional = data.get("project", {}).get("optional-dependencies", {})
    assert isinstance(optional, dict)
    missing = sorted(_EXPECTED_SQL_EXTRAS - set(optional))
    assert not missing, f"missing SQL extras in pyproject.toml: {missing}"


def test_maturity_build_bumped_for_packaging_fix() -> None:
    data = _load_pyproject()
    maturity = data.get("tool", {}).get("databoar", {}).get("maturity_build")
    assert maturity == 202


def test_version_is_174_post_release_not_semver_bump() -> None:
    version = _load_pyproject().get("project", {}).get("version")
    assert version == "1.7.4.post1"
    assert not str(version).startswith("1.7.5")
    assert not str(version).startswith("1.8.")

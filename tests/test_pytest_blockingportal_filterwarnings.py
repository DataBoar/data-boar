"""#1871 Option A: keep ``-W error``; ignore only the starlette/anyio BlockingPortal alias."""

from __future__ import annotations

import warnings
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
CONFTEST = REPO_ROOT / "tests" / "conftest.py"
FILTER = "ignore:The anyio.abc.BlockingPortal alias is deprecated:DeprecationWarning"


def test_pyproject_keeps_werror_and_specific_blockingportal_filter() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    opts = data["tool"]["pytest"]["ini_options"]
    assert opts["addopts"] == "-v -W error"
    filters = opts["filterwarnings"]
    assert isinstance(filters, list)
    joined = "\n".join(filters)
    assert "ignore::DeprecationWarning" not in joined
    assert not any(
        f.endswith(":anyio.abc") or f.endswith(":anyio.abc:") for f in filters
    )
    assert FILTER in filters
    assert FILTER in CONFTEST.read_text(encoding="utf-8")


def test_blockingportal_alias_deprecation_is_filtered() -> None:
    """Must not fail under CI/quick-test ``pytest -v -W error`` once the filter is applied."""
    warnings.warn(
        "The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.",
        DeprecationWarning,
        stacklevel=1,
    )


def test_starlette_testclient_import_does_not_error_under_werror() -> None:
    """Collection of API tests imports this module; must not raise under ``-W error``."""
    import starlette.testclient as starlette_testclient

    assert starlette_testclient.TestClient is not None

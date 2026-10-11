"""#1915: starlette 1.7.0 ships Kludex/starlette#3498; the BlockingPortal ignore is gone."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
CONFTEST = REPO_ROOT / "tests" / "conftest.py"
RETIRED_FILTER = (
    "ignore:The anyio.abc.BlockingPortal alias is deprecated:DeprecationWarning"
)


def test_pyproject_keeps_werror_without_blockingportal_ignore() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    opts = data["tool"]["pytest"]["ini_options"]
    assert opts["addopts"] == "-v -W error"
    filters = opts.get("filterwarnings") or []
    assert isinstance(filters, list)
    joined = "\n".join(filters)
    assert "ignore::DeprecationWarning" not in joined
    assert not any(
        f.endswith(":anyio.abc") or f.endswith(":anyio.abc:") for f in filters
    )
    assert RETIRED_FILTER not in filters
    assert RETIRED_FILTER not in CONFTEST.read_text(encoding="utf-8")


def test_starlette_testclient_import_does_not_error_under_werror() -> None:
    """Collection of API tests imports this module; must not raise under ``-W error``."""
    import starlette.testclient as starlette_testclient

    assert starlette_testclient.TestClient is not None

"""
Pytest configuration: shared fixtures and CLI flags.

**Optional private lint:** Pass ``--include-private`` or set environment variable
``INCLUDE_PRIVATE_LINT=1`` (or ``true`` / ``yes``) to include **gitignored**
``docs/private/`` in markdown lint and optional PowerShell/bash syntax checks under
that tree. Default remains **exclude** so CI and ``check-all`` never depend on local
private notes.
"""

from __future__ import annotations

import os
import subprocess
import warnings

import pytest
from _pytest.config import parse_warning_filter

# Keep in lockstep with [tool.pytest.ini_options].filterwarnings (#1871 / #1915).
# Pytest applies ini filters *before* cmdline ``-W error`` (CI/quick-test pass
# ``-W error`` again), so collection still errors on ``import starlette.testclient``.
# Warm the import once under a filtered catch_warnings in pytest_configure (before
# collection). Re-apply the same ignore during collection and as a per-item mark
# so runtest still wins over ``-W error``. Message only — not ignore::DeprecationWarning.
_BLOCKINGPORTAL_DEPRECATION_FILTER = (
    "ignore:The anyio.abc.BlockingPortal alias is deprecated:DeprecationWarning"
)


def _ignore_blockingportal_alias() -> None:
    warnings.filterwarnings(
        *parse_warning_filter(_BLOCKINGPORTAL_DEPRECATION_FILTER, escape=False)
    )


def pytest_configure(config: pytest.Config) -> None:
    del config
    with warnings.catch_warnings():
        _ignore_blockingportal_alias()
        import starlette.testclient as _starlette_testclient  # noqa: F401


@pytest.hookimpl(wrapper=True)
def pytest_collection(session: pytest.Session):
    del session
    _ignore_blockingportal_alias()
    return (yield)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    mark = pytest.mark.filterwarnings(_BLOCKINGPORTAL_DEPRECATION_FILTER)
    for item in items:
        item.add_marker(mark)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--include-private",
        action="store_true",
        default=False,
        help=(
            "Include docs/private/ in markdown lint and optional script syntax checks "
            "(gitignored; default: skip)."
        ),
    )


@pytest.fixture(scope="session")
def include_private_lint(request: pytest.FixtureRequest) -> bool:
    """True if private trees should be linted (CLI flag or INCLUDE_PRIVATE_LINT env)."""
    env = os.environ.get("INCLUDE_PRIVATE_LINT", "").strip().lower()
    if env in ("1", "true", "yes"):
        return True
    return bool(request.config.getoption("--include-private"))


@pytest.fixture(scope="session")
def warm_pwsh() -> None:
    """#860: absorb the pwsh cold-start cost ONCE before ParseFile loops.

    The first pwsh invocation after boot can take >30s under load (assembly /
    JIT cache cold on Linux), which made the per-file 30s ParseFile timeout
    flake in ``test_maestro_scripts.py``. Warming the shell once per session
    (generous 120s budget) makes subsequent per-file parses fast (~0.2s).
    Missing shells are fine — parse tests skip/fall through on their own.
    """
    for pw in ("pwsh", "powershell"):
        try:
            subprocess.run(
                [pw, "-NoProfile", "-NonInteractive", "-Command", "exit 0"],
                capture_output=True,
                timeout=120,
                check=False,
            )
            return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

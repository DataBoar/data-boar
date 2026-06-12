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

import pytest


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

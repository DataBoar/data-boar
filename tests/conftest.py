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


# Stand-in operator list so existing *_from_env fixtures keep their YAML asserts.
_FIXTURE_OPERATOR_HOSTS = ",".join(
    (
        "127.0.0.1",
        "api.example.com",
        "api.good.example",
        "api.hubapi.com",
        "api.trusted.example",
        "attacker.example",
        "auth.example.com",
        "db.example",
        "db.example.com",
        "dav.example",
        "db.trusted.example",
        "evil.example.com",
        "example.com",
        "files.example",
        "files.example.com",
        "localhost",
        "login.microsoftonline.com",
        "mongo.example",
        "nas.example",
        "nfs.example.com",
        "org.crm.dynamics.com",
        "other.example",
        "192.0.2.10",
        "REPLACE_WITH_LAB_HOST_IP",
        "redis.example",
        "sharepoint.example",
        "sql.example.com",
        "xy12345.us-east-1",
        "xy12345.us-east-1.snowflakecomputing.com",
    )
)


@pytest.fixture(autouse=True)
def _operator_credential_host_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give existing env-credential fixtures an operator host list (#2103)."""
    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", _FIXTURE_OPERATOR_HOSTS)


@pytest.fixture(autouse=True)
def _restore_license_verify_key_loader():
    """Drop any test pin of the embedded verify key after the test."""
    yield
    from tests.license_verify_pin import restore_embedded_ed25519_loader

    restore_embedded_ed25519_loader()


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

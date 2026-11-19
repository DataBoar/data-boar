"""Anti-drift checks for Bash completion inventory (#1952, aligns with #1448)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import tomllib

from cli.bash_completion_inventory import (
    COMMAND_COMPLETION_INVENTORY,
    PUBLISHED_CONSOLE_SCRIPTS,
    choice_flags_from_help_text,
    long_options_from_help_text,
    short_options_from_help_text,
)


def test_long_options_from_help_ignores_prose_references() -> None:
    """Help prose cites other flags with punctuation; only synopsis flags count."""
    help_text = (
        "usage: data-boar [--export-dsar SESSION_ID]\n"
        "  --dsar-output PATH    Write DSAR. Requires --export-dsar.\n"
        "  --export-sarif SESSION_ID\n"
        "  --sarif-output PATH   Write SARIF. Requires --export-sarif.\n"
    )
    assert long_options_from_help_text(help_text) == frozenset(
        {
            "--dsar-output",
            "--export-dsar",
            "--export-sarif",
            "--sarif-output",
        }
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("--export-dsar", "--export-dsar"),
        ("--l3-max-rows", "--l3-max-rows"),
        ("--a0", "--a0"),
        ("--export-dsar.", "--export-dsar"),
        ("--export-", None),
        ("--export--dsar", None),
        ("---x", None),
        ("--0abc", None),
        ("--Abc", None),
        ("--", None),
        ("-x", None),
    ],
)
def test_parse_long_option_token_accepts_only_real_flags(
    raw: str, expected: str | None
) -> None:
    """Same accepted language after the ReDoS rewrite (CodeQL py/redos)."""
    from cli.bash_completion_inventory import _parse_long_option_token

    assert _parse_long_option_token(raw) == expected


def test_parse_long_option_token_is_linear_on_pathological_input() -> None:
    """No catastrophic backtracking: the CodeQL py/redos shapes finish at once.

    ``--a`` + many ``0`` and ``--a-`` + many ``00-`` followed by a char that
    forces the match to fail used to be exponential with nested quantifiers.
    """
    import time

    from cli.bash_completion_inventory import _parse_long_option_token

    for raw in ("--a" + "0" * 50_000 + "!", "--a-" + "00-" * 20_000 + "!"):
        start = time.perf_counter()
        assert _parse_long_option_token(raw) is None
        assert time.perf_counter() - start < 1.0


def test_long_options_from_help_rejects_wrapped_usage_fragments() -> None:
    """Argparse may hard-wrap usage; partial ``--export-`` is not a flag."""
    help_text = (
        "usage: data-boar [--export-\n                 audit-trail [PATH]]\n  --web\n"
    )
    opts = long_options_from_help_text(help_text)
    assert "--export-" not in opts
    assert "--web" in opts


REPO_ROOT = Path(__file__).resolve().parents[1]
BASH_COMPLETION_SCRIPT = REPO_ROOT / "scripts" / "bash-completion" / "data-boar.bash"


def _help_text(command: str) -> str:
    proc = subprocess.run(
        ["uv", "run", command, "--help"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


@pytest.mark.parametrize("command", PUBLISHED_CONSOLE_SCRIPTS)
def test_inventory_matches_live_help(command: str) -> None:
    inventory = COMMAND_COMPLETION_INVENTORY[command]
    help_text = _help_text(command)
    assert long_options_from_help_text(help_text) == inventory.long_options
    assert short_options_from_help_text(help_text) == inventory.short_options
    assert choice_flags_from_help_text(help_text) == dict(inventory.choice_flags)


def test_pyproject_console_scripts_match_inventory() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = tuple(sorted(data["project"]["scripts"]))
    assert scripts == tuple(sorted(PUBLISHED_CONSOLE_SCRIPTS))


def test_bash_completion_script_documents_inventory_flags() -> None:
    text = BASH_COMPLETION_SCRIPT.read_text(encoding="utf-8")
    for command, inventory in COMMAND_COMPLETION_INVENTORY.items():
        for opt in inventory.long_options:
            if opt == "--help":
                continue
            assert opt in text, f"{opt} for {command} missing from data-boar.bash"
        for short in inventory.short_options:
            assert short in text, f"{short} for {command} missing from data-boar.bash"
        for flag, choices in inventory.choice_flags.items():
            for value in choices:
                assert value in text, (
                    f"choice {value} for {flag} ({command}) missing from data-boar.bash"
                )

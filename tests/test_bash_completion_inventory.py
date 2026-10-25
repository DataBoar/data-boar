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

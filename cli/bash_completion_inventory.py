"""Inventory for published CLI Bash completion (#1952, anti-drift with #1448).

The tuples below are the contract checked by ``tests/test_bash_completion_inventory.py``
against live ``--help`` output. Update this module when argparse or console scripts change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

PUBLISHED_CONSOLE_SCRIPTS: tuple[str, ...] = (
    "data-boar",
    "data-boar-report",
    "data-boar-xlsx",
    "data-boar-pdf",
    "data-boar-docx",
    "data-boar-heatmap",
    "data-boar-dsar",
    "data-boar-audit",
)

_REPORT_FORMAT_CHOICES: frozenset[str] = frozenset(
    {
        "all",
        "audit-trail",
        "docx",
        "dsar",
        "heatmap",
        "json",
        "md",
        "pdf",
        "xlsx",
    }
)

_REPORT_LONG_OPTIONS: frozenset[str] = frozenset(
    {
        "--config",
        "--debug-traceback",
        "--dsar-include-samples",
        "--format",
        "--help",
        "--output",
        "--output-dir",
        "--session-id",
        "--sqlite",
        "--trial-rows-capped",
    }
)

_DATA_BOAR_LONG_OPTIONS: frozenset[str] = frozenset(
    {
        "--allow-insecure-http",
        "--allow-sample-export",
        "--check-extras",
        "--config",
        "--confirm-upgrade-to",
        "--content-type-check",
        "--demo",
        "--diff",
        "--dsar-include-samples",
        "--dsar-output",
        "--export-audit-trail",
        "--export-dsar",
        "--export-findings-sink",
        "--export-l1",
        "--export-l3",
        "--export-remediation-manifest",
        "--fail-on-new-high",
        "--governance-report",
        "--help",
        "--host",
        "--https-cert-file",
        "--https-key-file",
        "--jurisdiction-hint",
        "--l1-output",
        "--l3-allow-unprotected",
        "--l3-column",
        "--l3-grant",
        "--l3-max-rows",
        "--l3-persist",
        "--no-progress",
        "--plan",
        "--port",
        "--prefilter-status",
        "--progress",
        "--reconcile-integrity-anchor",
        "--regenerate-report",
        "--reset-data",
        "--resume",
        "--scan-compressed",
        "--scan-stego",
        "--session",
        "--technician",
        "--tenant",
        "--validate-config",
        "--validate-crypto",
        "--version",
        "--web",
    }
)


@dataclass(frozen=True)
class CommandCompletionInventory:
    """Known flags and enumerated values for one console script."""

    long_options: frozenset[str]
    short_options: frozenset[str]
    choice_flags: Mapping[str, frozenset[str]]


def _report_inventory() -> CommandCompletionInventory:
    return CommandCompletionInventory(
        long_options=_REPORT_LONG_OPTIONS,
        short_options=frozenset({"-h", "-o"}),
        choice_flags={"--format": _REPORT_FORMAT_CHOICES},
    )


COMMAND_COMPLETION_INVENTORY: dict[str, CommandCompletionInventory] = {
    "data-boar": CommandCompletionInventory(
        long_options=_DATA_BOAR_LONG_OPTIONS,
        short_options=frozenset({"-h"}),
        choice_flags={},
    ),
    "data-boar-report": _report_inventory(),
    "data-boar-xlsx": _report_inventory(),
    "data-boar-pdf": _report_inventory(),
    "data-boar-docx": _report_inventory(),
    "data-boar-heatmap": _report_inventory(),
    "data-boar-dsar": _report_inventory(),
    "data-boar-audit": _report_inventory(),
}


def long_options_from_help_text(help_text: str) -> frozenset[str]:
    """Parse documented long options from argparse ``--help`` text."""
    opts: set[str] = set()
    for line in help_text.splitlines():
        if line.startswith("usage:"):
            for match in re.finditer(r"(--[a-z][a-z0-9-]+)", line):
                opts.add(match.group(1))
        elif line.startswith("  -"):
            for token in line.split():
                if token.startswith("--"):
                    opts.add(token.rstrip(",:"))
    return frozenset(opts)


def short_options_from_help_text(help_text: str) -> frozenset[str]:
    """Parse documented short options from argparse ``--help`` text."""
    opts: set[str] = set()
    for line in help_text.splitlines():
        if not line.startswith("  -"):
            continue
        for token in line.split():
            if re.fullmatch(r"-[a-zA-Z]", token.rstrip(",")):
                opts.add(token.rstrip(","))
    usage = help_text.splitlines()[0] if help_text else ""
    for match in re.finditer(r"(?<![\w-])(-[a-zA-Z])(?![\w-])", usage):
        opts.add(match.group(1))
    return frozenset(opts)


def choice_flags_from_help_text(help_text: str) -> dict[str, frozenset[str]]:
    """Parse ``--flag {a,b,c}`` choice lists from help."""
    choices: dict[str, frozenset[str]] = {}
    for match in re.finditer(r"(--[a-z][a-z0-9-]*)\s+\{([^}]+)\}", help_text):
        flag = match.group(1)
        values = frozenset(part.strip() for part in match.group(2).split(","))
        choices[flag] = values
    return choices

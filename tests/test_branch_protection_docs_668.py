"""#668 — branch-protection runbook plus CONTRIBUTING PR requirements."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_RUNBOOK = _REPO / "docs" / "ops" / "BRANCH_PROTECTION.md"
_CONTRIBUTING = _REPO / "CONTRIBUTING.md"
_FOLLOWUPS = _REPO / "docs" / "ops" / "WORKFLOW_DEFERRED_FOLLOWUPS.md"

_RUNBOOK_MARKERS = (
    "## Classic rules vs rulesets",
    "## Required status checks on `main`",
    "## `ZIZMOR_ENFORCE`",
    "## Heat model (cold → warm → hot)",
    "Test (Python 3.12)",
    "Test (Python 3.13)",
    "Test (Python 3.14)",
)

_FOLLOWUP_MARKERS = (
    "BRANCH_PROTECTION.md",
    "#668",
)


def test_branch_protection_runbook_and_contributing_section() -> None:
    runbook = _RUNBOOK.read_text(encoding="utf-8")
    for marker in _RUNBOOK_MARKERS:
        assert marker in runbook, f"missing runbook marker {marker!r}"

    contributing = _CONTRIBUTING.read_text(encoding="utf-8").splitlines()
    heading = "## Pull Request requirements"
    assert any(line.rstrip() == heading for line in contributing), (
        f"missing {heading!r}"
    )
    assert "docs/ops/BRANCH_PROTECTION.md" in "\n".join(contributing)

    followups = _FOLLOWUPS.read_text(encoding="utf-8")
    for marker in _FOLLOWUP_MARKERS:
        assert marker in followups, f"missing follow-up marker {marker!r}"

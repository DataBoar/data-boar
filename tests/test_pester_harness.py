"""Structural guards for Pester harness (#984)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PESTER_REQUIRED_VERSION = "5.6.1"


def test_run_pester_script_pins_version() -> None:
    text = (REPO_ROOT / "scripts" / "run-pester.ps1").read_text(encoding="utf-8")
    assert f"$PesterRequiredVersion = '{PESTER_REQUIRED_VERSION}'" in text
    assert "Install-Module" in text
    assert "tests/pester" in text


def test_check_all_invokes_pester() -> None:
    ps1 = (REPO_ROOT / "scripts" / "check-all.ps1").read_text(encoding="utf-8")
    sh = (REPO_ROOT / "scripts" / "check-all.sh").read_text(encoding="utf-8")
    assert "run-pester.ps1" in ps1
    assert "run-pester.ps1" in sh
    gate = ps1.index("gatekeeper-audit.ps1")
    pester = ps1.index("run-pester.ps1")
    pre = ps1.index("pre-commit-and-tests.ps1")
    assert gate < pester < pre


def test_pester_tranche1_files_exist() -> None:
    root = REPO_ROOT / "tests" / "pester"
    expected = (
        "_RepoRoot.ps1",
        "Audit.Tests.ps1",
        "CheckAll.Tests.ps1",
        "InvAdr.Tests.ps1",
        "Wrappers.Tranche1.Tests.ps1",
    )
    for name in expected:
        assert (root / name).is_file(), f"missing Pester file: {name}"


def test_pester_tests_avoid_bare_scripts_activate_docs() -> None:
    """Pester suite must not teach invalid pwsh activate paths."""
    root = REPO_ROOT / "tests" / "pester"
    bad = re.compile(r"Scripts\\activate(?!\.ps1)", re.I)
    for path in root.glob("*.Tests.ps1"):
        text = path.read_text(encoding="utf-8")
        assert not bad.search(text), f"invalid activate path in {path.name}"

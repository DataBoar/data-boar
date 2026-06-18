"""Tests for the self-protecting gate tripwire (issue #944, ADR-0071).

The tripwire fails LOUD when a PR modifies a gate file without an operator marker,
so the gate that audits a PR can no longer be silently weakened inside that PR.
"""

from __future__ import annotations

import scripts.gate_change_tripwire as t

MARKER = "fix\n\nGate-Change-Approved-By: @FabioLeitao\n"


def test_gate_change_without_marker_blocks() -> None:
    code, touched = t.evaluate(["scripts/gatekeeper_audit.py"], "just a fix")
    assert code == 1
    assert "scripts/gatekeeper_audit.py" in touched


def test_gate_change_with_marker_passes() -> None:
    code, touched = t.evaluate(["scripts/gatekeeper_audit.py"], MARKER)
    assert code == 0
    assert touched == ["scripts/gatekeeper_audit.py"]


def test_seed_template_is_a_gate_file() -> None:
    code, _ = t.evaluate(
        ["docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt"],
        "no marker",
    )
    assert code == 1


def test_non_gate_change_passes() -> None:
    code, touched = t.evaluate(["README.md", "core/detector.py"], "feature work")
    assert code == 0
    assert touched == []


def test_marker_detection_is_case_insensitive_and_handle_optional() -> None:
    assert t.marker_present("gate-change-approved-by: FabioLeitao")
    assert t.marker_present("Gate-Change-Approved-By: @FabioLeitao")
    assert not t.marker_present("no approval trailer here")


def test_gate_files_set_covers_core_surfaces() -> None:
    for path in (
        "scripts/gatekeeper_audit.py",
        "scripts/gatekeeper-audit.ps1",
        "scripts/pii_history_guard.py",
        ".github/CODEOWNERS",
        ".pre-commit-config.yaml",
        "security/pii_gate_allowlist.txt",
    ):
        assert path in t.GATE_FILES


def test_windows_path_separator_normalized() -> None:
    code, touched = t.evaluate(["scripts\\gatekeeper_audit.py"], "no marker")
    assert code == 1
    assert touched == ["scripts/gatekeeper_audit.py"]

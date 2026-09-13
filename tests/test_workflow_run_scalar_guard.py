"""#1918: generic guard — folded YAML ``run:`` plus shell ``\\`` (#1904 / #1906)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import scripts.workflow_run_scalar_guard as g

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures" / "workflow_run_scalar"
GUARD = REPO / "scripts" / "workflow_run_scalar_guard.py"


def test_folded_backslash_fixture_fails() -> None:
    path = FIXTURES / "folded_backslash.yml"
    findings = g.iter_folded_run_findings(path.read_text(encoding="utf-8"), path)
    assert len(findings) == 1
    assert findings[0].line == 8
    assert "folded YAML" in findings[0].message


def test_literal_backslash_fixture_passes() -> None:
    path = FIXTURES / "literal_backslash.yml"
    findings = g.iter_folded_run_findings(path.read_text(encoding="utf-8"), path)
    assert findings == []


def test_folded_without_backslash_passes() -> None:
    path = FIXTURES / "folded_no_backslash.yml"
    findings = g.iter_folded_run_findings(path.read_text(encoding="utf-8"), path)
    assert findings == []


def test_defaults_run_mapping_is_not_a_shell_scalar() -> None:
    path = FIXTURES / "defaults_run_mapping.yml"
    findings = g.iter_folded_run_findings(path.read_text(encoding="utf-8"), path)
    assert findings == []


def test_scan_fixture_dir_cli_fails_on_broken_yaml() -> None:
    proc = subprocess.run(
        [sys.executable, str(GUARD), "--workflows-dir", str(FIXTURES)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "folded_backslash.yml" in proc.stderr
    assert "literal_backslash.yml" not in proc.stderr


def test_repo_workflows_pass_the_guard() -> None:
    findings = g.scan_workflows_dir(REPO / ".github" / "workflows")
    assert findings == [], "\n".join(f.format() for f in findings)


def test_pre_commit_and_check_all_wire_the_guard() -> None:
    pre = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "id: workflow-run-scalar-guard" in pre
    assert "scripts/workflow_run_scalar_guard.py" in pre
    sh = (REPO / "scripts" / "check-all.sh").read_text(encoding="utf-8")
    ps1 = (REPO / "scripts" / "check-all.ps1").read_text(encoding="utf-8")
    for text in (sh, ps1):
        assert "workflow_run_scalar_guard.py" in text
        assert "ABORTED by workflow_run_scalar_guard" in text
    assert 'uv run python "$REPO_ROOT/scripts/workflow_run_scalar_guard.py" || {' in sh
    assert "workflow_run_scalar_guard.py || true" not in sh

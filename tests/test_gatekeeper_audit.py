"""Smoke tests for scripts/gatekeeper_audit.py — parity knobs from gatekeeper-audit.ps1.

Real seed literals stay out of tracked tests; callers use tempfile paths only."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_GATE_SCRIPT = REPO_ROOT / "scripts" / "gatekeeper_audit.py"


def _run_script(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_GATE_SCRIPT), *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def _load_gatekeeper_audit_module():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(
        "_gatekeeper_audit_under_test", _GATE_SCRIPT
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_require_seeds_missing_file_exits_one(tmp_path: Path) -> None:
    missing = tmp_path / "PII_LOCAL_SEEDS.txt"
    proc = _run_script(["--require-seeds", "--seeds-path", str(missing)])
    assert proc.returncode == 1
    assert "missing" in proc.stderr.lower()


def test_comment_only_seeds_file_exits_zero(tmp_path: Path) -> None:
    seeds = tmp_path / "only_comments.txt"
    seeds.write_text("# header only\n\n  # spaced\n", encoding="utf-8")
    proc = _run_script(["--require-seeds", "--seeds-path", str(seeds)])
    assert proc.returncode == 0
    assert "no active seed lines" in proc.stderr.lower()


def test_public_identity_seed_excluded_contract() -> None:
    m = _load_gatekeeper_audit_module()
    assert m.public_identity_seed_excluded("fabioleitao") is True
    assert m.public_identity_seed_excluded("c:/users/fabio") is True
    assert m.public_identity_seed_excluded("/home/leitao/") is True
    assert m.public_identity_seed_excluded("GENERIC_PLACEHOLDER_TOKEN_XYZ") is False

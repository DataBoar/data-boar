"""Gitleaks kombi — ``gitleaks detect --config .gitleaks.toml`` parity (PLAN_NO_COAUTHORSHIP_GATE).

Defense-in-depth with ``tests/test_commit_no_tool_coauthorship.py`` (commit messages).
regression-anchor: aiidcobpp-v1.4-gitleaks-detect-config
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".gitleaks.toml"


def test_gitleaks_toml_extend_and_no_coauthorship_rule() -> None:
    """Repo config must extend defaults and declare the no-coauthorship governance rule."""
    assert CONFIG.is_file(), f"missing {CONFIG}"
    text = CONFIG.read_text(encoding="utf-8")
    assert "useDefault = true" in text
    assert "no-coauthorship-at-all" in text


@pytest.mark.skipif(shutil.which("gitleaks") is None, reason="gitleaks CLI not on PATH")
def test_gitleaks_detect_uses_repo_config() -> None:
    """Run ``gitleaks detect --config .gitleaks.toml`` from repo root (kombi contract)."""
    proc = subprocess.run(
        ["gitleaks", "detect", "--config", ".gitleaks.toml"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        "gitleaks detect --config .gitleaks.toml failed\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )

"""Regression: destructive history rewrite script must stay opt-in (primary Windows dev PC policy)."""

from pathlib import Path


def test_run_pii_history_rewrite_requires_opt_in_env():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "run-pii-history-rewrite.ps1"
    text = script.read_text(encoding="utf-8")
    assert "DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS" in text
    assert "PRIMARY_WINDOWS_WORKSTATION_PROTECTION" in text

"""PS1 vs bash pairing audit — report gaps, never invent empty .sh twins."""

from scripts.check_cross_platform_gaps import classify, missing_twins


def test_classify_returns_top_level_ps1():
    rows = classify()
    names = {r["ps1"] for r in rows}
    assert "check-all.ps1" in names
    check_all = next(r for r in rows if r["ps1"] == "check-all.ps1")
    assert check_all["has_sh"] == "yes"
    assert check_all["priority"] == "—"


def test_missing_twins_do_not_include_paired_gates():
    gaps = {r["ps1"] for r in missing_twins(classify())}
    assert "check-all.ps1" not in gaps
    assert "lint-only.ps1" not in gaps
    assert "check-cross-platform-gaps.ps1" not in gaps


def test_shorthands_hub_points_to_auditor_not_filename_dump():
    from pathlib import Path

    hub = Path("docs/hubs/SHORTHANDS_HUB.md").read_text(encoding="utf-8")
    assert "check_cross_platform_gaps.py" in hub
    assert "PII seeds" in hub
    assert "| Script PS1 |" not in hub

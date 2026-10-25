"""Tests for optional heuristic jurisdiction hints (Report info only)."""

from report.jurisdiction_hints import (
    build_jurisdiction_hint_report_rows,
    jurisdiction_hints_effective,
    jurisdiction_hints_enabled,
)


def test_jurisdiction_hints_disabled_by_default():
    assert jurisdiction_hints_enabled({}) is False
    assert jurisdiction_hints_enabled({"report": {}}) is False
    assert (
        jurisdiction_hints_enabled(
            {"report": {"jurisdiction_hints": {"enabled": False}}}
        )
        is False
    )


def test_jurisdiction_hints_enabled_from_config():
    cfg = {"report": {"jurisdiction_hints": {"enabled": True}}}
    assert jurisdiction_hints_enabled(cfg) is True


def test_jurisdiction_hints_effective_from_session_meta():
    cfg = {"report": {"jurisdiction_hints": {"enabled": False}}}
    assert jurisdiction_hints_effective(cfg, {"jurisdiction_hint": True}) is True


def test_build_rows_empty_when_not_effective():
    rows = build_jurisdiction_hint_report_rows(
        [{"column_name": "x", "pattern_detected": "CCPA"}],
        [],
        {"report": {"jurisdiction_hints": {"enabled": False}}},
        {"jurisdiction_hint": False},
    )
    assert rows == []


def test_build_rows_us_ca_when_ccpa_in_metadata():
    cfg = {"report": {"jurisdiction_hints": {"enabled": True, "us_ca": True}}}
    db_rows = [
        {
            "column_name": "notice_ccpa",
            "pattern_detected": "FOO",
            "norm_tag": "CCPA",
        }
    ]
    rows = build_jurisdiction_hint_report_rows(db_rows, [], cfg, None)
    fields = [r["Field"] for r in rows]
    assert any("US-CA" in f for f in fields)
    assert any("CCPA / CPRA" in r["Value"] for r in rows)


def test_build_rows_colorado():
    cfg = {"report": {"jurisdiction_hints": {"enabled": True, "min_score_us_co": 1}}}
    # Token "Denver" as a word (word boundaries; underscores would break \\bDENVER\\b).
    db_rows = [{"column_name": "Denver metro office", "table_name": "t"}]
    rows = build_jurisdiction_hint_report_rows(db_rows, [], cfg, None)
    assert any("US-CO" in r["Field"] for r in rows)


def test_build_rows_japan_appi():
    cfg = {"report": {"jurisdiction_hints": {"enabled": True}}}
    db_rows = [{"column_name": "APPI_export_flag", "pattern_detected": "X"}]
    rows = build_jurisdiction_hint_report_rows(db_rows, [], cfg, None)
    assert any("JP" in r["Field"] for r in rows)
    assert any("Japan APPI" in r["Value"] for r in rows)

"""#1765: Report info Advisory is loud and never blocks report generation."""

from __future__ import annotations

from report.generator import _build_report_info

_META = {
    "started_at": "",
    "tenant_name": "",
    "technician_name": "",
    "config_scope_hash": "",
}

_PENDING = "sev=critical · 1.7.4 → 1.7.6 · fix disponível · visto em 2026-08-26T14:02Z"


def _about(**overrides: object) -> dict:
    about = {
        "name": "Data Boar",
        "version": "1.8.0-beta",
        "author": "Fabio Leitao",
        "license": "BSD 3-Clause License",
        "copyright": "Copyright (c) 2025-2026, Fabio Leitao",
        "build_trust": "expected",
        "integrity_state": "validated",
    }
    about.update(overrides)
    return about


def _rows(about: dict) -> list[dict]:
    return _build_report_info(
        session_id="s-advisory",
        meta=_META,
        about=about,
        db_rows=[],
        fs_rows=[],
        license_ctx=None,
        config={},
    )


def test_report_info_advisory_loud_when_severity_pending() -> None:
    fields = {r["Field"]: r["Value"] for r in _rows(_about(advisory=_PENDING))}
    assert fields["Advisory"] == _PENDING


def test_report_info_advisory_unknown_when_absent_still_builds() -> None:
    """Missing advisory must not refuse the report; default matches Integrity state."""
    about = _about()
    assert "advisory" not in about
    rows = _rows(about)
    fields = {r["Field"]: r["Value"] for r in rows}
    assert fields["Advisory"] == "unknown"
    assert fields["Application"] == "Data Boar"
    assert fields["Integrity state"] == "validated"


def test_generate_report_succeeds_without_pending_severity(
    tmp_path, monkeypatch
) -> None:
    from pathlib import Path

    import pandas as pd

    from report.generator import generate_report

    class _Mgr:
        def get_findings(self, _sid):
            db = [
                {
                    "target_name": "t1",
                    "table_name": "tbl",
                    "column_name": "cpf",
                    "pattern_detected": "LGPD_CPF",
                    "sensitivity_level": "HIGH",
                    "sample_value": "***",
                }
            ]
            return db, [], [], []

        def save_aggregated_identification_risks(self, *_a, **_k):
            return None

        def get_aggregated_identification_risks(self, _sid):
            return []

        def list_sessions(self):
            return [
                {
                    "session_id": "sess-advisory-none",
                    "started_at": "2026-01-01T00:00:00",
                    "tenant_name": "lab",
                    "technician_name": "op",
                }
            ]

    monkeypatch.setattr(
        "report.generator._create_heatmap",
        lambda *_a, **_k: None,
    )
    path = generate_report(
        _Mgr(), "sess-advisory-none", output_dir=str(tmp_path), config={}
    )
    assert path
    assert Path(path).is_file()
    info = pd.read_excel(path, sheet_name="Report info")
    advisory = info.loc[info["Field"] == "Advisory", "Value"]
    assert not advisory.empty
    assert str(advisory.iloc[0]) == "unknown"


def test_format_release_advisory_none_vs_unknown() -> None:
    from core.about import format_release_advisory, get_about_info

    assert format_release_advisory(None) == "unknown"
    assert format_release_advisory({}) == "none"
    payload = {
        "sev": "critical",
        "current": "1.7.4",
        "target": "1.7.6",
        "seen_at": "2026-08-26T14:02Z",
    }
    assert format_release_advisory(payload) == _PENDING
    assert get_about_info()["advisory"] == "unknown"

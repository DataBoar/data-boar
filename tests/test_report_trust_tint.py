"""S2a wave-2c: Excel trust tint policy (watermark + untrusted stubs)."""

from __future__ import annotations

import report.trust_tint as tt


def test_resolve_trusted_no_watermark(monkeypatch):
    monkeypatch.setattr(
        "core.canonical_trust.get_canonical_trust_snapshot",
        lambda _cfg: {
            "trust_state": "trusted",
            "trust_reasons": [],
            "output_confidence": "full",
        },
    )
    tint = tt.resolve_excel_trust_tint({})
    assert tint["show_watermark"] is False
    assert tint["detail_sheets_stub"] is False
    assert tt.trust_tint_report_info_rows(tint) == []


def test_resolve_degraded_watermark_keeps_detail_sheets(monkeypatch):
    monkeypatch.setattr(
        "core.canonical_trust.get_canonical_trust_snapshot",
        lambda _cfg: {
            "trust_state": "degraded",
            "trust_reasons": ["plaintext_http_explicit"],
            "output_confidence": "reduced",
        },
    )
    tint = tt.resolve_excel_trust_tint({})
    assert tint["show_watermark"] is True
    assert tint["detail_sheets_stub"] is False
    rows = tt.trust_tint_report_info_rows(tint)
    fields = [r["Field"] for r in rows]
    assert fields[0] == "TRUST WATERMARK"
    assert "Trust state" in fields
    assert "Output confidence" in fields
    assert "REDUCED CONFIDENCE" in rows[0]["Value"]
    assert "plaintext_http_explicit" in rows[2]["Value"]


def test_resolve_untrusted_stub_policy(monkeypatch):
    monkeypatch.setattr(
        "core.canonical_trust.get_canonical_trust_snapshot",
        lambda _cfg: {
            "trust_state": "untrusted",
            "trust_reasons": ["integrity_tampered"],
            "output_confidence": "minimal",
        },
    )
    tint = tt.resolve_excel_trust_tint({})
    assert tint["detail_sheets_stub"] is True
    assert "MINIMAL OUTPUT" in tint["watermark_message"]
    stub = tt.stub_detail_sheet_rows(
        sheet_label="Database findings",
        retained_count=12,
        tint=tint,
    )
    assert stub[0]["Field"] == "Output withheld"
    assert stub[1]["Value"] == "12"
    assert "integrity_tampered" in stub[2]["Value"]
    # Stub is notice rows only — no finding payload columns
    assert all(set(r.keys()) == {"Field", "Value"} for r in stub)


def test_generate_report_prepends_watermark_when_degraded(tmp_path, monkeypatch):
    """Smoke: Excel Report info carries TRUST WATERMARK under degraded trust."""
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
            return db, [], []

        def save_aggregated_identification_risks(self, *_a, **_k):
            return None

        def get_aggregated_identification_risks(self, _sid):
            return []

        def list_sessions(self):
            return [
                {
                    "session_id": "sess-tint-degraded",
                    "started_at": "2026-01-01T00:00:00",
                    "tenant_name": "lab",
                    "technician_name": "op",
                }
            ]

    monkeypatch.setattr(
        "core.canonical_trust.get_canonical_trust_snapshot",
        lambda _cfg: {
            "trust_state": "degraded",
            "trust_reasons": ["tls_cipher_baseline_weak"],
            "output_confidence": "reduced",
        },
    )
    monkeypatch.setattr(
        "report.generator._create_heatmap",
        lambda *_a, **_k: None,
    )
    path = generate_report(
        _Mgr(), "sess-tint-degraded", output_dir=str(tmp_path), config={}
    )
    assert path
    info = pd.read_excel(path, sheet_name="Report info")
    assert info.iloc[0]["Field"] == "TRUST WATERMARK"
    db = pd.read_excel(path, sheet_name="Database findings")
    # Findings still present (degraded keeps detail)
    assert len(db) >= 1
    assert "Output withheld" not in set(db.get("Field", pd.Series(dtype=str)).tolist())


def test_generate_report_stubs_findings_when_untrusted(tmp_path, monkeypatch):
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
            return db, [], []

        def save_aggregated_identification_risks(self, *_a, **_k):
            return None

        def get_aggregated_identification_risks(self, _sid):
            return []

        def list_sessions(self):
            return [
                {
                    "session_id": "sess-tint-untrusted",
                    "started_at": "2026-01-01T00:00:00",
                    "tenant_name": "lab",
                    "technician_name": "op",
                }
            ]

    monkeypatch.setattr(
        "core.canonical_trust.get_canonical_trust_snapshot",
        lambda _cfg: {
            "trust_state": "untrusted",
            "trust_reasons": ["integrity_tampered"],
            "output_confidence": "minimal",
        },
    )
    path = generate_report(
        _Mgr(), "sess-tint-untrusted", output_dir=str(tmp_path), config={}
    )
    assert path
    info = pd.read_excel(path, sheet_name="Report info")
    assert info.iloc[0]["Field"] == "TRUST WATERMARK"
    db = pd.read_excel(path, sheet_name="Database findings")
    assert list(db.columns) == ["Field", "Value"]
    assert db.iloc[0]["Field"] == "Output withheld"
    assert db.iloc[1]["Value"] == "1"
    fs = pd.read_excel(path, sheet_name="Filesystem findings")
    assert fs.iloc[0]["Field"] == "Output withheld"
    assert fs.iloc[1]["Value"] == "0"

"""Scan evidence manifest + stakeholder Markdown + APG mapping (PoC slice)."""

from pathlib import Path

import yaml

from core.database import LocalDBManager
from report.generator import generate_report
from report.scan_evidence import apg_row_for_pattern, write_scan_evidence_artifacts


def test_apg_row_credit_card() -> None:
    row = apg_row_for_pattern("CREDIT_CARD", shadow_context=False)
    assert "PCI" in row["risk_band"]
    assert (
        "Tokenização" in row["recommended_action"]
        and "PCI-DSS" in row["recommended_action"]
    )


def test_apg_row_cpf_uses_core_dictionary_action() -> None:
    row = apg_row_for_pattern("LGPD_CPF", shadow_context=False)
    assert "Mascaramento Dinâmico" in row["recommended_action"]


def test_write_scan_evidence_artifacts_standalone(tmp_path) -> None:
    man, md = write_scan_evidence_artifacts(
        output_dir=str(tmp_path),
        session_id="abcdef0123456789",
        meta={
            "started_at": "2026-01-01T10:00:00+00:00",
            "finished_at": "2026-01-01T10:42:00+00:00",
            "config_scope_hash": "deadbeef",
        },
        about={"name": "Data Boar", "version": "9.9.9-test"},
        config={
            "targets": [{"name": "db1", "type": "database"}],
            "file_scan": {"sample_limit": 50, "extensions": [".csv"]},
        },
        db_rows=[
            {
                "target_name": "db1",
                "schema_name": "dbo",
                "table_name": "customers",
                "column_name": "doc",
                "pattern_detected": "LGPD_CPF",
                "engine_details": "mssql+pyodbc",
            }
        ],
        fs_rows=[],
        fail_rows=[],
        report_rows_capped=False,
    )
    assert Path(man).is_file()
    assert Path(md).is_file()
    loaded = yaml.safe_load(Path(man).read_text(encoding="utf-8"))
    assert loaded["evidence_schema_version"] == "1"
    assert loaded["scan_window"]["duration_minutes"] == 42.0
    assert loaded["safety_tags"]["sampling_row_cap_resolved"] >= 1
    assert "audit_trail" in loaded
    assert loaded["audit_trail"]["component"] == "EvidenceCollector"
    assert any("NOLOCK" in b for b in loaded["audit_trail"]["dba_facing_summary_pt"])
    assert "LGPD_CPF" in str(loaded.get("apg_phase_a"))
    md_text = Path(md).read_text(encoding="utf-8")
    assert "inteligência e governança de risco" in md_text
    assert "Metodologia e segurança" in md_text
    assert "Plano de ação (APG)" in md_text
    assert "NOLOCK" in md_text
    assert "scan_manifest" in md_text


def test_scan_manifest_includes_plugin_volatility_when_set(tmp_path) -> None:
    plugin_path = tmp_path / "patterns.yaml"
    plugin_path.write_text(
        """
regex_patterns:
  - name: LIVE_SESSION_TOKEN
    pattern: "\\\\btoken\\\\b"
    norm_tag: "Custom"
    volatility_class: HIGH
""",
        encoding="utf-8",
    )
    man, _md = write_scan_evidence_artifacts(
        output_dir=str(tmp_path / "out"),
        session_id="vol-session-01",
        meta={
            "started_at": "2026-01-01T10:00:00+00:00",
            "finished_at": "2026-01-01T10:05:00+00:00",
        },
        about={"name": "Data Boar", "version": "9.9.9-test"},
        config={
            "patterns_plugin_file": str(plugin_path),
            "targets": [{"name": "db1", "type": "database"}],
        },
        db_rows=[],
        fs_rows=[],
        fail_rows=[],
    )
    loaded = yaml.safe_load(Path(man).read_text(encoding="utf-8"))
    triage = loaded["plugin_metadata"]["volatility_triage"]
    assert triage[0]["pattern_id"] == "LIVE_SESSION_TOKEN"
    assert triage[0]["volatility_class"] == "HIGH"


def test_generate_report_writes_evidence_files(tmp_path) -> None:
    db_path = str(tmp_path / "audit.db")
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        sid = "evidence-session-00"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)
        mgr.save_finding(
            "database",
            target_name="T1",
            server_ip="",
            engine_details="postgresql+psycopg2",
            schema_name="public",
            table_name="test_shadow_copy",
            column_name="email_col",
            data_type="varchar",
            sensitivity_level="MEDIUM",
            pattern_detected="EMAIL",
            norm_tag="GDPR Art. 4(1)",
            ml_confidence=0,
        )
        mgr.finish_session(sid)
        path = generate_report(
            mgr,
            sid,
            output_dir=out_dir,
            config={"file_scan": {"sample_limit": 200}},
        )
        assert path is not None
        prefix = sid[:16]
        assert (Path(out_dir) / f"scan_manifest_{prefix}.yaml").is_file()
        assert (Path(out_dir) / f"POC_SUMMARY_{prefix}.md").is_file()
    finally:
        mgr.dispose()

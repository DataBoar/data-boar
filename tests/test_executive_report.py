"""Relatório executivo Markdown (sanitização + Top 3 APG)."""

from __future__ import annotations

from pathlib import Path

from core.database import LocalDBManager
from report.executive_report import generate_executive_report


def _minimal_manifest() -> dict:
    return {
        "engine_signature": {"manifest_generated_at_utc": "2026-01-01T00:00:00+00:00"},
        "scan_window": {"duration_minutes": 5.0},
        "audit_trail": {"dba_facing_summary_pt": ["Amostragem limitada por coluna."]},
        "safety_tags": {"sampling_row_cap_resolved": 500},
        "scope_snapshot": {
            "findings_counts": {
                "database_findings": 2,
                "filesystem_findings": 1,
                "scan_failures": 0,
            },
            "unique_database_tables_with_findings": 1,
        },
    }


def test_generate_executive_report_no_table_or_column_names() -> None:
    """Stakeholder MD must not echo discovery names (sanitization)."""
    manifest = _minimal_manifest()
    db_rows = [
        {
            "sensitivity_level": "HIGH",
            "pattern_detected": "EMAIL",
            "table_name": "SECRET_CUSTOMERS",
            "column_name": "email_addr",
        },
        {
            "sensitivity_level": "HIGH",
            "pattern_detected": "CREDIT_CARD",
            "table_name": "SECRET_CUSTOMERS",
            "column_name": "pan_col",
        },
    ]
    fs_rows = [{"sensitivity_level": "MEDIUM", "pattern_detected": "EMAIL"}]
    apg_rows = [
        {
            "pattern_detected": "EMAIL",
            "finding_count": 2,
            "risk_band": "Médio",
            "recommended_action": "Homologar mascaramento.",
        },
        {
            "pattern_detected": "CREDIT_CARD",
            "finding_count": 1,
            "risk_band": "Bloqueante (PCI)",
            "recommended_action": "Tokenizar PAN.",
        },
    ]
    md = generate_executive_report(
        session_id="session-abcdef-1234567890",
        about={"name": "Data Boar", "version": "1.0.0-test"},
        manifest=manifest,
        db_rows=db_rows,
        fs_rows=fs_rows,
        _fail_rows=[],
        apg_rows=apg_rows,
        report_rows_capped=False,
    )
    assert "SECRET_CUSTOMERS" not in md
    assert "email_addr" not in md
    assert "pan_col" not in md
    assert "CREDIT_CARD" in md
    assert "Prioridades imediatas (Top 3)" in md
    assert "Metodologia e segurança" in md
    assert "Plano de ação (APG)" in md
    assert "Inventário por tipo de dado" in md
    assert "Homologar mascaramento" in md
    assert "Tokenizar PAN" in md
    assert "inteligência e governança de risco" in md


def test_top3_credit_card_before_email_same_mock_counts() -> None:
    """APG ordering: PCI-like patterns surface first."""
    manifest = _minimal_manifest()
    manifest["scope_snapshot"]["findings_counts"]["database_findings"] = 2
    apg_rows = [
        {
            "pattern_detected": "EMAIL",
            "finding_count": 5,
            "risk_band": "Médio",
            "recommended_action": "A",
        },
        {
            "pattern_detected": "CREDIT_CARD",
            "finding_count": 5,
            "risk_band": "Bloqueante (PCI)",
            "recommended_action": "B",
        },
    ]
    md = generate_executive_report(
        session_id="session-priority-test-00",
        about={"name": "Data Boar", "version": "0"},
        manifest=manifest,
        db_rows=[],
        fs_rows=[],
        _fail_rows=[],
        apg_rows=apg_rows,
        report_rows_capped=False,
    )
    pos_cc = md.find("CREDIT_CARD")
    pos_em = md.find("EMAIL")
    assert pos_cc != -1 and pos_em != -1
    assert pos_cc < pos_em


def test_cli_reporter_default_output_md(tmp_path) -> None:
    from cli.reporter import main
    from report.safe_prefix import safe_session_prefix

    repo_root = Path(__file__).resolve().parents[1]
    root_reports_before = set(repo_root.glob("executive_report_*.md"))

    db_path = str(tmp_path / "audit.db")
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        f"""sqlite_path: {db_path}
report:
  output_dir: {tmp_path.as_posix()}
targets:
  - name: t1
    type: database
""",
        encoding="utf-8",
    )
    mgr = LocalDBManager(db_path)
    sid = "cli-exec-report-01"
    mgr.set_current_session_id(sid)
    mgr.create_session_record(sid)
    mgr.save_finding(
        "database",
        target_name="T1",
        server_ip="",
        engine_details="postgresql+psycopg2",
        schema_name="public",
        table_name="t_user",
        column_name="c_email",
        data_type="varchar",
        sensitivity_level="MEDIUM",
        pattern_detected="EMAIL",
        norm_tag="",
        ml_confidence=0,
    )
    mgr.finish_session(sid)
    try:
        rc = main(
            [
                "--config",
                str(cfg_path),
                "--session-id",
                sid,
            ]
        )
    finally:
        mgr.dispose()
    assert rc == 0
    out_path = tmp_path / f"executive_report_{safe_session_prefix(sid, max_len=8)}.md"
    out = out_path.read_text(encoding="utf-8")
    assert "inteligência e governança de risco" in out
    assert "Metodologia e segurança" in out
    assert "t_user" not in out
    root_reports_after = set(repo_root.glob("executive_report_*.md"))
    assert root_reports_after == root_reports_before, (
        "executive_report_*.md must not appear in repo root "
        f"(before={root_reports_before}, after={root_reports_after})"
    )

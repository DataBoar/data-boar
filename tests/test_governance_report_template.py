"""Governance Lens Phase C — Jinja template + CLI --governance-report."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from core.database import LocalDBManager
from report.governance_report import (
    build_governance_report_context,
    render_governance_report_markdown,
)

_FIXTURE_MAP = "tests/fixtures/governance_framework_map_test.yaml"
_REPO_ROOT = Path(__file__).resolve().parents[1]


def _pro_gov_config(db_path: str, out_dir: str) -> dict:
    return {
        "sqlite_path": db_path,
        "report": {"output_dir": out_dir},
        "licensing": {"mode": "open", "effective_tier": "pro"},
        "governance": {
            "enabled": True,
            "tier": "pro",
            "map_file": _FIXTURE_MAP,
        },
    }


def _write_config(path: Path, cfg: dict) -> None:
    path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")


def _seed_session(db_path: str) -> str:
    sid = "gov-md-s1"
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid, tenant_name="Acme Lab", technician_name="Ops")
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name="homolog-postgres",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def _run_main(cfg_path: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "main.py", "--config", str(cfg_path), *extra]
    return subprocess.run(
        cmd,
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_template_renders_with_minimal_findings(tmp_path):
    db_path = str(tmp_path / "gov.db")
    sid = _seed_session(db_path)
    cfg = _pro_gov_config(db_path, str(tmp_path / "out"))
    mgr = LocalDBManager(db_path)
    try:
        md = render_governance_report_markdown(cfg, mgr, sid)
    finally:
        mgr.dispose()

    assert "Governance Lens" in md
    assert sid in md
    assert "Acme Lab" in md
    assert "lang: pt-BR" in md


def test_template_includes_all_framework_sections(tmp_path):
    db_path = str(tmp_path / "gov2.db")
    sid = _seed_session(db_path)
    cfg = _pro_gov_config(db_path, str(tmp_path / "out2"))
    mgr = LocalDBManager(db_path)
    try:
        ctx = build_governance_report_context(cfg, mgr, sid)
        md = render_governance_report_markdown(cfg, mgr, sid)
    finally:
        mgr.dispose()

    assert ctx["total_gaps"] >= 1
    for heading in (
        "ISO/IEC 38500",
        "ISO/IEC 27014",
        "COBIT 2019",
        "ITIL 4",
        "ISO/IEC 27001",
        "Roadmap de Remediação",
        "Metodologia e Limitações",
        "Anexo A",
        "Anexo B",
    ):
        assert heading in md


def test_cli_governance_report_creates_file(tmp_path):
    db_path = str(tmp_path / "audit.db")
    out_dir = tmp_path / "reports"
    out_dir.mkdir()
    report_path = out_dir / "relatorio_grc.md"
    sid = _seed_session(db_path)
    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, _pro_gov_config(db_path, str(out_dir)))

    r = _run_main(cfg_path, "--governance-report", str(report_path), "--session", sid)
    assert r.returncode == 0, r.stderr
    assert report_path.is_file()
    assert str(report_path.resolve()) in r.stdout.strip()
    body = report_path.read_text(encoding="utf-8")
    assert "COBIT-DSS05.04" in body or "LGPD" in body


def test_cli_governance_report_rejects_web_flag(tmp_path):
    db_path = str(tmp_path / "audit.db")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _seed_session(db_path)
    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, _pro_gov_config(db_path, str(out_dir)))

    r = _run_main(cfg_path, "--governance-report", str(out_dir / "x.md"), "--web")
    assert r.returncode == 2
    assert "Cannot combine --governance-report" in r.stderr


def test_pandoc_governance_defaults_file_exists():
    pandoc_cfg = _REPO_ROOT / "config" / "pandoc_governance.yaml"
    ref_doc = _REPO_ROOT / "docs" / "templates" / "governance_reference.docx"
    assert pandoc_cfg.is_file()
    assert ref_doc.is_file()
    text = pandoc_cfg.read_text(encoding="utf-8")
    assert "reference-doc: docs/templates/governance_reference.docx" in text

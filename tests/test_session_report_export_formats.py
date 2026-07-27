"""Per-format session export via ``data-boar-report`` (#1326)."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from core.database import LocalDBManager
from report import generator as report_generator

_REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _seed_session(db_path: Path, session_id: str = SESSION_ID) -> None:
    mgr = LocalDBManager(str(db_path))
    try:
        mgr.set_current_session_id(session_id)
        mgr.create_session_record(session_id)
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="email_col",
            sensitivity_level="MEDIUM",
            pattern_detected="EMAIL",
            norm_tag="LGPD",
            ml_confidence=80,
        )
        mgr.finish_session(session_id)
    finally:
        mgr.dispose()


def _minimal_config(tmp_path: Path) -> tuple[Path, Path]:
    out_dir = tmp_path / "reports"
    db_path = tmp_path / "audit.db"
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {out_dir.as_posix()}
sqlite_path: {db_path.as_posix()}
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    _seed_session(db_path)
    return cfg, out_dir


def _run_reporter(cfg: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "cli.reporter",
        "--config",
        str(cfg),
        "--session-id",
        SESSION_ID,
        *extra,
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize(
    ("fmt", "glob_pattern"),
    [
        ("md", "executive_report_*.md"),
        ("docx", "executive_report_*.docx"),
        ("pdf", "executive_report_*.pdf"),
        ("xlsx", "Relatorio_Auditoria_*.xlsx"),
        pytest.param(
            "heatmap",
            "heatmap_*.png",
            marks=pytest.mark.skipif(
                not report_generator._PLOT_AVAILABLE,
                reason="matplotlib/seaborn not available",
            ),
        ),
        ("dsar", "dsar_export_*.json"),
        ("json", "scan_manifest_*.json"),
        ("audit-trail", "audit_trail_*.json"),
    ],
)
def test_session_export_format_writes_artifact(tmp_path, fmt, glob_pattern):
    cfg, out_dir = _minimal_config(tmp_path)
    r = _run_reporter(cfg, "--format", fmt)
    assert r.returncode == 0, r.stdout + r.stderr
    matches = list(out_dir.glob(glob_pattern))
    assert matches, f"expected {glob_pattern} under {out_dir}, got stdout={r.stdout!r}"
    if fmt == "pdf":
        assert matches[0].read_bytes()[:4] == b"%PDF"
    if fmt == "docx":
        assert zipfile.is_zipfile(matches[0])
    if fmt in {"dsar", "json", "audit-trail"}:
        payload = json.loads(matches[0].read_text(encoding="utf-8"))
        assert isinstance(payload, dict)


def test_session_export_all_writes_bundle(tmp_path):
    cfg, out_dir = _minimal_config(tmp_path)
    r = _run_reporter(cfg, "--format", "all")
    assert r.returncode == 0, r.stdout + r.stderr
    required = (
        "executive_report_*.md",
        "executive_report_*.docx",
        "executive_report_*.pdf",
        "Relatorio_Auditoria_*.xlsx",
        "dsar_export_*.json",
        "scan_manifest_*.json",
        "audit_trail_*.json",
    )
    for pattern in required:
        assert list(out_dir.glob(pattern)), f"missing {pattern} after --format all"
    if report_generator._PLOT_AVAILABLE:
        assert list(out_dir.glob("heatmap_*.png"))


def test_reporter_help_lists_format_flag():
    r = subprocess.run(
        [sys.executable, "-m", "cli.reporter", "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=60,
        check=False,
    )
    assert r.returncode == 0
    assert "--format" in r.stdout
    assert "audit-trail" in r.stdout


def test_format_wrapper_xlsx_invokes_report_cli(tmp_path):
    cfg, out_dir = _minimal_config(tmp_path)
    from cli.format_entrypoints import main_xlsx

    rc = main_xlsx(
        ["--config", str(cfg), "--session-id", SESSION_ID],
    )
    assert rc == 0
    assert list(out_dir.glob("Relatorio_Auditoria_*.xlsx"))

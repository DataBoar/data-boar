"""Pre-flight output directories (#1324) and --regenerate-report CLI (#1325)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from core.database import LocalDBManager
from core.output_paths import OutputPathError, ensure_config_output_directories


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_main(
    cfg: Path, *extra: str, timeout: int = 120
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(_repo_root() / "main.py"), "--config", str(cfg), *extra]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_repo_root()),
        timeout=timeout,
        check=False,
    )


def _minimal_config(tmp_path: Path, *, output_dir: str | None = None) -> Path:
    out = output_dir if output_dir is not None else str(tmp_path / "reports")
    db = tmp_path / "audit.db"
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {out}
sqlite_path: {db.as_posix()}
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    return cfg


def test_ensure_creates_missing_report_output_dir(tmp_path):
    missing = tmp_path / "nested" / "report_hml_db"
    config = {
        "report": {"output_dir": str(missing)},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    assert not missing.exists()
    created = ensure_config_output_directories(config)
    assert missing.is_dir()
    assert any("report.output_dir" in msg for msg in created)


def test_ensure_creates_sqlite_parent_and_learned_patterns_parent(tmp_path):
    db = tmp_path / "data" / "sessions" / "audit.db"
    learned = tmp_path / "patterns" / "learned_patterns.yaml"
    config = {
        "report": {"output_dir": str(tmp_path / "reports")},
        "sqlite_path": str(db),
        "learned_patterns": {"enabled": True, "output_file": str(learned)},
    }
    created = ensure_config_output_directories(config)
    assert db.parent.is_dir()
    assert learned.parent.is_dir()
    labels = " ".join(created)
    assert "sqlite_path" in labels
    assert "learned_patterns" in labels


def test_ensure_raises_when_path_is_a_file(tmp_path):
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x", encoding="utf-8")
    config = {"report": {"output_dir": str(blocker)}}
    with pytest.raises(OutputPathError, match="not a directory"):
        ensure_config_output_directories(config)


def test_validate_config_creates_missing_output_dir(tmp_path):
    missing = tmp_path / "preflight_reports"
    cfg = _minimal_config(tmp_path, output_dir=missing.as_posix())
    r = _run_main(cfg, "--validate-config")
    assert r.returncode == 0, r.stdout + r.stderr
    assert missing.is_dir()
    assert "created" in r.stdout or missing.exists()


def test_regenerate_report_writes_xlsx_and_heatmap(tmp_path):
    out_dir = tmp_path / "out_regen"
    db_path = tmp_path / "audit_regen.db"
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
    session_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    mgr = LocalDBManager(str(db_path))
    try:
        mgr.set_current_session_id(session_id)
        mgr.create_session_record(session_id)
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session(session_id)
    finally:
        mgr.dispose()

    r = _run_main(cfg, "--regenerate-report", session_id)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Report written:" in r.stdout
    xlsx_files = list(out_dir.glob("Relatorio_Auditoria_*.xlsx"))
    assert xlsx_files, f"expected XLSX under {out_dir}, got stdout={r.stdout!r}"


def test_regenerate_report_unknown_session_exits_2(tmp_path):
    cfg = _minimal_config(tmp_path)
    r = _run_main(cfg, "--regenerate-report", "00000000-0000-0000-0000-000000000000")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Unknown session" in r.stderr


def test_regenerate_report_rejects_web_combo(tmp_path):
    cfg = _minimal_config(tmp_path)
    r = _run_main(cfg, "--regenerate-report", "sess", "--web")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Cannot combine --regenerate-report" in r.stderr


def test_main_help_lists_regenerate_report():
    r = subprocess.run(
        [sys.executable, str(_repo_root() / "main.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_repo_root()),
        timeout=60,
        check=False,
    )
    assert r.returncode == 0
    assert "--regenerate-report" in r.stdout

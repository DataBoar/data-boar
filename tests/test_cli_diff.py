"""CLI and LocalDBManager: session --diff and --fail-on-new-high."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.database import LocalDBManager


def _seed_sessions(db_path: str) -> tuple[str, str]:
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record("aaa111")
        mgr.set_current_session_id("aaa111")
        mgr.save_finding(
            "database",
            target_name="prod-postgres",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
        )
        mgr.finish_session("aaa111")

        mgr.create_session_record("bbb222")
        mgr.set_current_session_id("bbb222")
        mgr.save_finding(
            "database",
            target_name="prod-postgres",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
        )
        mgr.save_finding(
            "database",
            target_name="prod-postgres",
            schema_name="public",
            table_name="users",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
        )
        mgr.save_finding(
            "filesystem",
            target_name="/data/exports",
            path="/data/exports",
            file_name="report.csv",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
        )
        mgr.finish_session("bbb222")
    finally:
        mgr.dispose()
    return "aaa111", "bbb222"


def test_diff_sessions_new_high_and_resolved(tmp_path):
    db_path = str(tmp_path / "audit.db")
    s_a, s_b = _seed_sessions(db_path)
    mgr = LocalDBManager(db_path)
    try:
        result = mgr.diff_sessions(s_a, s_b)
        assert result["new_high_count"] == 2
        assert len(result["database"]["new"]) == 1
        assert "cpf" in next(iter(result["database"]["new"].values())).column_name
        assert len(result["filesystem"]["new"]) == 1
    finally:
        mgr.dispose()


def test_diff_sessions_unknown_session_raises(tmp_path):
    db_path = str(tmp_path / "audit.db")
    s_a, _s_b = _seed_sessions(db_path)
    mgr = LocalDBManager(db_path)
    try:
        try:
            mgr.diff_sessions(s_a, "no-such-session")
        except ValueError as e:
            assert "Unknown session" in str(e)
        else:
            raise AssertionError("expected ValueError")
    finally:
        mgr.dispose()


def _minimal_config(tmp_path: Path, db_path: Path) -> Path:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path.as_posix()}
sqlite_path: {db_path.as_posix()}
api:
  port: 8765
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    return cfg


def test_cli_diff_ok_without_fail_flag(tmp_path):
    db_path = tmp_path / "audit.db"
    s_a, s_b = _seed_sessions(str(db_path))
    cfg = _minimal_config(tmp_path, db_path)
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--diff",
            s_a,
            s_b,
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Diff:" in r.stdout
    assert "Summary:" in r.stdout


def test_cli_diff_fail_on_new_high_exits_one(tmp_path):
    db_path = tmp_path / "audit.db"
    s_a, s_b = _seed_sessions(str(db_path))
    cfg = _minimal_config(tmp_path, db_path)
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--diff",
            s_a,
            s_b,
            "--fail-on-new-high",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
    )
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[FAIL] --fail-on-new-high" in r.stdout


def test_cli_diff_unknown_session_exits_two(tmp_path):
    db_path = tmp_path / "audit.db"
    s_a, s_b = _seed_sessions(str(db_path))
    cfg = _minimal_config(tmp_path, db_path)
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--diff",
            s_a,
            "missing-session-id",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Session error" in r.stderr

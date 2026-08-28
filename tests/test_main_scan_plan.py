"""CLI: main.py --plan does not start a scan (filesystem target, no TCP peer)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_plan(cfg: Path) -> subprocess.CompletedProcess[str]:
    repo = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, str(repo / "main.py"), "--config", str(cfg), "--plan"],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
    )


def test_plan_filesystem_exits_zero_without_scan(tmp_path: Path) -> None:
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "a.db"
    cfg.write_text(
        f"""targets:
  - name: files-share
    type: filesystem
    path: {tmp_path.as_posix()}
report:
  output_dir: {tmp_path.as_posix()}
sqlite_path: {db.as_posix()}
api:
  port: 8765
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    r = _run_plan(cfg)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Scan plan" in r.stdout
    assert "files-share" in r.stdout
    assert "not a SQL/Snowflake catalog target" in r.stdout
    assert not db.exists()


def test_plan_rejects_web_combo(tmp_path: Path) -> None:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        """targets: []
report:
  output_dir: /tmp
sqlite_path: /tmp/x.db
""",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--plan",
            "--web",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=30,
        check=False,
    )
    assert r.returncode == 2
    assert "Cannot combine --plan" in r.stderr

"""CLI: --reconcile-integrity-anchor --confirm-upgrade-to (#1262)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.about import _package_version
from core.integrity_anchor import (
    ensure_integrity_anchor,
    reset_integrity_anchor_for_tests,
)


def _base_config(tmp_path: Path) -> Path:
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "a.db"
    cfg.write_text(
        f"""targets: []
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
    return cfg


def _run(cfg: Path, extra: list[str]) -> subprocess.CompletedProcess[str]:
    repo = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(repo / "main.py"), "--config", str(cfg), *extra]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
    )


def test_reconcile_requires_both_flags(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    r = _run(cfg, ["--reconcile-integrity-anchor"])
    assert r.returncode == 2
    assert "--confirm-upgrade-to" in r.stderr
    r2 = _run(cfg, ["--confirm-upgrade-to", "1.0.0"])
    assert r2.returncode == 2
    assert "--reconcile-integrity-anchor" in r2.stderr


def test_reconcile_incompatible_with_web(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    r = _run(
        cfg,
        [
            "--reconcile-integrity-anchor",
            "--confirm-upgrade-to",
            _package_version(),
            "--web",
            "--allow-insecure-http",
        ],
    )
    assert r.returncode == 2
    assert "Cannot combine --reconcile-integrity-anchor" in r.stderr


def test_reconcile_ok_matching_installed_version(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    sqlite = tmp_path / "a.db"
    reset_integrity_anchor_for_tests()
    ensure_integrity_anchor({"sqlite_path": str(sqlite)})
    ver = _package_version()
    r = _run(
        cfg,
        ["--reconcile-integrity-anchor", "--confirm-upgrade-to", ver],
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[OK] integrity anchor re-baselined" in r.stdout
    assert ver in r.stdout


def test_reconcile_refuses_wrong_version(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    r = _run(
        cfg,
        [
            "--reconcile-integrity-anchor",
            "--confirm-upgrade-to",
            "9.9.9-not-installed",
        ],
    )
    assert r.returncode == 1
    assert "Integrity reconcile refused" in r.stderr

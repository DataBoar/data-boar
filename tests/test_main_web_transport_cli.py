"""CLI: main.py --web requires TLS paths or explicit --allow-insecure-http."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def test_main_web_exits_without_transport_choice(tmp_path):
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "a.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  port: 8765
scan:
  max_workers: 1
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
            "--web",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=30,
        check=False,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Dashboard transport error" in r.stderr


def test_main_web_accepts_allow_insecure_http(tmp_path):
    """With explicit opt-in, web mode stays up (uvicorn) instead of exiting at transport gate."""
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "a.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  port: 8766
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--web",
            "--allow-insecure-http",
            "--host",
            "127.0.0.1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(repo),
    )
    try:
        time.sleep(2.0)
        assert proc.poll() is None, (
            "Server should still be running (transport gate passed)."
        )
    finally:
        proc.kill()
        proc.wait(timeout=15)


def test_main_web_refuses_non_loopback_without_resolved_auth(tmp_path):
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "a.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  port: 8767
scan:
  max_workers: 1
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
            "--web",
            "--allow-insecure-http",
            "--host",
            "0.0.0.0",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=30,
        check=False,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Refusing startup with non-loopback API bind" in r.stderr

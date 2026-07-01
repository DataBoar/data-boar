"""CLI ``--demo`` contract (#1113)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "main.py"


def _run_demo_args(*extra: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(MAIN), "--demo", *extra]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_main_py_demo_flag_in_help() -> None:
    proc = subprocess.run(
        [sys.executable, str(MAIN), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--demo" in proc.stdout


def test_demo_headless_scan_completes() -> None:
    """Headless demo path must finish scan with exit 0 and write a report."""
    proc = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts" / "demo.sh"), "--headless"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Report written:" in proc.stdout or "Report written:" in proc.stderr


def test_demo_sh_multi_step_disables_python_atexit_cleanup() -> None:
    """Headless demo.sh must not register Python atexit cleanup (bash trap owns it)."""
    script = (REPO_ROOT / "scripts" / "demo.sh").read_text(encoding="utf-8")
    assert "register_cleanup=False" in script


def test_config_not_found_suggests_demo() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(MAIN),
            "--config",
            "/nonexistent/data_boar_config_missing.yaml",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    combined = proc.stdout + proc.stderr
    assert "--demo" in combined


@pytest.mark.skipif(
    not (REPO_ROOT / "core" / "demo" / "synthetic_corpus.py").exists(),
    reason="core.demo package required",
)
def test_prepare_demo_workspace_loopback_host() -> None:
    from core.demo.runtime import prepare_demo_workspace

    demo_dir, config_path, config = prepare_demo_workspace(
        port=18088, register_cleanup=False
    )
    try:
        assert config_path.exists()
        assert config["api"]["host"] == "127.0.0.1"
        assert (demo_dir / "corpus").is_dir()
    finally:
        import shutil

        shutil.rmtree(demo_dir, ignore_errors=True)

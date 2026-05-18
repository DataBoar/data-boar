"""Smoke tests for scripts/image_inspect.py (operator rich-media CLI)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_image_inspect_help() -> None:
    proc = subprocess.run(
        ["uv", "run", "python", "scripts/image_inspect.py", "--help"],
        cwd=_root(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = (proc.stdout or "").lower()
    assert "metadata" in out
    assert "ocr" in out


def test_image_inspect_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.jpg"
    proc = subprocess.run(
        ["uv", "run", "python", "scripts/image_inspect.py", str(missing)],
        cwd=_root(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 2

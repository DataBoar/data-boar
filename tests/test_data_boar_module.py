"""``python -m data_boar`` package surface (native nfpm / embed channel — #1437)."""

from __future__ import annotations

import subprocess
import sys


def test_data_boar_module_version_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "data_boar", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = (proc.stdout or "") + (proc.stderr or "")
    assert "1." in out or "data" in out.lower() or "boar" in out.lower()

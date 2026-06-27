"""CLI: main.py --version prints public version and exits before config load."""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

from core.about import _package_version


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _maturity_build_octet() -> int:
    with (_repo_root() / "pyproject.toml").open("rb") as f:
        return int(tomllib.load(f)["tool"]["databoar"]["maturity_build"])


def test_main_version_prints_public_version_exit_zero(tmp_path):
    """--version must not require config.yaml and must not leak maturity_build."""
    repo = _repo_root()
    # Run from an empty dir so default config.yaml is absent.
    r = subprocess.run(
        [sys.executable, str(repo / "main.py"), "--version"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=30,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    expected = f"Data Boar {_package_version()}"
    assert r.stdout.strip() == expected
    assert r.stderr == ""

    maturity = _maturity_build_octet()
    assert f".{maturity}" not in r.stdout
    assert not re.search(r"\d+\.\d+\.\d+\.\d+", r.stdout)

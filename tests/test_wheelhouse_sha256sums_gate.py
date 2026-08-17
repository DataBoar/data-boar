"""Gate: SHA256SUMS must cover every local .whl (#1410)."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "wheelhouse"
    / "verify_release_sha256sums.sh"
)


def _whl(path: Path, name: str, payload: bytes) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_bytes(payload)


def _sums(path: Path, names: list[str]) -> None:
    lines = []
    for name in names:
        digest = hashlib.sha256((path / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (path / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.skipif(not SCRIPT.is_file(), reason="verify_release_sha256sums.sh missing")
def test_verify_release_sha256sums_ok(tmp_path: Path) -> None:
    _whl(tmp_path, "a-cp314-cp314t-manylinux.whl", b"aaa")
    _whl(tmp_path, "b-cp312-cp312-musllinux.whl", b"bbb")
    _sums(tmp_path, ["a-cp314-cp314t-manylinux.whl", "b-cp312-cp312-musllinux.whl"])
    r = subprocess.run(
        ["bash", str(SCRIPT), "--dir", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK:" in r.stdout


@pytest.mark.skipif(not SCRIPT.is_file(), reason="verify_release_sha256sums.sh missing")
def test_verify_release_sha256sums_fails_when_sum_lags_wheel(tmp_path: Path) -> None:
    _whl(tmp_path, "old.whl", b"old")
    _whl(tmp_path, "new-cp314t.whl", b"new")
    _sums(tmp_path, ["old.whl"])  # lag: new wheel not in SUMS
    r = subprocess.run(
        ["bash", str(SCRIPT), "--dir", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "FAIL:" in (r.stdout + r.stderr)

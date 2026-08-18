"""Gate: SHA256SUMS must cover every local .whl (#1410)."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "wheelhouse"
    / "verify_release_sha256sums.sh"
)

# Windows runners ship Git for Windows; bare ``bash`` often resolves to the
# System32 WSL shim (no distro) and fails every job (#1619 / PR #1618).
_WIN_GIT_BASH_REL = (
    Path("Git") / "bin" / "bash.exe",
    Path("Git") / "usr" / "bin" / "bash.exe",
)


def resolve_bash_executable() -> str:
    """Return a bash binary that can run repo ``.sh`` scripts.

    On Windows, prefer Git Bash over ``shutil.which("bash")`` (WSL shim).
    """
    if sys.platform == "win32":
        roots = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for root in roots:
            if not root:
                continue
            base = Path(root)
            for rel in _WIN_GIT_BASH_REL:
                candidate = base / rel
                if candidate.is_file():
                    return str(candidate)
            # Portable / user installs under LocalAppData\Programs\Git\...
            portable = base / "Programs" / "Git" / "bin" / "bash.exe"
            if portable.is_file():
                return str(portable)

        which = shutil.which("bash")
        if which:
            lowered = which.replace("/", "\\").lower()
            # Reject WSL / Store shims that cannot run Git-style bash scripts.
            if "system32" not in lowered and "windowsapps" not in lowered:
                return which
        pytest.skip(
            "Git Bash not found; install Git for Windows or set PATH to "
            r"C:\Program Files\Git\bin\bash.exe (#1619)"
        )

    found = shutil.which("bash")
    if found:
        return found
    return "bash"


def _whl(path: Path, name: str, payload: bytes) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_bytes(payload)


def _sums(path: Path, names: list[str]) -> None:
    lines = []
    for name in names:
        digest = hashlib.sha256((path / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (path / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_resolve_bash_executable_prefers_git_bash_on_windows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """#1619: do not pick System32 WSL bash when Git Bash exists."""
    if sys.platform != "win32":
        git_bash = tmp_path / "Git" / "bin" / "bash.exe"
        git_bash.parent.mkdir(parents=True)
        git_bash.write_text("", encoding="utf-8")
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("ProgramFiles", str(tmp_path))
        monkeypatch.delenv("ProgramFiles(x86)", raising=False)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.setattr(
            shutil,
            "which",
            lambda _name: r"C:\Windows\System32\bash.exe",
        )
        assert resolve_bash_executable() == str(git_bash)
        return

    # On a real Windows host/CI: resolved path must be Git Bash, not System32.
    resolved = resolve_bash_executable()
    lowered = resolved.replace("/", "\\").lower()
    assert "system32" not in lowered
    assert resolved.lower().endswith("bash.exe")
    assert Path(resolved).is_file()


@pytest.mark.skipif(not SCRIPT.is_file(), reason="verify_release_sha256sums.sh missing")
def test_verify_release_sha256sums_ok(tmp_path: Path) -> None:
    _whl(tmp_path, "a-cp314-cp314t-manylinux.whl", b"aaa")
    _whl(tmp_path, "b-cp312-cp312-musllinux.whl", b"bbb")
    _sums(tmp_path, ["a-cp314-cp314t-manylinux.whl", "b-cp312-cp312-musllinux.whl"])
    bash = resolve_bash_executable()
    r = subprocess.run(
        [bash, str(SCRIPT), "--dir", str(tmp_path)],
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
    bash = resolve_bash_executable()
    r = subprocess.run(
        [bash, str(SCRIPT), "--dir", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "FAIL:" in (r.stdout + r.stderr)

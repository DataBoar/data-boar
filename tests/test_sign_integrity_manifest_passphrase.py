"""D2239-9: the manifest signer takes the key passphrase only at the terminal (#2239)."""

from __future__ import annotations

import ctypes
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization

from core.integrity_anchor import CRITICAL_MODULES
from core.integrity_signed_manifest import evaluate_signed_manifest
from tests.integrity_manifest_helpers import (
    generate_test_signing_key,
    pin_signed_manifest,
)
from tests.tty_session import (
    PTY_AVAILABLE,
    PTY_SKIP_REASON,
    env_without_ci,
    run_under_pty,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SIGNER = REPO_ROOT / "scripts" / "sign-integrity-manifest.py"
PASSWORD_ENV = "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD"
PEM_FILE_ENV = "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE"
_KEY_PHRASE = "manifest-test-phrase"


@pytest.fixture
def encrypted_signer_key(tmp_path: Path) -> tuple[Path, str]:
    private_key, public_pem = generate_test_signing_key()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            _KEY_PHRASE.encode("utf-8")
        ),
    )
    path = tmp_path / "signer-enc.pem"
    path.write_bytes(pem)
    return path, public_pem


def _env(key_path: Path, **extra: str) -> dict[str, str]:
    env = {
        k: v
        for k, v in env_without_ci().items()
        if k not in {PASSWORD_ENV, "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM"}
    }
    env[PEM_FILE_ENV] = str(key_path)
    env.update(extra)
    return env


def test_d2239_9_password_env_without_tty_exits_2_and_writes_nothing(
    encrypted_signer_key, tmp_path
):
    """D2239-9 (a): the right passphrase in the env signs nothing without a terminal."""
    key_path, _public_pem = encrypted_signer_key
    out = tmp_path / "manifest.json"
    proc = subprocess.run(
        [sys.executable, str(SIGNER), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
        env=_env(key_path, **{PASSWORD_ENV: _KEY_PHRASE}),
        stdin=subprocess.DEVNULL,
    )
    assert proc.returncode == 2
    assert "run this command in an interactive terminal" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert _KEY_PHRASE not in proc.stderr + proc.stdout
    assert not out.exists()


@pytest.mark.skipif(not PTY_AVAILABLE, reason=PTY_SKIP_REASON)
def test_d2239_9_passphrase_typed_on_the_tty_signs_a_valid_manifest(
    encrypted_signer_key, tmp_path, monkeypatch
):
    """D2239-9 (b): typed at the terminal, the key signs a manifest that verifies."""
    key_path, public_pem = encrypted_signer_key
    out = tmp_path / "manifest.json"
    result = run_under_pty(
        [sys.executable, str(SIGNER), "--out", str(out)],
        env=_env(key_path),
        cwd=str(REPO_ROOT),
        prompt_marker=b"passphrase:",
        typed=_KEY_PHRASE,
        timeout=120,
    )
    assert result.timed_out is False
    assert result.prompted is True
    assert result.exit_code == 0, result.output
    document = json.loads(out.read_text(encoding="utf-8"))
    assert set(document["files"]) == set(CRITICAL_MODULES)
    pin_signed_manifest(monkeypatch, out, public_pem)
    verdict = evaluate_signed_manifest(
        document["files"], document["release_label"], None
    )
    assert verdict["integrity_state"] == "validated", verdict["detail"]


@pytest.mark.skipif(not PTY_AVAILABLE, reason=PTY_SKIP_REASON)
def test_d2239_9_verify_only_never_prompts(encrypted_signer_key, tmp_path):
    """D2239-9 (c): ``--verify-only`` uses the public key and never asks for a passphrase."""
    key_path, _public_pem = encrypted_signer_key
    result = run_under_pty(
        [sys.executable, str(SIGNER), "--verify-only"],
        env=_env(key_path),
        cwd=str(REPO_ROOT),
        prompt_marker=b"passphrase:",
        typed=None,
        timeout=120,
    )
    assert result.timed_out is False
    assert result.prompted is False
    assert result.exit_code in (0, 1), result.output
    assert "signed_manifest" in result.output


# ---------------------------------------------------------------------------
# PR #2379 CI fixes: unit tests of the shared passphrase module (#2239).
#
# The Windows console itself cannot be reproduced on this POSIX host: the
# detection helper is exercised against a fake kernel32 boundary
# (monkeypatched ``ctypes.WinDLL``) and the module platform flag. The
# isatty-lie regression below reproduces the exact NUL/DEVNULL condition
# that hung the GHAS Windows job; the Windows job is the final proof that
# the real console path works.
# ---------------------------------------------------------------------------


class _FakeWinApi:
    """Callable stand-in for a ctypes kernel32 function (restype settable)."""

    restype: object = None
    argtypes: object = None

    def __init__(self, impl: Callable[..., object]) -> None:
        self._impl = impl

    def __call__(self, *args: object) -> object:
        return self._impl(*args)


class _FakeKernel32:
    """The kernel32 surface used by the console-detection helper."""

    def __init__(self, *, std_handle: object, console_mode_rc: int) -> None:
        self.GetStdHandle = _FakeWinApi(lambda _handle: std_handle)
        self.GetConsoleMode = _FakeWinApi(lambda _handle, _mode: console_mode_rc)


class _FakeStdinWithFd:
    """A real fd 0 without a terminal: a Windows child whose stdin is NUL."""

    @staticmethod
    def fileno() -> int:
        return 0


def _patch_windows_console(
    monkeypatch: pytest.MonkeyPatch,
    *,
    std_handle: object = 1,
    console_mode_rc: int,
) -> None:
    """Point ``ctypes.WinDLL`` at a fake kernel32 for the detection helper."""

    def fake_windll(name: str, use_last_error: bool = False) -> _FakeKernel32:
        if name != "kernel32":
            raise AssertionError(f"unexpected DLL: {name}")
        return _FakeKernel32(std_handle=std_handle, console_mode_rc=console_mode_rc)

    monkeypatch.setattr(ctypes, "WinDLL", fake_windll, raising=False)


def test_windows_devnull_stdin_is_not_interactive_even_when_isatty_lies(monkeypatch):
    """#2239 Windows CI hang: NUL makes ``os.isatty`` lie; must fail closed."""
    import os

    from scripts import issuer_key_passphrase as mod

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(mod, "_IS_WINDOWS", True, raising=False)
    # NUL is a character device: isatty lies True, GetConsoleMode fails.
    _patch_windows_console(monkeypatch, console_mode_rc=0)
    monkeypatch.setattr(os, "isatty", lambda _fd: True)
    monkeypatch.setattr(mod.sys, "stdin", _FakeStdinWithFd())
    assert mod.stdin_is_interactive() is False


def test_windows_console_stdin_is_interactive(monkeypatch):
    """A real Windows console (CONIN$) is interactive even if isatty says no."""
    import os

    from scripts import issuer_key_passphrase as mod

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(mod, "_IS_WINDOWS", True, raising=False)
    _patch_windows_console(monkeypatch, console_mode_rc=1)
    monkeypatch.setattr(os, "isatty", lambda _fd: False)
    monkeypatch.setattr(mod.sys, "stdin", _FakeStdinWithFd())
    assert mod.stdin_is_interactive() is True


@pytest.mark.parametrize(
    "bad_handle",
    [None, 0, ctypes.c_void_p(-1).value],
    ids=["null-handle", "zero-handle", "invalid-handle"],
)
def test_windows_stdin_console_check_false_without_a_stdin_handle(
    monkeypatch, bad_handle
):
    """NULL/INVALID stdin handles are never treated as a console."""
    from scripts import issuer_key_passphrase as mod

    _patch_windows_console(monkeypatch, std_handle=bad_handle, console_mode_rc=1)
    assert mod._windows_stdin_is_console() is False


def test_windows_stdin_console_check_fails_closed_without_kernel32(monkeypatch):
    """No console API (non-Windows host, DLL load failure): fail closed."""
    import ctypes

    def no_windll(name: str, use_last_error: bool = False) -> None:
        raise OSError("kernel32 unavailable")

    monkeypatch.setattr(ctypes, "WinDLL", no_windll, raising=False)
    from scripts import issuer_key_passphrase as mod

    assert mod._windows_stdin_is_console() is False


def test_ignored_passphrase_env_warns_on_presence_alone(monkeypatch, capsys):
    """Ignored-env warning keys on presence only; the value is never read.

    A value-less (empty) assignment still draws the fixed warning, once per
    process. Presence-only keeps password data out of the log path (CodeQL
    high, PR #2379).
    """
    from scripts import issuer_key_passphrase as mod

    monkeypatch.setattr(mod, "_ignored_env_warned", False)
    monkeypatch.setenv(mod.PASSPHRASE_ENV_IGNORED, "")
    # Generated at runtime (never a literal PEM block in the source tree) so the
    # gitleaks private-key rule has nothing to flag in the committed file.
    private_key, _ = generate_test_signing_key()
    clean_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    assert mod.resolve_issuer_key_password(clean_pem, prompt="p: ") is None
    assert mod.resolve_issuer_key_password(clean_pem, prompt="p: ") is None
    err = capsys.readouterr().err
    assert "license issuer private key password env var is set and ignored" in err
    assert err.count("is set and ignored") == 1

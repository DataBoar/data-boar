"""D2239-9: the manifest signer takes the key passphrase only at the terminal (#2239)."""

from __future__ import annotations

import json
import subprocess
import sys
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

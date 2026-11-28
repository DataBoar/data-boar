"""
QA local license issuer contract (enforcement wave PR2).

The env bypass was removed (#719); ``scripts/issue_dev_license_jwt.py`` is the
only QA path for ``licensing.mode: enforced``. Contract:

- default expiry **60 days** (short-lived);
- default tier **enterprise**;
- default ``dbmfp`` binding to the issuing machine (``--dbmfp auto``);
- bound license validates on the bound machine and dies elsewhere.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard
from core.licensing import reset_license_guard_for_tests
from core.licensing.verify import CLAIM_MLDSA_SIG
from tests.hybrid_license_fixture import (
    pin_test_mldsa_anchor,
    test_mldsa_public_pem as dev_mldsa_public_pem,
)
from tests.license_verify_pin import pin_embedded_ed25519_pem
from tests.tty_session import (
    PTY_AVAILABLE,
    PTY_SKIP_REASON,
    env_without_ci,
    run_under_pty,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUER = REPO_ROOT / "scripts" / "issue_dev_license_jwt.py"


@pytest.fixture
def keypair(tmp_path):
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    priv_path = tmp_path / "priv.pem"
    priv_path.write_bytes(priv_pem)
    return priv_path, pub_pem.decode("ascii"), priv.public_key()


@pytest.fixture
def encrypted_keypair(tmp_path):
    """Ed25519 private key in an AES-encrypted PKCS#8 PEM (#910)."""
    passphrase = "qa-test-passphrase"  # noqa: S105 - test-only, not a real secret
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            passphrase.encode("utf-8")
        ),
    )
    priv_path = tmp_path / "priv-enc.pem"
    priv_path.write_bytes(priv_pem)
    return priv_path, priv.public_key(), passphrase


@pytest.fixture(autouse=True)
def _clean_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()
    os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)


def _dev_mldsa_file(tmp_path: Path) -> Path:
    from cryptography.hazmat.primitives import serialization
    from tests.hybrid_license_fixture import test_mldsa_private

    pem = test_mldsa_private().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path = tmp_path / "dev-mldsa.pem"
    path.write_bytes(pem)
    return path


def _issuer_env(tmp_path: Path, **extra: str) -> dict[str, str]:
    env = dict(os.environ)
    env["DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_PEM_FILE"] = str(
        _dev_mldsa_file(tmp_path)
    )
    env.update(extra)
    return env


def _run_issuer(*argv: str, env: dict | None = None) -> str:
    proc = _run_issuer_proc(*argv, env=env)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _run_issuer_proc(
    *argv: str, env: dict | None = None
) -> subprocess.CompletedProcess[str]:
    # stdin=DEVNULL makes sys.stdin.isatty() deterministically False in the child,
    # so the encrypted-key-without-env path exits instead of blocking on getpass.
    return subprocess.run(
        [sys.executable, str(ISSUER), *argv],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
        env=env,
        stdin=subprocess.DEVNULL,
    )


def test_issuer_defaults_60d_enterprise_machine_bound(keypair):
    priv_path, _pub_pem, pub_key = keypair
    token = _run_issuer("--private-key-pem-file", str(priv_path))
    claims = jwt.decode(token, pub_key, algorithms=["EdDSA"])
    assert claims["dbtier"] == "enterprise"
    # 60-day default expiry (allow scheduling slack of a few minutes).
    lifetime_days = (claims["exp"] - claims["iat"]) / 86400
    assert 59.9 <= lifetime_days <= 60.1
    # Machine-bound by default to the issuing machine.
    assert claims["dbmfp"] == compute_machine_fingerprint()
    assert isinstance(claims[CLAIM_MLDSA_SIG], str) and claims[CLAIM_MLDSA_SIG]


def test_issuer_show_machine_fingerprint(keypair):
    out = _run_issuer("--show-machine-fingerprint")
    assert out == compute_machine_fingerprint()


def test_issuer_dbmfp_none_unbound(keypair):
    priv_path, _pub_pem, pub_key = keypair
    token = _run_issuer("--private-key-pem-file", str(priv_path), "--dbmfp", "none")
    claims = jwt.decode(token, pub_key, algorithms=["EdDSA"])
    assert "dbmfp" not in claims


def test_bound_license_valid_on_this_machine(keypair, tmp_path):
    priv_path, pub_pem, _pub_key = keypair
    lic = tmp_path / "qa.lic"
    _run_issuer(
        "--private-key-pem-file",
        str(priv_path),
        "--out",
        str(lic),
        env=_issuer_env(tmp_path),
    )
    pin_embedded_ed25519_pem(pub_pem)
    pin_test_mldsa_anchor(dev_mldsa_public_pem())
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "VALID", g.context.detail
    assert "hybrid_mldsa65_verified" in g.context.detail
    assert g.context.dbtier == "enterprise"
    assert g.allows_scan() is True


def test_dev_token_without_claim_is_rejected(keypair, tmp_path):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    priv_path, pub_pem, pub_key = keypair
    token = _run_issuer(
        "--private-key-pem-file",
        str(priv_path),
        env=_issuer_env(tmp_path),
    )
    claims = jwt.decode(
        token, pub_key, algorithms=["EdDSA"], options={"verify_exp": False}
    )
    claims.pop(CLAIM_MLDSA_SIG)
    ed_private = load_pem_private_key(priv_path.read_bytes(), password=None)
    bare = jwt.encode(claims, ed_private, algorithm="EdDSA")
    lic = tmp_path / "bare.lic"
    lic.write_text(bare, encoding="utf-8")
    pin_embedded_ed25519_pem(pub_pem)
    pin_test_mldsa_anchor(dev_mldsa_public_pem())
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "INVALID"
    assert g.context.detail == "hybrid_claim_required"


def test_bound_license_rejected_on_other_machine(keypair, tmp_path):
    priv_path, pub_pem, _pub_key = keypair
    lic = tmp_path / "qa.lic"
    _run_issuer(
        "--private-key-pem-file",
        str(priv_path),
        "--dbmfp",
        "f" * 64,  # some other machine's fingerprint
        "--out",
        str(lic),
        env=_issuer_env(tmp_path),
    )
    pin_embedded_ed25519_pem(pub_pem)
    pin_test_mldsa_anchor(dev_mldsa_public_pem())
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "MACHINE_MISMATCH"
    assert g.allows_scan() is False


def _maestro_handler_licensing_matrix() -> Path | None:
    """DataBoar/maestro handlers/Handle-LicensingMatrix.ps1 (spinout #8)."""
    env = (os.environ.get("MAESTRO_ROOT") or "").strip()
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))
    parent = REPO_ROOT.parent
    candidates.extend([parent / "maestro", parent / "Maestro"])
    for root in candidates:
        path = root / "handlers" / "Handle-LicensingMatrix.ps1"
        if path.is_file():
            return path
    return None


def test_maestro_handler_issues_60d_machine_bound():
    """Handle-LicensingMatrix.ps1 passes --days 60 and --dbmfp auto (#719)."""
    path = _maestro_handler_licensing_matrix()
    if path is None:
        pytest.skip(
            "DataBoar/maestro clone not found (set MAESTRO_ROOT or sibling ../maestro)"
        )
    src = path.read_text(encoding="utf-8")
    assert "--days 60" in src
    assert "--dbmfp auto" in src


PASSWORD_ENV = "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD"


_TTY_REQUIRED = "run this command in an interactive terminal"
_IGNORED_WARNING = (
    "Warning: license issuer private key password env var is set and ignored: "
    "the signing key passphrase is read only from the terminal prompt."
)


def test_d2239_1_password_env_is_ignored_and_no_tty_fails_closed(
    encrypted_keypair, tmp_path
):
    """D2239-1: the right passphrase in the env issues nothing without a terminal.

    Replaces ``test_issuer_encrypted_key_with_password_env`` (#910), which
    asserted the env path issued a token (#2239 removes that path).
    """
    priv_path, _pub_key, passphrase = encrypted_keypair
    env = _issuer_env(tmp_path, **{PASSWORD_ENV: passphrase})
    proc = _run_issuer_proc("--private-key-pem-file", str(priv_path), env=env)
    assert proc.returncode == 1
    assert _TTY_REQUIRED in proc.stderr
    assert proc.stdout.strip() == ""
    assert "Traceback" not in proc.stderr


def test_d2239_2_password_env_warns_and_never_echoes_the_value(
    encrypted_keypair, tmp_path
):
    """D2239-2: the env var draws the fixed warning; its value never shows up."""
    priv_path, _pub_key, passphrase = encrypted_keypair
    env = _issuer_env(tmp_path, **{PASSWORD_ENV: passphrase})
    proc = _run_issuer_proc("--private-key-pem-file", str(priv_path), env=env)
    assert _IGNORED_WARNING in proc.stderr
    assert passphrase not in proc.stderr
    assert passphrase not in proc.stdout


def test_d2239_4_clean_key_with_password_env_issues_and_warns(keypair, tmp_path):
    """D2239-4: an unencrypted key still issues; the stray env var is reported."""
    priv_path, _pub_pem, pub_key = keypair
    env = _issuer_env(tmp_path, **{PASSWORD_ENV: "any-value"})
    proc = _run_issuer_proc("--private-key-pem-file", str(priv_path), env=env)
    assert proc.returncode == 0, proc.stderr
    claims = jwt.decode(proc.stdout.strip(), pub_key, algorithms=["EdDSA"])
    assert claims["dbtier"] == "enterprise"
    assert _IGNORED_WARNING in proc.stderr
    assert "any-value" not in proc.stderr


def test_issuer_clean_key_without_password_env(keypair):
    """Backward-compat (#910): unencrypted key + no password env still issues."""
    priv_path, _pub_pem, pub_key = keypair
    env = {k: v for k, v in os.environ.items() if k != PASSWORD_ENV}
    token = _run_issuer("--private-key-pem-file", str(priv_path), env=env)
    claims = jwt.decode(token, pub_key, algorithms=["EdDSA"])
    assert claims["dbtier"] == "enterprise"


def test_d2239_3_encrypted_key_without_tty_exits_without_naming_the_env(
    encrypted_keypair, tmp_path
):
    """D2239-3: no env, no TTY: exit 1, no traceback, and no env var is suggested.

    Replaces ``test_issuer_encrypted_key_without_env_or_tty_exits_actionably``
    (#910), which required the env var name in the message.
    """
    priv_path, _pub_key, _passphrase = encrypted_keypair
    env = {k: v for k, v in _issuer_env(tmp_path).items() if k != PASSWORD_ENV}
    proc = _run_issuer_proc("--private-key-pem-file", str(priv_path), env=env)
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert PASSWORD_ENV not in proc.stderr
    assert _TTY_REQUIRED in proc.stderr


# --- #2239: signing-key passphrase only from the terminal prompt ------------------------------

_GETPASS_PROBE = (
    "import getpass, sys\n"
    "value = getpass.getpass('probe passphrase: ')\n"
    "sys.stdout.write('GOT:' + value + '\\n')\n"
)


@pytest.mark.skipif(not PTY_AVAILABLE, reason=PTY_SKIP_REASON)
def test_d2239_0_getpass_reads_tty_and_falls_back_to_a_pipe(tmp_path):
    """D2239-0 (premise PR-1): getpass reads the pty; without a TTY it reads the pipe.

    The pipe fallback is why the issuer must check for a TTY *before* getpass:
    otherwise a passphrase piped on stdin would be accepted.
    """
    probe = tmp_path / "getpass_probe.py"
    probe.write_text(_GETPASS_PROBE, encoding="utf-8")
    on_tty = run_under_pty(
        [sys.executable, str(probe)],
        env=env_without_ci(),
        cwd=str(tmp_path),
        prompt_marker=b"probe passphrase:",
        typed="from-the-terminal",
    )
    assert on_tty.timed_out is False
    assert on_tty.exit_code == 0, on_tty.output
    assert "GOT:from-the-terminal" in on_tty.output

    piped = subprocess.run(
        [sys.executable, str(probe)],
        input="from-the-pipe\n",
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=60,
        env=env_without_ci(),
        start_new_session=True,
    )
    assert piped.returncode == 0, piped.stderr
    assert "GOT:from-the-pipe" in piped.stdout
    assert "GetPassWarning" in piped.stderr


def _issuer_on_tty(
    priv_path: Path, tmp_path: Path, typed: str | None
) -> tuple[object, Path]:
    lic = tmp_path / "tty.lic"
    env = {
        k: v
        for k, v in env_without_ci(
            {
                "DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_PEM_FILE": str(
                    _dev_mldsa_file(tmp_path)
                )
            }
        ).items()
        if k != PASSWORD_ENV
    }
    result = run_under_pty(
        [
            sys.executable,
            str(ISSUER),
            "--private-key-pem-file",
            str(priv_path),
            "--out",
            str(lic),
        ],
        env=env,
        cwd=str(REPO_ROOT),
        prompt_marker=b"passphrase:",
        typed=typed,
    )
    return result, lic


@pytest.mark.skipif(not PTY_AVAILABLE, reason=PTY_SKIP_REASON)
def test_d2239_5_passphrase_typed_on_the_tty_issues_a_valid_token(
    encrypted_keypair, tmp_path
):
    """D2239-5: the passphrase typed at the terminal unlocks the key."""
    priv_path, pub_key, passphrase = encrypted_keypair
    result, lic = _issuer_on_tty(priv_path, tmp_path, passphrase)
    assert result.timed_out is False
    assert result.prompted is True
    assert result.exit_code == 0, result.output
    claims = jwt.decode(
        lic.read_text(encoding="utf-8").strip(), pub_key, algorithms=["EdDSA"]
    )
    assert claims["dbtier"] == "enterprise"


@pytest.mark.skipif(not PTY_AVAILABLE, reason=PTY_SKIP_REASON)
def test_d2239_6_wrong_passphrase_on_the_tty_exits_without_traceback(
    encrypted_keypair, tmp_path
):
    """D2239-6: a wrong passphrase is a fixed message and exit 1, never a traceback."""
    priv_path, _pub_key, _passphrase = encrypted_keypair
    result, lic = _issuer_on_tty(priv_path, tmp_path, "not-the-passphrase")
    assert result.timed_out is False
    assert result.exit_code == 1
    assert "Could not decrypt the signing key" in result.output
    assert "Traceback" not in result.output
    assert not lic.exists()


@pytest.mark.skipif(not PTY_AVAILABLE, reason=PTY_SKIP_REASON)
def test_d2239_7_empty_passphrase_on_the_tty_aborts(encrypted_keypair, tmp_path):
    """D2239-7: an empty answer at the prompt aborts signing."""
    priv_path, _pub_key, _passphrase = encrypted_keypair
    result, lic = _issuer_on_tty(priv_path, tmp_path, "")
    assert result.timed_out is False
    assert result.exit_code == 1
    assert "Empty passphrase" in result.output
    assert "Traceback" not in result.output
    assert not lic.exists()


def test_d2239_8_typed_passphrase_is_not_stripped(encrypted_keypair, monkeypatch):
    """D2239-8: surrounding spaces are part of the passphrase (no silent strip, P11)."""
    from scripts import issuer_key_passphrase as mod

    priv_path, _pub_key, _passphrase = encrypted_keypair
    prompts: list[str] = []

    def fake_getpass(prompt: str = "") -> str:
        prompts.append(prompt)
        return " a b "

    monkeypatch.delenv(PASSWORD_ENV, raising=False)
    monkeypatch.setattr(mod, "getpass", fake_getpass, raising=False)
    monkeypatch.setattr(mod, "stdin_is_interactive", lambda: True)
    pem = priv_path.read_text(encoding="utf-8")
    assert mod.resolve_issuer_key_password(pem, prompt="p: ") == b" a b "
    assert prompts == ["p: "]

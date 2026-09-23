"""Hybrid Ed25519 + ML-DSA license JWT verify (#48 / license-studio parity)."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard
from core.licensing.verify import (
    CLAIM_MLDSA_SIG,
    decode_license_jwt,
    decode_license_jwt_hybrid,
    load_ed25519_public_key_pem,
    load_mldsa65_public_key_pem,
)

_FIXTURE_DIR = Path(__file__).resolve().parent / "data" / "licensing_hybrid"
_TOKEN_PATH = _FIXTURE_DIR / "hybrid_hostile.jwt"
_ED_PUB_PATH = _FIXTURE_DIR / "ed25519-pub.pem"
_MLDSA_PUB_PATH = _FIXTURE_DIR / "mldsa-pub.pem"

pytestmark = pytest.mark.skipif(
    not backend.mldsa_supported(),
    reason="OpenSSL backend has no ML-DSA support",
)


@pytest.fixture(scope="module")
def hybrid_token() -> str:
    return _TOKEN_PATH.read_text(encoding="utf-8").strip()


@pytest.fixture(scope="module")
def ed25519_pub(hybrid_token: str):
    return load_ed25519_public_key_pem(_ED_PUB_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mldsa_pub():
    return load_mldsa65_public_key_pem(_MLDSA_PUB_PATH.read_text(encoding="utf-8"))


def test_decode_license_jwt_ignores_extra_dbmldsa_sig_claim(
    hybrid_token: str, ed25519_pub
) -> None:
    """Retrocompat: Ed25519-only path accepts JWT with unknown/extra ``dbmldsa_sig`` claim."""
    claims = decode_license_jwt(hybrid_token, ed25519_pub)
    assert claims["sub"].startswith("hostile")
    assert CLAIM_MLDSA_SIG in claims
    assert isinstance(claims[CLAIM_MLDSA_SIG], str)
    assert len(claims[CLAIM_MLDSA_SIG]) > 100


def test_decode_license_jwt_hybrid_verifies_with_mldsa_key(
    hybrid_token: str, ed25519_pub, mldsa_pub
) -> None:
    claims = decode_license_jwt_hybrid(hybrid_token, ed25519_pub, mldsa_pub)
    assert "grants" in claims
    assert claims["dbmfp"] == "fp-fixture-48"


def test_decode_license_jwt_hybrid_fail_closed_without_mldsa_key(
    hybrid_token: str, ed25519_pub
) -> None:
    with pytest.raises(ValueError, match="ML-DSA public key required"):
        decode_license_jwt_hybrid(hybrid_token, ed25519_pub, mldsa_pub=None)


def test_decode_license_jwt_hybrid_rejects_corrupted_mldsa_sig(
    ed25519_pub, mldsa_pub
) -> None:
    bad_token = (
        (_FIXTURE_DIR / "hybrid_hostile_bad_mldsa.jwt")
        .read_text(encoding="utf-8")
        .strip()
    )
    with pytest.raises(InvalidSignature):
        decode_license_jwt_hybrid(bad_token, ed25519_pub, mldsa_pub)


def _pem_mldsa_public(private_key: MLDSA65PrivateKey) -> str:
    raw = private_key.public_key().public_bytes_raw()
    body = base64.b64encode(raw).decode("ascii")
    lines = [body[i : i + 64] for i in range(0, len(body), 64)]
    return (
        "-----BEGIN ML-DSA-65 PUBLIC KEY-----\n"
        + "\n".join(lines)
        + "\n-----END ML-DSA-65 PUBLIC KEY-----\n"
    )


def _issue_hybrid_token(
    ed_private: Ed25519PrivateKey,
    ml_private: MLDSA65PrivateKey,
    *,
    corrupt_mldsa: bool = False,
) -> str:
    """Machine-bound hybrid JWT using the same ML-DSA message as verify.py."""
    from core.licensing.verify import _mldsa_payload_json_without_sig

    now = datetime.now(timezone.utc)
    claims = {
        "sub": "hybrid-guard-1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp()),
        "dbcid": "lab-dev",
        "dbcname": "Lab",
        "dbenv": "qa",
        "dbissuer": "test",
        "dbkid": "dev",
        "dbtier": "enterprise",
        "dbmfp": compute_machine_fingerprint(),
    }
    unsigned = jwt.encode(claims, ed_private, algorithm="EdDSA")
    header_b64 = unsigned.split(".", 1)[0]
    payload_json = _mldsa_payload_json_without_sig(claims)
    payload_b64 = (
        base64.urlsafe_b64encode(payload_json.encode("utf-8"))
        .decode("ascii")
        .rstrip("=")
    )
    sig = ml_private.sign(f"{header_b64}.{payload_b64}".encode("utf-8"))
    sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    if corrupt_mldsa:
        sig_b64 = "A" * len(sig_b64)
    claims[CLAIM_MLDSA_SIG] = sig_b64
    token = jwt.encode(claims, ed_private, algorithm="EdDSA")
    if token.split(".", 1)[0] != header_b64:
        raise AssertionError("JWT header changed after attaching dbmldsa_sig")
    return token


def test_license_guard_verifies_dbmldsa_sig_when_present(tmp_path, monkeypatch) -> None:
    ed_private = Ed25519PrivateKey.generate()
    ml_private = MLDSA65PrivateKey.generate()
    token = _issue_hybrid_token(ed_private, ml_private)
    lic = tmp_path / "hybrid.lic"
    lic.write_text(token, encoding="utf-8")
    ed_pem = (
        ed_private.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )
    ml_pem = _pem_mldsa_public(ml_private)
    monkeypatch.setenv("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", ed_pem)
    monkeypatch.setenv("DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PEM", ml_pem)
    monkeypatch.delenv("DATA_BOAR_LICENSE_PATH", raising=False)
    monkeypatch.delenv("DATA_BOAR_EXPECTED_BUILD_DIGEST", raising=False)

    guard = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert guard.context.state == "VALID"
    assert guard.context.detail == "hybrid_mldsa65_verified"

    bad = _issue_hybrid_token(ed_private, ml_private, corrupt_mldsa=True)
    bad_path = tmp_path / "hybrid-bad.lic"
    bad_path.write_text(bad, encoding="utf-8")
    denied = LicenseGuard(
        {"licensing": {"mode": "enforced", "license_path": str(bad_path)}}
    )
    assert denied.context.state == "INVALID"
    assert denied.context.detail == "mldsa_signature_invalid"

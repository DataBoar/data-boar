"""Regression: present-but-invalid ``dbmldsa_sig`` must fail closed (#1996).

Covers the library (``decode_license_jwt_hybrid``) and the real enforcement path
(``LicenseGuard``), which must not route a present-but-invalid claim to the
Ed25519-only verifier.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard, _token_has_mldsa_claim
from core.licensing.verify import CLAIM_MLDSA_SIG, decode_license_jwt_hybrid

_ABSENT = object()

_INVALID_CLAIM_VALUES = [None, "", 1, True, {"sig": "nope"}]

_KEY_ENV_VARS = (
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_PATH",
    "DATA_BOAR_EXPECTED_BUILD_DIGEST",
)


def _base_claims() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "sub": "hybrid-claim-presence",
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


def _token_with_mldsa_claim(ed_private: Ed25519PrivateKey, mldsa_value) -> str:
    claims = _base_claims()
    if mldsa_value is not _ABSENT:
        claims[CLAIM_MLDSA_SIG] = mldsa_value
    return jwt.encode(claims, ed_private, algorithm="EdDSA")


def _ed_public_pem(ed_private: Ed25519PrivateKey) -> str:
    return (
        ed_private.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )


def _mldsa_public_pem() -> str:
    from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey

    raw = MLDSA65PrivateKey.generate().public_key().public_bytes_raw()
    body = base64.b64encode(raw).decode("ascii")
    lines = [body[i : i + 64] for i in range(0, len(body), 64)]
    return (
        "-----BEGIN ML-DSA-65 PUBLIC KEY-----\n"
        + "\n".join(lines)
        + "\n-----END ML-DSA-65 PUBLIC KEY-----\n"
    )


@pytest.fixture
def ed25519_pub():
    private = Ed25519PrivateKey.generate()
    return private, private.public_key()


def _guard_for(tmp_path, monkeypatch, token: str, ed_pem: str, mldsa_pem: str):
    for name in _KEY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        "core.licensing.guard.load_embedded_official_public_key_pem",
        lambda: ed_pem,
    )
    monkeypatch.setattr(
        "core.licensing.trust_anchor.load_embedded_mldsa_anchor_pem",
        lambda: mldsa_pem,
    )
    lic = tmp_path / "claim.lic"
    lic.write_text(token, encoding="utf-8")
    return LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})


# --- library: decode_license_jwt_hybrid -------------------------------------


def test_decode_license_jwt_hybrid_absent_mldsa_claim_ok(ed25519_pub) -> None:
    ed_private, ed_pub = ed25519_pub
    token = _token_with_mldsa_claim(ed_private, _ABSENT)
    claims = decode_license_jwt_hybrid(token, ed_pub, mldsa_pub=None)
    assert CLAIM_MLDSA_SIG not in claims
    assert claims["sub"] == "hybrid-claim-presence"


def test_decode_license_jwt_hybrid_null_claim_requires_mldsa_key(ed25519_pub) -> None:
    ed_private, ed_pub = ed25519_pub
    token = _token_with_mldsa_claim(ed_private, None)
    with pytest.raises(ValueError, match="ML-DSA public key required"):
        decode_license_jwt_hybrid(token, ed_pub, mldsa_pub=None)


@pytest.mark.parametrize("bad_value", _INVALID_CLAIM_VALUES)
def test_decode_license_jwt_hybrid_rejects_present_invalid_mldsa_claim(
    ed25519_pub, bad_value
) -> None:
    ed_private, ed_pub = ed25519_pub
    token = _token_with_mldsa_claim(ed_private, bad_value)
    with pytest.raises(ValueError, match=CLAIM_MLDSA_SIG):
        decode_license_jwt_hybrid(token, ed_pub, mldsa_pub=MagicMock())


# --- guard: path selection + real enforcement --------------------------------


@pytest.mark.parametrize("bad_value", _INVALID_CLAIM_VALUES)
def test_token_has_mldsa_claim_true_for_any_present_value(
    ed25519_pub, bad_value
) -> None:
    ed_private, _ = ed25519_pub
    assert _token_has_mldsa_claim(_token_with_mldsa_claim(ed_private, bad_value))


def test_token_has_mldsa_claim_false_when_absent(ed25519_pub) -> None:
    ed_private, _ = ed25519_pub
    assert not _token_has_mldsa_claim(_token_with_mldsa_claim(ed_private, _ABSENT))


def test_license_guard_absent_mldsa_claim_is_valid(
    tmp_path, monkeypatch, ed25519_pub
) -> None:
    ed_private, _ = ed25519_pub
    token = _token_with_mldsa_claim(ed_private, _ABSENT)
    guard = _guard_for(tmp_path, monkeypatch, token, _ed_public_pem(ed_private), "")
    assert guard.context.state == "VALID"


@pytest.mark.parametrize("bad_value", _INVALID_CLAIM_VALUES)
def test_license_guard_rejects_invalid_mldsa_claim_without_anchor(
    tmp_path, monkeypatch, ed25519_pub, bad_value
) -> None:
    ed_private, _ = ed25519_pub
    token = _token_with_mldsa_claim(ed_private, bad_value)
    guard = _guard_for(tmp_path, monkeypatch, token, _ed_public_pem(ed_private), "")
    assert guard.context.state == "INVALID"


@pytest.mark.skipif(
    not backend.mldsa_supported(),
    reason="OpenSSL backend has no ML-DSA support",
)
@pytest.mark.parametrize("bad_value", _INVALID_CLAIM_VALUES)
def test_license_guard_rejects_invalid_mldsa_claim_with_anchor(
    tmp_path, monkeypatch, ed25519_pub, bad_value
) -> None:
    ed_private, _ = ed25519_pub
    token = _token_with_mldsa_claim(ed_private, bad_value)
    guard = _guard_for(
        tmp_path,
        monkeypatch,
        token,
        _ed_public_pem(ed_private),
        _mldsa_public_pem(),
    )
    assert guard.context.state == "INVALID"

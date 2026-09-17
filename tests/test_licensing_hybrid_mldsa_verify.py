"""Hybrid Ed25519 + ML-DSA license JWT verify (#48 / license-studio parity)."""

from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends.openssl.backend import backend

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

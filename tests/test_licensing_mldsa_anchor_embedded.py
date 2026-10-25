"""Packaged ML-DSA-65 trust anchor (#2042 / #1462).

Hybrid ``dbmldsa_sig`` verification stays optional; this file only pins the
embedded public anchor bytes and loader behavior.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing import trust_anchor
from core.licensing.verify import (
    CLAIM_MLDSA_SIG,
    decode_license_jwt,
    load_mldsa65_public_key_pem,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_PEM = REPO_ROOT / "core" / "licensing" / "license-mldsa-pub-v1.pem"

# Canonical SHA-256 is over UTF-8 bytes with LF line endings (2717 bytes on disk).
CANONICAL_ANCHOR_SHA256 = (
    "37faef8ff167cf01a0fc6a2bc8b7cfcac6bfe5651360051b1eb00a0a60fa85b8"
)
MLDSA65_PUBLIC_KEY_RAW_BYTES = 1952

pytestmark = pytest.mark.skipif(
    not backend.mldsa_supported(),
    reason="OpenSSL backend has no ML-DSA support",
)


def _sha256_normalized_pem_text(text: str) -> str:
    # Windows checkouts may use CRLF; the canonical digest uses LF-only bytes.
    normalized = text.replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def test_committed_mldsa_anchor_pem_matches_canonical_sha256() -> None:
    assert ANCHOR_PEM.is_file(), "missing packaged anchor PEM in source tree"
    text = ANCHOR_PEM.read_text(encoding="utf-8")
    assert text.strip().startswith("-----BEGIN ML-DSA-65 PUBLIC KEY-----")
    assert _sha256_normalized_pem_text(text) == CANONICAL_ANCHOR_SHA256
    assert "PRIVATE" not in text.upper()


def test_load_embedded_mldsa_anchor_pem_matches_committed_file() -> None:
    loaded = trust_anchor.load_embedded_mldsa_anchor_pem()
    assert loaded is not None
    committed = ANCHOR_PEM.read_text(encoding="utf-8").strip()
    assert loaded == committed
    # ``load_embedded_mldsa_anchor_pem`` strips whitespace; canonical SHA-256 is
    # over the on-disk file bytes (see ``test_committed_mldsa_anchor_pem_*``).


def test_load_embedded_mldsa_anchor_pem_none_when_resource_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        trust_anchor,
        "EMBEDDED_MLDSA_ANCHOR_RESOURCE",
        "license-mldsa-pub-v1-missing.pem",
    )
    assert trust_anchor.load_embedded_mldsa_anchor_pem() is None


def test_embedded_mldsa_anchor_loads_as_mldsa65_public_key() -> None:
    pem = trust_anchor.load_embedded_mldsa_anchor_pem()
    assert pem is not None
    key = load_mldsa65_public_key_pem(pem)
    raw = key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    assert len(raw) == MLDSA65_PUBLIC_KEY_RAW_BYTES


def test_decode_license_jwt_without_dbmldsa_claim_is_ed25519_only() -> None:
    """Unchanged semantics: no hybrid claim → Ed25519 path only (no ML-DSA key)."""
    priv = Ed25519PrivateKey.generate()
    token = jwt.encode(
        {"sub": "ed-only", "exp": 9_999_999_999},
        priv,
        algorithm="EdDSA",
    )
    assert CLAIM_MLDSA_SIG not in jwt.decode(token, options={"verify_signature": False})
    claims = decode_license_jwt(token, priv.public_key())
    assert claims["sub"] == "ed-only"
    assert CLAIM_MLDSA_SIG not in claims


def test_embedded_mldsa_pem_has_no_private_block() -> None:
    pem = trust_anchor.load_embedded_mldsa_anchor_pem()
    assert pem is not None
    assert not re.search(r"BEGIN\s+.*PRIVATE", pem, flags=re.IGNORECASE)

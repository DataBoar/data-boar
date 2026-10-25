"""Test-only ML-DSA key so enforced licenses can carry a required dbmldsa_sig.

The private key is generated in the test process. It is never the org anchor
and never written into the repository.
"""

from __future__ import annotations

import base64
import json

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey

from core.licensing.verify import CLAIM_MLDSA_SIG, _mldsa_payload_json_without_sig

_TEST_MLDSA: MLDSA65PrivateKey | None = None


def test_mldsa_private() -> MLDSA65PrivateKey:
    global _TEST_MLDSA
    if _TEST_MLDSA is None:
        _TEST_MLDSA = MLDSA65PrivateKey.generate()
    return _TEST_MLDSA


def test_mldsa_public_pem() -> str:
    raw = test_mldsa_private().public_key().public_bytes_raw()
    body = base64.b64encode(raw).decode("ascii")
    lines = [body[i : i + 64] for i in range(0, len(body), 64)]
    return (
        "-----BEGIN ML-DSA-65 PUBLIC KEY-----\n"
        + "\n".join(lines)
        + "\n-----END ML-DSA-65 PUBLIC KEY-----\n"
    )


def pin_test_mldsa_anchor(pem: str | None = None) -> None:
    import core.licensing.trust_anchor as trust_anchor

    pinned = pem if pem is not None else test_mldsa_public_pem()
    trust_anchor.load_embedded_mldsa_anchor_pem = lambda: pinned


def seal_enforced_test_token(
    ed_private: Ed25519PrivateKey,
    token: str,
    *,
    mldsa_private: MLDSA65PrivateKey | None = None,
    pin: bool = True,
) -> str:
    """Return ``token`` with a valid test ``dbmldsa_sig``.

    ``pin=False`` leaves the ML-DSA loader alone (rotation tests already
    installed the anchor the attestation must verify against).
    """
    signer = mldsa_private or test_mldsa_private()
    if pin:
        if mldsa_private is None:
            pin_test_mldsa_anchor()
        else:
            raw = signer.public_key().public_bytes_raw()
            body = base64.b64encode(raw).decode("ascii")
            lines = [body[i : i + 64] for i in range(0, len(body), 64)]
            pin_test_mldsa_anchor(
                "-----BEGIN ML-DSA-65 PUBLIC KEY-----\n"
                + "\n".join(lines)
                + "\n-----END ML-DSA-65 PUBLIC KEY-----\n"
            )
    payload_b64 = token.split(".")[1]
    pad = "=" * (-len(payload_b64) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
    if not isinstance(claims, dict):
        raise AssertionError("test token payload is not an object")
    if CLAIM_MLDSA_SIG in claims:
        return token
    header_b64 = token.split(".", 1)[0]
    payload_json = _mldsa_payload_json_without_sig(claims)
    signed_payload_b64 = (
        base64.urlsafe_b64encode(payload_json.encode("utf-8"))
        .decode("ascii")
        .rstrip("=")
    )
    sig = signer.sign(f"{header_b64}.{signed_payload_b64}".encode("utf-8"))
    claims[CLAIM_MLDSA_SIG] = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    sealed = jwt.encode(claims, ed_private, algorithm="EdDSA")
    if sealed.split(".", 1)[0] != header_b64:
        raise AssertionError("JWT header changed after attaching dbmldsa_sig")
    return sealed

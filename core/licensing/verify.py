"""
Verify signed license JWT (Ed25519 / EdDSA) and optional revocation list.
"""

from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# pyjwt[crypto] uses cryptography for EdDSA


def load_ed25519_public_key_pem(pem_data: str) -> Any:
    """Load Ed25519 public key from PEM string."""
    return serialization.load_pem_public_key(
        pem_data.encode("utf-8"),
        backend=default_backend(),
    )


def load_public_key_from_path(path: str) -> Any:
    p = Path(path)
    pem = p.read_text(encoding="utf-8")
    return load_ed25519_public_key_pem(pem)


def decode_license_jwt(token: str, public_key: Any) -> dict[str, Any]:
    """
    Verify signature and return claims. Raises jwt.PyJWTError on failure.

    ``exp`` / ``dbgrace`` time windows are evaluated in ``LicenseGuard`` (VALID →
    GRACE → EXPIRED). PyJWT must not reject an expired signature before that
    chain runs — otherwise GRACE is unreachable (#1212).
    """
    return jwt.decode(
        token,
        public_key,
        algorithms=["EdDSA"],
        options={
            "verify_aud": False,
            "verify_exp": False,
            "require": ["exp", "sub"],
        },
    )


class RevocationListUnverified(Exception):
    """Configured revocation list could not be verified (fail-closed).

    Mirrors license-studio ``revoke.Verify``: never a silent empty set.
    ``reason`` is a stable token for ``LicenseContext.detail``.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def load_revocation_ids(path: str | None, public_key: Any | None = None) -> set[str]:
    """Return revoked ids, or empty if no path is configured (opt-in).

    When ``path`` is set, fail closed: missing JSON, missing ``path+".sig"``,
    malformed signature, or Ed25519 mismatch against ``public_key`` raise
    ``RevocationListUnverified``. Signature covers the **exact bytes on disk**
    of the JSON file (license-studio#26 / data-boar#1753).
    """
    if not path:
        return set()
    if public_key is None:
        raise RevocationListUnverified("missing_public_key")
    if not isinstance(public_key, Ed25519PublicKey):
        raise RevocationListUnverified("public_key_not_ed25519")

    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as e:
        raise RevocationListUnverified("missing_list") from e

    sig_path = Path(str(p) + ".sig")
    try:
        sig_text = sig_path.read_text(encoding="utf-8")
    except OSError as e:
        raise RevocationListUnverified("missing_signature") from e

    try:
        sig = base64.b64decode(sig_text.strip(), validate=True)
    except (ValueError, binascii.Error) as e:
        raise RevocationListUnverified("malformed_signature") from e

    if not sig:
        raise RevocationListUnverified("malformed_signature")

    try:
        public_key.verify(sig, raw)
    except InvalidSignature as e:
        raise RevocationListUnverified("bad_signature") from e

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RevocationListUnverified("malformed_list") from e
    if not isinstance(data, dict):
        raise RevocationListUnverified("malformed_list")
    ids = data.get("revoked_license_ids")
    if ids is None:
        return set()
    if not isinstance(ids, list):
        raise RevocationListUnverified("malformed_list")
    return {str(x) for x in ids if x}


def utc_now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()

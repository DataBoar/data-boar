"""
Verify signed license JWT (Ed25519 / EdDSA) and optional revocation list.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

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


def load_revocation_ids(path: str | None) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.is_file():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    ids = data.get("revoked_license_ids")
    if not isinstance(ids, list):
        return set()
    return {str(x) for x in ids if x}


def utc_now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()

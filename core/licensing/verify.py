"""
Verify signed license JWT (Ed25519 / EdDSA) and optional revocation list.
"""

from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime, timezone
from importlib.resources import files as resource_files
from pathlib import Path
from typing import Any

import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PublicKey

# pyjwt[crypto] uses cryptography for EdDSA

# Optional hybrid PQC claim (license-studio #48); JOSE alg remains EdDSA.
CLAIM_MLDSA_SIG = "dbmldsa_sig"

# Official issuer verify key shipped in the wheel (#1331). Public material only.
EMBEDDED_LICENSE_PUBKEY_RESOURCE = "license-pub-v1.pem"


def load_embedded_official_public_key_pem() -> str | None:
    """Return the packaged official Ed25519 public PEM, or None if missing."""
    try:
        traversable = resource_files("core.licensing").joinpath(
            EMBEDDED_LICENSE_PUBKEY_RESOURCE
        )
    except (ModuleNotFoundError, AttributeError):
        return None
    try:
        is_file = getattr(traversable, "is_file", None)
        if callable(is_file) and not is_file():
            return None
        text = traversable.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError, ValueError):
        return None
    return text or None


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


def load_mldsa65_public_key_pem(pem_data: str) -> MLDSA65PublicKey:
    """Load ML-DSA-65 public key from ``ML-DSA-65 PUBLIC KEY`` PEM (raw bytes, not PKIX)."""
    body_lines: list[str] = []
    in_block = False
    for line in pem_data.splitlines():
        stripped = line.strip()
        if stripped.startswith("-----BEGIN"):
            in_block = True
            continue
        if stripped.startswith("-----END"):
            break
        if in_block and stripped:
            body_lines.append(stripped)
    if not body_lines:
        raise ValueError("mldsa: PEM missing ML-DSA-65 PUBLIC KEY block")
    try:
        raw = base64.b64decode("".join(body_lines), validate=True)
    except (ValueError, binascii.Error) as e:
        raise ValueError("mldsa: invalid PEM base64") from e
    return MLDSA65PublicKey.from_public_bytes(raw)


def _mldsa_payload_json_without_sig(claims: dict[str, Any]) -> str:
    """Rebuild payload JSON like Go ``encoding/json`` (sorted keys + HTML-safe escapes)."""
    without = {k: v for k, v in claims.items() if k != CLAIM_MLDSA_SIG}
    payload_json = json.dumps(
        without,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    for char, escaped in (
        ("<", "\\u003c"),
        (">", "\\u003e"),
        ("&", "\\u0026"),
        ("\u2028", "\\u2028"),
        ("\u2029", "\\u2029"),
    ):
        payload_json = payload_json.replace(char, escaped)
    return payload_json


def _verify_mldsa_claim(
    header_b64: str,
    claims: dict[str, Any],
    raw_sig: Any,
    mldsa_pub: MLDSA65PublicKey,
) -> None:
    if not isinstance(raw_sig, str):
        raise ValueError(f"{CLAIM_MLDSA_SIG} must be a string")
    try:
        mldsa_sig = base64.urlsafe_b64decode(raw_sig + "=" * (-len(raw_sig) % 4))
    except (ValueError, binascii.Error) as e:
        raise ValueError(f"{CLAIM_MLDSA_SIG} is not valid base64url") from e
    payload_json = _mldsa_payload_json_without_sig(claims)
    payload_b64 = (
        base64.urlsafe_b64encode(payload_json.encode("utf-8"))
        .decode("ascii")
        .rstrip("=")
    )
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    try:
        mldsa_pub.verify(mldsa_sig, msg)
    except InvalidSignature:
        raise
    except Exception as e:
        raise InvalidSignature("ML-DSA verification failed") from e


def decode_license_jwt_hybrid(
    token: str,
    ed25519_pub: Any,
    mldsa_pub: MLDSA65PublicKey | None = None,
) -> dict[str, Any]:
    """
    Verify EdDSA (``decode_license_jwt``) and optional ``dbmldsa_sig`` (ML-DSA-65).

    When ``dbmldsa_sig`` is present, ``mldsa_pub`` is required (fail-closed). The ML-DSA
    message is ``header_b64`` + ``.`` + base64url(JSON payload without that claim), with
    JSON matching license-studio ``pkg/verify/hybrid.go`` (sorted keys, Go HTML escapes).

    The claim is optional: an attacker who forges Ed25519 can omit ``dbmldsa_sig`` and
    ``decode_license_jwt`` still accepts the token — hybrid verify does not raise the forgery
    bar until a future enforcement policy requires ML-DSA.
    """
    claims = decode_license_jwt(token, ed25519_pub)
    raw = claims.get(CLAIM_MLDSA_SIG)
    if raw is None:
        return claims
    if mldsa_pub is None:
        raise ValueError(
            "hybrid claim present: ML-DSA public key required (decode_license_jwt_hybrid)"
        )
    parts = token.split(".")
    if len(parts) != 3:
        raise jwt.DecodeError("Not enough segments")
    _verify_mldsa_claim(parts[0], claims, raw, mldsa_pub)
    return claims


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

"""Trust-anchor resolution for license verify keys (#1992 / #1462).

Production verifies licenses with the embedded Ed25519 anchor, or with a
replacement pair whose attestation is signed by **both** embedded anchors
(Ed25519 and ML-DSA-65) at an epoch ``>= MIN_ACCEPTED_KEY_EPOCH``.

A raw public key from the environment or from YAML is not a verify key.
Tests replace ``LicenseGuard._resolve_verify_key_sources`` (or the embedded
loaders) with ``monkeypatch``. There is no environment flag that enables an
override.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
from importlib.resources import files as resource_files

from cryptography.exceptions import InvalidSignature

from core.licensing.verify import (
    load_ed25519_public_key_pem,
    load_mldsa65_public_key_pem,
)

# Floor shipped with the embedded anchors. Raise it in a release to retire
# a rotation whose private keys were later compromised.
MIN_ACCEPTED_KEY_EPOCH = 1

EMBEDDED_MLDSA_ANCHOR_RESOURCE = "license-mldsa-pub-v1.pem"

# Domain separation, same shape as bestiais-sdk ``ATTEST_DOMAIN`` (attest.rs).
# The NUL keeps this label from being a prefix of another protocol's message.
ROTATION_DOMAIN = b"data-boar/license-key-rotation/v1\0"


class UntrustedKeyOverride(Exception):
    """Env or YAML named a raw verify key. Production does not accept that."""


class RotationRejected(Exception):
    """Rotation attestation failed closed. ``detail`` is a stable token."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def load_embedded_mldsa_anchor_pem() -> str | None:
    """Packaged ML-DSA-65 anchor PEM, or None when the resource is absent."""
    try:
        traversable = resource_files("core.licensing").joinpath(
            EMBEDDED_MLDSA_ANCHOR_RESOURCE
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


def raw_key_override_configured(
    public_key_path: str, mldsa_public_key_path: str = ""
) -> bool:
    """True when a raw verify-key override is present (always rejected).

    Covers Ed25519 and ML-DSA. An environment or YAML public key is not a
    trust anchor, including the hybrid ``dbmldsa_sig`` key (#1993 + #1992).
    """
    for name in (
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PATH",
    ):
        if (os.environ.get(name) or "").strip():
            return True
    if (public_key_path or "").strip():
        return True
    return bool((mldsa_public_key_path or "").strip())


def canonical_rotation_message(
    epoch: int, ed25519_pub_pem: str, mldsa_pub_pem: str
) -> bytes:
    """Bytes both anchors sign.

    Layout: ``ROTATION_DOMAIN || epoch_u64be || canonical_key_json``.

    ``epoch`` is an 8-byte big-endian integer inside those bytes, not a field
    checked beside the signature (data-boar-sdk#12: a freshness value left
    outside the verified message is a replay). Signatures are not part of the
    message.
    """
    epoch_int = int(epoch)
    if epoch_int < 0:
        raise RotationRejected("invalid_epoch")
    try:
        epoch_bytes = epoch_int.to_bytes(8, "big", signed=False)
    except OverflowError as exc:
        raise RotationRejected("invalid_epoch") from exc
    keys = {
        "ed25519_pub_pem": ed25519_pub_pem.strip(),
        "mldsa_pub_pem": mldsa_pub_pem.strip(),
    }
    key_json = json.dumps(
        keys, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return ROTATION_DOMAIN + epoch_bytes + key_json


def _b64_sig(value: object) -> bytes:
    if not isinstance(value, str) or not value.strip():
        raise RotationRejected("missing_signature")
    try:
        return base64.b64decode(value.strip(), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RotationRejected("invalid_signature_encoding") from exc


def verify_rotation_attestation(
    document: str,
    *,
    ed25519_anchor_pem: str,
    mldsa_anchor_pem: str | None,
    min_epoch: int | None = None,
) -> tuple[str, str, int]:
    """Return ``(new_ed25519_pem, new_mldsa_pem, epoch)`` or raise.

    Both embedded anchors must sign the same canonical message. One signature
    is not enough. ``epoch`` must be ``>= min_epoch`` (default
    ``MIN_ACCEPTED_KEY_EPOCH``).
    """
    if not (ed25519_anchor_pem or "").strip():
        raise RotationRejected("missing_ed25519_anchor")
    if not (mldsa_anchor_pem or "").strip():
        raise RotationRejected("missing_mldsa_anchor")
    floor = MIN_ACCEPTED_KEY_EPOCH if min_epoch is None else int(min_epoch)
    try:
        doc = json.loads(document)
    except json.JSONDecodeError as exc:
        raise RotationRejected("invalid_attestation") from exc
    if not isinstance(doc, dict):
        raise RotationRejected("invalid_attestation")
    try:
        epoch = int(doc["epoch"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RotationRejected("invalid_epoch") from exc
    if epoch < floor:
        raise RotationRejected(f"epoch_too_old:{epoch}<{floor}")
    ed_pem = doc.get("ed25519_pub_pem")
    ml_pem = doc.get("mldsa_pub_pem")
    if not isinstance(ed_pem, str) or not ed_pem.strip():
        raise RotationRejected("missing_ed25519_pub")
    if not isinstance(ml_pem, str) or not ml_pem.strip():
        raise RotationRejected("missing_mldsa_pub")
    message = canonical_rotation_message(epoch, ed_pem, ml_pem)
    ed_sig = _b64_sig(doc.get("sig_ed25519"))
    ml_sig = _b64_sig(doc.get("sig_mldsa"))
    try:
        load_ed25519_public_key_pem(ed25519_anchor_pem).verify(ed_sig, message)
        load_mldsa65_public_key_pem(mldsa_anchor_pem).verify(ml_sig, message)
        load_ed25519_public_key_pem(ed_pem)
        load_mldsa65_public_key_pem(ml_pem)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise RotationRejected("signature") from exc
    return ed_pem.strip(), ml_pem.strip(), epoch

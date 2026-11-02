"""Release-signed CRITICAL_MODULES manifest (#2168).

Trust root is the project's existing Ed25519 license verify key, already
packaged as ``core/licensing/license-pub-v1.pem``. The SQLite anchor is
forensic only. A private key is never created or stored here.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from packaging.version import InvalidVersion, Version

from core.licensing.verify import (
    load_ed25519_public_key_pem,
    load_embedded_official_public_key_pem,
)

SCHEMA = "data-boar.integrity-manifest.v1"
PACKAGED_MANIFEST_NAME = "integrity_manifest.json"


def packaged_manifest_path() -> Path:
    return Path(__file__).resolve().parent / "licensing" / PACKAGED_MANIFEST_NAME


def resolve_manifest_path() -> Path | None:
    path = packaged_manifest_path()
    return path if path.is_file() else None


def load_integrity_verify_pem() -> str | None:
    return load_embedded_official_public_key_pem()


def canonical_payload_bytes(body: dict[str, Any]) -> bytes:
    payload = {
        "files": body.get("files"),
        "release_label": body.get("release_label"),
        "schema": body.get("schema"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_manifest_body(
    files: dict[str, str],
    release_label: str,
    private_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    body = {
        "schema": SCHEMA,
        "release_label": release_label,
        "files": dict(sorted(files.items())),
    }
    signature = base64.b64encode(
        private_key.sign(canonical_payload_bytes(body))
    ).decode("ascii")
    return {**body, "signature": signature}


def _tampered(mismatched: list[str], detail: str) -> dict[str, Any]:
    return {
        "integrity_state": "tampered",
        "trust_level": "adulterated",
        "mismatched_files": list(mismatched),
        "detail": detail,
        "signed_release_label": None,
    }


def _is_downgrade(current: str, previous: str) -> bool:
    try:
        return Version(current) < Version(previous)
    except InvalidVersion:
        return bool(previous) and current != previous


def evaluate_signed_manifest(
    current_hashes: dict[str, str],
    current_label: str,
    previous_signed_label: str | None,
) -> dict[str, Any]:
    """Decide validated vs tampered from the signed release manifest only."""
    path = resolve_manifest_path()
    if path is None or not path.is_file():
        return _tampered([], "signed_manifest_absent")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return _tampered([], "signed_manifest_unreadable")
    if not isinstance(data, dict):
        return _tampered([], "signed_manifest_invalid")
    sig_b64 = data.get("signature")
    if not isinstance(sig_b64, str) or not sig_b64.strip():
        return _tampered([], "signed_manifest_unsigned")
    pem = load_integrity_verify_pem()
    if not pem:
        return _tampered([], "signed_manifest_no_verify_key")
    try:
        public_key = load_ed25519_public_key_pem(pem)
        if not isinstance(public_key, Ed25519PublicKey):
            return _tampered([], "signed_manifest_signature_invalid")
        public_key.verify(base64.b64decode(sig_b64), canonical_payload_bytes(data))
    except (InvalidSignature, ValueError, TypeError, OSError):
        return _tampered([], "signed_manifest_signature_invalid")
    files = data.get("files")
    if not isinstance(files, dict):
        return _tampered([], "signed_manifest_files_invalid")
    file_map = {str(key): str(value) for key, value in files.items()}
    mismatched = sorted(
        rel
        for rel in set(current_hashes) | set(file_map)
        if current_hashes.get(rel) != file_map.get(rel)
    )
    if mismatched:
        return _tampered(mismatched, "signed_manifest_hash_mismatch")
    release_label = str(data.get("release_label") or "").strip()
    if previous_signed_label and (
        _is_downgrade(current_label, previous_signed_label)
        or (release_label and _is_downgrade(release_label, previous_signed_label))
    ):
        return _tampered([], "signed_manifest_downgrade")
    return {
        "integrity_state": "validated",
        "trust_level": "expected",
        "mismatched_files": [],
        "detail": "signed_manifest_ok",
        "signed_release_label": release_label or current_label,
    }

"""Test helpers for #2168 signed integrity manifests.

Pins use ``monkeypatch.setattr`` on production call sites. There is no
public key-swap or path-swap API in ``core.integrity_signed_manifest``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.integrity_anchor import _release_label, compute_module_hashes
from core.integrity_signed_manifest import sign_manifest_body

_MISSING_MANIFEST = Path("/nonexistent/integrity_manifest.json")


def generate_test_signing_key() -> tuple[Ed25519PrivateKey, str]:
    private_key = Ed25519PrivateKey.generate()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_key, public_pem


def write_signed_manifest(
    path: Path,
    files: dict[str, str],
    release_label: str,
    private_key: Ed25519PrivateKey,
) -> Path:
    path.write_text(
        json.dumps(sign_manifest_body(files, release_label, private_key), indent=2)
        + "\n",
        encoding="utf-8",
    )
    return path


def pin_signed_manifest(monkeypatch: Any, path: Path, public_pem: str | None) -> None:
    monkeypatch.setattr(
        "core.integrity_signed_manifest.packaged_manifest_path",
        lambda: path,
    )
    monkeypatch.setattr(
        "core.integrity_signed_manifest.load_embedded_official_public_key_pem",
        lambda: public_pem,
    )


def install_matching_signed_manifest(
    directory: Path,
    monkeypatch: Any,
    release_label: str | None = None,
) -> Path:
    private_key, public_pem = generate_test_signing_key()
    label = release_label or _release_label()
    path = write_signed_manifest(
        Path(directory) / "integrity_manifest.json",
        compute_module_hashes(),
        label,
        private_key,
    )
    pin_signed_manifest(monkeypatch, path, public_pem)
    return path


def reset_signed_manifest_pins(monkeypatch: Any) -> None:
    pin_signed_manifest(monkeypatch, _MISSING_MANIFEST, None)

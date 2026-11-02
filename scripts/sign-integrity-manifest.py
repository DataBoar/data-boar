#!/usr/bin/env python3
"""Sign or verify the packaged CRITICAL_MODULES integrity manifest (#2168).

Operator TTY only for signing. Reuses the existing license issuer Ed25519 key
(``DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM`` /
``DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE``). Never creates a key.
Never prints key material. CI may run ``--verify-only`` (public key only).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.integrity_anchor import compute_module_hashes  # noqa: E402
from core.integrity_signed_manifest import (  # noqa: E402
    evaluate_signed_manifest,
    packaged_manifest_path,
    sign_manifest_body,
)


def _read_issuer_pem() -> str:
    path = os.environ.get("DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE", "").strip()
    inline = os.environ.get("DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM", "").strip()
    if path:
        return Path(path).expanduser().read_text(encoding="utf-8")
    if inline:
        return inline
    print(
        "Missing issuer key: set DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE "
        "or DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM",
        file=sys.stderr,
    )
    sys.exit(2)


def _load_ed25519_private() -> Ed25519PrivateKey:
    pem = _read_issuer_pem()
    password = os.environ.get(
        "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD", ""
    ).strip()
    key = load_pem_private_key(
        pem.encode("utf-8"),
        password=password.encode("utf-8") if password else None,
    )
    if not isinstance(key, Ed25519PrivateKey):
        print(
            "Issuer key must be Ed25519 (same key as license verify).", file=sys.stderr
        )
        sys.exit(2)
    return key


def _package_version() -> str:
    try:
        from core.about import _package_version

        return _package_version()
    except Exception:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify the packaged manifest with the embedded public key.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=packaged_manifest_path(),
        help="Output path (default: packaged core/licensing/integrity_manifest.json).",
    )
    args = parser.parse_args()
    hashes = compute_module_hashes()
    label = _package_version()
    if args.verify_only:
        verdict = evaluate_signed_manifest(hashes, label, None)
        print(verdict["detail"], verdict["integrity_state"])
        return 0 if verdict["integrity_state"] == "validated" else 1
    document = sign_manifest_body(hashes, label, _load_ed25519_private())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} files={len(hashes)} release_label={label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Issue a signed commercial license JWT (Ed25519) for lab/homelab only.

Private keys must never be committed: use a file under docs/private/ or an env var
set at runtime. See docs/private.example/licensing/README.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def _load_private_key_pem() -> str:
    path = os.environ.get("DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE", "").strip()
    inline = os.environ.get("DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM", "").strip()
    if path:
        return Path(path).expanduser().read_text(encoding="utf-8")
    if inline:
        return inline
    print(
        "Missing key material: set DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE "
        "or DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Emit Ed25519-signed license JWT (dev/lab). Do not commit private keys."
    )
    p.add_argument(
        "--private-key-pem-file",
        help="Override: path to Ed25519 private PEM (else use env vars)",
    )
    p.add_argument("--sub", default="dev-lic-1", help="JWT sub (license id)")
    p.add_argument(
        "--dbtier",
        default="pro",
        choices=["community", "pro", "enterprise"],
        help="dbtier claim (community, pro, or enterprise)",
    )
    p.add_argument("--days", type=int, default=7, help="Validity in days from now")
    p.add_argument("--out", help="Write token to this file (.lic); default stdout")
    args = p.parse_args()

    if args.private_key_pem_file:
        pem = Path(args.private_key_pem_file).expanduser().read_text(encoding="utf-8")
    else:
        pem = _load_private_key_pem()

    key = load_pem_private_key(pem.encode("utf-8"), password=None)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": args.sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=args.days)).timestamp()),
        "dbcid": "lab-dev",
        "dbcname": "Lab",
        "dbenv": "debug",
        "dbissuer": "issue_dev_license_jwt",
        "dbkid": "dev",
        "dbtier": args.dbtier.strip(),
    }
    token = jwt.encode(payload, key, algorithm="EdDSA")
    if args.out:
        Path(args.out).write_text(token + "\n", encoding="utf-8")
    else:
        print(token)


if __name__ == "__main__":
    main()

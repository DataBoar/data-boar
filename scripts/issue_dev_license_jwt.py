#!/usr/bin/env python3
"""
Issue a signed QA/lab license JWT (Ed25519) — the ONLY test path in enforced mode.

The env-based tier bypass was removed (#719): QA against ``licensing.mode:
enforced`` requires a real signed license. This issuer emits short-lived
(default **60 days**), **machine-bound** (``dbmfp`` of the current machine by
default) enterprise-tier tokens, so a leaked QA license expires quickly and
only runs on the machines it was bound to.

Private keys must never be committed: use a file under docs/private/ or an env var
set at runtime. See docs/private.example/licensing/README.md and
docs/ops/QA_LOCAL_LICENSE.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from getpass import getpass
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Default QA validity: short enough that a leaked license dies on its own.
DEFAULT_QA_DAYS = 60

# Running by path puts scripts/ first on sys.path; core/ lives at repo root.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _machine_fingerprint() -> str:
    from core.licensing.fingerprint import compute_machine_fingerprint

    return compute_machine_fingerprint()


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


def _resolve_key_password(pem: str) -> bytes | None:
    """Resolve the signing-key passphrase for ``load_pem_private_key`` (#910).

    Backward-compatible: an unencrypted PEM still loads with ``password=None``.
    For an AES-encrypted PKCS#8 PEM the passphrase is resolved in this order:

    1. ``DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD`` env var (non-interactive
       path — Maestro / automation set this before calling the issuer).
    2. Interactive ``getpass`` prompt when stdin is a TTY (operator issuing a
       real license at the keyboard).
    3. Encrypted key with neither env var nor a TTY: exit with an actionable
       message instead of a raw ``TypeError`` traceback from cryptography.
    """
    pw = os.environ.get("DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD", "").strip()
    if pw:
        return pw.encode("utf-8")
    if "ENCRYPTED" in pem:
        if sys.stdin.isatty():
            entered = getpass("License signing key passphrase: ").strip()
            if entered:
                return entered.encode("utf-8")
        sys.exit(
            "Signing key is encrypted: set "
            "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD or run in a TTY to "
            "enter the passphrase."
        )
    return None


def _resolve_dbmfp(raw: str) -> str:
    """Resolve --dbmfp: 'auto' = bind to this machine, 'none' = unbound."""
    value = raw.strip().lower()
    if value == "none":
        return ""
    if value == "auto":
        return _machine_fingerprint()
    return value


def _resolve_dbmfp_pack(raw: str) -> list[str]:
    """
    Resolve --dbmfp-pack: comma-separated fingerprints (deployment pack, #846).

    Each entry is a hex fingerprint from --show-machine-fingerprint on the
    target machine; the literal 'auto' binds THIS machine as one pack member.
    """
    pack: list[str] = []
    for part in raw.split(","):
        value = part.strip().lower()
        if not value:
            continue
        if value == "auto":
            value = _machine_fingerprint()
        if value not in pack:
            pack.append(value)
    return pack


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Emit Ed25519-signed QA license JWT (60-day, machine-bound by "
            "default). Do not commit private keys."
        )
    )
    p.add_argument(
        "--private-key-pem-file",
        help="Override: path to Ed25519 private PEM (else use env vars)",
    )
    p.add_argument("--sub", default="dev-lic-1", help="JWT sub (license id)")
    p.add_argument(
        "--dbtier",
        default="enterprise",
        choices=["community", "pro", "enterprise"],
        help="dbtier claim (default: enterprise — full QA surface)",
    )
    p.add_argument(
        "--days",
        type=int,
        default=DEFAULT_QA_DAYS,
        help=f"Validity in days from now (default: {DEFAULT_QA_DAYS})",
    )
    p.add_argument(
        "--dbmfp",
        default="auto",
        help=(
            "Machine fingerprint binding: 'auto' (default — bind to THIS "
            "machine), 'none' (unbound; lab only), or an explicit fingerprint "
            "hex from the tester machine (--show-machine-fingerprint)"
        ),
    )
    p.add_argument(
        "--dbmfp-pack",
        help=(
            "Deployment pack (#846): comma-separated fingerprint hexes to bind "
            "the license to N machines (use 'auto' for THIS machine, e.g. "
            "'auto,<tester-hex>'). Overrides --dbmfp. Runtime validates only "
            "its own fingerprint; the pack size is issuance-enforced."
        ),
    )
    p.add_argument(
        "--pack-id",
        help="dbdeployment_pack_id claim (audit trail; default: '<sub>-pack' when --dbmfp-pack is used)",
    )
    p.add_argument(
        "--dbmax-deployments",
        type=int,
        help=(
            "dbmax_deployments claim — licensed site count. Default: pack size "
            "when --dbmfp-pack is used, else omitted. Enterprise contracts may "
            "use 0 = unlimited."
        ),
    )
    p.add_argument(
        "--show-machine-fingerprint",
        action="store_true",
        help="Print this machine's fingerprint (send to the issuer) and exit",
    )
    p.add_argument("--out", help="Write token to this file (.lic); default stdout")
    args = p.parse_args()

    if args.show_machine_fingerprint:
        print(_machine_fingerprint())
        return

    if args.private_key_pem_file:
        pem = Path(args.private_key_pem_file).expanduser().read_text(encoding="utf-8")
    else:
        pem = _load_private_key_pem()

    key = load_pem_private_key(pem.encode("utf-8"), password=_resolve_key_password(pem))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": args.sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=args.days)).timestamp()),
        "dbcid": "lab-dev",
        "dbcname": "Lab",
        "dbenv": "qa",
        "dbissuer": "issue_dev_license_jwt",
        "dbkid": "dev",
        "dbtier": args.dbtier.strip(),
    }
    if args.dbmfp_pack:
        pack = _resolve_dbmfp_pack(args.dbmfp_pack)
        if not pack:
            print("--dbmfp-pack resolved to an empty pack", file=sys.stderr)
            sys.exit(1)
        payload["dbmfp"] = pack
        payload["dbdeployment_pack_id"] = args.pack_id or f"{args.sub}-pack"
        payload["dbmax_deployments"] = (
            args.dbmax_deployments if args.dbmax_deployments is not None else len(pack)
        )
    else:
        dbmfp = _resolve_dbmfp(args.dbmfp)
        if dbmfp:
            payload["dbmfp"] = dbmfp
        if args.dbmax_deployments is not None:
            payload["dbmax_deployments"] = args.dbmax_deployments
        if args.pack_id:
            payload["dbdeployment_pack_id"] = args.pack_id
    token = jwt.encode(payload, key, algorithm="EdDSA")
    if args.out:
        Path(args.out).write_text(token + "\n", encoding="utf-8")
    else:
        print(token)


if __name__ == "__main__":
    main()

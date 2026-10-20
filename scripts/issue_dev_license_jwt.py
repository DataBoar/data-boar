#!/usr/bin/env python3
"""
Issue a signed QA/lab license JWT (Ed25519 + ML-DSA-65) — the ONLY test path in enforced mode.

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
import base64
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from getpass import getpass
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Default QA validity: short enough that a leaked license dies on its own.
DEFAULT_QA_DAYS = 60
_DBMFP_HEX_RE = re.compile(r"[0-9a-f]{64}")

# Running by path puts scripts/ first on sys.path; core/ lives at repo root.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _load_dev_mldsa_private() -> MLDSA65PrivateKey:
    """DEV/QA ML-DSA signer. Never the packaged anchor private key.

    ``DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_PEM_FILE`` or
    ``DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_PEM`` supplies the key.
    When both are unset, an ephemeral key is generated for this process.
    That token will not verify against the packaged anchor; tests pin the
    matching public key in-process. This is not a production verify override.
    """
    path = os.environ.get(
        "DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_PEM_FILE", ""
    ).strip()
    inline = os.environ.get(
        "DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_PEM", ""
    ).strip()
    if path:
        blob = Path(path).expanduser().read_text(encoding="utf-8")
    elif inline:
        blob = inline
    else:
        return MLDSA65PrivateKey.generate()
    key = load_pem_private_key(blob.encode("utf-8"), password=None)
    if not isinstance(key, MLDSA65PrivateKey):
        print(
            "DATA_BOAR_LICENSE_ISSUER_MLDSA_PRIVATE_KEY_* must be an ML-DSA-65 private key",
            file=sys.stderr,
        )
        sys.exit(1)
    _reject_packaged_mldsa_anchor(key)
    return key


def _reject_packaged_mldsa_anchor(key: MLDSA65PrivateKey) -> None:
    from core.licensing.trust_anchor import load_embedded_mldsa_anchor_pem
    from core.licensing.verify import load_mldsa65_public_key_pem

    embedded = load_embedded_mldsa_anchor_pem()
    if not embedded:
        return
    packaged = load_mldsa65_public_key_pem(embedded)
    if key.public_key().public_bytes_raw() == packaged.public_bytes_raw():
        print(
            "refusing to sign with the packaged ML-DSA anchor private key",
            file=sys.stderr,
        )
        sys.exit(1)


def _attach_dev_mldsa_sig(
    token: str, ed_private: object, mldsa_private: MLDSA65PrivateKey
) -> str:
    from core.licensing.verify import CLAIM_MLDSA_SIG, _mldsa_payload_json_without_sig

    payload_b64 = token.split(".")[1]
    claims = json.loads(
        base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
    )
    if not isinstance(claims, dict):
        print("issuer payload is not an object", file=sys.stderr)
        sys.exit(1)
    header_b64 = token.split(".", 1)[0]
    payload_json = _mldsa_payload_json_without_sig(claims)
    signed_payload_b64 = (
        base64.urlsafe_b64encode(payload_json.encode("utf-8"))
        .decode("ascii")
        .rstrip("=")
    )
    sig = mldsa_private.sign(f"{header_b64}.{signed_payload_b64}".encode("utf-8"))
    claims[CLAIM_MLDSA_SIG] = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    sealed = jwt.encode(claims, ed_private, algorithm="EdDSA")
    if sealed.split(".", 1)[0] != header_b64:
        print("JWT header changed after attaching dbmldsa_sig", file=sys.stderr)
        sys.exit(1)
    return sealed


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


def _stdin_is_interactive() -> bool:
    """True only when a real console is attached (never block under pytest/CI).

    On Windows, ``subprocess.DEVNULL`` as stdin can still make
    ``sys.stdin.isatty()`` return True; prefer ``os.isatty(fileno)``.
    """
    if os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}:
        return False
    try:
        fd = sys.stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return False
    try:
        return bool(os.isatty(fd))
    except OSError:
        return False


def _resolve_key_password(pem: str) -> bytes | None:
    """Resolve the signing-key passphrase for ``load_pem_private_key`` (#910).

    Backward-compatible: an unencrypted PEM still loads with ``password=None``.
    For an AES-encrypted PKCS#8 PEM the passphrase is resolved in this order:

    1. ``DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD`` env var (non-interactive
       path — Maestro / automation set this before calling the issuer).
    2. Interactive ``getpass`` prompt when stdin is a real TTY (operator issuing a
       real license at the keyboard).
    3. Encrypted key with neither env var nor a TTY: exit with an actionable
       message instead of a raw ``TypeError`` traceback from cryptography.
    """
    pw = os.environ.get("DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD", "").strip()
    if pw:
        return pw.encode("utf-8")
    if "ENCRYPTED" in pem:
        if _stdin_is_interactive():
            entered = getpass("License signing key passphrase: ").strip()
            if entered:
                return entered.encode("utf-8")
        sys.exit(
            "Signing key is encrypted: set "
            "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD or run in a TTY to "
            "enter the passphrase."
        )
    return None


def _require_fingerprint_hex(value: str) -> str:
    """Reject at issuance what the runtime guard would reject (#1939)."""
    if not _DBMFP_HEX_RE.fullmatch(value):
        sys.exit(f"invalid fingerprint {value!r}: expected 64 lowercase hex chars")
    return value


def _resolve_dbmfp(raw: str) -> str:
    """Resolve --dbmfp: 'auto' = bind to this machine, 'none' = unbound."""
    value = raw.strip().lower()
    if value == "none":
        return ""
    if value == "auto":
        return _machine_fingerprint()
    return _require_fingerprint_hex(value) if value else ""


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
        _require_fingerprint_hex(value)
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
    token = _attach_dev_mldsa_sig(
        jwt.encode(payload, key, algorithm="EdDSA"),
        key,
        _load_dev_mldsa_private(),
    )
    if args.out:
        Path(args.out).write_text(token + "\n", encoding="utf-8")
    else:
        print(token)


if __name__ == "__main__":
    main()

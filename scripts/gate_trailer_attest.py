#!/usr/bin/env python3
"""Gate trailer SSH ed25519 attestation (ADR-0056 file namespace + ADR-0071 marker).

Decorative *file*-namespace detached signatures over the Gate-* trailer line
(``Gate-Change-Approved-By:`` or ``Gate-Close-Approved-By:``). Complements:

- ``gate_change_tripwire.py`` (regex marker only; no crypto)
- ``git verify-commit`` (``git`` namespace over the whole commit object)

Payload rule (verified on commit ``888f175e`` / PR #1063): sign/verify the
trailer line **without** a trailing newline.

Usage (from repo root)::

    uv run python scripts/gate_trailer_attest.py verify --commit 888f175e
    uv run python scripts/gate_trailer_attest.py sign --text 'Gate-Change-Approved-By: @FabioLeitao | ...'
    uv run python scripts/gate_trailer_attest.py format-commit-body --text '...' --signature-file trailer.sig

Exit codes: 0 ok, 1 verify/sign failure, 2 usage/tool error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWED_SIGNERS = REPO_ROOT / "docs" / "adr" / "allowed_signers"
DEFAULT_PRINCIPAL = "fabio.tleitao@gmail.com"
NAMESPACE = "file"

GATE_TRAILER_RE = re.compile(
    r"^Gate-(?:Change|Close)-Approved-By:\s*@?\S+.*$",
    re.MULTILINE,
)
SIG_BLOCK_RE = re.compile(
    r"-----BEGIN SSH SIGNATURE-----\s*(.*?)\s*-----END SSH SIGNATURE-----",
    re.DOTALL,
)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def extract_trailer_line(text: str) -> str | None:
    for line in text.splitlines():
        if GATE_TRAILER_RE.match(line):
            return line
    return None


def extract_signature_pem(text: str) -> str | None:
    m = SIG_BLOCK_RE.search(text)
    if not m:
        return None
    inner = re.sub(r"\s+", "", m.group(1))
    lines = [inner[i : i + 70] for i in range(0, len(inner), 70)]
    body = "\n".join(lines)
    return f"-----BEGIN SSH SIGNATURE-----\n{body}\n-----END SSH SIGNATURE-----\n"


def trailer_payload_bytes(trailer_line: str) -> bytes:
    """Canonical bytes to sign/verify (no trailing newline)."""
    return trailer_line.encode("utf-8")


def verify_trailer_signature(
    trailer_line: str,
    signature_pem: str,
    *,
    allowed_signers: Path,
    principal: str = DEFAULT_PRINCIPAL,
) -> tuple[bool, str]:
    if not allowed_signers.is_file():
        return False, f"allowed_signers missing: {allowed_signers}"
    with tempfile.TemporaryDirectory() as td:
        sig_path = Path(td) / "trailer.sig"
        sig_path.write_text(signature_pem, encoding="utf-8")
        proc = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowed_signers),
                "-I",
                principal,
                "-n",
                NAMESPACE,
                "-s",
                str(sig_path),
            ],
            input=trailer_payload_bytes(trailer_line),
            capture_output=True,
            text=False,
            check=False,
        )
        out = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        if proc.returncode == 0:
            return True, out or "Good signature"
        return False, err or out or "verify failed"


def sign_trailer(
    trailer_line: str,
    key_path: Path,
    *,
    principal: str = DEFAULT_PRINCIPAL,
) -> tuple[bool, str]:
    if not key_path.is_file():
        return False, f"signing key not found: {key_path}"
    with tempfile.TemporaryDirectory() as td:
        payload_path = Path(td) / "trailer.txt"
        sig_path = Path(td) / "trailer.sig"
        payload_path.write_bytes(trailer_payload_bytes(trailer_line))
        proc = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "sign",
                "-f",
                str(key_path),
                "-n",
                NAMESPACE,
                "-I",
                principal,
                "-s",
                str(sig_path),
                str(payload_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "sign failed").strip()
            return False, err
        if not sig_path.is_file():
            return False, "ssh-keygen did not write signature file"
        return True, sig_path.read_text(encoding="utf-8")


def format_commit_body(trailer_line: str, signature_pem: str) -> str:
    sig_inner = SIG_BLOCK_RE.search(signature_pem)
    if sig_inner:
        block = signature_pem.strip()
    else:
        block = signature_pem.strip()
    return f"{trailer_line}\n\n```\n{block}\n```\n"


def cmd_verify(args: argparse.Namespace) -> int:
    trailer: str | None = args.trailer
    sig_pem: str | None = None

    if args.commit:
        log = _git(["show", "-s", "--format=%B", args.commit])
        if log.returncode != 0:
            sys.stderr.write(log.stderr or f"git show failed for {args.commit}\n")
            return 2
        body = log.stdout
        trailer = trailer or extract_trailer_line(body)
        sig_pem = extract_signature_pem(body)
    elif args.message_file:
        body = Path(args.message_file).read_text(encoding="utf-8")
        trailer = trailer or extract_trailer_line(body)
        sig_pem = sig_pem or extract_signature_pem(body)
    else:
        if args.trailer_file:
            trailer = (
                Path(args.trailer_file).read_text(encoding="utf-8").splitlines()[0]
            )
        if args.signature_file:
            sig_pem = Path(args.signature_file).read_text(encoding="utf-8")

    if not trailer:
        sys.stderr.write("gate-trailer-attest: no Gate-*-Approved-By line found\n")
        return 1
    if not sig_pem:
        sys.stderr.write("gate-trailer-attest: no SSH SIGNATURE block found\n")
        return 1

    ok, msg = verify_trailer_signature(
        trailer,
        sig_pem,
        allowed_signers=Path(args.allowed_signers),
        principal=args.principal,
    )
    if ok:
        sys.stdout.write(f"GATE-TRAILER-ATTEST: OK\n{msg}\n")
        sys.stdout.write(f"trailer_bytes={len(trailer_payload_bytes(trailer))}\n")
        return 0
    sys.stderr.write(f"GATE-TRAILER-ATTEST: FAIL\n{msg}\n")
    return 1


def cmd_sign(args: argparse.Namespace) -> int:
    trailer = args.text
    if args.trailer_file:
        trailer = Path(args.trailer_file).read_text(encoding="utf-8").splitlines()[0]
    if not trailer:
        sys.stderr.write("gate-trailer-attest: --text or --trailer-file required\n")
        return 2
    if not GATE_TRAILER_RE.match(trailer):
        sys.stderr.write(
            "gate-trailer-attest: line does not match Gate-*-Approved-By\n"
        )
        return 2
    ok, out = sign_trailer(
        trailer,
        Path(args.key),
        principal=args.principal,
    )
    if not ok:
        sys.stderr.write(f"GATE-TRAILER-ATTEST: sign failed\n{out}\n")
        return 1
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        sys.stdout.write(f"Wrote signature: {args.output}\n")
    else:
        sys.stdout.write(out)
    return 0


def cmd_format_body(args: argparse.Namespace) -> int:
    trailer = args.text
    if args.trailer_file:
        trailer = Path(args.trailer_file).read_text(encoding="utf-8").splitlines()[0]
    if not trailer:
        sys.stderr.write("gate-trailer-attest: --text or --trailer-file required\n")
        return 2
    sig_pem = ""
    if args.signature_file:
        sig_pem = Path(args.signature_file).read_text(encoding="utf-8")
    elif args.commit:
        log = _git(["show", "-s", "--format=%B", args.commit])
        if log.returncode != 0:
            return 2
        sig_pem = extract_signature_pem(log.stdout) or ""
    if not sig_pem:
        sys.stderr.write("gate-trailer-attest: --signature-file or --commit required\n")
        return 2
    sys.stdout.write(format_commit_body(trailer, sig_pem))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--allowed-signers",
        default=str(DEFAULT_ALLOWED_SIGNERS),
        help="allowed_signers trust anchor (default: docs/adr/allowed_signers)",
    )
    p.add_argument(
        "--principal",
        default=DEFAULT_PRINCIPAL,
        help="Signer principal for ssh-keygen -I",
    )
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser(
        "verify", help="Verify decorative file-namespace trailer signature"
    )
    v.add_argument("--commit", help="Git commit SHA (reads message body)")
    v.add_argument("--message-file", help="Full commit message file")
    v.add_argument("--trailer", help="Trailer line (overrides extract)")
    v.add_argument("--trailer-file", help="File with trailer line")
    v.add_argument("--signature-file", help="Detached .sig PEM file")
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("sign", help="Sign trailer line (operator key; file namespace)")
    s.add_argument("--text", help="Trailer line to sign")
    s.add_argument("--trailer-file", help="File with trailer line")
    s.add_argument(
        "--key", required=True, help="Private SSH key for ssh-keygen -Y sign"
    )
    s.add_argument("--output", "-o", help="Write signature PEM to file")
    s.set_defaults(func=cmd_sign)

    f = sub.add_parser(
        "format-commit-body",
        help="Print trailer + fenced signature block for commit message paste",
    )
    f.add_argument("--text", help="Trailer line")
    f.add_argument("--trailer-file", help="File with trailer line")
    f.add_argument("--signature-file", help="Signature PEM from sign subcommand")
    f.add_argument("--commit", help="Reuse signature block from an existing commit")
    f.set_defaults(func=cmd_format_body)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

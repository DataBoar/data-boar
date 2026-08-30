#!/usr/bin/env python3
"""PR attestation guard (GitHub #1709) — brother of issue-close guard #990.

Fails when a PR is in scope (label ``operator-gated`` **or** diff touches
``GATE_FILES`` from ``gate_change_tripwire.py``) unless the **latest** PR
comment is a ``Gate-Change-Approved-By:`` trailer **plus** a verified
file-namespace SSHSIG (``gate_trailer_attest.py``) over the **PR-bound**
payload (trailer + PR number + head SHA).

Does **not** scan PR body or comment history. Does **not** trust
``github.actor``. Trailer without SSHSIG is not approval. Exit codes are
not swallowed by this module (CLI returns them).

Exit: 0 skip or attested, 1 missing/invalid attestation, 2 tool error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.gate_change_tripwire import GATE_FILES, REPO_ROOT, gate_files_touched
from scripts.gate_trailer_attest import (
    DEFAULT_ALLOWED_SIGNERS,
    bound_pr_payload_bytes,
    extract_signature_pem,
    extract_trailer_line,
    verify_trailer_signature,
)

OPERATOR_GATED_LABEL = "operator-gated"
CHANGE_MARKER = re.compile(r"(?im)^\s*Gate-Change-Approved-By:\s*@?FabioLeitao\b")


def needs_attestation(changed: list[str], labels: list[str]) -> bool:
    labs = {lab.strip() for lab in labels if lab and lab.strip()}
    if OPERATOR_GATED_LABEL in labs:
        return True
    return bool(gate_files_touched(changed))


def latest_comment_approves(
    body: str,
    *,
    pr_number: int,
    head_sha: str,
) -> tuple[bool, str]:
    """Evaluate **only** this comment (caller must pass the newest one).

    The SSHSIG must cover ``bound_pr_payload_bytes`` (trailer + PR + head),
    not the trailer line alone — otherwise a signature from git history
    can be replayed as the latest comment.
    """
    text = body or ""
    if not CHANGE_MARKER.search(text):
        return False, "latest comment has no Gate-Change-Approved-By trailer"
    line = extract_trailer_line(text)
    sig = extract_signature_pem(text)
    if line is None:
        return False, "could not extract trailer line"
    if sig is None:
        return False, "trailer without verified SSHSIG block"
    try:
        payload = bound_pr_payload_bytes(line, pr_number, head_sha)
    except ValueError as exc:
        return False, str(exc)
    ok, msg = verify_trailer_signature(
        line,
        sig,
        allowed_signers=DEFAULT_ALLOWED_SIGNERS,
        payload=payload,
    )
    if not ok:
        return False, msg or "SSHSIG verify failed"
    return True, msg


def _git_changed_vs_base(base: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip() or proc.stdout.strip() or "git diff failed"
        )
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git merge-base tip (e.g. origin/main)")
    parser.add_argument(
        "--labels",
        default="",
        help="comma-separated PR labels",
    )
    parser.add_argument(
        "--message-file",
        type=Path,
        help="body of the newest PR comment only",
    )
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="changed path (repeatable; skips git when set)",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="GitHub PR number (required when in scope)",
    )
    parser.add_argument(
        "--head",
        help="40-hex PR head SHA (required when in scope)",
    )
    args = parser.parse_args(argv)

    labels = [p.strip() for p in args.labels.split(",") if p.strip()]
    try:
        if args.changed:
            changed = list(args.changed)
        elif args.base:
            changed = _git_changed_vs_base(args.base)
        else:
            print("operator_gated_pr_guard: need --base or --changed", file=sys.stderr)
            return 2
    except RuntimeError as exc:
        print(f"operator_gated_pr_guard: {exc}", file=sys.stderr)
        return 2

    if not needs_attestation(changed, labels):
        print(
            "operator_gated_pr_guard: out of scope (no GATE_FILES, no operator-gated)"
        )
        return 0

    if args.pr is None or not args.head:
        print(
            "operator_gated_pr_guard: in scope but missing --pr and --head "
            "(bind attestation to this PR).",
            file=sys.stderr,
        )
        return 2

    if args.message_file is None or not args.message_file.is_file():
        print(
            "operator_gated_pr_guard: in scope but missing --message-file "
            "(latest PR comment).",
            file=sys.stderr,
        )
        return 1

    body = args.message_file.read_text(encoding="utf-8")
    ok, msg = latest_comment_approves(body, pr_number=args.pr, head_sha=args.head)
    if ok:
        print(f"operator_gated_pr_guard: attested — {msg}")
        return 0
    print(f"operator_gated_pr_guard: BLOCKED — {msg}", file=sys.stderr)
    touched = gate_files_touched(changed)
    if touched:
        print("GATE_FILES in this PR:", ", ".join(touched), file=sys.stderr)
    print(
        "Reuse GATE_FILES from gate_change_tripwire.py:",
        len(GATE_FILES),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

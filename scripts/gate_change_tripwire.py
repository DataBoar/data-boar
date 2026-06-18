#!/usr/bin/env python3
"""Self-protecting gate tripwire (issue #944, ADR-0071).

Fails LOUD when a PR/commit range modifies a *gate file* (the PII matcher, history
guard, hooks, CI wiring, CODEOWNERS, the FP allowlist, gate ADRs, or the hard rule)
*unless* the range carries an explicit operator marker trailer.

This closes the "the gated modifies the gate" failure mode: the gate that audits a
PR can no longer be silently weakened inside that same PR. The cryptographic control
is signed commits + CODEOWNERS review (operator-configured branch protection); this
tripwire is the LOUD, reviewable secondary signal that the change was *intentional*
and acknowledged.

Marker (one line in any commit message of the range)::

    Gate-Change-Approved-By: @<operator-handle>

Exit codes: 0 ok/approved/out-of-scope, 1 gate touched without marker, 2 tool error.

The matcher logic is NEVER the place to silence a false positive: use the
operator-approved per-location allowlist (security/pii_gate_allowlist.txt) instead.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Tracked files whose change must be acknowledged by the gate owner.
# The live denylist docs/private/security_audit/PII_LOCAL_SEEDS.txt is gitignored,
# so it never appears in a diff; its tracked template carries the policy instead.
GATE_FILES: frozenset[str] = frozenset(
    {
        "scripts/gatekeeper_audit.py",
        "scripts/gatekeeper-audit.ps1",
        "scripts/pii_history_guard.py",
        "scripts/gate_change_tripwire.py",
        ".pre-commit-config.yaml",
        ".github/workflows/ci.yml",
        ".github/CODEOWNERS",
        "tests/test_pii_guard.py",
        "tests/test_gatekeeper_audit_word_boundary.py",
        "tests/test_gate_change_tripwire.py",
        "security/pii_gate_allowlist.txt",
        "docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt",
        "docs/adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md",
        "docs/adr/ADR-0020-ci-full-git-history-pii-gate.md",
        "docs/adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md",
        "docs/adr/ADR-0071-self-protecting-pii-gate.md",
        "docs/plans/PLAN_PII_GATE_INTEGRITY.md",
        ".cursor/rules/never-weaken-security-gates.mdc",
    }
)

MARKER_RE = re.compile(r"(?im)^\s*Gate-Change-Approved-By:\s*@?\S+")


def gate_files_touched(changed: list[str]) -> list[str]:
    norm = {c.replace("\\", "/").strip() for c in changed if c.strip()}
    return sorted(norm & GATE_FILES)


def marker_present(commit_messages: str) -> bool:
    return bool(MARKER_RE.search(commit_messages or ""))


def evaluate(changed: list[str], commit_messages: str) -> tuple[int, list[str]]:
    """Pure decision core (unit-testable): (exit_code, touched_gate_files)."""
    touched = gate_files_touched(changed)
    if not touched:
        return 0, []
    if marker_present(commit_messages):
        return 0, touched
    return 1, touched


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _resolve_base(base: str) -> str | None:
    if _git(["rev-parse", "--verify", "--quiet", base]).returncode == 0:
        return base
    return None


def _detect_range(base: str) -> tuple[list[str], str] | None:
    resolved = _resolve_base(base)
    if resolved is None:
        return None
    diff = _git(["diff", "--name-only", f"{resolved}...HEAD"])
    if diff.returncode != 0:
        return None
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    log = _git(["log", "--format=%B", f"{resolved}..HEAD"])
    messages = log.stdout if log.returncode == 0 else ""
    return changed, messages


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base ref to diff HEAD against (default: origin/main).",
    )
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=None,
        help="Override changed file list (testing). Skips git detection.",
    )
    parser.add_argument(
        "--commit-messages",
        default=None,
        help="Override commit-message text to scan for the marker (testing).",
    )
    args = parser.parse_args(argv)

    if args.changed_files is not None or args.commit_messages is not None:
        changed = args.changed_files or []
        messages = args.commit_messages or ""
    else:
        detected = _detect_range(args.base)
        if detected is None:
            # Fail open: base ref unresolvable (e.g. shallow clone without
            # origin/main). CODEOWNERS + signed-commit branch protection remain the
            # hard control; do not block unrelated CI on a missing ref.
            sys.stderr.write(
                "GATE-TRIPWIRE: SKIP -- could not resolve base "
                f"'{args.base}' (range undetermined). CODEOWNERS still enforces.\n"
            )
            return 0
        changed, messages = detected

    code, touched = evaluate(changed, messages)
    if code == 0 and not touched:
        sys.stderr.write("GATE-TRIPWIRE: OK (no gate files changed in range).\n")
        return 0
    if code == 0:
        sys.stderr.write(
            "GATE-TRIPWIRE: OK (gate files changed WITH operator marker):\n"
            + "".join(f"  - {p}\n" for p in touched)
        )
        return 0

    sys.stderr.write(
        "GATE-TRIPWIRE: BLOCKED -- this change modifies the security gate that "
        "audits it.\n"
        "The following gate file(s) changed without an operator marker:\n"
        + "".join(f"  - {p}\n" for p in touched)
        + "\n"
        "A gate change MUST be intentional and operator-acknowledged. Either:\n"
        "  1. The operator reviews + approves via CODEOWNERS (branch protection), AND\n"
        "  2. a commit in this range carries the trailer:\n"
        "       Gate-Change-Approved-By: @FabioLeitao\n\n"
        "NEVER weaken/disable/bypass a security gate to pass CI. A false positive is "
        "resolved by tightening the pattern + the per-location allowlist "
        "(security/pii_gate_allowlist.txt), never by loosening the matcher. "
        "See ADR-0071 / issue #944.\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

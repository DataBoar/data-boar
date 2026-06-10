"""
History-focused PII anti-recurrence guard.

Default mode scans added lines in `origin/main...HEAD` diffs (three-dot / merge-base)
to block new sensitive patterns before commit/PR. The logical range label remains
`origin/main..HEAD` for rev-list semantics; `git diff` uses three-dot syntax.

Optional `--full-history` scans added lines across full git history.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_RANGE = "origin/main..HEAD"

FORBIDDEN_LINE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Windows absolute user path (non-placeholder)",
        re.compile(
            r"(?i)\bc:\\users\\"
            r"(?!<username>|<you>|user(?:name)?\b|public\b|default\b|all users\b|\.\.\.)"
            r"(?!fabio\\)"
            r"[a-z0-9._-]+\\"
        ),
    ),
    (
        "Linux absolute /home path (non-placeholder)",
        re.compile(
            r"(?i)(?<!\w)/home/"
            r"(?!user/|you/|<user>/|replace_user/|\{\{|leitao/)"
            r"[a-z0-9._-]+/"
        ),
    ),
    (
        "LinkedIn profile URL (explicit personal slug)",
        re.compile(
            r"(?i)https?://(?:www\.)?linkedin\.com/in/"
            r"(?!example(?:[\"'\s`]|\Z)|<|\.{3}|replaced|redacted|\$|\{)"
            r"[^\s\"')]+"
        ),
    ),
    (
        "Family relationship phrase (sensitive context)",
        re.compile(r"(?i)\b(my\s+wif[e]|my\s+sister(?:'s|s)\s+husband|cunhad[oa])\b"),
    ),
    (
        "Family phrase (Portuguese, high-signal)",
        re.compile(r"(?i)\btrabalho\s+da\s+esposa\b"),
    ),
    (
        "SSH URL with embedded user",
        re.compile(
            r"(?i)\bssh://(?!USER_REDACTED\b)([a-z0-9._-]+)@"
            r"(?!myserver\.example\.com\b|example\.com\b)"
        ),
    ),
)

_HISTORY_GUARD_EXEMPT_PATHS = {
    "scripts/pii_history_guard.py",
    "scripts/filter_repo_pii_replacements.txt",
    "tests/test_pii_guard.py",
    # cd45be6e (#786) added real SSH URL before this guard existed — pending filter-repo cleanup
    "docs/plans/PLAN_MAESTRO_LINUX_ORCHESTRATOR.md",
}

# Template tree: may document sensitive *topics* with redacted wording; do not treat as new leaks.
_HISTORY_PATH_PREFIX_EXEMPT = ("docs/private.example/",)


def _path_exempt_from_history_scan(path: str) -> bool:
    norm = path.replace("\\", "/")
    return any(norm.startswith(pfx) for pfx in _HISTORY_PATH_PREFIX_EXEMPT)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc


def _resolve_scan_range(full_history: bool) -> str:
    if full_history:
        return "--all"
    origin_main = _git(["rev-parse", "--verify", "origin/main"])
    if origin_main.returncode == 0:
        return DEFAULT_SCAN_RANGE
    return "HEAD"


def _extract_added_lines(patch_text: str) -> list[str]:
    if not patch_text:
        return []
    lines: list[str] = []
    current_path = ""
    for raw in patch_text.splitlines():
        if raw.startswith("+++ b/"):
            current_path = raw.removeprefix("+++ b/")
            continue
        if raw.startswith("+++ "):
            continue
        if raw.startswith("+"):
            if current_path in _HISTORY_GUARD_EXEMPT_PATHS:
                continue
            if _path_exempt_from_history_scan(current_path):
                continue
            lines.append(raw[1:])
    return lines


_DEFAULT_MAX_DIFF_SIZE_MB = 500


def _collect_lines_to_scan(scan_range: str, max_diff_size_mb: int) -> list[str]:
    if scan_range == "--all":
        proc = _git(["log", "--all", "-p", "--unified=0", "--no-color", "--", "."])
    else:
        scan_range_for_diff = (
            scan_range.replace("..HEAD", "...HEAD")
            if not scan_range.startswith("-")
            else scan_range
        )
        proc = _git(
            ["diff", "--unified=0", "--no-color", scan_range_for_diff, "--", "."]
        )
    if proc.returncode != 0:
        raise RuntimeError(f"git patch scan failed: {proc.stderr.strip()}")
    diff_bytes = len(proc.stdout.encode("utf-8", errors="replace"))
    limit_bytes = max_diff_size_mb * 1024 * 1024
    if diff_bytes > limit_bytes:
        raise RuntimeError(
            f"pii_history_guard: diff output is {diff_bytes // (1024 * 1024)} MB "
            f"which exceeds --max-diff-size-mb {max_diff_size_mb}. "
            "Run with a larger limit or narrow the scan range. "
            "See docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md §Memory."
        )
    return _extract_added_lines(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="PII history anti-recurrence guard")
    parser.add_argument(
        "--full-history",
        action="store_true",
        help="scan complete git history instead of origin/main...HEAD range",
    )
    parser.add_argument(
        "--max-diff-size-mb",
        type=int,
        default=_DEFAULT_MAX_DIFF_SIZE_MB,
        metavar="MB",
        help=(
            "Abort if the combined git diff/log patch output exceeds this size "
            f"in megabytes (default: {_DEFAULT_MAX_DIFF_SIZE_MB} MB). "
            "Prevents OOM on very large repositories. "
            "Increase for repos with unusually large histories. "
            "See docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md §Memory."
        ),
    )
    args = parser.parse_args()

    if not (REPO_ROOT / ".git").exists():
        print("pii_history_guard: not a git repository; skipping.")
        return 0

    scan_range = _resolve_scan_range(args.full_history)
    lines = _collect_lines_to_scan(scan_range, args.max_diff_size_mb)
    violations: list[str] = []
    for idx, line in enumerate(lines, start=1):
        for label, pattern in FORBIDDEN_LINE_PATTERNS:
            if pattern.search(line):
                snippet = line.strip()
                if len(snippet) > 180:
                    snippet = snippet[:177] + "..."
                violations.append(f"{label} :: line#{idx} :: {snippet}")

    if violations:
        scope = "full history" if args.full_history else "origin/main...HEAD"
        print("PII history guard failed. Found forbidden patterns in git history:")
        print(f"  scope: {scope}")
        for violation in violations[:20]:
            print(f"  - {violation}")
        if len(violations) > 20:
            print(f"  ... {len(violations) - 20} more")
        print(
            "Remediate before commit/PR (filter-repo if needed). "
            "Do not push sensitive history."
        )
        return 1

    scope = "full history" if args.full_history else "origin/main...HEAD"
    print(f"PII history guard: OK (no forbidden literals in {scope}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

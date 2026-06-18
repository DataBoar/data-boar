#!/usr/bin/env python3
"""PII seed gate for staged blobs — parity with scripts/gatekeeper-audit.ps1.

Loads fixed-string seeds from docs/private/security_audit/PII_LOCAL_SEEDS.txt (usually
gitignored). Excludes public maintainer / lab anchors that match gatekeeper-audit.ps1.

Exit codes: 0 ok/skip, 1 seed hit or --require-seeds with missing file, 2 git/tool failure.

Never logs raw seed literals on failure — prints git grep locations only.

"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SEEDS_REL = Path("docs") / "private" / "security_audit" / "PII_LOCAL_SEEDS.txt"
ALLOWLIST_REL = Path("security") / "pii_gate_allowlist.txt"


def load_allowlist(path: Path) -> list[tuple[str, str]]:
    """Operator-approved per-location FP exceptions: (repo_relative_path, seed).

    Sanctioned way to silence a confirmed false positive (issue #944, ADR-0071) --
    NEVER by loosening the matcher. File is CODEOWNERS-protected.
    """
    if not path.is_file():
        return []
    entries: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split("|")
        if len(parts) < 2:
            continue
        rel = parts[0].strip().replace("\\", "/")
        seed = parts[1].strip()
        if rel and seed:
            entries.append((rel, seed))
    return entries


def _seeds_in_line(content: str, strict_seeds: list[str]) -> set[str]:
    """Strict seeds present in a line under word-boundary semantics (mirror -w)."""
    found: set[str] = set()
    for seed in strict_seeds:
        if re.search(r"(?<!\w)" + re.escape(seed) + r"(?!\w)", content):
            found.add(seed)
    return found


def filter_allowlisted(
    hit_text: str,
    strict_seeds: list[str],
    allowlist: list[tuple[str, str]],
) -> str:
    """Drop hit lines whose every matched seed is allowlisted for that path.

    Fail-safe: if a line's seed set cannot be identified, the line is KEPT.
    """
    if not allowlist:
        return hit_text
    allow_by_path: dict[str, set[str]] = {}
    for rel, seed in allowlist:
        allow_by_path.setdefault(rel, set()).add(seed)

    kept: list[str] = []
    for line in hit_text.splitlines():
        m = re.match(r"^(.*?):(\d+):(.*)$", line)
        if not m:
            kept.append(line)
            continue
        path = m.group(1).replace("\\", "/")
        content = m.group(3)
        seeds_here = _seeds_in_line(content, strict_seeds)
        allowed = allow_by_path.get(path, set())
        if seeds_here and not (seeds_here - allowed):
            continue  # every matched seed is an approved FP at this path
        kept.append(line)
    return "\n".join(kept)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_seeds_filtered(path: Path) -> tuple[list[str], list[str]]:
    """Return (strict_seeds, all_non_comment_seeds_without_public_filter)."""
    if not path.is_file():
        return [], []

    raw = path.read_text(encoding="utf-8").splitlines()
    all_rows: list[str] = []
    for line in raw:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        all_rows.append(s)

    strict: list[str] = []
    for s in all_rows:
        if public_identity_seed_excluded(s):
            continue
        strict.append(s)

    return strict, all_rows


def public_identity_seed_excluded(seed: str) -> bool:
    """Match scripts/gatekeeper-audit.ps1 Test-PublicIdentitySeedExcluded."""

    t = seed.strip()
    if not t:
        return True
    lower = t.lower()
    if lower == "fabioleitao":
        return True

    pathish = lower.replace("/", "\\")
    if pathish in {"c:\\users\\fabio", "c:\\users\\fabio\\"}:
        return True

    if lower in {"/home/leitao", "/home/leitao/"}:
        return True
    if pathish in {"\\home\\leitao", "\\home\\leitao\\"}:
        return True

    return False


def git_grep_strict_seeds(
    repo: Path,
    strict_seeds: list[str],
    paths: list[str],
    allowlist: list[tuple[str, str]] | None = None,
) -> tuple[str | None, int]:
    """Return (stdout hit text or None, exit code 0/1/2).

    Operator-approved per-location FP exceptions (allowlist) are filtered out before
    a hit is reported -- never by loosening the matcher (issue #944, ADR-0071).
    """

    allowlist = allowlist or []
    kept_all: list[str] = []
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.writelines(line + "\n" for line in strict_seeds)

        batch = 60
        for i in range(0, len(paths), batch):
            chunk = paths[i : i + batch]
            proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "grep",
                    "-n",
                    # -w (word-boundary): a seed only matches when delimited by non-word
                    # chars, so a short seed (e.g. a given name) never substring-collides
                    # with a larger word (issue #944). Sensitivity is preserved: whole-word
                    # and full-string seeds still match. Pair with distinctive seeds
                    # (full name / rare bigram), never isolated common fragments.
                    "-w",
                    "-F",
                    "-f",
                    str(tmp_path),
                    "--cached",
                    "--",
                    *chunk,
                ],
                capture_output=True,
                text=True,
            )
            stdout = proc.stdout.strip()
            if proc.returncode == 0:
                if stdout:
                    filtered = filter_allowlisted(stdout, strict_seeds, allowlist)
                    if filtered.strip():
                        kept_all.append(filtered)
            elif proc.returncode == 1:
                if stdout:
                    sys.stderr.write(
                        "GATEKEEPER-AUDIT: Unexpected output from git grep with exit code 1\n"
                    )
                    return stdout, 2
            else:
                sys.stderr.write(
                    f"GATEKEEPER-AUDIT: git grep failed ({proc.returncode}):\n"
                    f"{proc.stdout}\n{proc.stderr}".strip()
                    + "\n"
                )
                return None, 2

    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:  # noqa: BLE001
                pass  # temp cleanup best-effort

    if kept_all:
        return "\n".join(kept_all), 0
    return None, 0


def run_gate(*, repo: Path, seeds_path: Path, require_seeds: bool) -> int:
    cw = sys.stderr.write

    if not seeds_path.is_file():
        if require_seeds:
            cw(
                f"GATEKEEPER-AUDIT: Seeds file required but missing: {seeds_path}\n"
                "Copy from docs/private.example/security_audit/"
                "PII_LOCAL_SEEDS.example.txt\n"
            )
            return 1
        cw(
            "GATEKEEPER-AUDIT: SKIP (no seeds file). Not an error — enable by copying "
            "PII_LOCAL_SEEDS.example.txt to docs/private/security_audit/"
            "PII_LOCAL_SEEDS.txt\n"
        )
        return 0

    strict, all_rows = load_seeds_filtered(seeds_path)

    # Parity with gatekeeper-audit.ps1: comment-only seeds file skips before header.
    if not all_rows:
        cw(
            "GATEKEEPER-AUDIT: No active seed lines (only comments/blank). "
            "Nothing to scan.\n"
        )
        return 0

    skipped_pub = len(all_rows) - len(strict)

    cw(
        "=== gatekeeper-audit: PII seeds vs staged paths (--cached, strict seeds "
        "only) ===\n"
        f"  Seeds file: {seeds_path} ({len(all_rows)} active; {len(strict)} after "
        "public-identity filter)\n"
    )
    if skipped_pub > 0:
        cw(
            f"  Public-identity seeds excluded from scan: {skipped_pub} "
            "(FabioLeitao, C:\\Users\\fabio, /home/leitao)\n"
        )

    if not strict:
        cw("GATEKEEPER-AUDIT: OK (no strict seeds to scan).\n")
        return 0

    exclude_leaf = frozenset({"uv.lock"})
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRT",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        cw(
            "GATEKEEPER-AUDIT: git diff --cached --name-only failed:\n"
            f"{proc.stdout}\n{proc.stderr}".strip()
            + "\n"
        )
        return 2

    staged = [p.strip() for p in proc.stdout.splitlines() if p.strip()]
    if not staged:
        cw("GATEKEEPER-AUDIT: OK (nothing staged; no paths to scan).\n")
        return 0

    paths: list[str] = []
    skipped_lock = 0
    for p in staged:
        if Path(p).name in exclude_leaf:
            skipped_lock += 1
            continue
        paths.append(p)

    if skipped_lock > 0:
        cw(
            f"  Skipped seed scan for {skipped_lock} path(s) "
            "(machine-generated: uv.lock).\n"
        )

    if not paths:
        cw(
            "GATEKEEPER-AUDIT: OK (only machine-generated paths staged; nothing "
            "left to scan).\n"
        )
        return 0

    cw(f"  Staged path(s) scanned: {len(paths)} (of {len(staged)} total staged)\n")

    allowlist = load_allowlist(repo / ALLOWLIST_REL)
    if allowlist:
        cw(
            f"  Sanctioned FP allowlist: {len(allowlist)} entr(y/ies) from "
            f"{ALLOWLIST_REL} (operator-approved, per-location).\n"
        )

    hit, code = git_grep_strict_seeds(repo, strict, paths, allowlist)
    if code != 0:
        return code
    if hit:
        cw(
            "GATEKEEPER-AUDIT: HIT — staged content matches a strict PII seed "
            "(not public-identity allowlist):\n"
        )
        cw(hit + "\n")
        cw("GATEKEEPER-AUDIT: ABORT — redact or unstage before commit/push.\n")
        return 1

    cw("GATEKEEPER-AUDIT: OK (no strict seed hits in staged paths).\n")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--require-seeds",
        action="store_true",
        help="Fail exit 1 if the seeds file is missing.",
    )
    parser.add_argument(
        "--seeds-path",
        type=Path,
        default=None,
        help="Override path to PII_LOCAL_SEEDS.txt.",
    )
    args = parser.parse_args(argv)

    repo = _repo_root()
    seeds_path = Path(args.seeds_path) if args.seeds_path else repo / DEFAULT_SEEDS_REL
    if not seeds_path.is_absolute():
        seeds_path = (repo / seeds_path).resolve()

    os.chdir(repo)
    return run_gate(repo=repo, seeds_path=seeds_path, require_seeds=args.require_seeds)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

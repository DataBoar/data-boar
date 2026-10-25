#!/usr/bin/env python3
"""Build a single UTF-8 text bundle for external LLM review (Gemini, etc.).

- Includes **only tracked** paths from ``git ls-files`` (no accidental private copy).
- Each file is wrapped with ``--- FILE: relative/path ---`` so you can split, diff, or re-verify.
- Optionally appends GitHub Actions workflows and compliance sample YAML.

Does **not** read ``docs/private/`` (those paths are not in Git).

Usage (bash):
  uv run python scripts/export_public_gemini_bundle.py \\
      --output docs/private/gemini_bundles/public_bundle_$(date -I).txt

Usage (PowerShell — do not use ``$(date -I)``; it is bash-only and breaks the path):
  uv run python scripts/export_public_gemini_bundle.py `
      --output "docs/private/gemini_bundles/public_bundle_$(Get-Date -Format 'yyyy-MM-dd').txt" `
      --compliance-yaml --verify

  uv run python scripts/export_public_gemini_bundle.py -o /tmp/bundle.txt --verify

See ``docs/ops/GEMINI_PUBLIC_BUNDLE_REVIEW.md`` for the suggested review prompt.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_FILE_HEADER = re.compile(r"^--- FILE: (.+?) ---\s*$", re.MULTILINE)


def _git_ls_files(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
    )
    raw = proc.stdout.decode("utf-8", errors="replace")
    return [p for p in raw.split("\0") if p]


def collect_paths(
    repo_root: Path,
    *,
    include_md: bool,
    include_workflows: bool,
    include_compliance_yaml: bool,
    include_cursor: bool,
    include_plans: bool,
) -> list[str]:
    all_files = _git_ls_files(repo_root)
    out: list[str] = []
    for f in all_files:
        if f.startswith("docs/private/"):
            continue
        if not include_cursor and f.startswith(".cursor/"):
            continue
        if not include_plans and f.startswith("docs/plans/"):
            continue
        if include_md and f.endswith(".md"):
            out.append(f)
            continue
        if include_workflows:
            if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml")):
                out.append(f)
                continue
            if f == ".github/dependabot.yml":
                out.append(f)
                continue
        if include_compliance_yaml:
            if f.startswith("docs/compliance-samples/") and f.endswith(".yaml"):
                out.append(f)
                continue
    return sorted(set(out), key=lambda p: p.replace("/", "\0"))


def verify_bundle(
    bundle_path: Path,
    repo_root: Path,
    *,
    include_md: bool,
    include_workflows: bool,
    include_compliance_yaml: bool,
    include_cursor: bool,
    include_plans: bool,
) -> int:
    """Ensure every expected FILE section matches disk content sequentially.

    We intentionally avoid regex-based marker scanning here because marker-like text
    can appear inside documentation examples and would cause false mismatches.
    """
    text = bundle_path.read_text(encoding="utf-8")
    expected_paths = collect_paths(
        repo_root,
        include_md=include_md,
        include_workflows=include_workflows,
        include_compliance_yaml=include_compliance_yaml,
        include_cursor=include_cursor,
        include_plans=include_plans,
    )

    pos = 0
    bad = 0
    checked = 0
    for rel in expected_paths:
        p = repo_root / rel
        if not p.is_file():
            continue
        disk = p.read_text(encoding="utf-8")
        header = f"--- FILE: {rel} ---\n"
        expected_block = header + disk
        block_len = len(expected_block)
        candidate = text[pos : pos + block_len]
        if candidate != expected_block:
            print(f"MISMATCH: {rel}", file=sys.stderr)
            bad += 1
        else:
            print(f"OK {rel}")
        pos += block_len
        checked += 1

    if pos != len(text):
        print(
            f"MISMATCH: trailing or missing content after verify cursor ({len(text) - pos} chars delta)",
            file=sys.stderr,
        )
        bad += 1
    print(f"--- verify: {checked} sections, {bad} problems ---", file=sys.stderr)
    return 1 if bad else 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Output bundle path (UTF-8)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--no-md",
        action="store_true",
        help="Exclude *.md",
    )
    parser.add_argument(
        "--no-workflows",
        action="store_true",
        help="Exclude .github/workflows and dependabot.yml",
    )
    parser.add_argument(
        "--compliance-yaml",
        action="store_true",
        help="Include docs/compliance-samples/*.yaml",
    )
    parser.add_argument(
        "--cursor",
        action="store_true",
        help="Include .cursor/**/*.md (off by default)",
    )
    parser.add_argument(
        "--plans",
        action="store_true",
        help="Include docs/plans/**/*.md (off by default; large)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="After write, re-read and diff each section vs repo",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print path count and first/last paths only",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    paths = collect_paths(
        repo_root,
        include_md=not args.no_md,
        include_workflows=not args.no_workflows,
        include_compliance_yaml=args.compliance_yaml,
        include_cursor=args.cursor,
        include_plans=args.plans,
    )
    if args.dry_run:
        print(f"Would bundle {len(paths)} paths")
        if paths:
            print(f"  first: {paths[0]}")
            print(f"  last: {paths[-1]}")
        return 0

    parts: list[str] = []
    for rel in paths:
        p = repo_root / rel
        try:
            body = p.read_text(encoding="utf-8")
        except OSError as e:
            print(f"SKIP (read error) {rel}: {e}", file=sys.stderr)
            continue
        parts.append(f"--- FILE: {rel} ---\n{body}")

    out_path = args.output.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_text = "".join(parts)
    if not bundle_text.endswith("\n"):
        bundle_text += "\n"
    out_path.write_text(bundle_text, encoding="utf-8", newline="\n")
    n = bundle_text.count("--- FILE:")
    print(
        f"Wrote {n} sections, {len(bundle_text.encode('utf-8'))} bytes -> {out_path}",
        file=sys.stderr,
    )

    if args.verify:
        return verify_bundle(
            out_path,
            repo_root,
            include_md=not args.no_md,
            include_workflows=not args.no_workflows,
            include_compliance_yaml=args.compliance_yaml,
            include_cursor=args.cursor,
            include_plans=args.plans,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

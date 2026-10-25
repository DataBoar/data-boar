#!/usr/bin/env python3
"""
Regenerate the auto-generated plan table in docs/plans/PLANS_HUB.md.

Every PLAN_*.md under docs/plans/ and docs/plans/completed/ should appear
exactly once. Optional per-plan hints in the plan file body:

  <!-- plans-hub-summary: One line describing intent for humans. -->
  <!-- plans-hub-related: PLAN_OTHER.md, completed/PLAN_OLD.md -->

Usage:
  python scripts/plans_hub_sync.py --write
  python scripts/plans_hub_sync.py --check
  python scripts/plans_hub_sync.py --stdout
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = REPO_ROOT / "docs" / "plans"
COMPLETED_DIR = PLANS_DIR / "completed"
HUB_PATH = PLANS_DIR / "PLANS_HUB.md"
START = "<!-- PLANS_HUB_TABLE:START -->"
END = "<!-- PLANS_HUB_TABLE:END -->"

SUMMARY_RE = re.compile(r"<!--\s*plans-hub-summary:\s*(.+?)\s*-->", re.DOTALL)
RELATED_RE = re.compile(r"<!--\s*plans-hub-related:\s*(.+?)\s*-->", re.DOTALL)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sync PLANS_HUB.md auto table with PLAN_*.md files."
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", action="store_true", help="Refresh block in PLANS_HUB.md"
    )
    mode.add_argument("--check", action="store_true", help="Fail if block is stale")
    mode.add_argument("--stdout", action="store_true", help="Print block only")
    return p.parse_args()


def discover_plan_files() -> list[tuple[Path, str]]:
    """Return (absolute_path, link_prefix) where link_prefix is '' or 'completed/'."""
    out: list[tuple[Path, str]] = []
    # Sort by basename string only; Path ordering differs on Windows vs POSIX (CI/Linux).
    for p in sorted(PLANS_DIR.glob("PLAN_*.md"), key=lambda x: x.name):
        out.append((p, ""))
    for p in sorted(COMPLETED_DIR.glob("PLAN_*.md"), key=lambda x: x.name):
        out.append((p, "completed/"))
    return out


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            return stripped[2:].strip()
    return "Untitled"


def _pipe_safe(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def _extract_summary(text: str) -> str:
    m = SUMMARY_RE.search(text)
    if m:
        return _pipe_safe(m.group(1))[:220]
    purpose = re.search(
        r"^\*\*Purpose:\*\*\s*(.+)$", text, re.MULTILINE | re.IGNORECASE
    )
    if purpose:
        return _pipe_safe(purpose.group(1))[:220]
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip().startswith("# "):
        i += 1
    i += 1
    buf: list[str] = []
    for j in range(i, min(i + 40, len(lines))):
        line = lines[j].strip()
        if not line:
            if buf:
                break
            continue
        if line.startswith("#"):
            break
        if line.startswith("```") or line.startswith("|"):
            continue
        if line.startswith("<!--"):
            continue
        if re.match(r"^\*\*(Português|English|Synced with)", line):
            continue
        buf.append(line)
        if sum(len(x) for x in buf) > 200:
            break
    joined = _pipe_safe(" ".join(buf))
    return joined[:220] if joined else "—"


def _extract_related(text: str, _basename: str) -> str:
    m = RELATED_RE.search(text)
    if not m:
        return "—"
    parts = [x.strip() for x in m.group(1).split(",") if x.strip()]
    links: list[str] = []
    for ref in parts[:6]:
        ref = ref.replace("\\", "/")
        label = Path(ref).name
        if not label.endswith(".md"):
            label = f"{label}.md"
        target = ref if ref.endswith(".md") else f"{ref}.md"
        links.append(f"[{label}]({target})")
    return " ".join(links) if links else "—"


def compute_table_block() -> str:
    rows: list[str] = [
        "| Status | Document | Title | Summary | Related plans |",
        "| ------ | -------- | ----- | ------- | -------------- |",
    ]
    for path, prefix in discover_plan_files():
        text = path.read_text(encoding="utf-8")
        name = path.name
        status = "**Completed**" if prefix else "**Open**"
        title = _pipe_safe(_extract_title(text))
        summary = _extract_summary(text)
        related = _extract_related(text, name)
        link = f"[{name}]({prefix}{name})"
        rows.append(f"| {status} | {link} | {title} | {summary} | {related} |")
    return "\n".join(rows) + "\n"


def _replace_block(full: str, new_inner: str) -> str:
    if START not in full or END not in full:
        msg = f"{HUB_PATH}: missing {START} or {END}"
        raise SystemExit(msg)
    before, rest = full.split(START, 1)
    _, after = rest.split(END, 1)
    inner = f"\n{new_inner}\n"
    return f"{before}{START}{inner}{END}{after}"


def main() -> None:
    args = parse_args()
    block = compute_table_block()
    if args.stdout:
        print(block, end="")
        return
    if not HUB_PATH.is_file():
        print(f"Missing {HUB_PATH}", file=sys.stderr)
        sys.exit(1)
    text = HUB_PATH.read_text(encoding="utf-8")
    expected = _replace_block(text, block)
    if args.write:
        HUB_PATH.write_text(expected, encoding="utf-8", newline="\n")
        return
    if args.check:
        if START not in text or END not in text:
            print("PLANS_HUB.md: missing markers", file=sys.stderr)
            sys.exit(1)
        inner_start = text.index(START) + len(START)
        inner_end = text.index(END)
        current = text[inner_start:inner_end].strip("\n") + "\n"
        if current != block:
            print(
                "PLANS_HUB.md table is stale. Run: python scripts/plans_hub_sync.py --write",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()

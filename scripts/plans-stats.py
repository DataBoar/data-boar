#!/usr/bin/env python3
"""
Generate and validate an auto-updated "Status dashboard" block in docs/plans/PLANS_TODO.md.

Usage:
  python scripts/plans-stats.py --write   # refresh block in-place
  python scripts/plans-stats.py --check   # fail if block is stale
  python scripts/plans-stats.py --stdout  # print block only
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

START = "<!-- PLANS_STATUS_DASHBOARD:START -->"
END = "<!-- PLANS_STATUS_DASHBOARD:END -->"

DEFAULT_PATH = Path("docs/plans/PLANS_TODO.md")
HORIZONS = ("H0", "H1", "H2", "H3", "H4", "H5", "UNSPECIFIED")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Refresh/check PLANS_TODO status dashboard."
    )
    p.add_argument("--path", default=str(DEFAULT_PATH), help="Path to PLANS_TODO.md")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", action="store_true", help="Write refreshed block in file"
    )
    mode.add_argument("--check", action="store_true", help="Check block is up-to-date")
    mode.add_argument("--stdout", action="store_true", help="Print generated block")
    return p.parse_args()


def _extract_horizon(heading_line: str) -> str | None:
    m = re.search(r"\b(H[0-5])\b", heading_line)
    return m.group(1) if m else None


def _is_status_row(line: str) -> bool:
    if not line.startswith("|"):
        return False
    # Skip markdown separators.
    if re.match(r"^\|\s*-+\s*\|", line):
        return False
    return any(
        token in line
        for token in (
            "✅",
            "⬜",
            "🔄",
            "Under consideration",
            "Tracked (partially done)",
        )
    )


def compute_stats(text: str) -> dict:
    current_horizon = "UNSPECIFIED"
    done = 0
    incomplete = 0
    pending = 0
    tracked = 0
    under_consideration = 0
    backlog = 0
    total_rows = 0
    by_h_total: dict[str, int] = defaultdict(int)
    by_h_done: dict[str, int] = defaultdict(int)
    by_h_incomplete: dict[str, int] = defaultdict(int)

    for line in text.splitlines():
        if line.startswith("#"):
            h = _extract_horizon(line)
            if h:
                current_horizon = h
        if not _is_status_row(line):
            continue

        total_rows += 1
        by_h_total[current_horizon] += 1
        row_done = "✅" in line
        if row_done:
            done += 1
            by_h_done[current_horizon] += 1
        else:
            incomplete += 1
            by_h_incomplete[current_horizon] += 1
            if "⬜" in line:
                pending += 1
            if "🔄" in line or "Tracked (partially done)" in line:
                tracked += 1
            if "Under consideration" in line:
                under_consideration += 1
            if "Backlog" in line:
                backlog += 1

    # Ensure all horizons appear in output order.
    for h in HORIZONS:
        by_h_total[h] += 0
        by_h_done[h] += 0
        by_h_incomplete[h] += 0

    return {
        "total_rows": total_rows,
        "done": done,
        "incomplete": incomplete,
        "pending": pending,
        "tracked": tracked,
        "under_consideration": under_consideration,
        "backlog": backlog,
        "by_h_total": dict(by_h_total),
        "by_h_done": dict(by_h_done),
        "by_h_incomplete": dict(by_h_incomplete),
    }


def render_dashboard(stats: dict) -> str:
    lines: list[str] = []
    lines.append(START)
    lines.append("## Status dashboard (auto-generated)")
    lines.append("")
    lines.append(
        "Do not edit this block manually; refresh with `python scripts/plans-stats.py --write`."
    )
    lines.append("")
    lines.append(
        f"- **Status rows counted:** {stats['total_rows']}  "
        f"(Done: {stats['done']} | Incomplete: {stats['incomplete']})"
    )
    lines.append(
        f"- **Incomplete breakdown:** Pending `⬜`={stats['pending']}, "
        f"Tracked `🔄` / `Tracked (partially done)`={stats['tracked']}, "
        f"Under consideration={stats['under_consideration']}, "
        f"Backlog-marked rows={stats['backlog']}"
    )
    lines.append("")
    lines.append("| Horizon | Total rows | Done | Incomplete |")
    lines.append("| ------- | ----------: | ----: | ----------: |")
    for h in HORIZONS:
        lines.append(
            f"| `{h}` | {stats['by_h_total'][h]} | {stats['by_h_done'][h]} | {stats['by_h_incomplete'][h]} |"
        )
    lines.append(END)
    return "\n".join(lines)


def replace_block(original: str, block: str) -> str:
    if START in original and END in original:
        pattern = re.compile(
            re.escape(START) + r".*?" + re.escape(END), re.DOTALL | re.MULTILINE
        )
        return pattern.sub(block, original, count=1)
    # Insert after the top intro paragraph chunk (before first --- separator), fallback prepend.
    sep = "\n---\n"
    idx = original.find(sep)
    if idx != -1:
        return original[:idx] + block + "\n\n" + original[idx:]
    return block + "\n\n" + original


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"plans-stats: file not found: {path}", file=sys.stderr)
        return 2

    original = path.read_text(encoding="utf-8")
    stats = compute_stats(original)
    block = render_dashboard(stats)
    refreshed = replace_block(original, block)

    if args.stdout:
        print(block)
        return 0
    if args.write:
        if refreshed != original:
            path.write_text(refreshed, encoding="utf-8")
            print(f"plans-stats: updated {path}")
        else:
            print(f"plans-stats: no changes ({path} already up-to-date)")
        return 0
    if args.check:
        if refreshed != original:
            print(
                "plans-stats: dashboard is stale. Run: python scripts/plans-stats.py --write",
                file=sys.stderr,
            )
            return 1
        print("plans-stats: dashboard is up-to-date")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

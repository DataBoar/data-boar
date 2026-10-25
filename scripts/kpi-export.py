#!/usr/bin/env python3
"""
Export a small W-KPI markdown snapshot from GitHub data.

Token-aware scope:
- KPI 1 (auto): CI pass rate across last N merged PRs to main.
- KPI 2 (semi-auto): Dependabot response latency summary from merged/open Dependabot PRs.

Requires GitHub CLI auth (`gh auth status`).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run_gh_json(args: list[str]) -> Any:
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or "gh call failed")
    return json.loads(proc.stdout or "null")


def _as_dt(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _business_days(start: dt.datetime, end: dt.datetime) -> int:
    if end < start:
        return 0
    day = start.date()
    end_day = end.date()
    count = 0
    while day <= end_day:
        if day.weekday() < 5:
            count += 1
        day += dt.timedelta(days=1)
    return max(0, count - 1)


def _compute_ci_pass_rate(prs: list[dict[str, Any]]) -> tuple[int, int, int]:
    total = len(prs)
    if total == 0:
        return 0, 0, 0
    passed = 0
    for pr in prs:
        checks = pr.get("statusCheckRollup") or []
        # Conservative: if no checks are attached, count as non-passing.
        if checks and all(
            (c.get("conclusion") or "").upper() == "SUCCESS" for c in checks
        ):
            passed += 1
    pct = int(round((passed / total) * 100))
    return passed, total, pct


def _compute_dependabot_latency(prs: list[dict[str, Any]]) -> tuple[str, str]:
    merged_days: list[int] = []
    open_count = 0
    for pr in prs:
        created = _as_dt(pr.get("createdAt"))
        merged = _as_dt(pr.get("mergedAt"))
        if created and merged:
            merged_days.append(_business_days(created, merged))
        elif created and not merged:
            open_count += 1
    avg = (
        "-" if not merged_days else str(int(round(sum(merged_days) / len(merged_days))))
    )
    p95 = "-"
    if merged_days:
        ordered = sorted(merged_days)
        idx = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
        p95 = str(ordered[idx])
    return f"{avg} bd (p95: {p95})", str(open_count)


def _render_block(
    ci_passed: int,
    ci_total: int,
    ci_pct: int,
    dep_latency: str,
    dep_open: str,
    generated_utc: str,
) -> str:
    return "\n".join(
        [
            "### W-KPI snapshot (auto export)",
            "",
            f"- Generated at (UTC): `{generated_utc}`",
            "",
            "| KPI | Current value | Target | Source |",
            "| --- | --- | --- | --- |",
            f"| CI pass rate (last merged PRs) | `{ci_passed}/{ci_total}` (`{ci_pct}%`) | `>= 90%` | `gh pr list --state merged --json statusCheckRollup` |",
            f"| Dependabot response latency (merged) | `{dep_latency}` | `<= 5 business days` | `gh pr list --author app/dependabot` |",
            f"| Dependabot open PRs | `{dep_open}` | `0-2` (context-dependent) | `gh pr list --state open --author app/dependabot` |",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export W-KPI markdown snapshot.")
    parser.add_argument(
        "--limit-prs", type=int, default=10, help="Merged PR sample size"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="Optional output markdown path; prints to stdout when omitted",
    )
    args = parser.parse_args()

    merged_prs = _run_gh_json(
        [
            "pr",
            "list",
            "--state",
            "merged",
            "--base",
            "main",
            "--limit",
            str(max(1, args.limit_prs)),
            "--json",
            "number,mergedAt,statusCheckRollup",
        ]
    )
    dependabot_prs = _run_gh_json(
        [
            "pr",
            "list",
            "--state",
            "all",
            "--search",
            "author:app/dependabot",
            "--limit",
            "30",
            "--json",
            "state,createdAt,mergedAt",
        ]
    )

    ci_passed, ci_total, ci_pct = _compute_ci_pass_rate(merged_prs or [])
    dep_latency, dep_open = _compute_dependabot_latency(dependabot_prs or [])
    generated_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    block = _render_block(
        ci_passed, ci_total, ci_pct, dep_latency, dep_open, generated_utc
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(block, encoding="utf-8")
        print(f"kpi-export: wrote {out_path}")
        return 0
    print(block)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"kpi-export: {exc}", file=sys.stderr)
        raise SystemExit(2)

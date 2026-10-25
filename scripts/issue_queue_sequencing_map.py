#!/usr/bin/env python3
"""
Regenerate docs/ops/ISSUE_QUEUE_SEQUENCING_MAP.md from live GitHub state.

Requires: ``gh`` CLI authenticated for DataBoar/data-boar (GraphQL + issue view).

Usage:
  uv run python scripts/issue_queue_sequencing_map.py --write
  uv run python scripts/issue_queue_sequencing_map.py --check
  uv run python scripts/issue_queue_sequencing_map.py --stdout
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPO_ROOT / "docs" / "ops" / "ISSUE_QUEUE_SEQUENCING_MAP.md"

GRAPHQL_QUERY = """
query($cursor: String) {
  repository(owner: "DataBoar", name: "data-boar") {
    issues(first: 100, after: $cursor, states: OPEN) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        body
        issueType { name }
        milestone { title }
        labels(first: 30) { nodes { name } }
      }
    }
  }
}
"""

BLOCKER_RE = re.compile(
    r"N[AÃ]O\s+INICIAR\s+ANTES\s+DE\s+#(\d+)",
    re.IGNORECASE,
)
P_RE = re.compile(r"\[P([0-3])\]", re.IGNORECASE)
U_RE = re.compile(r"\[U([0-3])\]", re.IGNORECASE)

MILESTONE_MERMAID_ORDER = (
    "v1.8.0",
    "v1.8.1",
    "v1.8.2",
    "v1.8.3",
    "v1.8.4",
    "backlog",
)
ACTIVE_MILESTONE = "v1.8.0"
ISSUE_TYPE_ORDER = ("Bug", "Feature", "Task")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sync ISSUE_QUEUE_SEQUENCING_MAP.md from gh."
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Rewrite the map file")
    mode.add_argument("--check", action="store_true", help="Fail if map is stale")
    mode.add_argument("--stdout", action="store_true", help="Print map to stdout")
    return p.parse_args()


def _gh_graphql(cursor: str | None) -> dict:
    args = ["gh", "api", "graphql", "-f", f"query={GRAPHQL_QUERY}"]
    if cursor:
        args.extend(["-f", f"cursor={cursor}"])
    return json.loads(subprocess.check_output(args, text=True, cwd=REPO_ROOT))


def fetch_open_issues() -> list[dict]:
    issues: list[dict] = []
    cursor: str | None = None
    while True:
        payload = _gh_graphql(cursor)
        conn = payload["data"]["repository"]["issues"]
        issues.extend(conn["nodes"])
        if not conn["pageInfo"]["hasNextPage"]:
            break
        cursor = conn["pageInfo"]["endCursor"]
    return issues


def _issue_state(number: int, cache: dict[int, str]) -> str:
    if number not in cache:
        raw = subprocess.check_output(
            ["gh", "issue", "view", str(number), "--json", "state"],
            text=True,
            cwd=REPO_ROOT,
        )
        cache[number] = json.loads(raw)["state"]
    return cache[number]


def _axis_counts(issues: list[dict], pattern: re.Pattern[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for issue in issues:
        labels = " ".join(n["name"] for n in issue.get("labels", {}).get("nodes", []))
        text = f"{issue.get('title') or ''}\n{issue.get('body') or ''}\n{labels}"
        match = pattern.search(text)
        key = match.group(1) if match else "sem"
        counts[key] += 1
    return counts


def _scan_blockers(
    issues: list[dict],
) -> tuple[dict[int, list[int]], list[tuple[int, int]]]:
    open_nums = {i["number"] for i in issues}
    state_cache: dict[int, str] = {n: "OPEN" for n in open_nums}
    active: dict[int, list[int]] = {}
    stale: list[tuple[int, int]] = []
    for issue in issues:
        text = f"{issue.get('body') or ''}\n{issue.get('title') or ''}"
        for match in BLOCKER_RE.finditer(text):
            blocker = int(match.group(1))
            blocked = issue["number"]
            if blocker in open_nums:
                active.setdefault(blocker, []).append(blocked)
            elif _issue_state(blocker, state_cache) == "CLOSED":
                stale.append((blocked, blocker))
    for nums in active.values():
        nums.sort()
    stale.sort()
    return active, stale


def _milestone_label(title: str, count: int) -> str:
    if title == ACTIVE_MILESTONE:
        return f"Active milestone: {title} ({count} open)"
    if title == "backlog":
        return f"Milestone: backlog ({count} open)"
    return f"Milestone: {title} ({count} open)"


def _mermaid_block(milestone_counts: Counter[str], unassigned: int) -> str:
    lines = ["```mermaid", "flowchart TD", ""]
    node_id = 0
    for ms in MILESTONE_MERMAID_ORDER:
        count = milestone_counts.get(ms, 0)
        if count <= 0:
            continue
        node_id += 1
        sid = f"ms_{node_id}"
        label = _milestone_label(ms, count)
        lines.append(f'subgraph {sid}["{label}"]')
        lines.append(f'  n{node_id}["{count} open in {ms}"]:::p3')
        lines.append("end")
        lines.append("")
    if unassigned:
        node_id += 1
        lines.append(f'subgraph unassigned["No milestone ({unassigned} open)"]')
        lines.append(f'  n{node_id}["{unassigned} open — unassigned"]:::p3')
        lines.append("end")
        lines.append("")
    lines.extend(
        [
            "classDef p0 fill:#c0392b,color:#fff",
            "classDef p1 fill:#e67e22,color:#fff",
            "classDef p2 fill:#2980b9,color:#fff",
            "classDef p3 fill:#7f8c8d,color:#fff",
            "```",
        ]
    )
    return "\n".join(lines)


def _format_v181_list(issues: list[dict]) -> str:
    nums = sorted(
        i["number"]
        for i in issues
        if (i.get("milestone") or {}).get("title") == "v1.8.1"
    )
    if not nums:
        return ""
    joined = ", ".join(f"`#{n}`" for n in nums)
    return (
        f"**v1.8.1** (GitHub, {len(nums)} open — do **not** treat as v1.8.0 work in "
        f"`PLANS_TODO.md`): {joined}."
    )


def build_map(issues: list[dict], *, as_of: date | None = None) -> str:
    as_of = as_of or date.today()
    total = len(issues)
    milestone_counts: Counter[str] = Counter()
    unassigned: list[int] = []
    for issue in issues:
        ms = (issue.get("milestone") or {}).get("title")
        if ms:
            milestone_counts[ms] += 1
        else:
            unassigned.append(issue["number"])

    issue_type_counts: Counter[str] = Counter()
    for issue in issues:
        it = (issue.get("issueType") or {}).get("name") or "(none)"
        issue_type_counts[it] += 1

    p_counts = _axis_counts(issues, P_RE)
    u_counts = _axis_counts(issues, U_RE)
    active, stale = _scan_blockers(issues)

    ms_values = [str(milestone_counts.get(ms, 0)) for ms in MILESTONE_MERMAID_ORDER]
    ms_values.append(str(len(unassigned)))
    milestone_row = " / ".join(ms_values)

    type_values = [str(issue_type_counts.get(name, 0)) for name in ISSUE_TYPE_ORDER]
    if issue_type_counts.get("(none)", 0):
        type_values.append(str(issue_type_counts["(none)"]))
    issue_type_row = " / ".join(type_values)

    p_row = (
        " / ".join(str(p_counts.get(str(n), 0)) for n in range(4))
        + f" / {p_counts.get('sem', 0)}"
    )
    u_row = (
        " / ".join(str(u_counts.get(str(n), 0)) for n in range(4))
        + f" / {u_counts.get('sem', 0)}"
    )

    blocker_rows = []
    if active:
        for blocker in sorted(active):
            blocked = ", ".join(f"#{n}" for n in active[blocker])
            blocker_rows.append(
                f"| [#{blocker}](https://github.com/DataBoar/data-boar/issues/{blocker}) | {blocked} |"
            )
    else:
        blocker_rows.append(
            f"| — | **None** (scan of open issue bodies on {as_of.isoformat()}) |"
        )

    stale_rows = []
    for blocked, blocker in stale:
        stale_rows.append(
            f"| [#{blocked}](https://github.com/DataBoar/data-boar/issues/{blocked}) "
            f"| `#{blocker}` | closed |"
        )
    if not stale_rows:
        stale_rows.append("| — | — | — |")

    unassigned_note = ""
    if unassigned:
        nums = ", ".join(f"`#{n}`" for n in sorted(unassigned))
        unassigned_note = (
            f"\n**No milestone** ({len(unassigned)} open): {nums} — assign or defer via "
            "[#1522](https://github.com/DataBoar/data-boar/issues/1522) hygiene.\n"
        )

    v181_line = _format_v181_list(issues)
    v181_block = f"\n{v181_line}\n" if v181_line else "\n"

    return f"""# Issue Queue Sequencing Map
<!-- auto-maintained: run `uv run python scripts/issue_queue_sequencing_map.py --write` -->
**Última atualização:** {as_of.isoformat()}
**Total open issues:** {total}

Snapshot via `gh issue list --state open` + GraphQL `issueType` (DataBoar/data-boar). **GitHub is the source of truth for milestone assignment** — this file mirrors that distribution; do not move issues in GitHub to match stale `.md`. Contagens ±5% por race com o GitHub.

- Cross-milestone re-alignment protocol (HITL): [#1522](https://github.com/DataBoar/data-boar/issues/1522) · [ADR-0061](../adr/ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md)
- Hard-blocker helper (follow-up): [#1523](https://github.com/DataBoar/data-boar/issues/1523)

{_mermaid_block(milestone_counts, len(unassigned))}

Governance Lens Phases A–E ([#539](https://github.com/DataBoar/data-boar/issues/539)–[#543](https://github.com/DataBoar/data-boar/issues/543)) are **closed** — the previous `NÃO INICIAR ANTES DE #539` edges are **not** live.
{v181_block}{unassigned_note}
## Hard-blockers (active)

Open issues whose bodies still contain `**NÃO INICIAR ANTES DE #N**` (or equivalent) **and** whose blocker `#N` is still open:

| Blocker | Blocks (open) |
| --- | --- |
{chr(10).join(blocker_rows)}

### Stale `NÃO INICIAR` text (blocker already closed)

Not drawn as live edges — body cleanup is out of scope for this refresh:

| Open issue | Still cites | Blocker state |
| --- | --- | --- |
{chr(10).join(stale_rows)}

Removed from the previous map: `#539 → #540–#543` (all five closed); `#668` citing `#406` (`#668` now closed); `#406 → #606` (both closed); `#382` citing `#381` (both closed as of {as_of.isoformat()}).

## Contagens

| Dimensão | Distribuição |
| --- | --- |
| Total open | {total} |
| Issue Type Bug / Feature / Task / (none) | {issue_type_row} |
| P0 / P1 / P2 / P3 / sem P (`[Pn]` in title, body, or labels) | {p_row} |
| Milestone v1.8.0 / v1.8.1 / v1.8.2 / v1.8.3 / v1.8.4 / backlog / (none) | {milestone_row} |
| U0 / U1 / U2 / U3 / sem U (`[Un]` in title or body) | {u_row} |
| Active hard-blocker edges | {sum(len(v) for v in active.values())} |
"""


def main() -> int:
    args = parse_args()
    issues = fetch_open_issues()
    content = build_map(issues)
    normalized = content.rstrip() + "\n"

    if args.stdout:
        sys.stdout.write(normalized)
        return 0

    if args.check:
        if not MAP_PATH.is_file():
            print(f"MISSING: {MAP_PATH}", file=sys.stderr)
            return 1
        current = MAP_PATH.read_text(encoding="utf-8")
        if current != normalized:
            print(f"STALE: {MAP_PATH} (run --write)", file=sys.stderr)
            return 1
        print(f"OK: {MAP_PATH}")
        return 0

    MAP_PATH.write_text(normalized, encoding="utf-8")
    print(f"Wrote {MAP_PATH} ({len(issues)} open issues)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

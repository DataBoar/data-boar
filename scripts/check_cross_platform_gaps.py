#!/usr/bin/env python3
"""Audit scripts/*.ps1 vs sibling .sh and docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md.

Does not create missing .sh twins. Windows-only scripts without a twin are expected.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAIRING = REPO_ROOT / "docs" / "ops" / "SCRIPTS_CROSS_PLATFORM_PAIRING.md"
PS1_TICK = re.compile(r"`(?:scripts/)?([A-Za-z0-9_.-]+\.ps1)`")

# Documented as single-platform in pairing prose or by filename convention.
# Keep this list tiny; prefer pairing.md mentions.
INTENTIONAL_UNPAIRED = {
    "es-find.ps1",  # Windows Everything; Linux uses find/fd/locate
    "run-pester.ps1",  # invoked from check-all.sh when pwsh exists
}


def _top_level_ps1() -> list[str]:
    scripts_dir = REPO_ROOT / "scripts"
    return sorted(p.name for p in scripts_dir.glob("*.ps1") if p.is_file())


def _mentioned_in_pairing(text: str) -> set[str]:
    return {m.group(1) for m in PS1_TICK.finditer(text)}


def classify() -> list[dict[str, str]]:
    pairing_text = PAIRING.read_text(encoding="utf-8") if PAIRING.is_file() else ""
    mentioned = _mentioned_in_pairing(pairing_text)
    rows: list[dict[str, str]] = []
    for name in _top_level_ps1():
        sh = REPO_ROOT / "scripts" / name.replace(".ps1", ".sh")
        has_sh = sh.is_file()
        in_doc = name in mentioned
        if has_sh:
            gap = "none (twin exists)"
            if not in_doc:
                gap = "has .sh but not listed in pairing doc"
            priority = "—"
        elif name in INTENTIONAL_UNPAIRED or in_doc:
            gap = "unpaired by design (see pairing doc / Windows-only)"
            priority = "—"
        else:
            gap = "no .sh twin (do not invent an empty script)"
            priority = "P3"
        rows.append(
            {
                "ps1": name,
                "gap": gap,
                "priority": priority,
                "in_pairing": "yes" if in_doc else "no",
                "has_sh": "yes" if has_sh else "no",
            }
        )
    return rows


def markdown_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Script PS1 | In pairing doc | Has `.sh` | Gap | Priority |",
        "| ---------- | -------------- | --------- | --- | -------- |",
    ]
    for r in rows:
        lines.append(
            f"| `{r['ps1']}` | {r['in_pairing']} | {r['has_sh']} | {r['gap']} | {r['priority']} |"
        )
    return "\n".join(lines)


def missing_twins(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in rows if r["priority"] == "P3"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Print only P3 rows (ps1 without .sh and not documented as unpaired)",
    )
    args = parser.parse_args()
    rows = classify()
    show = missing_twins(rows) if args.missing_only else rows
    print(markdown_table(show))
    print(
        f"\n# {len(rows)} top-level scripts/*.ps1; {len(missing_twins(rows))} P3 gaps"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

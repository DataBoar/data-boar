#!/usr/bin/env python3
"""Validate hub index paths and PRIMERS_HUB markdown links (repo root)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HUBS_INDEX = REPO_ROOT / "docs" / "hubs" / "INDEX.md"
PRIMERS_HUB = REPO_ROOT / "docs" / "plans" / "PRIMERS_HUB.md"

BACKTICK_PATH = re.compile(r"`((?:docs|AGENTS\.md|\.\./)[^`]+)`")
MD_LINK = re.compile(r"\]\((docs/plans/[A-Za-z0-9_./-]+\.md)\)")


def _check_paths(label: str, paths: list[str]) -> list[str]:
    broken: list[str] = []
    for rel in paths:
        p = REPO_ROOT / rel.replace("\\", "/")
        if not p.is_file():
            broken.append(f"{label}: missing file `{rel}`")
    return broken


def paths_from_hubs_index(text: str) -> list[str]:
    found = BACKTICK_PATH.findall(text)
    # Normalize AGENTS.md at repo root
    return sorted(set(found))


def paths_from_primers_hub(text: str) -> list[str]:
    return sorted(set(MD_LINK.findall(text)))


def main() -> int:
    errors: list[str] = []
    if HUBS_INDEX.is_file():
        text = HUBS_INDEX.read_text(encoding="utf-8")
        errors.extend(_check_paths("docs/hubs/INDEX.md", paths_from_hubs_index(text)))
    else:
        errors.append("docs/hubs/INDEX.md not found")

    if PRIMERS_HUB.is_file():
        text = PRIMERS_HUB.read_text(encoding="utf-8")
        errors.extend(
            _check_paths("docs/plans/PRIMERS_HUB.md", paths_from_primers_hub(text))
        )
    else:
        errors.append("docs/plans/PRIMERS_HUB.md not found")

    if errors:
        print("check_hubs: FAILED\n" + "\n".join(errors), file=sys.stderr)
        return 1
    n_hub = len(paths_from_hubs_index(HUBS_INDEX.read_text(encoding="utf-8")))
    n_pr = len(paths_from_primers_hub(PRIMERS_HUB.read_text(encoding="utf-8")))
    print(f"check_hubs: OK ({n_hub} hub index paths, {n_pr} primer links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

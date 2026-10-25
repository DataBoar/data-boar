#!/usr/bin/env python3
"""Fail when tracked paths collide on a case-insensitive filesystem.

``README.md`` and ``readme.md`` coexist on Linux. Windows and default macOS
keep one of them. ``git ls-files`` does not reject the pair. This guard groups
tracked paths by their lowercased form and exits 1 when a group has more than
one distinct path (#2044).
"""

from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def colliding_groups(paths: list[str]) -> list[tuple[str, ...]]:
    """Return sorted groups of distinct paths that share a lowercased key."""
    buckets: dict[str, set[str]] = defaultdict(set)
    for raw in paths:
        path = raw.replace("\\", "/").strip()
        if not path:
            continue
        buckets[path.lower()].add(path)
    groups = [tuple(sorted(names)) for names in buckets.values() if len(names) > 1]
    groups.sort()
    return groups


def git_ls_files(repo: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return [part.decode("utf-8") for part in proc.stdout.split(b"\0") if part]


def main() -> int:
    paths = git_ls_files(REPO_ROOT)
    groups = colliding_groups(paths)
    if groups:
        print("check_case_collisions: FAILED", file=sys.stderr)
        for group in groups:
            print("  " + " <=> ".join(group), file=sys.stderr)
        return 1
    print(f"check_case_collisions: OK ({len(paths)} tracked paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

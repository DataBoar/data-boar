#!/usr/bin/env python3
"""Validate fenced blocks under '## Thread pronta' in X draft markdown files.

Reads ``docs/private/social_drafts/drafts/2026*_x_*.md`` (local operator tree).
Falls back to ``social_drafts/2026*_x_*.md`` if ``drafts/`` is absent. Exit 1 if any
block exceeds max_len (default 279). Skips silently if no matching files.

Draft filenames use prefix ``YYYY-MM-DD`` (publication or planned date); see
private ``editorial/SOCIAL_HUB.md``.

Usage (repo root):
  uv run python scripts/social_x_thread_lengths.py
  uv run python scripts/social_x_thread_lengths.py --max-len 279
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def extract_thread_blocks(text: str) -> list[str]:
    """Return fenced ``` contents after the first '## Thread pronta' heading."""
    marker = "## Thread pronta"
    idx = text.find(marker)
    if idx < 0:
        return []
    sub = text[idx:]
    # ``` with optional language tag on same line as opening fence
    pattern = re.compile(r"^```[a-zA-Z0-9]*\s*\n(.*?)```", re.MULTILINE | re.DOTALL)
    return [m.group(1).rstrip("\n") for m in pattern.finditer(sub)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check X draft thread block lengths.")
    parser.add_argument(
        "--max-len",
        type=int,
        default=279,
        help="Maximum allowed characters per fenced block (default 279).",
    )
    parser.add_argument(
        "--drafts-dir",
        type=Path,
        default=None,
        help="Override path to social_drafts root (default: docs/private/social_drafts). X files are read from social_drafts/drafts/ when present.",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    drafts_dir = args.drafts_dir or (repo_root / "docs" / "private" / "social_drafts")
    if not drafts_dir.is_dir():
        print(f"SKIP: drafts dir not found: {drafts_dir}")
        return 0

    nested = drafts_dir / "drafts"
    x_dir = nested if nested.is_dir() else drafts_dir
    files = sorted(x_dir.glob("2026*_x_*.md"))
    if not files:
        print(f"SKIP: no 2026*_x_*.md under {x_dir}")
        return 0

    failed = False
    for path in files:
        text = path.read_text(encoding="utf-8")
        blocks = extract_thread_blocks(text)
        if not blocks:
            print(f"WARN: no '## Thread pronta' fenced blocks: {path.name}")
            continue
        for i, block in enumerate(blocks, 1):
            n = len(block)
            status = "OK" if n <= args.max_len else "TOO_LONG"
            if n > args.max_len:
                failed = True
            print(f"{path.name}  block {i}  len={n}  {status}")
            if n > args.max_len:
                snippet = block[:120].replace("\n", "\\n")
                print(f"  --> {snippet!s}...")

    if failed:
        print(
            f"\nFAIL: one or more blocks exceed {args.max_len} characters.",
            file=sys.stderr,
        )
        return 1
    print(f"\nOK: all checked blocks <= {args.max_len}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

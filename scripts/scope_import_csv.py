#!/usr/bin/env python3
"""
Emit a YAML config fragment (targets only) from the canonical scope-import CSV.

Usage:
  uv run python scripts/scope_import_csv.py path/to/assets.csv
  uv run python scripts/scope_import_csv.py path/to/assets.csv -o targets.fragment.yaml

See docs/USAGE.md (Scope import) and docs/plans/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root on sys.path when run as scripts/scope_import_csv.py
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.scope_import_csv import csv_to_fragment_yaml  # noqa: E402
from utils.file_encoding import read_text_auto_encoding  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Convert canonical scope-import CSV to a YAML fragment "
            "(targets only) for merge into config.yaml."
        )
    )
    p.add_argument(
        "csv_file",
        type=Path,
        help="Path to UTF-8 (or legacy-encoded) CSV with a header row",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write YAML here (default: stdout)",
    )
    p.add_argument(
        "--no-merge-hint",
        action="store_true",
        help="Omit the leading comment block (YAML only)",
    )
    args = p.parse_args()

    if not args.csv_file.is_file():
        print(f"error: file not found: {args.csv_file}", file=sys.stderr)
        return 2

    text = read_text_auto_encoding(args.csv_file)
    try:
        yaml_out = csv_to_fragment_yaml(text, merge_hint=not args.no_merge_hint)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.output is not None:
        args.output.write_text(yaml_out, encoding="utf-8")
    else:
        sys.stdout.write(yaml_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

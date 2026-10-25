"""
CLI: GLPI Computer export → Data Boar canonical scope CSV → YAML fragment.

Usage:
    python scripts/scope_import_glpi.py glpi_export.csv [--yaml] [--out config_fragment.yaml]

Without ``--yaml`` the script writes the canonical intermediate CSV to stdout (useful for
inspection / manual editing before the YAML conversion step).

With ``--yaml`` it pipes the canonical CSV through
:func:`config.scope_import_csv.parse_csv_to_yaml_fragment` and prints the YAML fragment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a GLPI Computer export CSV to a Data Boar scope YAML fragment."
    )
    parser.add_argument("input", help="GLPI export CSV file path")
    parser.add_argument(
        "--yaml",
        action="store_true",
        help="Emit YAML fragment (default: emit canonical intermediate CSV)",
    )
    parser.add_argument(
        "--out",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    parser.add_argument(
        "--include-retired",
        action="store_true",
        help="Include rows with Retired / Disposed status (default: skip)",
    )
    parser.add_argument(
        "--source-system",
        default="GLPI",
        help="Value for the source_system column (default: GLPI)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"error: file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        raw_text = input_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raw_text = input_path.read_text(encoding="latin-1")

    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    canonical_csv = glpi_csv_to_canonical_csv(
        raw_text,
        skip_retired=not args.include_retired,
        source_system=args.source_system,
    )

    if args.yaml:
        from config.scope_import_csv import parse_csv_to_yaml_fragment

        output_text = parse_csv_to_yaml_fragment(canonical_csv)
    else:
        output_text = canonical_csv

    if args.out:
        Path(args.out).write_text(output_text, encoding="utf-8")
        print(f"Written to {args.out}", file=sys.stderr)
    else:
        print(output_text, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

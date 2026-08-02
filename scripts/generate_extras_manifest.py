#!/usr/bin/env python3
"""Generate EXTRAS_MANIFEST.json from pyproject.toml (#1401).

Usage:
  uv run python scripts/generate_extras_manifest.py --probe --write EXTRAS_MANIFEST.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root on path when invoked as scripts/...
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.extras_manifest import write_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        type=Path,
        required=True,
        help="Output path for EXTRAS_MANIFEST.json",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=None,
        help="Path to pyproject.toml (default: repo root)",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Set in_artifact by probing imports in this environment",
    )
    parser.add_argument(
        "--no-probe",
        action="store_true",
        help="Mark in_artifact from IMAGE_BASE_EXTRAS only (no import probe)",
    )
    args = parser.parse_args()
    probe = bool(args.probe) and not bool(args.no_probe)
    if not args.probe and not args.no_probe:
        probe = True  # default: probe (Docker build / CI)
    write_manifest(args.write, pyproject=args.pyproject, probe=probe)
    print(f"wrote {args.write} (probe={probe})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

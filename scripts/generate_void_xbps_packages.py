#!/usr/bin/env python3
"""Generate packaging/void/generated/ from EXTRAS_MANIFEST (#1404).

Usage:
  uv run python scripts/generate_void_xbps_packages.py --write
  uv run python scripts/generate_void_xbps_packages.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.extras_manifest import (
    EMBEDDED_INTERPRETER_NATIVE,
    build_manifest,
)
from core.void_xbps import (
    assert_generated_in_sync,
    generated_dir,
    write_generated_void,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--write",
        action="store_true",
        help="Regenerate packaging/void/generated/ (template + runit + meta)",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if generated overlay drifts from EXTRAS_MANIFEST",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override generated/ directory (default: packaging/void/generated)",
    )
    args = parser.parse_args()

    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    if args.check:
        assert_generated_in_sync(generated=args.out_dir, manifest=manifest)
        print("void xbps generated/: OK (in sync with EXTRAS_MANIFEST)")
        return 0

    written = write_generated_void(out_dir=args.out_dir, manifest=manifest)
    print(
        f"wrote {len(written)} void overlay file(s) under {args.out_dir or generated_dir()}"
    )
    for name, path in written.items():
        print(f"  {name}: {path}")
    print(
        "embedded_interpreter:",
        json.dumps(EMBEDDED_INTERPRETER_NATIVE, ensure_ascii=False),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

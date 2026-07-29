#!/usr/bin/env python3
"""Load scripts/wheelhouse/recipe-manifest.yaml (single source of truth for #1379)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml / uv sync") from exc

MANIFEST = Path(__file__).resolve().parent / "recipe-manifest.yaml"


def load() -> dict:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"invalid manifest: {MANIFEST}")
    return data


def _get(data: dict, dotted: str):
    cur: object = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise SystemExit(f"missing key {dotted!r} in {MANIFEST}")
        cur = cur[part]
    return cur


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--path", action="store_true", help="print manifest path")
    p.add_argument("--json", action="store_true", help="dump full manifest as JSON")
    p.add_argument("--get", metavar="DOTTED.KEY", help="print one value")
    p.add_argument(
        "--export-build-env",
        action="store_true",
        help="print shell assignments for in-container scientific build",
    )
    args = p.parse_args()
    if args.path:
        print(MANIFEST)
        return 0
    data = load()
    if args.json:
        json.dump(data, sys.stdout, indent=2, sort_keys=True)
        print()
        return 0
    if args.get:
        val = _get(data, args.get)
        if isinstance(val, (list, dict)):
            json.dump(val, sys.stdout)
            print()
        else:
            print(val)
        return 0
    if args.export_build_env:
        pkgs = data["packages"]
        gates = data["gates"]
        build = data["build"]
        meson = " ".join(f"-C setup-args={a}" for a in build["numpy_meson_args"])
        pure = " ".join(pkgs["pure_wheels"])
        print(f"export NUMPY_SPEC={pkgs['numpy']!r}")
        print(f"export SCIPY_SPEC={pkgs['scipy']!r}")
        print(f"export SKLEARN_SPEC={pkgs['scikit-learn']!r}")
        print(f"export PANDAS_SPEC={pkgs['pandas']!r}")
        print(f"export PURE_WHEELS={pure!r}")
        print(f"export NUMPY_MESON_PIP_ARGS={meson!r}")
        print(f"export GATE_POPCNT_MAX={gates['numpy_popcnt_max']}")
        print(f"export GATE_UMATH_MAX_BYTES={gates['numpy_umath_so_max_bytes']}")
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compatibility wrapper — use scripts/sync_sdk_schema_pin.py.

Refreshes the L1 metadata_manifest pin only (same behaviour as before #1334).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CANON = _ROOT / "scripts" / "sync_sdk_schema_pin.py"


def main() -> int:
    cmd = [
        sys.executable,
        str(_CANON),
        "--schema",
        "metadata_manifest",
        *sys.argv[1:],
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

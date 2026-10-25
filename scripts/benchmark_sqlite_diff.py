"""Compare two SQLite databases for lab benchmark notes (tables + column deltas)."""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path


def _safe_sql_ident(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"unsafe sqlite identifier: {name!r}")
    return name


def _tables(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {str(r[0]) for r in cur.fetchall()}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    ident = _safe_sql_ident(table)
    cur = conn.execute(f"PRAGMA table_info({ident})")
    return {str(r[1]) for r in cur.fetchall()}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("db_baseline", type=Path, help="Older / tag-side database path")
    p.add_argument("db_head", type=Path, help="Newer / HEAD-side database path")
    args = p.parse_args()
    a, b = args.db_baseline, args.db_head
    if not a.is_file():
        print(f"missing baseline db: {a}", file=sys.stderr)
        return 2
    if not b.is_file():
        print(f"missing head db: {b}", file=sys.stderr)
        return 2
    ca = sqlite3.connect(str(a))
    cb = sqlite3.connect(str(b))
    try:
        ta, tb = _tables(ca), _tables(cb)
        print("=== tables only in HEAD db ===")
        for t in sorted(tb - ta):
            print(f"  + {t}")
        print("=== tables only in baseline db ===")
        for t in sorted(ta - tb):
            print(f"  - {t}")
        common = ta & tb
        print("=== column additions per shared table (HEAD vs baseline) ===")
        for t in sorted(common):
            ca_set, cb_set = _columns(ca, t), _columns(cb, t)
            added = sorted(cb_set - ca_set)
            removed = sorted(ca_set - cb_set)
            if added or removed:
                print(f"  [{t}]")
                for c in added:
                    print(f"    + {c}")
                for c in removed:
                    print(f"    - {c}")
        # Optional audit row the operator asked about (if table exists on either side).
        meta = "scan_metadata"
        if meta in ta or meta in tb:
            print(f"=== {meta} (operator checklist) ===")
            for label, conn, has in (
                ("baseline", ca, meta in ta),
                ("head", cb, meta in tb),
            ):
                if not has:
                    print(f"  {label}: table absent")
                    continue
                cols = _columns(conn, meta)
                want = ("safety_protocol", "sampling_method")
                for w in want:
                    print(f"  {label}.{w}: {'yes' if w in cols else 'no'}")
    finally:
        ca.close()
        cb.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

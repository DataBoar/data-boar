#!/usr/bin/env python3
"""
Lab completão — data contract preflight.

Validates that configured lab databases still expose required column names before
host smoke / scans run. Intended to be invoked from lab-completao-orchestrate.ps1
when manifest key completaoDataContractsPath points at a YAML file.

Secrets: connection strings must come from environment variables named in the
YAML (url_from_env), never from committed files.

Process exit codes (DATA_BOAR_COMPLETAO_EXIT_v1 — align with docs/ops/LAB_COMPLETAO_RUNBOOK.md):

- 0 — all configured checks passed.
- 1 — infrastructure / credentials / connectivity (unset DB URL env, DB TCP/auth errors, etc.).
- 2 — data or contract shape (YAML/contract file issues, missing required columns, wrong document shape).
- 3 — reserved for explicit compliance-violation hooks (not used by this script today).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine, inspect


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"contracts file must be a mapping at top level: {path}")
    return data


def _check_one(entry: dict[str, Any], index: int) -> list[str]:
    errs: list[str] = []
    prefix = f"check[{index}]"
    name = entry.get("name")
    if not name:
        errs.append(f"{prefix}: missing 'name'")
        return errs
    prefix = f"check[{index}] '{name}'"

    conn = entry.get("connection") or {}
    if not isinstance(conn, dict):
        errs.append(f"{prefix}: 'connection' must be a mapping")
        return errs
    env_key = (conn.get("url_from_env") or "").strip()
    if not env_key:
        errs.append(f"{prefix}: connection.url_from_env is required")
        return errs

    url = (os.environ.get(env_key) or "").strip()
    if not url:
        errs.append(f"{prefix}: environment variable {env_key!r} is empty or unset")
        return errs

    schema = entry.get("schema")
    if schema is not None and not isinstance(schema, str):
        errs.append(f"{prefix}: 'schema' must be a string or null")
        return errs
    schema_s = (schema or "").strip() or None

    table = (entry.get("table") or "").strip()
    if not table:
        errs.append(f"{prefix}: 'table' is required")
        return errs

    req = entry.get("require_columns")
    if not isinstance(req, list) or not req:
        errs.append(f"{prefix}: 'require_columns' must be a non-empty list")
        return errs
    required = [str(c).strip() for c in req if str(c).strip()]
    if not required:
        errs.append(f"{prefix}: require_columns must contain non-empty strings")

    if errs:
        return errs

    engine = create_engine(url)
    try:
        insp = inspect(engine)
        cols_raw = insp.get_columns(table, schema=schema_s)
    except Exception as e:  # noqa: BLE001 — surface any connect/introspection failure
        errs.append(f"{prefix}: database error: {e}")
        return errs
    finally:
        try:
            engine.dispose()
        except Exception:
            pass

    have = {str(c["name"]).lower() for c in cols_raw}
    for col in required:
        if col.lower() not in have:
            sample = ", ".join(sorted(have)[:24])
            more = " …" if len(have) > 24 else ""
            errs.append(
                f"{prefix}: missing column {col!r} on "
                f"{schema_s + '.' if schema_s else ''}{table} "
                f"(have: {sample}{more})"
            )
    return errs


def main() -> int:
    p = argparse.ArgumentParser(description="Lab completão data contract preflight")
    p.add_argument(
        "--contracts",
        required=True,
        type=Path,
        help="Path to completao_data_contracts YAML (see docs/private.example/homelab/)",
    )
    args = p.parse_args()
    path: Path = args.contracts
    if not path.is_file():
        print(f"ERROR: contracts file not found: {path}", file=sys.stderr)
        return 2

    try:
        doc = _load_yaml(path)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: failed to load YAML: {e}", file=sys.stderr)
        return 2

    ver = doc.get("version", 1)
    if ver != 1:
        print(
            f"ERROR: unsupported contracts version: {ver!r} (only 1)", file=sys.stderr
        )
        return 2

    checks = doc.get("checks")
    if checks is None:
        checks = []
    if not isinstance(checks, list):
        print("ERROR: 'checks' must be a list", file=sys.stderr)
        return 2

    if not checks:
        print("lab_completao_data_contract_check: no checks defined (ok)")
        return 0

    all_errs: list[str] = []
    for i, c in enumerate(checks):
        if not isinstance(c, dict):
            all_errs.append(f"check[{i}]: entry must be a mapping")
            continue
        all_errs.extend(_check_one(c, i))

    if all_errs:
        print("Data contract check FAILED:", file=sys.stderr)
        for line in all_errs:
            print(f"  {line}", file=sys.stderr)
        for line in all_errs:
            low = line.lower()
            if "environment variable" in low and (
                "empty or unset" in low or "unset" in low
            ):
                return 1
            if "database error:" in low:
                return 1
        return 2

    print(f"lab_completao_data_contract_check: {len(checks)} check(s) OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

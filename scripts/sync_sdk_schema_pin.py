#!/usr/bin/env python3
"""Refresh SDK schema pins (L1 metadata_manifest and/or L3 transformed_rows).

Canonical contracts live in DataBoar/data-boar-sdk. This script writes an
unmodified byte copy plus pin metadata (commit SHA, blob SHA, $id,
contract_version, date). Not a second contract.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = "DataBoar/data-boar-sdk"

CONTRACTS: dict[str, dict[str, str]] = {
    "metadata_manifest": {
        "path": "schema/metadata_manifest.schema.json",
        "comment": (
            "PIN of DataBoar/data-boar-sdk schema/metadata_manifest.schema.json. "
            "This is not a second contract. Canonical remains "
            "https://github.com/DataBoar/data-boar-sdk. The sibling .schema.json "
            "file is an unmodified byte pin of that path at sdk_commit. Bump with "
            "scripts/sync_sdk_schema_pin.py --schema metadata_manifest after "
            "reviewing the SDK diff. co_columns is tracked as "
            "DataBoar/data-boar-sdk#41 (not this pin)."
        ),
    },
    "transformed_rows": {
        "path": "schema/transformed_rows.schema.json",
        "comment": (
            "PIN of DataBoar/data-boar-sdk schema/transformed_rows.schema.json. "
            "This is not a second contract. Canonical remains "
            "https://github.com/DataBoar/data-boar-sdk. The sibling .schema.json "
            "file is an unmodified byte pin of that path at sdk_commit. Bump with "
            "scripts/sync_sdk_schema_pin.py --schema transformed_rows after "
            "reviewing the SDK diff."
        ),
    },
}


def _gh_json(endpoint: str) -> dict:
    proc = subprocess.run(
        ["gh", "api", endpoint],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        raise SystemExit(proc.returncode or 1)
    return json.loads(proc.stdout)


def _pin_one(repo_root: Path, name: str, ref: str) -> None:
    meta = CONTRACTS[name]
    sdk_path = meta["path"]
    schema_out = repo_root / "docs" / "sdk" / f"{name}.schema.json"
    pin_out = repo_root / "docs" / "sdk" / f"{name}.pin.json"

    commit = _gh_json(f"repos/{REPO}/commits/{ref}")
    sha = commit["sha"]
    contents = _gh_json(f"repos/{REPO}/contents/{sdk_path}?ref={sha}")
    blob = base64.b64decode(contents["content"])
    schema = json.loads(blob)
    schema_id = schema.get("$id")
    contract_version = "1.0.0"
    if isinstance(schema_id, str) and "/sdk/" in schema_id:
        mid = schema_id.split("/sdk/", 1)[1].split("/", 1)[0]
        if mid:
            contract_version = mid

    schema_out.write_bytes(blob)
    pin = {
        "$comment": meta["comment"],
        "canonical_repo": REPO,
        "canonical_path": sdk_path,
        "id": schema_id,
        "contract_version": contract_version,
        "sdk_commit": sha,
        "sdk_blob_sha": contents["sha"],
        "pinned_at": datetime.now(tz=UTC).date().isoformat(),
    }
    pin_out.write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {schema_out} ({len(blob)} bytes) pin commit {sha[:12]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref",
        default="main",
        help="SDK git ref to pin (default: main)",
    )
    parser.add_argument(
        "--schema",
        choices=["metadata_manifest", "transformed_rows", "all"],
        default="all",
        help="Which pin to refresh (default: all)",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    names = list(CONTRACTS) if args.schema == "all" else [args.schema]
    for name in names:
        _pin_one(repo_root, name, args.ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

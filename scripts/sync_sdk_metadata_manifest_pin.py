#!/usr/bin/env python3
"""Refresh the L1 metadata_manifest schema pin from DataBoar/data-boar-sdk.

Canonical contract lives in the SDK repo. This script writes an unmodified byte
copy plus pin metadata (commit SHA, blob SHA, $id, contract_version, date).
Does not invent fields (co_columns waits on sdk#41).
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
PATH = "schema/metadata_manifest.schema.json"


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref",
        default="main",
        help="SDK git ref to pin (default: main)",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    schema_out = repo_root / "docs" / "sdk" / "metadata_manifest.schema.json"
    pin_out = repo_root / "docs" / "sdk" / "metadata_manifest.pin.json"

    commit = _gh_json(f"repos/{REPO}/commits/{args.ref}")
    sha = commit["sha"]
    contents = _gh_json(f"repos/{REPO}/contents/{PATH}?ref={sha}")
    blob = base64.b64decode(contents["content"])
    schema = json.loads(blob)
    schema_id = schema.get("$id")
    # $id is …/sdk/<semver>/metadata_manifest.schema.json
    contract_version = "1.0.0"
    if isinstance(schema_id, str) and "/sdk/" in schema_id:
        mid = schema_id.split("/sdk/", 1)[1].split("/", 1)[0]
        if mid:
            contract_version = mid

    schema_out.write_bytes(blob)
    pin = {
        "$comment": (
            "PIN of DataBoar/data-boar-sdk schema/metadata_manifest.schema.json. "
            "This is not a second contract. Canonical remains "
            "https://github.com/DataBoar/data-boar-sdk. The sibling .schema.json "
            "file is an unmodified byte pin of that path at sdk_commit. Bump with "
            "scripts/sync_sdk_metadata_manifest_pin.py after reviewing the SDK "
            "diff. co_columns is tracked as DataBoar/data-boar-sdk#41 (not this pin)."
        ),
        "canonical_repo": REPO,
        "canonical_path": PATH,
        "id": schema_id,
        "contract_version": contract_version,
        "sdk_commit": sha,
        "sdk_blob_sha": contents["sha"],
        "pinned_at": datetime.now(tz=UTC).date().isoformat(),
    }
    pin_out.write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {schema_out} ({len(blob)} bytes) pin commit {sha[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

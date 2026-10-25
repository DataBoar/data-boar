"""
Optional release integrity checks (tamper-evident, not tamper-proof).

Compares DATA_BOAR_EXPECTED_BUILD_DIGEST to the embedded digest in
core/licensing/_build_digest.txt (replaced at release build time).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _embedded_build_digest() -> str:
    p = Path(__file__).resolve().parent / "_build_digest.txt"
    if not p.exists():
        return "unknown"
    return p.read_text(encoding="utf-8").strip() or "unknown"


def check_build_digest_expected() -> tuple[bool, str]:
    """
    If DATA_BOAR_EXPECTED_BUILD_DIGEST is set, it must equal the embedded digest.
    Returns (ok, detail_message).
    """
    expected = (os.environ.get("DATA_BOAR_EXPECTED_BUILD_DIGEST") or "").strip().lower()
    if not expected:
        return True, "no_expected_digest"
    got = _embedded_build_digest().lower()
    if got == expected:
        return True, "digest_match"
    return False, f"digest_mismatch:embedded={got}:expected={expected}"


def verify_manifest_optional(manifest_path: str | None) -> tuple[bool, str]:
    """
    If manifest_path points to a JSON file, verify listed files' SHA-256 on disk
    relative to cwd or absolute paths.

    Schema: {"files": [{"path": "relative/or/abs", "sha256": "hex"}]}
    """
    if not manifest_path:
        return True, "no_manifest"
    p = Path(manifest_path)
    if not p.is_file():
        return True, "manifest_missing_skipped"
    try:
        data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return False, f"manifest_invalid:{e}"
    files = data.get("files")
    if not isinstance(files, list):
        return False, "manifest_no_files_array"
    root = Path.cwd()
    for item in files:
        if not isinstance(item, dict):
            continue
        rel = item.get("path")
        want = (item.get("sha256") or "").strip().lower()
        if not rel or not want:
            continue
        fp = Path(rel)
        if not fp.is_absolute():
            fp = root / fp
        if not fp.is_file():
            return False, f"missing_file:{fp}"
        h = hashlib.sha256()
        with fp.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        if h.hexdigest().lower() != want:
            return False, f"hash_mismatch:{fp}"
    return True, "manifest_ok"

"""Offline pin consistency + optional network canary for the SDK schema pin."""

from __future__ import annotations

import os
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from core.l1_metadata_manifest import (
    load_l1_schema,
    load_pin_metadata,
    schema_pin_paths,
    sdk_schema_check_enabled,
)

SDK_RAW_URL = (
    "https://raw.githubusercontent.com/DataBoar/data-boar-sdk/"
    "main/schema/metadata_manifest.schema.json"
)


def test_pin_metadata_agrees_with_local_schema() -> None:
    schema_path, pin_path = schema_pin_paths()
    assert schema_path.is_file()
    assert pin_path.is_file()
    pin = load_pin_metadata()
    schema = load_l1_schema()
    assert pin["id"] == schema["$id"]
    assert pin["canonical_path"] == "schema/metadata_manifest.schema.json"
    assert pin["sdk_commit"]
    assert pin["sdk_blob_sha"]
    assert pin["pinned_at"]


def test_canary_env_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_BOAR_SDK_SCHEMA_CHECK", raising=False)
    assert sdk_schema_check_enabled(dict(os.environ)) is False
    assert sdk_schema_check_enabled({"DATA_BOAR_SDK_SCHEMA_CHECK": "1"}) is True
    assert sdk_schema_check_enabled({"DATA_BOAR_SDK_SCHEMA_CHECK": "true"}) is True


@pytest.mark.skipif(
    not sdk_schema_check_enabled(),
    reason="DATA_BOAR_SDK_SCHEMA_CHECK is unset (default CI stays offline)",
)
def test_pin_matches_sdk_default_branch() -> None:
    schema_path, _pin = schema_pin_paths()
    local = schema_path.read_bytes()
    req = Request(SDK_RAW_URL, method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            remote = resp.read()
    except URLError as exc:
        pytest.fail(f"SDK schema canary fetch failed: {exc}")
    if local != remote:
        pytest.fail(
            "Pinned metadata_manifest.schema.json drifted from "
            "DataBoar/data-boar-sdk main. Review the SDK diff and run "
            "scripts/sync_sdk_metadata_manifest_pin.py (do not emit degraded)."
        )

"""Offline pin consistency + optional network canary for SDK schema pins."""

from __future__ import annotations

import os
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from core.l1_metadata_manifest import (
    load_l1_schema,
    load_pin_metadata as load_l1_pin,
    schema_pin_paths as l1_schema_pin_paths,
    sdk_schema_check_enabled,
)
from core.l3_transformed_rows import (
    load_l3_schema,
    load_pin_metadata as load_l3_pin,
    schema_pin_paths as l3_schema_pin_paths,
)

_SDK_RAW = {
    "metadata_manifest": (
        "https://raw.githubusercontent.com/DataBoar/data-boar-sdk/"
        "main/schema/metadata_manifest.schema.json"
    ),
    "transformed_rows": (
        "https://raw.githubusercontent.com/DataBoar/data-boar-sdk/"
        "main/schema/transformed_rows.schema.json"
    ),
}


def test_l1_pin_metadata_agrees_with_local_schema() -> None:
    schema_path, pin_path = l1_schema_pin_paths()
    assert schema_path.is_file()
    assert pin_path.is_file()
    pin = load_l1_pin()
    schema = load_l1_schema()
    assert pin["id"] == schema["$id"]
    assert pin["canonical_path"] == "schema/metadata_manifest.schema.json"
    assert pin["sdk_commit"]
    assert pin["sdk_blob_sha"]
    assert pin["pinned_at"]
    assert "not a second contract" in str(pin["$comment"]).lower()


def test_l3_pin_metadata_agrees_with_local_schema() -> None:
    schema_path, pin_path = l3_schema_pin_paths()
    assert schema_path.is_file()
    assert pin_path.is_file()
    pin = load_l3_pin()
    schema = load_l3_schema()
    assert pin["id"] == schema["$id"]
    assert pin["canonical_path"] == "schema/transformed_rows.schema.json"
    assert pin["sdk_commit"]
    assert pin["sdk_blob_sha"]
    assert pin["pinned_at"]
    assert "not a second contract" in str(pin["$comment"]).lower()


def test_canary_env_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_BOAR_SDK_SCHEMA_CHECK", raising=False)
    assert sdk_schema_check_enabled(dict(os.environ)) is False
    assert sdk_schema_check_enabled({"DATA_BOAR_SDK_SCHEMA_CHECK": "1"}) is True
    assert sdk_schema_check_enabled({"DATA_BOAR_SDK_SCHEMA_CHECK": "true"}) is True


def _assert_pin_matches_remote(contract: str, local_bytes: bytes) -> None:
    req = Request(_SDK_RAW[contract], method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            remote = resp.read()
    except URLError as exc:
        pytest.fail(f"SDK schema canary fetch failed ({contract}): {exc}")
    if local_bytes != remote:
        pytest.fail(
            f"Pinned {contract}.schema.json drifted from DataBoar/data-boar-sdk "
            "main. Review the SDK diff and run "
            f"scripts/sync_sdk_schema_pin.py --schema {contract} "
            "(do not emit degraded)."
        )


@pytest.mark.skipif(
    not sdk_schema_check_enabled(),
    reason="DATA_BOAR_SDK_SCHEMA_CHECK is unset (default CI stays offline)",
)
def test_pins_match_sdk_default_branch() -> None:
    l1_path, _ = l1_schema_pin_paths()
    l3_path, _ = l3_schema_pin_paths()
    _assert_pin_matches_remote("metadata_manifest", l1_path.read_bytes())
    _assert_pin_matches_remote("transformed_rows", l3_path.read_bytes())

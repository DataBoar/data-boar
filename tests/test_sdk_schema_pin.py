"""Offline pin consistency tests for SDK schema pins."""

from __future__ import annotations

from core.l1_metadata_manifest import (
    load_l1_schema,
    load_pin_metadata as load_l1_pin,
    schema_pin_paths as l1_schema_pin_paths,
)
from core.l3_transformed_rows import (
    load_l3_schema,
    load_pin_metadata as load_l3_pin,
    schema_pin_paths as l3_schema_pin_paths,
)


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

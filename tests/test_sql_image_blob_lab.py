"""Lab + fixture tests for #2362 D2362-24 .. D2362-26 (skip when lab unset)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from connectors.sql_connector import SQLConnector
from core.image_blob import column_type_family, sniff_image_kind
from core.database import LocalDBManager

_INIT = Path(__file__).resolve().parents[1] / "deploy" / "lab-smoke-stack" / "init"
_HAS_LAB = bool(os.environ.get("DATA_BOAR_LAB_HOST", "").strip())
_LAB_REASON = "DATA_BOAR_LAB_HOST unset — live lab tests skipped"


def _pg_target() -> dict:
    host = os.environ["DATA_BOAR_LAB_HOST"]
    port = int(os.environ.get("LAB_PG_PORT", "55432"))
    user = os.environ.get("LAB_PG_USER", "lab_smoke")
    password = os.environ.get("DATA_BOAR_LAB_PG_PASSWORD", "lab_smoke_change_me")
    database = os.environ.get("LAB_PG_DATABASE", "lab_smoke_pg")
    return {
        "type": "database",
        "driver": "postgresql+psycopg2",
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "name": "LabSmokePGImageBlob",
        "allow_private_networks": True,
        "allowed_hosts": [host],
    }


@pytest.mark.parametrize("engine", ("postgres",))
def test_D2362_lab_04_sql_seed_present(engine: str) -> None:
    path = _INIT / engine / "04_lab_image_blob.sql"
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "lab_image_blob" in text
    assert "Synthetic lab data only" in text


def test_D2362_24_postgres_column_families_from_catalog_types() -> None:
    """Static contract: column types in seed map to text/binary families."""
    expectations = {
        "foto_documento": "BYTEA",
        "anexo": "BYTEA",
        "foto_b64": "TEXT",
        "hash_blob": "BYTEA",
    }
    for _col, typ in expectations.items():
        fam = column_type_family(typ)
        if _col == "foto_b64":
            assert fam == "text"
        else:
            assert fam == "binary"


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
def test_D2362_24_discover_lab_image_blob_columns() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(
        _pg_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        tables = conn.discover()
        row = next(t for t in tables if t.get("table") == "lab_image_blob")
        by_name = {c["name"]: c["type"] for c in row["columns"]}
        assert column_type_family(by_name["foto_documento"]) == "binary"
        assert column_type_family(by_name["foto_b64"]) == "text"
        assert column_type_family(by_name["hash_blob"]) == "binary"
    finally:
        conn.close()


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
def test_D2362_25_prefix_sample_foto_documento_jpeg() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 3}}
    conn = SQLConnector(
        _pg_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        tables = conn.discover()
        row = next(t for t in tables if t.get("table") == "lab_image_blob")
        schema = row.get("schema") or "public"
        blobs = conn._sample_column_prefixes(
            schema, "lab_image_blob", "foto_documento", "BYTEA", limit=3
        )
        assert blobs
        assert all(isinstance(b, (bytes, bytearray)) for b in blobs)
        assert all(len(b) <= 64 for b in blobs)
        assert sniff_image_kind(blobs[0]) == "jpeg"
    finally:
        conn.close()


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
def test_D2362_26_run_image_findings_lab_postgres(tmp_path: Path) -> None:
    from tests.test_sql_image_blob import _LowScanner, _image_rows

    audit = tmp_path / "lab-audit.db"
    db = LocalDBManager(str(audit))
    db.set_current_session_id("lab-img-26")
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(_pg_target(), _LowScanner(), db, detection_config=det)
    conn.run()
    rows, _, _, _ = db.get_findings("lab-img-26")
    img = _image_rows(rows)
    patterns = {(r.get("column_name"), r.get("pattern_detected")) for r in img}
    assert ("foto_documento", "IMAGE_BLOB_IN_COLUMN") in patterns
    assert ("foto_b64", "IMAGE_BASE64_IN_COLUMN") in patterns
    assert not any(r.get("column_name") == "hash_blob" for r in img)

"""Live lab-stack tests for #2362 (D2362-24 .. D2362-26).

Requires DATA_BOAR_LAB_HOST and the lab smoke stack seeds. Public CI job
``test-extras`` ignores this module (same pattern as Maestro clone guards)
so the skip ceiling measures optional Python extras only.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from connectors.sql_connector import SQLConnector
from core.image_blob import column_type_family, sniff_image_kind
from core.database import LocalDBManager

_HAS_LAB = bool(os.environ.get("DATA_BOAR_LAB_HOST", "").strip())
_LAB_REASON = "DATA_BOAR_LAB_HOST unset — live lab tests skipped"


def _driver_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


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


def _mariadb_target() -> dict:
    host = os.environ["DATA_BOAR_LAB_HOST"]
    port = int(os.environ.get("LAB_MY_PORT", "33306"))
    user = os.environ.get("LAB_MY_USER", "lab_smoke")
    password = os.environ.get("DATA_BOAR_LAB_MY_PASSWORD", "lab_smoke_change_me")
    database = os.environ.get("LAB_MY_DATABASE", "lab_smoke_my")
    return {
        "type": "database",
        "driver": "mysql+pymysql",
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "name": "LabSmokeMariaImageBlob",
        "allow_private_networks": True,
        "allowed_hosts": [host],
    }


def _mssql_target() -> dict:
    host = os.environ["DATA_BOAR_LAB_HOST"]
    port = int(os.environ.get("LAB_MSSQL_PORT", "14333"))
    password = os.environ.get(
        "DATA_BOAR_LAB_MSSQL_SA_PASSWORD", "Lab_Smoke_Change_Me1!"
    )
    return {
        "type": "database",
        "driver": "mssql+pymssql",
        "host": host,
        "port": port,
        "user": "sa",
        "password": password,
        "database": "lab_smoke_mssql",
        "name": "LabSmokeMssqlImageBlob",
        "allow_private_networks": True,
        "allowed_hosts": [host],
    }


def _oracle_target() -> dict:
    host = os.environ["DATA_BOAR_LAB_HOST"]
    port = int(os.environ.get("LAB_ORACLE_PORT", "15211"))
    user = os.environ.get("LAB_ORACLE_USER", "lab_smoke")
    password = os.environ.get(
        "DATA_BOAR_LAB_ORACLE_PASSWORD", "lab_smoke_oracle_change_me"
    )
    return {
        "type": "database",
        "driver": "oracle+oracledb",
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": os.environ.get("LAB_ORACLE_SERVICE", "XEPDB1"),
        "name": "LabSmokeOracleImageBlob",
        "allow_private_networks": True,
        "allowed_hosts": [host],
    }


def _lab_row(conn: SQLConnector) -> dict:
    tables = conn.discover()
    return next(t for t in tables if t.get("table") == "lab_image_blob")


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(
    not _driver_available("psycopg2"),
    reason="psycopg2 not installed",
)
def test_D2362_24_discover_lab_image_blob_columns_postgres() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(
        _pg_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        row = _lab_row(conn)
        by_name = {c["name"]: c["type"] for c in row["columns"]}
        assert column_type_family(by_name["foto_documento"]) == "binary"
        assert column_type_family(by_name["foto_b64"]) == "text"
        assert column_type_family(by_name["hash_blob"]) == "binary"
    finally:
        conn.close()


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(
    not _driver_available("pymysql"),
    reason="pymysql not installed",
)
def test_D2362_24_discover_lab_image_blob_columns_mariadb() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(
        _mariadb_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        row = _lab_row(conn)
        by_name = {c["name"]: c["type"] for c in row["columns"]}
        assert column_type_family(by_name["foto_documento"]) == "binary"
        assert column_type_family(by_name["foto_b64"]) == "text"
    finally:
        conn.close()


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(not _driver_available("pymssql"), reason="pymssql not installed")
def test_D2362_24_discover_lab_image_blob_columns_mssql() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(
        _mssql_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        row = _lab_row(conn)
        by_name = {c["name"]: c["type"] for c in row["columns"]}
        assert column_type_family(by_name["foto_documento"]) == "binary"
        assert column_type_family(by_name["foto_b64"]) == "text"
    finally:
        conn.close()


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(
    not _driver_available("oracledb"),
    reason="oracledb not installed",
)
def test_D2362_24_discover_lab_image_blob_columns_oracle() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(
        _oracle_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        row = _lab_row(conn)
        by_name = {c["name"]: c["type"] for c in row["columns"]}
        assert column_type_family(by_name["foto_documento"]) == "binary"
        assert column_type_family(by_name["foto_b64"]) == "text"
    finally:
        conn.close()


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(
    not _driver_available("psycopg2"),
    reason="psycopg2 not installed",
)
def test_D2362_25_prefix_sample_foto_documento_jpeg_postgres() -> None:
    det = {"image_blob": {"enabled": True, "sampling_rows": 3}}
    conn = SQLConnector(
        _pg_target(),
        None,
        LocalDBManager(":memory:"),
        detection_config=det,
    )
    conn.connect()
    try:
        row = _lab_row(conn)
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
@pytest.mark.skipif(
    not _driver_available("psycopg2"),
    reason="psycopg2 not installed",
)
def test_D2362_26_run_image_findings_lab_postgres(tmp_path: Path) -> None:
    from tests.test_sql_image_blob import _LowScanner, _image_rows

    audit = tmp_path / "lab-audit.db"
    db = LocalDBManager(str(audit))
    db.set_current_session_id("lab-img-26-pg")
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(_pg_target(), _LowScanner(), db, detection_config=det)
    conn.run()
    conn.close()
    rows, _, _, _ = db.get_findings("lab-img-26-pg")
    img = _image_rows(rows)
    patterns = {(r.get("column_name"), r.get("pattern_detected")) for r in img}
    assert ("foto_documento", "IMAGE_BLOB_IN_COLUMN") in patterns
    assert ("foto_b64", "IMAGE_BASE64_IN_COLUMN") in patterns
    assert not any(r.get("column_name") == "hash_blob" for r in img)


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(
    not _driver_available("pymysql"),
    reason="pymysql not installed",
)
def test_D2362_26_run_image_findings_lab_mariadb(tmp_path: Path) -> None:
    from tests.test_sql_image_blob import _LowScanner, _image_rows

    audit = tmp_path / "lab-audit-my.db"
    db = LocalDBManager(str(audit))
    db.set_current_session_id("lab-img-26-my")
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(_mariadb_target(), _LowScanner(), db, detection_config=det)
    conn.run()
    conn.close()
    rows, _, _, _ = db.get_findings("lab-img-26-my")
    img = _image_rows(rows)
    patterns = {(r.get("column_name"), r.get("pattern_detected")) for r in img}
    assert ("foto_documento", "IMAGE_BLOB_IN_COLUMN") in patterns
    assert ("foto_b64", "IMAGE_BASE64_IN_COLUMN") in patterns
    assert ("anexo", "IMAGE_BLOB_IN_COLUMN") in patterns
    assert not any(r.get("column_name") == "hash_blob" for r in img)


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(not _driver_available("pymssql"), reason="pymssql not installed")
def test_D2362_26_run_image_findings_lab_mssql(tmp_path: Path) -> None:
    from tests.test_sql_image_blob import _LowScanner, _image_rows

    audit = tmp_path / "lab-audit-ms.db"
    db = LocalDBManager(str(audit))
    db.set_current_session_id("lab-img-26-ms")
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(_mssql_target(), _LowScanner(), db, detection_config=det)
    conn.run()
    conn.close()
    rows, _, _, _ = db.get_findings("lab-img-26-ms")
    img = _image_rows(rows)
    patterns = {(r.get("column_name"), r.get("pattern_detected")) for r in img}
    assert ("foto_documento", "IMAGE_BLOB_IN_COLUMN") in patterns
    assert ("foto_b64", "IMAGE_BASE64_IN_COLUMN") in patterns
    assert not any(r.get("column_name") == "hash_blob" for r in img)


@pytest.mark.skipif(not _HAS_LAB, reason=_LAB_REASON)
@pytest.mark.skipif(
    not _driver_available("oracledb"),
    reason="oracledb not installed",
)
def test_D2362_26_run_image_findings_lab_oracle(tmp_path: Path) -> None:
    from tests.test_sql_image_blob import _LowScanner, _image_rows

    audit = tmp_path / "lab-audit-ora.db"
    db = LocalDBManager(str(audit))
    db.set_current_session_id("lab-img-26-ora")
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn = SQLConnector(_oracle_target(), _LowScanner(), db, detection_config=det)
    conn.run()
    conn.close()
    rows, _, _, _ = db.get_findings("lab-img-26-ora")
    img = _image_rows(rows)
    patterns = {(r.get("column_name"), r.get("pattern_detected")) for r in img}
    assert ("foto_documento", "IMAGE_BLOB_IN_COLUMN") in patterns
    assert ("foto_b64", "IMAGE_BASE64_IN_COLUMN") in patterns
    assert not any(r.get("column_name") == "hash_blob" for r in img)

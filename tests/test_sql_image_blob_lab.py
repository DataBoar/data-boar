"""Lab + fixture tests for #2362 D2362-24 .. D2362-26 (skip when lab unset)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from connectors.sql_connector import SQLConnector
from core.image_blob import column_type_family, sniff_image_kind
from core.database import LocalDBManager

_INIT = Path(__file__).resolve().parents[1] / "deploy" / "lab-smoke-stack" / "init"
_HAS_LAB = bool(os.environ.get("DATA_BOAR_LAB_HOST", "").strip())
_LAB_REASON = "DATA_BOAR_LAB_HOST unset — live lab tests skipped"

_SEED_ENGINES = ("postgres", "mariadb", "mssql", "oracle")
_COLUMN_TYPES: dict[str, dict[str, str]] = {
    "postgres": {
        "foto_documento": "BYTEA",
        "anexo": "BYTEA",
        "foto_b64": "TEXT",
        "hash_blob": "BYTEA",
    },
    "mariadb": {
        "foto_documento": "LONGBLOB",
        "anexo": "VARBINARY(255)",
        "foto_b64": "LONGTEXT",
        "hash_blob": "LONGBLOB",
    },
    "mssql": {
        "foto_documento": "VARBINARY(MAX)",
        "anexo": "IMAGE",
        "foto_b64": "NVARCHAR(MAX)",
        "hash_blob": "VARBINARY(MAX)",
    },
    "oracle": {
        "foto_documento": "BLOB",
        "anexo": "RAW(2000)",
        "foto_b64": "CLOB",
        "hash_blob": "BLOB",
    },
}


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


@pytest.mark.parametrize("engine", _SEED_ENGINES)
def test_D2362_lab_04_sql_seed_present(engine: str) -> None:
    path = _INIT / engine / "04_lab_image_blob.sql"
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "lab_image_blob" in text
    assert "Synthetic lab data only" in text


def test_D2362_lab_apply_scripts_list_04_seed() -> None:
    mssql = (_INIT / "mssql" / "apply_lab_smoke.sh").read_text(encoding="utf-8")
    oracle = (_INIT / "oracle" / "apply_lab_smoke_pdb.sh").read_text(encoding="utf-8")
    assert "04_lab_image_blob.sql" in mssql
    assert "04_lab_image_blob.sql" in oracle


@pytest.mark.parametrize("engine", _SEED_ENGINES)
def test_D2362_24_static_column_families_from_contract(engine: str) -> None:
    """Static contract: column types in each seed map to text/binary families."""
    for col, typ in _COLUMN_TYPES[engine].items():
        fam = column_type_family(typ)
        if col == "foto_b64":
            assert fam == "text", f"{engine}.{col} ({typ})"
        elif col == "hash_blob":
            assert fam == "binary", f"{engine}.{col} ({typ})"
        else:
            assert fam == "binary", f"{engine}.{col} ({typ})"


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

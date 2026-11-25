"""D2362-14 .. D2362-22 — image/BLOB probe on SQLConnector (SQLite fixture)."""

from __future__ import annotations

import base64
import logging
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from connectors.sql_connector import (
    SCAN_FAILURE_REASON_IMAGE_PROBE_ERROR,
    SQLConnector,
)
from core.database import LocalDBManager
from core.image_blob import (
    IMAGE_BASE64_PATTERN,
    IMAGE_BLOB_PATTERN,
    column_type_family,
)

_SESSION = "sess-img-blob"
_TARGET = "ImgBlobSQLite"

_JPEG = bytes.fromhex("ffd8ffe0") + b"\x00" * 512
_PDF = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 200
_NOISE = bytes([0xDE, 0xAD, 0xBE, 0xEF] * 16)
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 120
_PNG_B64 = "data:image/png;base64," + base64.b64encode(_PNG).decode("ascii")
_TOKEN_B64 = base64.b64encode(bytes(range(80)) * 2).decode("ascii")[:150]


class _LowScanner:
    def scan_column(
        self, cname: str, sample: str, connector_data_type: str | None = None
    ) -> dict[str, Any]:
        return {
            "sensitivity_level": "LOW",
            "pattern_detected": "NONE",
            "norm_tag": "",
            "ml_confidence": 0,
        }


def _create_docs_db(path: Path, *, foto_rows: int = 3) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            CREATE TABLE docs (
                foto BLOB,
                anexo BLOB,
                ruido BLOB,
                foto_b64 TEXT,
                token TEXT,
                notas TEXT
            )
            """
        )
        for _ in range(foto_rows):
            conn.execute(
                "INSERT INTO docs VALUES (?,?,?,?,?,?)",
                (
                    _JPEG,
                    _PDF,
                    _NOISE,
                    _PNG_B64,
                    _TOKEN_B64,
                    "texto operacional sem imagem",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _connector(
    db_path: Path,
    audit: Path,
    *,
    enabled: bool,
    sampling_rows: int = 5,
    workers: int = 1,
) -> tuple[SQLConnector, LocalDBManager]:
    db = LocalDBManager(str(audit))
    db.set_current_session_id(_SESSION)
    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": _TARGET,
        "_intra_target_workers": workers,
    }
    det = {"image_blob": {"enabled": enabled, "sampling_rows": sampling_rows}}
    conn = SQLConnector(target, _LowScanner(), db, sample_limit=5, detection_config=det)
    return conn, db


def _run(conn: SQLConnector) -> tuple[list[dict], list[dict]]:
    conn.run()
    db_rows, _, _, fails = conn.db_manager.get_findings(_SESSION)
    return db_rows, fails


def _image_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if (r.get("pattern_detected") or "").startswith("IMAGE_")]


def _pick(rows: list[dict], column: str) -> dict | None:
    for r in rows:
        if r.get("column_name") == column:
            return r
    return None


@pytest.fixture()
def docs_db(tmp_path: Path) -> Path:
    p = tmp_path / "docs.sqlite"
    _create_docs_db(p)
    return p


@pytest.fixture()
def audit_db(tmp_path: Path) -> Path:
    return tmp_path / "audit.db"


def test_D2362_14_image_blob_findings_enabled(docs_db: Path, audit_db: Path):
    conn, _db = _connector(docs_db, audit_db, enabled=True)
    rows, _ = _run(conn)
    img = _image_rows(rows)
    foto = _pick(img, "foto")
    anexo = _pick(img, "anexo")
    assert foto is not None
    assert foto["pattern_detected"] == IMAGE_BLOB_PATTERN
    assert foto["sensitivity_level"] == "MEDIUM"
    assert "jpeg" in (foto.get("norm_tag") or "")
    assert "column name suggests image" in (foto.get("norm_tag") or "")
    assert anexo is not None
    assert anexo["pattern_detected"] == IMAGE_BLOB_PATTERN
    assert "pdf" in (anexo.get("norm_tag") or "")
    assert _pick(img, "ruido") is None
    assert _pick(img, "token") is None
    assert _pick(img, "notas") is None


def test_D2362_15_base64_column_finding(docs_db: Path, audit_db: Path):
    conn, _ = _connector(docs_db, audit_db, enabled=True)
    rows, _ = _run(conn)
    row = _pick(_image_rows(rows), "foto_b64")
    assert row is not None
    assert row["pattern_detected"] == IMAGE_BASE64_PATTERN
    assert "png" in (row.get("norm_tag") or "")


def test_D2362_16_disabled_matches_non_image_findings(docs_db: Path, audit_db: Path):
    conn_off, db_off = _connector(docs_db, audit_db, enabled=False)
    off_rows, _ = _run(conn_off)
    audit2 = audit_db.parent / "audit2.db"
    conn_on, db_on = _connector(docs_db, audit2, enabled=True)
    on_rows, _ = _run(conn_on)
    non_image_off = {
        (
            r.get("table_name"),
            r.get("column_name"),
            r.get("pattern_detected"),
        )
        for r in off_rows
        if not (r.get("pattern_detected") or "").startswith("IMAGE_")
    }
    non_image_on = {
        (
            r.get("table_name"),
            r.get("column_name"),
            r.get("pattern_detected"),
        )
        for r in on_rows
        if not (r.get("pattern_detected") or "").startswith("IMAGE_")
    }
    assert non_image_off == non_image_on


def test_D2362_17_extra_substr_queries_only_binary(
    docs_db: Path, audit_db: Path, monkeypatch: pytest.MonkeyPatch
):
    calls: list[tuple[str, str]] = []
    orig = SQLConnector._sample_column_prefixes

    def spy(self, schema, table, column_name, ctype, *, limit):
        calls.append((column_name, ctype))
        return orig(self, schema, table, column_name, ctype, limit=limit)

    monkeypatch.setattr(SQLConnector, "_sample_column_prefixes", spy)
    off_audit = audit_db.parent / "off.db"
    on_audit = audit_db.parent / "on.db"
    conn_off, _ = _connector(docs_db, off_audit, enabled=False)
    conn_off.run()
    n_off = len(calls)
    conn_on, _ = _connector(docs_db, on_audit, enabled=True)
    conn_on.run()
    assert n_off == 0
    assert len(calls) - n_off == 3
    assert all(column_type_family(ctype) == "binary" for _, ctype in calls[n_off:])


def test_D2362_18_default_disabled_no_image_findings(docs_db: Path, audit_db: Path):
    db = LocalDBManager(str(audit_db))
    db.set_current_session_id(_SESSION)
    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(docs_db),
        "name": _TARGET,
    }
    conn = SQLConnector(target, _LowScanner(), db, sample_limit=5)
    rows, _ = _run(conn)
    assert _image_rows(rows) == []


def test_D2362_19_sampling_rows_limits_cells(
    docs_db: Path, audit_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    big = tmp_path / "many.sqlite"
    _create_docs_db(big, foto_rows=10)
    seen: list[int] = []
    import core.image_blob as ib

    real = ib.cell_to_bytes

    def counting(cell: object) -> bytes | None:
        out = real(cell)
        if out is not None:
            seen.append(len(out))
        return out

    monkeypatch.setattr(ib, "cell_to_bytes", counting)
    conn, _ = _connector(big, audit_db, enabled=True, sampling_rows=2)
    conn.run()
    assert len(seen) <= 2


def test_D2362_20_probe_failure_reason(
    docs_db: Path, audit_db: Path, monkeypatch: pytest.MonkeyPatch
):
    import connectors.sql_sampling as sm

    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(sm.SamplingManager, "build_column_prefix_sample", boom)
    conn, db = _connector(docs_db, audit_db, enabled=True)
    conn.run()
    *_, fails = db.get_findings(_SESSION)
    reasons = [f.get("reason") for f in fails]
    assert SCAN_FAILURE_REASON_IMAGE_PROBE_ERROR in reasons
    assert all(r != "sampling_error" for r in reasons if r)
    assert any((f.get("details") or "").startswith("image_probe ") for f in fails)


def test_D2362_21_no_raw_bytes_in_logs_or_db(docs_db: Path, audit_db: Path, caplog):
    caplog.set_level(logging.DEBUG)
    conn, db = _connector(docs_db, audit_db, enabled=True)
    _run(conn)
    blob = caplog.text + str(db.get_findings(_SESSION))
    assert "ffd8ff" not in blob.lower()
    assert "%PDF" not in blob
    assert _PNG_B64[:32] not in blob


def test_D2362_22_parallel_matches_serial(docs_db: Path, tmp_path: Path):
    audit_s = tmp_path / "serial.db"
    audit_p = tmp_path / "parallel.db"
    db_s = LocalDBManager(str(audit_s))
    db_s.set_current_session_id("serial-img")
    db_p = LocalDBManager(str(audit_p))
    db_p.set_current_session_id("parallel-img")
    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(docs_db),
        "name": _TARGET,
    }
    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    conn_s = SQLConnector(
        {**target, "_intra_target_workers": 1},
        _LowScanner(),
        db_s,
        sample_limit=5,
        detection_config=det,
    )
    conn_p = SQLConnector(
        {**target, "_intra_target_workers": 2},
        _LowScanner(),
        db_p,
        sample_limit=5,
        detection_config=det,
    )
    conn_s.run()
    conn_p.run()

    def sig(rows: list[dict]) -> set[tuple]:
        return {
            (
                r.get("table_name"),
                r.get("column_name"),
                r.get("pattern_detected"),
                r.get("norm_tag"),
            )
            for r in _image_rows(rows)
        }

    s_rows, _, _, _ = db_s.get_findings("serial-img")
    p_rows, _, _, _ = db_p.get_findings("parallel-img")
    assert sig(s_rows) == sig(p_rows)


_HOSTILE_SESSION = "sess-hostile-ident"


def test_D2362_23_hostile_sqlite_identifiers_png_no_leak(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """E2E: quoted hostile table/column names, PNG prefix probe, no byte leak (D2362-21 pattern)."""
    db_path = tmp_path / "hostile_ident.sqlite"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute('CREATE TABLE "tb; order" ("pic sel" BLOB, notes TEXT)')
        conn.execute(
            'INSERT INTO "tb; order" ("pic sel", notes) VALUES (?, ?)',
            (_PNG, "notas operacionais"),
        )
        conn.commit()
    finally:
        conn.close()

    audit = tmp_path / "audit_hostile.db"
    db = LocalDBManager(str(audit))
    db.set_current_session_id(_HOSTILE_SESSION)
    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "HostileIdentSQLite",
    }
    det = {"image_blob": {"enabled": True, "sampling_rows": 3}}
    caplog.set_level(logging.DEBUG)
    sql_conn = SQLConnector(
        target, _LowScanner(), db, sample_limit=5, detection_config=det
    )
    sql_conn.run()
    rows, _, _, _ = db.get_findings(_HOSTILE_SESSION)
    imgs = _image_rows(rows)
    assert imgs, "expected IMAGE_* finding for hostile BLOB column"
    assert any((r.get("pattern_detected") or "").startswith("IMAGE_") for r in imgs)
    leak = caplog.text + str(db.get_findings(_HOSTILE_SESSION))
    assert "ffd8ff" not in leak.lower()
    assert "%PDF" not in leak
    assert _PNG_B64[:32] not in leak
    assert _PNG[:8].hex() not in leak.lower()

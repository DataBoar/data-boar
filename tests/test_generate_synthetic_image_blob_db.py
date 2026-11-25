"""D2362-23 — synthetic SQLite generator + scan smoke."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.brazilian_cpf import cpf_checksum_valid
from core.database import LocalDBManager

import random

from scripts.generate_synthetic_image_blob_db import _build, _synthetic_cpf
from tests.test_sql_image_blob import _LowScanner, _image_rows, _pick


def _run_script(
    output: Path, *, force: bool = False, seed: int = 1729
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(
            Path(__file__).resolve().parents[1]
            / "scripts/generate_synthetic_image_blob_db.py"
        ),
        "--output",
        str(output),
        "--seed",
        str(seed),
    ]
    if force:
        cmd.append("--force")
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def test_D2362_23_generator_refuses_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "synth.sqlite"
    _build(out, seed=1729)
    rc = _run_script(out, force=False)
    assert rc.returncode == 2
    assert "refusing to overwrite" in rc.stderr


def test_D2362_23_generator_deterministic_and_scan(tmp_path: Path) -> None:
    out = tmp_path / "synth.sqlite"
    proc = _run_script(out, force=True, seed=1729)
    assert proc.returncode == 0
    assert proc.stdout.strip() == f"wrote {out} tables=2 rows=12"
    proc2 = _run_script(tmp_path / "synth2.sqlite", force=True, seed=1729)
    assert proc2.returncode == 0
    assert "tables=2 rows=12" in proc2.stdout
    assert proc.stdout.strip().endswith("tables=2 rows=12")
    assert proc2.stdout.strip().endswith("tables=2 rows=12")
    import sqlite3

    conn = sqlite3.connect(str(out))
    conn2 = sqlite3.connect(str(tmp_path / "synth2.sqlite"))
    try:
        blob1 = conn.execute(
            "SELECT foto_documento FROM cadastro_documentos WHERE id=1"
        ).fetchone()[0]
        blob2 = conn2.execute(
            "SELECT foto_documento FROM cadastro_documentos WHERE id=1"
        ).fetchone()[0]
    finally:
        conn.close()
        conn2.close()
    assert blob1 == blob2

    audit = tmp_path / "audit.db"
    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(out),
        "name": "SynthImg",
    }
    db = LocalDBManager(str(audit))
    db.set_current_session_id("gen-23")
    from connectors.sql_connector import SQLConnector

    det = {"image_blob": {"enabled": True, "sampling_rows": 5}}
    connector = SQLConnector(target, _LowScanner(), db, detection_config=det)
    connector.run()
    connector.close()
    rows, _, _, _ = db.get_findings("gen-23")
    img = _image_rows(rows)
    assert _pick(img, "foto_documento") is not None
    assert "jpeg" in (_pick(img, "foto_documento") or {}).get("norm_tag", "")
    assert _pick(img, "foto_b64") is not None
    assert "png" in (_pick(img, "foto_b64") or {}).get("norm_tag", "")
    assert _pick(img, "anexo") is not None
    assert "pdf" in (_pick(img, "anexo") or {}).get("norm_tag", "")
    assert _pick(img, "hash_blob") is None

    rng = random.Random(1729)
    for _ in range(6):
        assert cpf_checksum_valid(_synthetic_cpf(rng))

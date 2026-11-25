"""Static lab seed + contract tests for #2362 (no live DATA_BOAR_LAB_HOST)."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.image_blob import column_type_family

_INIT = Path(__file__).resolve().parents[1] / "deploy" / "lab-smoke-stack" / "init"

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

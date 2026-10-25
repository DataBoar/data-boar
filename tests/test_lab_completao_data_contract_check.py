"""Tests for scripts/lab_completao_data_contract_check.py (SQLite only)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine, text


def _run_script(contracts: Path) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "lab_completao_data_contract_check.py"
    return subprocess.run(
        [sys.executable, str(script), "--contracts", str(contracts)],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )


def test_data_contract_check_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dbf = tmp_path / "contract.db"
    url = f"sqlite:///{dbf.as_posix()}"
    eng = create_engine(url)
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE people (id INTEGER, email TEXT)"))
    eng.dispose()

    doc = {
        "version": 1,
        "checks": [
            {
                "name": "people_cols",
                "connection": {"url_from_env": "TEST_LAB_CONTRACT_SQL_URL"},
                "schema": None,
                "table": "people",
                "require_columns": ["id", "email"],
            }
        ],
    }
    yml = tmp_path / "contracts.yaml"
    yml.write_text(yaml.safe_dump(doc), encoding="utf-8")
    monkeypatch.setenv("TEST_LAB_CONTRACT_SQL_URL", url)

    proc = _run_script(yml)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_data_contract_check_fails_on_missing_column(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dbf = tmp_path / "contract2.db"
    url = f"sqlite:///{dbf.as_posix()}"
    eng = create_engine(url)
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE people (id INTEGER)"))
    eng.dispose()

    doc = {
        "version": 1,
        "checks": [
            {
                "name": "people_missing_email",
                "connection": {"url_from_env": "TEST_LAB_CONTRACT_SQL_URL"},
                "table": "people",
                "require_columns": ["id", "email"],
            }
        ],
    }
    yml = tmp_path / "contracts2.yaml"
    yml.write_text(yaml.safe_dump(doc), encoding="utf-8")
    monkeypatch.setenv("TEST_LAB_CONTRACT_SQL_URL", url)

    proc = _run_script(yml)
    assert proc.returncode == 2
    assert "missing column" in proc.stderr.lower()


def test_data_contract_check_fails_on_missing_env(tmp_path: Path) -> None:
    doc = {
        "version": 1,
        "checks": [
            {
                "name": "no_env",
                "connection": {"url_from_env": "TEST_LAB_CONTRACT_SQL_URL_MISSING"},
                "table": "people",
                "require_columns": ["id"],
            }
        ],
    }
    yml = tmp_path / "contracts3.yaml"
    yml.write_text(yaml.safe_dump(doc), encoding="utf-8")

    proc = _run_script(yml)
    assert proc.returncode == 1
    assert "unset" in proc.stderr.lower() or "empty" in proc.stderr.lower()

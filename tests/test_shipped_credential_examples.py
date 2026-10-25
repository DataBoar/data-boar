"""Shipped sample YAML must load under the #2086 credential env gate."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from config.loader import normalize_config

_REPO = Path(__file__).resolve().parents[1]
_SAMPLES = (
    _REPO / "deploy" / "samples" / "config.starter-lgpd-eval.yaml",
    _REPO / "deploy" / "compat-matrix-config-ref" / "config-db.yaml",
)


def test_shipped_credential_examples_normalize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_BOAR_DEMO_DB_PASSWORD", "demo-secret")
    monkeypatch.setenv("DATA_BOAR_LAB_PG_PASSWORD", "pg-secret")
    monkeypatch.setenv("DATA_BOAR_LAB_MY_PASSWORD", "my-secret")
    monkeypatch.setenv("DATA_BOAR_LAB_MSSQL_SA_PASSWORD", "mssql-secret")
    monkeypatch.setenv("DATA_BOAR_LAB_ORACLE_PASSWORD", "oracle-secret")
    for path in _SAMPLES:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        out = normalize_config(raw)
        assert out["targets"]

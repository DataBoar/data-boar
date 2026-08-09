"""
Phase 1: scan.validate_crypto / --validate-crypto / API validate_crypto wiring.

Off by default; CLI and API body override config for the run; engine skips crypto
signals when the flag is false or absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.crypto_audit import validate_crypto_enabled
from core.engine import AuditEngine


def test_validate_crypto_enabled_defaults_false() -> None:
    assert validate_crypto_enabled(None) is False
    assert validate_crypto_enabled({}) is False
    assert validate_crypto_enabled({"scan": {}}) is False
    assert validate_crypto_enabled({"scan": {"validate_crypto": False}}) is False


def test_validate_crypto_enabled_true_from_config() -> None:
    assert validate_crypto_enabled({"scan": {"validate_crypto": True}}) is True


def test_cli_help_includes_validate_crypto() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--validate-crypto" in proc.stdout


def _engine_with_pg_target(
    config: dict, monkeypatch: pytest.MonkeyPatch
) -> AuditEngine:
    class DummyConnector:
        def __init__(self, *args, **kwargs):
            pass

        def run(self) -> None:
            return None

    def fake_connector_for_target(target):
        return DummyConnector, target

    from core import engine as engine_mod

    monkeypatch.setattr(
        engine_mod, "connector_for_target", fake_connector_for_target, raising=True
    )
    eng = AuditEngine(config)
    eng._run_audit_targets()
    return eng


def test_engine_skips_crypto_signals_when_validate_crypto_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "targets": [
            {
                "name": "pg-secure",
                "type": "database",
                "driver": "postgresql+psycopg2",
                "dsn": "postgresql+psycopg2://user:pass@host:5432/db?sslmode=require",
            }
        ],
        "file_scan": {"extensions": [".txt"]},
        "detection": {},
        "scan": {"validate_crypto": False},
    }
    eng = _engine_with_pg_target(config, monkeypatch)
    assert eng.crypto_signals == []


def test_engine_skips_crypto_signals_when_validate_crypto_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "targets": [
            {
                "name": "pg-secure",
                "type": "database",
                "driver": "postgresql+psycopg2",
                "dsn": "postgresql+psycopg2://user:pass@host:5432/db?sslmode=require",
            }
        ],
        "file_scan": {"extensions": [".txt"]},
        "detection": {},
    }
    eng = _engine_with_pg_target(config, monkeypatch)
    assert eng.crypto_signals == []


@pytest.mark.parametrize("endpoint", ["/scan", "/start"])
def test_post_scan_validate_crypto_sets_scan_flag_for_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    out_dir = str(tmp_path).replace("\\", "/")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "notes.txt").write_text("hello\n", encoding="utf-8")
    scan_path = str(data_dir).replace("\\", "/")
    config_yaml = f"""targets:
  - name: fs1
    type: filesystem
    path: {scan_path}
    recursive: false
file_scan:
  extensions: [.txt]
  recursive: true
  scan_sqlite_as_db: false
  sample_limit: 2
report:
  output_dir: {out_dir}
api:
  port: 8088
sqlite_path: {out_dir}/audit_results.db
scan:
  max_workers: 1
  validate_crypto: false
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    seen: list[bool] = []

    import api.routes as routes
    from core import engine as engine_mod

    original_run = engine_mod.AuditEngine._run_audit_targets

    def capturing_run(self):
        seen.append(validate_crypto_enabled(self.config))
        return original_run(self)

    monkeypatch.setattr(
        engine_mod.AuditEngine, "_run_audit_targets", capturing_run, raising=True
    )

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None

        client = TestClient(routes.app)
        resp = client.post(endpoint, json={"validate_crypto": True})
        assert resp.status_code == 200, resp.text
        assert seen == [True]
        # Restore after run: persistent config must not keep the override.
        eng = routes._get_engine()
        assert validate_crypto_enabled(eng.config) is False
    finally:
        routes._config_path = original_config_path
        routes._config = original_config
        routes._audit_engine = original_engine

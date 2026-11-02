"""#2164 — a 1.7.x config must load in 1.8.x without renaming env vars."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from config.loader import load_config, normalize_config
from core.about import _package_version
from core.integrity_anchor import (
    ensure_integrity_anchor,
    reset_integrity_anchor_for_tests,
)

REPO = Path(__file__).resolve().parents[1]
LEGACY_FIXTURE = (
    REPO / "tests" / "data" / "upgrade_2162" / "pre_1_8_0_legacy_credentials.yaml"
)


def _legacy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_STRICT", raising=False)
    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_HOSTS_UNRESTRICTED", raising=False)
    monkeypatch.setenv("DATABOAR_PG_PASSWORD", "pg-secret")
    monkeypatch.setenv("MEU_BANCO_SENHA", "smb-secret")
    monkeypatch.setenv("DATABOAR_MONGO_PASS", "mongo-secret")
    monkeypatch.setenv("DATABOAR_REDIS_PASS", "redis-secret")


def test_legacy_unprefixed_non_rest_config_loads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _legacy_env(monkeypatch)
    cfg = load_config(LEGACY_FIXTURE)
    by_name = {t["name"]: t for t in cfg["targets"]}
    assert by_name["pg-legacy"]["pass"] == "pg-secret"
    assert by_name["smb-legacy"]["pass"] == "smb-secret"
    assert by_name["mongo-legacy"]["pass"] == "mongo-secret"
    assert by_name["redis-legacy"]["pass"] == "redis-secret"


def test_strict_mode_rejects_legacy_config_without_host_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _legacy_env(monkeypatch)
    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_STRICT", "1")
    with pytest.raises(ValueError, match="DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS"):
        load_config(LEGACY_FIXTURE)


def test_rest_target_still_rejects_unprefixed_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LAB_REST_PASSWORD", "rest-secret")
    data = {
        "targets": [
            {
                "name": "rest1",
                "type": "api",
                "base_url": "https://api.example.com",
                "pass_from_env": "LAB_REST_PASSWORD",
                "allowed_hosts": ["api.example.com"],
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    # Loader copies REST env secrets; the #1977 prefix is enforced at connect.
    out = normalize_config(data)
    assert out["targets"][0]["pass"] == "rest-secret"
    from connectors.rest_connector import _validate_target_env_var_names

    with pytest.raises(ValueError, match="pass_from_env.*#1977"):
        _validate_target_env_var_names(out["targets"][0])


@pytest.mark.parametrize(
    "reserved",
    ("DATA_BOAR_LICENSE_PATH", "DATA_BOAR_HTML_CSRF_SECRET"),
)
@pytest.mark.parametrize("kind", ["database", "smb", "mongodb", "redis", "api"])
def test_reserved_env_name_refused_on_every_target_type(
    reserved: str, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(reserved, "must-not-copy")
    target: dict = {
        "name": "t1",
        "type": kind,
        "pass_from_env": reserved,
    }
    if kind == "api":
        target["base_url"] = "https://api.example.com"
    else:
        target["host"] = "db.example"
    with pytest.raises(ValueError, match="reserved for this process"):
        normalize_config(
            {"targets": [target], "api": {}, "report": {"output_dir": "."}}
        )


def test_version_ignores_unprefixed_target_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _legacy_env(monkeypatch)
    cfg = tmp_path / "legacy.yaml"
    cfg.write_text(LEGACY_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(REPO / "main.py"), "--config", str(cfg), "--version"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=30,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "Config error" not in r.stdout + r.stderr
    assert "pass_from_env" not in r.stdout + r.stderr


def test_reconcile_ignores_unprefixed_target_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _legacy_env(monkeypatch)
    db = tmp_path / "a.db"
    body = LEGACY_FIXTURE.read_text(encoding="utf-8").replace(
        "audit_legacy_upgrade.db", db.as_posix()
    )
    cfg = tmp_path / "legacy.yaml"
    cfg.write_text(body, encoding="utf-8")
    reset_integrity_anchor_for_tests()
    ensure_integrity_anchor({"sqlite_path": str(db)})
    ver = _package_version()
    r = subprocess.run(
        [
            sys.executable,
            str(REPO / "main.py"),
            "--config",
            str(cfg),
            "--reconcile-integrity-anchor",
            "--confirm-upgrade-to",
            ver,
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Config error" not in r.stdout + r.stderr
    assert "[OK] integrity anchor re-baselined" in r.stdout

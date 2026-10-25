"""
#1190 — /logs role gate follows rbac_enforcement_active (same as middleware).

Four corners:
1. Community, no require_api_key → 200
2. Community, require_api_key true, no key → 401
3. Pro + RBAC enabled, no principal → 401
4. Pro + RBAC off (opt-out / default) → 200
"""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from utils.logger import configure_audit_log_directory


def _setup(tmp_path: Path, config: dict):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    import api.routes as routes

    prev_path = routes._config_path
    prev_cfg = routes._config
    prev_engine = routes._audit_engine
    routes._config_path = str(cfg_path)
    routes._config = None
    routes._audit_engine = None
    return routes, TestClient(routes.app), (prev_path, prev_cfg, prev_engine)


def _teardown(routes, previous):
    prev_path, prev_cfg, prev_engine = previous
    if routes._audit_engine is not None:
        routes._audit_engine.db_manager.dispose()
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_engine
    configure_audit_log_directory(None)


def _base(tmp_path: Path, *, logs_dir: Path) -> dict:
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "audit_20260731.log").write_text(
        "session=deadbeefcafe\nFinding: demo\n", encoding="utf-8"
    )
    return {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "sqlite_path": str(tmp_path / "audit.db"),
        "api": {
            "port": 8088,
            "audit_logs": {
                "enabled": True,
                "directory": str(logs_dir),
            },
        },
    }


def test_community_logs_open_without_require_api_key(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    config = _base(tmp_path, logs_dir=logs_dir)
    config["licensing"] = {"effective_tier": "community"}
    routes, client, previous = _setup(tmp_path, config)
    try:
        resp = client.get("/logs")
        assert resp.status_code == 200
        by_sid = client.get("/logs/deadbeefcafe")
        assert by_sid.status_code == 200
    finally:
        _teardown(routes, previous)


def test_community_require_api_key_without_key_401(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    config = _base(tmp_path, logs_dir=logs_dir)
    config["licensing"] = {"effective_tier": "community"}
    config["api"]["require_api_key"] = True
    config["api"]["api_key"] = "community-lock-key"
    routes, client, previous = _setup(tmp_path, config)
    try:
        resp = client.get("/logs")
        assert resp.status_code == 401
    finally:
        _teardown(routes, previous)


def test_pro_rbac_enabled_without_principal_401(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    config = _base(tmp_path, logs_dir=logs_dir)
    config["licensing"] = {"effective_tier": "pro"}
    config["api"]["rbac"] = {"enabled": True, "api_key_roles": ["audit_logs.read"]}
    config["api"]["api_key"] = "pro-rbac-key"
    routes, client, previous = _setup(tmp_path, config)
    try:
        resp = client.get("/logs")
        assert resp.status_code == 401
        detail = resp.json().get("detail") or ""
        assert "Authentication required" in detail
    finally:
        _teardown(routes, previous)


def test_pro_rbac_disabled_logs_open_200(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    config = _base(tmp_path, logs_dir=logs_dir)
    config["licensing"] = {"effective_tier": "pro"}
    # rbac.enabled absent/false — same default as product; /logs like /findings
    routes, client, previous = _setup(tmp_path, config)
    try:
        resp = client.get("/logs")
        assert resp.status_code == 200
    finally:
        _teardown(routes, previous)

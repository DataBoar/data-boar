"""Regression tests for issue #1202 web-exposure hardening."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient


def _setup_client(tmp_path: Path, config: dict):
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
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_engine


def test_logs_endpoint_disabled_by_default(tmp_path: Path):
    config = {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8088},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    routes, client, previous = _setup_client(tmp_path, config)
    try:
        resp = client.get("/logs")
        assert resp.status_code == 403
    finally:
        _teardown(routes, previous)


def test_logs_endpoint_requires_specific_permission(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "audit_20260712.log").write_text(
        "session=abc123def456\n", encoding="utf-8"
    )
    config = {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "api": {
            "port": 8088,
            "api_key": "secret123",
            "audit_logs": {
                "enabled": True,
                "directory": str(logs_dir),
            },
            "rbac": {"api_key_roles": ["dashboard"]},
        },
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    routes, client, previous = _setup_client(tmp_path, config)
    try:
        resp = client.get("/logs", headers={"X-API-Key": "secret123"})
        assert resp.status_code == 403
        assert "audit_logs.read" in (resp.json().get("detail") or "")
    finally:
        _teardown(routes, previous)


def test_logs_endpoint_allows_audit_logs_read_permission(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_id = "abc123def456"
    (logs_dir / "audit_20260712.log").write_text(
        f"session={session_id}\n", encoding="utf-8"
    )
    config = {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "api": {
            "port": 8088,
            "api_key": "secret123",
            "audit_logs": {
                "enabled": True,
                "directory": str(logs_dir),
            },
            "rbac": {"api_key_roles": ["audit_logs.read"]},
        },
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    routes, client, previous = _setup_client(tmp_path, config)
    try:
        latest = client.get("/logs", headers={"X-API-Key": "secret123"})
        assert latest.status_code == 200
        by_session = client.get(
            f"/logs/{session_id}",
            headers={"X-API-Key": "secret123"},
        )
        assert by_session.status_code == 200
    finally:
        _teardown(routes, previous)


def test_scan_database_denies_adhoc_target_by_default(tmp_path: Path):
    config = {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8088},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    routes, client, previous = _setup_client(tmp_path, config)
    try:
        resp = client.post(
            "/scan_database",
            json={
                "name": "adhoc-db",
                "host": "127.0.0.1",
                "port": 5432,
                "user": "u",
                "password": "p",
                "database": "d",
                "driver": "postgresql+psycopg2",
            },
        )
        assert resp.status_code == 403
        assert "allow_adhoc_targets" in (resp.json().get("detail") or "")
    finally:
        _teardown(routes, previous)


def test_scan_database_allows_adhoc_target_when_opted_in(tmp_path: Path):
    config = {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8088, "allow_adhoc_targets": True},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    routes, client, previous = _setup_client(tmp_path, config)
    try:
        resp = client.post(
            "/scan_database",
            json={
                "name": "adhoc-db",
                "host": "127.0.0.1",
                "port": 5432,
                "user": "u",
                "password": "p",
                "database": "d",
                "driver": "postgresql+psycopg2",
            },
        )
        assert resp.status_code == 200
        assert resp.json().get("session_id")
    finally:
        _teardown(routes, previous)


def test_status_reflects_forwarded_header_trust_posture(tmp_path: Path):
    config = {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "api": {"port": 8088, "trusted_proxy_cidrs": ["10.0.0.0/8"]},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    routes, client, previous = _setup_client(tmp_path, config)
    try:
        resp = client.get("/status", headers={"X-Forwarded-Proto": "https"})
        assert resp.status_code == 200
        posture = resp.json().get("forwarded_headers") or {}
        assert posture.get("trusted_proxy_configured") is True
        assert posture.get("forwarded_proto_header_present") is True
        assert posture.get("forwarded_proto_trusted") is False
        assert posture.get("effective_scheme") == "http"
    finally:
        _teardown(routes, previous)

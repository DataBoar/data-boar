"""Audit log PII self-scan before export (#877)."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from core.log_self_scan import scan_text_for_pii
from utils.logger import configure_audit_log_directory, log_audit_trail_finding


def test_scan_text_for_pii_empty_returns_empty_dict() -> None:
    assert scan_text_for_pii("") == {}
    assert scan_text_for_pii("   \n") == {}


def test_scan_text_for_pii_clean_operational_log() -> None:
    text = "session=deadbeefcafe\nFinding: demo | target | loc | high | LGPD_CPF\n"
    assert scan_text_for_pii(text) == {}


def test_scan_text_for_pii_detects_categories_without_returning_cleartext() -> None:
    secret_cpf = "529.982.247-25"
    secret_email = "leak-test@example.com"
    text = f"DEBUG context user={secret_cpf} contact={secret_email}\n"
    counts = scan_text_for_pii(text)
    assert counts.get("LGPD_CPF", 0) >= 1
    assert counts.get("EMAIL", 0) >= 1
    assert secret_cpf not in str(counts)
    assert secret_email not in str(counts)


def test_log_audit_trail_finding_logs_counts_only(caplog) -> None:
    caplog.set_level("WARNING")
    secret = "529.982.247-25"
    log_audit_trail_finding({"LGPD_CPF": 2, "EMAIL": 1})
    joined = " ".join(r.message for r in caplog.records)
    assert "AuditTrailFinding" in joined
    assert "LGPD_CPF:2" in joined
    assert "EMAIL:1" in joined
    assert secret not in joined


def _setup_logs_client(tmp_path: Path, log_text: str):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "audit_20260911.log").write_text(log_text, encoding="utf-8")
    config = {
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
        "licensing": {"effective_tier": "community"},
    }
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


def _teardown(routes, previous) -> None:
    prev_path, prev_cfg, prev_engine = previous
    if routes._audit_engine is not None:
        routes._audit_engine.db_manager.dispose()
    routes._config_path = prev_path
    routes._config = prev_cfg
    routes._audit_engine = prev_engine
    configure_audit_log_directory(None)


def test_logs_export_serves_clean_audit_log(tmp_path: Path) -> None:
    routes, client, previous = _setup_logs_client(
        tmp_path, "session=deadbeefcafe\nFinding: demo\n"
    )
    try:
        resp = client.get("/logs")
        assert resp.status_code == 200
        assert b"deadbeefcafe" in resp.content
    finally:
        _teardown(routes, previous)


def test_logs_export_blocks_contaminated_audit_log_without_cleartext_body(
    tmp_path: Path,
) -> None:
    secret_cpf = "529.982.247-25"
    secret_email = "leak-test@example.com"
    contaminated = f"session=abc\nDEBUG leak {secret_cpf} {secret_email}\n"
    routes, client, previous = _setup_logs_client(tmp_path, contaminated)
    try:
        resp = client.get("/logs")
        assert resp.status_code == 422
        body = resp.json()
        detail = body.get("detail") or {}
        assert detail.get("error") == "audit_log_pii_self_scan_blocked"
        assert detail.get("categories", {}).get("LGPD_CPF", 0) >= 1
        assert detail.get("categories", {}).get("EMAIL", 0) >= 1
        raw = resp.text
        assert secret_cpf not in raw
        assert secret_email not in raw
    finally:
        _teardown(routes, previous)

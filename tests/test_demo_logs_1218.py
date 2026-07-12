"""Regression test for issue #1218 (demo audit trail lookup on /logs/{session_id})."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from core.demo.runtime import prepare_demo_workspace
from utils.logger import configure_audit_log_directory


def _setup_client_with_config(config_path: Path):
    import api.routes as routes

    prev_path = routes._config_path
    prev_cfg = routes._config
    prev_engine = routes._audit_engine
    routes._config_path = str(config_path)
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


def test_demo_session_log_is_downloadable_via_logs_endpoint(tmp_path: Path):
    """
    --demo sessions must be retrievable by session_id on /logs/{session_id}.

    Regression target: demo audit logs are stored in the demo workspace, while
    /logs historically searched only by session_id substring and missed files
    when the logger did not embed session IDs in each line.
    """
    demo_root = tmp_path / "demo_workspace"
    demo_dir, config_path, config = prepare_demo_workspace(
        port=18088,
        demo_root=demo_root,
        register_cleanup=False,
    )
    try:
        api_cfg = config.setdefault("api", {})
        api_cfg["api_key"] = "demo-secret"
        api_cfg["rbac"] = {"api_key_roles": ["audit_logs.read"]}
        config_path.write_text(
            yaml.safe_dump(config, sort_keys=False),
            encoding="utf-8",
        )

        routes, client, previous = _setup_client_with_config(config_path)
        try:
            engine = routes._get_engine()
            session_id = engine.start_audit()
            engine.generate_final_reports(session_id)

            logs_dir = Path(routes._get_config()["api"]["audit_logs"]["directory"])
            candidates = sorted(logs_dir.glob("audit_*.log"))
            assert candidates, (
                "demo scan should generate audit_*.log in demo audit_logs dir"
            )
            latest = candidates[-1]
            latest_text = latest.read_text(encoding="utf-8", errors="ignore")
            assert session_id not in latest_text, (
                "regression contract: fallback must work even when session_id is absent in log body"
            )

            resp = client.get(
                f"/logs/{session_id}",
                headers={"X-API-Key": "demo-secret"},
            )
            assert resp.status_code == 200
            assert resp.headers.get("content-type", "").startswith("text/plain")
            assert "Finding:" in resp.text or "Connected:" in resp.text
        finally:
            _teardown(routes, previous)
    finally:
        shutil.rmtree(demo_dir, ignore_errors=True)

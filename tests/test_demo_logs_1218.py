"""Regression tests for demo audit trail /logs (#1218 path + #1190 RBAC align)."""

from __future__ import annotations

import shutil
from pathlib import Path

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


def test_demo_workspace_has_no_api_key(tmp_path: Path):
    """#1190: --demo must not provision api.api_key / RBAC roles (OPEN loopback)."""
    demo_root = tmp_path / "demo_workspace"
    demo_dir, config_path, config = prepare_demo_workspace(
        port=18088,
        demo_root=demo_root,
        register_cleanup=False,
    )
    try:
        api_cfg = config["api"]
        assert not (api_cfg.get("api_key") or "").strip()
        assert not (api_cfg.get("rbac") or {}).get("enabled")
        yaml_text = config_path.read_text(encoding="utf-8")
        assert "api_key:" not in yaml_text
        assert "api_key_roles:" not in yaml_text
        assert api_cfg.get("audit_logs", {}).get("enabled") is True
    finally:
        shutil.rmtree(demo_dir, ignore_errors=True)


def test_demo_session_log_downloadable_without_api_key(tmp_path: Path):
    """
    --demo sessions must be retrievable by session_id on /logs/{session_id}.

    #1218: path alignment (writer/reader same demo audit_logs dir).
    #1190: without RBAC active, no principal required (same as /findings).
    """
    demo_root = tmp_path / "demo_workspace"
    demo_dir, config_path, _config = prepare_demo_workspace(
        port=18088,
        demo_root=demo_root,
        register_cleanup=False,
    )
    try:
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

            resp = client.get(f"/logs/{session_id}")
            assert resp.status_code == 200
            assert resp.headers.get("content-type", "").startswith("text/plain")
            assert "Finding:" in resp.text or "Connected:" in resp.text
        finally:
            _teardown(routes, previous)
    finally:
        shutil.rmtree(demo_dir, ignore_errors=True)


def test_print_demo_banner_has_no_secret(capsys) -> None:
    """Banner shows workspace/URL only — no API key or curl secret."""
    from core.demo.runtime import print_demo_banner

    print_demo_banner(8088, Path("/tmp/data_boar_demo"))
    out = capsys.readouterr().out
    assert "Dashboard:" in out
    assert "Workspace:" in out
    assert "X-API-Key" not in out
    assert "api_key" not in out.lower()
    assert not any(
        len(tok) == 64 and all(c in "0123456789abcdef" for c in tok)
        for tok in out.split()
    )

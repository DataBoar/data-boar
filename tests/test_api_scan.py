"""
Test that the web API POST /scan (Start scan) triggers a full audit using the config's targets.
Ensures the dashboard Start scan button flow runs the audit engine with the current config.
"""

from fastapi.testclient import TestClient


def test_post_scan_triggers_audit_using_config(tmp_path):
    """
    POST /scan must start a background audit that uses targets from the config file.
    With a minimal config (targets: []), the scan completes immediately; we assert
    the session is created and appears in /list.
    """
    out_dir = str(tmp_path).replace("\\", "/")
    config_yaml = f"""targets: []
file_scan:
  extensions: [.txt, .csv]
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
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    # Patch the API module to use our temp config and DB path in normalized config
    import api.routes as routes

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None

        app = routes.app
        client = TestClient(app)

        # Start scan (same as dashboard "Start scan" button: POST /scan)
        resp = client.post("/scan", json={})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("status") == "started"
        session_id = data.get("session_id")
        assert session_id is not None and len(session_id) > 0

        # TestClient runs background tasks after response; session should be created and scan done
        list_resp = client.get("/list")
        assert list_resp.status_code == 200
        sessions = list_resp.json().get("sessions", [])
        assert any(s.get("session_id") == session_id for s in sessions), (
            f"Expected session {session_id} in {[s.get('session_id') for s in sessions]}"
        )

        # Status should be idle after scan completes (background task ran)
        status_resp = client.get("/status")
        assert status_resp.status_code == 200
        body = status_resp.json()
        assert body.get("running") is False
        audit = body.get("audit_log") or {}
        assert audit.get("strategy") == "sampling"
        assert audit.get("sampling_row_cap_per_column") == 2
        assert audit.get("nolock") is False
        runtime_trust = body.get("runtime_trust") or {}
        assert runtime_trust.get("trust_state") in {"trusted", "degraded", "untrusted"}
        dt = status_resp.json().get("dashboard_transport") or {}
        assert dt.get("mode") == "not_configured"
    finally:
        routes._config_path = original_config_path
        routes._config = original_config
        routes._audit_engine = original_engine


def test_post_scan_and_scan_database_409_when_slot_claimed(tmp_path):
    """Request-time compare-and-set: overlapping starts get 409 before background work (#415)."""
    out_dir = str(tmp_path).replace("\\", "/")
    config_yaml = f"""targets: []
file_scan:
  extensions: [.txt]
  recursive: true
  sample_limit: 2
report:
  output_dir: {out_dir}
api:
  port: 8088
  allow_adhoc_targets: true
sqlite_path: {out_dir}/audit_results.db
scan:
  max_workers: 1
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None

        client = TestClient(routes.app)
        engine = routes._get_engine()
        assert engine.try_claim_running() is True
        try:
            scan_resp = client.post("/scan", json={})
            assert scan_resp.status_code == 409, scan_resp.text
            assert scan_resp.json().get("detail") == "Audit already in progress."

            db_resp = client.post(
                "/scan_database",
                json={
                    "name": "lab",
                    "host": "127.0.0.1",
                    "port": 5432,
                    "user": "u",
                    "password": "p",
                    "database": "d",
                },
            )
            assert db_resp.status_code == 409, db_resp.text
            assert db_resp.json().get("detail") == "Audit already in progress."
        finally:
            engine.clear_running()
    finally:
        routes._config_path = original_config_path
        routes._config = original_config
        routes._audit_engine = original_engine

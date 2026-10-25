"""Tests for rate limiting on scan-triggering API endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient


def _setup_routes(tmp_path: Path, extra_config: str = ""):
    """Helper to point api.routes at a temp config.yaml."""
    out_dir = str(tmp_path).replace("\\", "/")
    base_yaml = f"""targets: []
report:
  output_dir: {out_dir}
api:
  port: 8088
sqlite_path: {out_dir}/audit_results.db
scan:
  max_workers: 1
"""
    config_yaml = base_yaml + extra_config
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    routes._config_path = str(config_path)
    routes._config = None
    routes._audit_engine = None
    app = routes.app
    client = TestClient(app)
    return routes, client, original_config_path, original_config, original_engine


def _teardown_routes(routes, original_config_path, original_config, original_engine):
    routes._config_path = original_config_path
    routes._config = original_config
    routes._audit_engine = original_engine


def test_rate_limit_blocks_when_max_concurrent_reached(tmp_path):
    """When rate_limit.enabled and running sessions >= max_concurrent_scans, POST /scan returns 429."""
    extra = """rate_limit:
  enabled: true
  max_concurrent_scans: 1
  min_interval_seconds: 0
"""
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(tmp_path, extra)
    try:
        # Create a running session directly in the DB
        engine = routes._get_engine()
        mgr = engine.db_manager
        mgr.set_current_session_id("running-session")
        mgr.create_session_record("running-session")

        resp = client.post("/scan", json={})
        assert resp.status_code == 429
        data = resp.json()
        # detail may be a dict when rate-limited
        detail = data.get("detail")
        assert detail
        if isinstance(detail, dict):
            assert detail.get("error") == "rate_limited"
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_rate_limit_blocks_when_min_interval_not_elapsed(tmp_path):
    """When min_interval_seconds > 0 and the last session started very recently, POST /scan returns 429."""
    extra = """rate_limit:
  enabled: true
  max_concurrent_scans: 5
  min_interval_seconds: 3600
"""
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(tmp_path, extra)
    try:
        # Start one scan to create a recent session
        resp = client.post("/scan", json={})
        assert resp.status_code == 200

        # Second scan should be rejected due to min_interval_seconds
        resp2 = client.post("/scan", json={})
        assert resp2.status_code == 429
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_rate_limit_disabled_by_default_for_legacy_configs(tmp_path):
    """
    When rate_limit section is not present, behaviour should remain compatible:
    POST /scan still starts a scan (no explicit 429 from rate limiting).
    """
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(tmp_path)
    try:
        resp = client.post("/scan", json={})
        assert resp.status_code == 200
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)

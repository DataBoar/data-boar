"""
Tests for optional API key: when api.require_api_key is true, requests must provide
X-API-Key or Authorization: Bearer <key>; /health is always allowed without key.
"""

from fastapi.testclient import TestClient


def test_health_allowed_without_key_when_api_key_required(tmp_path):
    """GET /health must return 200 without API key even when require_api_key is true."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
  api_key: "secret123"
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_required_api_key_rejects_missing_key(tmp_path):
    """When require_api_key true, GET /status without key returns 401."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
  api_key: "secret123"
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status")
        assert resp.status_code == 401
        assert "detail" in resp.json()
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_required_api_key_accepts_x_api_key_header(tmp_path):
    """When require_api_key true, GET /status with X-API-Key returns 200."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
  api_key: "secret123"
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status", headers={"X-API-Key": "secret123"})
        assert resp.status_code == 200
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_required_api_key_accepts_bearer(tmp_path):
    """When require_api_key true, GET /status with Authorization: Bearer <key> returns 200."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
  api_key: "secret123"
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status", headers={"Authorization": "Bearer secret123"})
        assert resp.status_code == 200
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_required_api_key_rejects_wrong_key(tmp_path):
    """When require_api_key true, wrong key returns 401."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
  api_key: "secret123"
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_api_works_without_key_when_require_api_key_false(tmp_path):
    """When require_api_key is false/unset, /status works without any key (existing behaviour)."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status")
        assert resp.status_code == 200
        body = resp.json()
        assert "enterprise_surface" in body
        assert body["enterprise_surface"]["access_surface"]["rbac"] == "not_implemented"
        assert body["trust_state"] in ("trusted", "degraded", "untrusted")
        assert isinstance(body["trust_reasons"], list)
        assert body["output_confidence"] in ("full", "reduced", "minimal")
        health = client.get("/health")
        assert health.status_code == 200
        hbody = health.json()
        assert hbody["trust_state"] == body["trust_state"]
        assert "dashboard_transport" in hbody
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_require_api_key_without_configured_key_returns_503(tmp_path):
    """Misconfiguration: require_api_key true but no literal or env-backed key -> 503 on /status."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status")
        assert resp.status_code == 503
        assert "detail" in resp.json()
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_health_allowed_without_key_when_require_misconfigured(tmp_path):
    """GET /health stays 200 even when require_api_key is true but no key is configured."""
    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_required_api_key_accepts_x_api_key_when_key_from_env(tmp_path, monkeypatch):
    """api_key_from_env resolves at load_config time; X-API-Key must work."""
    monkeypatch.setenv("AUDIT_API_KEY", "fromenv-secret")

    config_yaml = f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
  require_api_key: true
  api_key_from_env: "AUDIT_API_KEY"
sqlite_path: {tmp_path}/audit.db
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        client = TestClient(routes.app)
        resp = client.get("/status", headers={"X-API-Key": "fromenv-secret"})
        assert resp.status_code == 200
        assert client.get("/status").status_code == 401
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_main_py_web_exits_when_require_api_key_unconfigured(tmp_path):
    """CLI --web refuses to start if require_api_key is true but no key is configured."""
    import subprocess
    import sys
    from pathlib import Path

    cfg = tmp_path / "nokey.yaml"
    db = tmp_path / "n.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
api:
  port: 8091
  require_api_key: true
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--web",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=30,
    )
    assert r.returncode == 2, r.stderr
    assert "require_api_key" in r.stderr or "API key" in r.stderr

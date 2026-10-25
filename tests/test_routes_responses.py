"""
Tests that validate SonarQube-related API contract: documented HTTP status codes
(400 for invalid session_id, 404 for missing resources, 429 for rate limit) and
that the OpenAPI schema declares these responses so they stay documented.
"""

from pathlib import Path

from fastapi.testclient import TestClient


def _minimal_config(tmp_path: Path) -> Path:
    """Write a minimal config and return its path."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
sqlite_path: {tmp_path}/audit.db
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    return config_path


def _client_with_config(tmp_path: Path):
    """Return (routes_module, TestClient) with routes pointed at tmp_path config. Caller must teardown."""
    import api.routes as routes

    config_path = _minimal_config(tmp_path)
    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    routes._config_path = str(config_path)
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app)
    return routes, client, (orig_path, orig_cfg, orig_engine)


def _teardown(routes, orig_path, orig_cfg, orig_engine):
    routes._config_path = orig_path
    routes._config = orig_cfg
    routes._audit_engine = orig_engine


# --- Invalid session_id must return 400 (S8415: document 400 in responses) ---


def test_invalid_session_id_empty_returns_400(tmp_path):
    """PATCH /sessions/{session_id} with empty path param or invalid id returns 400."""
    routes, client, orig = _client_with_config(tmp_path)
    try:
        # Path param "" may not be reachable; use invalid format
        r = client.patch("/sessions/ab", json={"tenant": "x"})
        assert r.status_code == 400
        detail = r.json().get("detail", "")
        assert "session_id" in detail.lower() or "invalid" in detail.lower()
    finally:
        _teardown(routes, *orig)


def test_invalid_session_id_too_short_returns_400(tmp_path):
    """Session_id with fewer than 12 chars returns 400."""
    routes, client, orig = _client_with_config(tmp_path)
    try:
        r = client.patch("/sessions/abc1234567", json={"tenant": "x"})
        assert r.status_code == 400
    finally:
        _teardown(routes, *orig)


def test_invalid_session_id_bad_characters_returns_400(tmp_path):
    """Session_id with characters outside alphanumeric/underscore (e.g. hyphen) returns 400."""
    routes, client, orig = _client_with_config(tmp_path)
    try:
        # 12+ chars but hyphen is not in \\w (ASCII) so rejected by _validate_session_id
        r = client.get("/reports/aaaaaaaaaaa-b")
        assert r.status_code == 400
    finally:
        _teardown(routes, *orig)


def test_invalid_session_id_returns_400_for_reports_heatmap_logs(tmp_path):
    """GET /reports/{id}, /heatmap/{id}, /logs/{id} return 400 for invalid session_id."""
    routes, client, orig = _client_with_config(tmp_path)
    try:
        bad_id = "x" * 11  # too short
        for path in ("/reports/", "/heatmap/", "/logs/"):
            r = client.get(f"{path}{bad_id}")
            assert r.status_code == 400, f"{path}{bad_id} returned {r.status_code}"
    finally:
        _teardown(routes, *orig)


# --- OpenAPI schema must document 429, 400, 404 (prevent S8415 regression) ---


def test_openapi_documents_429_for_scan_endpoints():
    """POST /scan, /start, and POST /scan_database declare 429 in responses."""
    from api.routes import app

    schema = app.openapi()
    paths = schema.get("paths", {})
    for path_key, method in [
        ("/scan", "post"),
        ("/start", "post"),
        ("/scan_database", "post"),
    ]:
        path_item = paths.get(path_key)
        assert path_item is not None, f"Path {path_key} not in OpenAPI"
        op = path_item.get(method)
        assert op is not None, f"{method.upper()} {path_key} not in OpenAPI"
        responses = op.get("responses", {})
        assert "429" in responses, (
            f"429 must be documented for {method.upper()} {path_key} (SonarQube S8415)"
        )


def test_openapi_documents_400_and_404_for_session_endpoints():
    """Endpoints that take session_id declare 400 and 404 in responses."""
    from api.routes import app

    schema = app.openapi()
    paths = schema.get("paths", {})
    session_endpoints = [
        ("/sessions/{session_id}", "patch"),
        ("/sessions/{session_id}/technician", "patch"),
        ("/reports/{session_id}", "get"),
        ("/heatmap/{session_id}", "get"),
        ("/logs/{session_id}", "get"),
    ]
    for path_key, method in session_endpoints:
        path_item = paths.get(path_key)
        assert path_item is not None, f"Path {path_key} not in OpenAPI"
        op = path_item.get(method)
        assert op is not None, f"{method.upper()} {path_key} not in OpenAPI"
        responses = op.get("responses", {})
        assert "400" in responses, (
            f"400 must be documented for {method.upper()} {path_key}"
        )
        assert "404" in responses, (
            f"404 must be documented for {method.upper()} {path_key}"
        )


def test_openapi_documents_404_for_report_heatmap_logs():
    """GET /report, GET /heatmap, GET /logs declare 404 in responses."""
    from api.routes import app

    schema = app.openapi()
    paths = schema.get("paths", {})
    for path_key in ("/report", "/heatmap", "/logs"):
        path_item = paths.get(path_key)
        assert path_item is not None, f"Path {path_key} not in OpenAPI"
        op = path_item.get("get")
        assert op is not None, f"GET {path_key} not in OpenAPI"
        responses = op.get("responses", {})
        assert "404" in responses, f"404 must be documented for GET {path_key}"


# --- Config page uses template constant (avoid duplicate literal) ---


def test_config_page_returns_200_and_uses_config_template(tmp_path):
    """GET /config returns 200 and renders the config template (validates _TEMPLATE_CONFIG in use)."""
    routes, client, orig = _client_with_config(tmp_path)
    try:
        r = client.get("/config")
        assert r.status_code == 200
        # Response body should contain config-related content (template was used)
        assert "config" in r.text.lower() or "yaml" in r.text.lower()
    finally:
        _teardown(routes, *orig)


# --- Session_id validation accepts valid format (no regression) ---


def test_valid_session_id_format_accepted_for_patch(tmp_path):
    """A session_id that matches pattern but does not exist returns 404, not 400."""
    routes, client, orig = _client_with_config(tmp_path)
    try:
        # 12+ alphanumeric/underscore: valid format, session won't exist
        valid_format_id = "a1b2c3d4e5f6_20250101"
        r = client.patch(f"/sessions/{valid_format_id}", json={"tenant": "x"})
        assert r.status_code == 404
        assert "not found" in r.json().get("detail", "").lower()
    finally:
        _teardown(routes, *orig)

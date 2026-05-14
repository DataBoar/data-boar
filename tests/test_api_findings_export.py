"""
Tests for the findings export endpoints (unified JSON + CSV).

Endpoints under test:
  GET /findings              → latest session findings as JSON
  GET /findings/csv          → latest session findings as CSV download
  GET /findings/{session_id} → specific session findings as JSON
  GET /findings/{session_id}/csv → specific session findings as CSV download

The tests use the ``api.routes`` TestClient pattern established in
``tests/test_api_scan.py`` with a minimal config + tmp SQLite DB.
Phase 1 identity fields (``source_mtime_ns``, ``source_size``,
``content_fingerprint``) must appear in the response (Phase 1, ADR-0051).
"""

import csv
import io

from fastapi.testclient import TestClient


def _make_config_and_client(tmp_path, targets=None):
    """Create a minimal config.yaml and return a TestClient + engine reset context."""
    import api.routes as routes

    out_dir = str(tmp_path).replace("\\", "/")
    config_yaml = f"""targets: {targets or []}
file_scan:
  extensions: [.txt]
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

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    routes._config_path = str(config_path)
    routes._config = None
    routes._audit_engine = None

    app = routes.app
    client = TestClient(app)
    return client, routes, original_config_path, original_config, original_engine


def test_get_findings_no_sessions_returns_404(tmp_path):
    """GET /findings returns 404 when no scans have been run yet."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        resp = client.get("/findings")
        assert resp.status_code == 404
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe


def test_get_findings_csv_no_sessions_returns_404(tmp_path):
    """GET /findings/csv returns 404 when no scans have been run yet."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        resp = client.get("/findings/csv")
        assert resp.status_code == 404
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe


def test_get_findings_after_scan_returns_json(tmp_path):
    """After a scan, GET /findings returns JSON with expected keys and Phase 1 fields."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        scan_resp = client.post("/scan", json={})
        assert scan_resp.status_code == 200
        session_id = scan_resp.json().get("session_id")
        assert session_id

        resp = client.get("/findings")
        assert resp.status_code == 200
        body = resp.json()
        assert "session_id" in body
        assert "count" in body
        assert isinstance(body.get("findings"), list)
        assert body["count"] == len(body["findings"])

        for item in body["findings"]:
            # Unified schema: required keys present
            assert "source_type" in item
            assert item["source_type"] in {"filesystem", "database"}
            assert "sensitivity_level" in item
            assert "pattern_detected" in item
            # Phase 1 identity fields must be present as keys (may be None if no findings)
            assert "source_mtime_ns" in item
            assert "source_size" in item
            assert "content_fingerprint" in item
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe


def test_get_findings_by_session_json(tmp_path):
    """GET /findings/{session_id} returns unified JSON for that session."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        scan_resp = client.post("/scan", json={})
        assert scan_resp.status_code == 200
        session_id = scan_resp.json().get("session_id")

        resp = client.get(f"/findings/{session_id}")
        # May be 200 (findings exist) or 404 (no findings for empty scan).
        # With targets=[] the scan produces no findings → 404.
        assert resp.status_code in {200, 404}
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("session_id") == session_id
            assert isinstance(body.get("findings"), list)
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe


def test_get_findings_csv_content_type(tmp_path):
    """GET /findings/csv (after scan) has text/csv content-type and valid CSV header."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        scan_resp = client.post("/scan", json={})
        assert scan_resp.status_code == 200

        resp = client.get("/findings/csv")
        if resp.status_code == 404:
            return  # Empty scan, acceptable
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")

        reader = csv.DictReader(io.StringIO(resp.text))
        header = reader.fieldnames or []
        # Phase 1 identity fields must be in CSV header
        assert "source_mtime_ns" in header
        assert "source_size" in header
        assert "content_fingerprint" in header
        assert "sensitivity_level" in header
        assert "source_type" in header
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe


def test_get_findings_by_session_csv_content_type(tmp_path):
    """GET /findings/{session_id}/csv has text/csv content-type and valid CSV structure."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        scan_resp = client.post("/scan", json={})
        assert scan_resp.status_code == 200
        session_id = scan_resp.json().get("session_id")

        resp = client.get(f"/findings/{session_id}/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert session_id[:10] in resp.headers.get("content-disposition", "")

        reader = csv.DictReader(io.StringIO(resp.text))
        header = reader.fieldnames or []
        assert "source_mtime_ns" in header
        assert "source_size" in header
        assert "content_fingerprint" in header
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe


def test_get_findings_invalid_session_returns_validation_error(tmp_path):
    """GET /findings/{session_id} with invalid session_id returns 4xx."""
    client, routes, ocp, oc, oe = _make_config_and_client(tmp_path)
    try:
        # A path traversal attempt should be rejected by _validate_session_id
        resp = client.get("/findings/../etc/passwd")
        assert resp.status_code in {400, 404, 422}
    finally:
        routes._config_path = ocp
        routes._config = oc
        routes._audit_engine = oe

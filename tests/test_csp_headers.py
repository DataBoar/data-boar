"""
Basic checks for CSP and security headers on HTML endpoints.

These tests ensure that:
- The security middleware attaches the expected headers.
- CSP no longer allows inline scripts (no 'unsafe-inline' in script-src).
"""

from fastapi.testclient import TestClient


def _make_client():
    import api.routes as routes

    return TestClient(routes.app)


def test_dashboard_has_csp_and_security_headers():
    """GET / should return security headers including a CSP without script-src 'unsafe-inline'."""
    client = _make_client()
    resp = client.get("/")
    assert resp.status_code == 200

    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    # script-src should not include 'unsafe-inline', but style-src may still use it.
    assert "script-src 'self'" in csp
    script_part = csp.split("style-src")[0]
    assert "'unsafe-inline'" not in script_part

    # Other basic security headers are present
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Referrer-Policy" in resp.headers
    assert "Permissions-Policy" in resp.headers


def test_help_page_inherits_csp_and_security_headers():
    """GET /help should also have the same security headers."""
    client = _make_client()
    resp = client.get("/help")
    assert resp.status_code == 200

    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    script_part = csp.split("style-src")[0]
    assert "'unsafe-inline'" not in script_part

    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"

"""
Anti-regression tests for the SSRF guard on outbound connector URLs (#832, #1552).

Default posture: reject link-local (cloud metadata), loopback, and private
hosts in base_url / discover_url / token_url / site_url. Each target config
may opt in with ``allow_private_networks: true`` — internal scanning is a
legitimate Data Boar use case, but it must be explicit.

#1552 / #1554: DNS resolution failure is fail-closed; httpx peers are pinned to IPs
validated at guard time (no request-time DNS rebinding). REST uses
``build_pinned_httpx_client`` (PinnedIPTransport); Mongo/SQL use HostResolutionPin.
"""

from __future__ import annotations

import ipaddress
from unittest.mock import MagicMock, patch

import pytest

from connectors.url_guard import (
    OPT_IN_KEY,
    PinnedIPHTTPAdapter,
    PinnedIPTransport,
    resolve_and_validate_outbound_url,
    target_allows_private,
    validate_outbound_url,
)


class _FailureRecorder:
    """Minimal db_manager stub capturing save_failure calls."""

    def __init__(self) -> None:
        self.failures: list[tuple[str, str, str]] = []

    def save_failure(self, name: str, status: str, message: str) -> None:
        self.failures.append((name, status, message))


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://169.254.0.1/",  # link-local
        "http://127.0.0.1:8080/api",  # loopback
        "http://localhost/api",  # loopback via name
        "http://10.0.0.5/api",  # RFC1918
        "http://172.16.1.1/api",  # RFC1918
        "http://192.168.0.10/api",  # RFC1918
        "http://[::1]/api",  # IPv6 loopback
        "http://[fe80::1]/api",  # IPv6 link-local
        "http://[fd00::1]/api",  # IPv6 ULA
        "http://0.0.0.0/api",  # unspecified
    ],
)
def test_guard_rejects_non_global_hosts_by_default(url: str) -> None:
    err = validate_outbound_url(url, allow_private=False, label="base_url")
    assert err is not None, f"Expected rejection for {url!r} (#832)"
    assert "#832" in err and OPT_IN_KEY in err, (
        "Rejection message must reference #832 and the opt-in key for "
        f"actionability, got: {err!r}"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/api",
        "http://localhost:9002/health",
    ],
)
def test_guard_allows_private_hosts_with_opt_in(url: str) -> None:
    assert validate_outbound_url(url, allow_private=True) is None, (
        f"Opt-in must allow {url!r} (#832)"
    )


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file",
        "file:///etc/passwd",
        "gopher://example.com/",
    ],
)
def test_guard_rejects_non_http_schemes(url: str) -> None:
    err = validate_outbound_url(url, allow_private=True)
    assert err is not None and "scheme" in err, (
        f"Expected scheme rejection for {url!r} even with opt-in (#832)"
    )


def test_guard_allows_empty_url() -> None:
    # Empty: nothing to guard (connector handles missing-url errors itself).
    assert validate_outbound_url("") is None


def test_guard_fail_closed_on_unresolvable_dns() -> None:
    # regression-anchor: #1552 — DNS failure must not skip address checks.
    err = validate_outbound_url(
        "https://nonexistent.invalid.example-tld-x/api", label="base_url"
    )
    assert err is not None
    assert "#1552" in err
    assert "DNS" in err or "resolv" in err.lower()


def test_pinned_transport_rejects_host_not_in_pin_map() -> None:
    # regression-anchor: #1552 — no second DNS path for unexpected hosts.
    import httpx

    if not hasattr(httpx, "Client"):
        pytest.skip("httpx not installed")
    transport = PinnedIPTransport({"api.example.com": ["203.0.113.10"]})
    req = httpx.Request("GET", "https://evil.example.com/x")
    with pytest.raises(ValueError, match="#1552"):
        transport.handle_request(req)


def test_pinned_transport_rewrites_url_host_to_pin() -> None:
    # regression-anchor: #1552 — TCP peer is the pre-validated IP.
    import httpx

    inner = MagicMock()
    inner.handle_request.return_value = httpx.Response(200, text="ok")
    transport = PinnedIPTransport({"api.example.com": ["203.0.113.10"]})
    transport._inner = inner
    req = httpx.Request("GET", "https://api.example.com/v1")
    transport.handle_request(req)
    pinned_req = inner.handle_request.call_args.args[0]
    assert pinned_req.url.host == "203.0.113.10"
    assert pinned_req.headers.get("host") == "api.example.com"
    assert pinned_req.extensions.get("sni_hostname") == "api.example.com"


def test_pinned_requests_adapter_rejects_host_not_in_pin_map() -> None:
    # regression-anchor: #1565 — requests path has no second DNS for unexpected hosts.
    import requests
    from requests.adapters import HTTPAdapter

    adapter = PinnedIPHTTPAdapter({"api.example.com": ["203.0.113.10"]})
    req = requests.Request("GET", "https://evil.example.com/x").prepare()
    with (
        pytest.raises(ValueError, match="#1552"),
        patch.object(HTTPAdapter, "send") as mock_send,
    ):
        adapter.send(req)
    mock_send.assert_not_called()


def test_pinned_requests_adapter_rewrites_url_host_to_pin() -> None:
    # regression-anchor: #1565 — TCP peer is the pre-validated IP; Host/SNI preserved.
    import requests
    from requests.adapters import HTTPAdapter

    adapter = PinnedIPHTTPAdapter({"api.example.com": ["203.0.113.10"]})
    req = requests.Request("GET", "https://api.example.com/v1").prepare()
    fake_response = MagicMock()
    with patch.object(HTTPAdapter, "send", return_value=fake_response) as mock_send:
        out = adapter.send(req)
    assert out is fake_response
    sent_req = mock_send.call_args.args[0]
    assert "203.0.113.10" in sent_req.url
    assert "api.example.com" not in urlparse_host(sent_req.url)
    assert sent_req.headers.get("Host") == "api.example.com"


def urlparse_host(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""


def test_resolve_and_validate_returns_pins_for_literal_global_ip() -> None:
    # 1.1.1.1 is global; TEST-NET 203.0.113.0/24 is is_private in Python ipaddress.
    err, ips = resolve_and_validate_outbound_url(
        "https://1.1.1.1/api", allow_private=False, label="base_url"
    )
    assert err is None
    assert [str(i) for i in ips] == ["1.1.1.1"]


def test_build_pinned_httpx_client_forwards_verify_to_transport() -> None:
    # regression-anchor: #1552 / Bugbot — custom transport must receive verify.
    import httpx

    from connectors.url_guard import build_pinned_httpx_client

    captured: dict = {}

    class _CapturingTransport(httpx.HTTPTransport):
        def __init__(self, **kwargs):
            captured.update(kwargs)
            super().__init__(**kwargs)

    with patch("httpx.HTTPTransport", _CapturingTransport):
        client = build_pinned_httpx_client(
            host_to_ips={"example.com": ["93.184.216.34"]},
            verify=False,
        )
        client.close()
    assert captured.get("verify") is False


def test_target_allows_private_reads_config_flag() -> None:
    assert target_allows_private({OPT_IN_KEY: True}) is True
    assert target_allows_private({OPT_IN_KEY: False}) is False
    assert target_allows_private({}) is False


def test_rest_connector_connect_passes_guard_pins_to_httpx_client() -> None:
    """#1554: REST must pin httpx peers to guard-validated IPs (no rebind TOCTOU).

    TCP connectors use HostResolutionPin; REST/httpx uses build_pinned_httpx_client
    (PinnedIPTransport) — same threat class, HTTP-appropriate mechanism (#1552).
    """
    from connectors.rest_connector import _HTTPX_AVAILABLE, RESTConnector

    if not _HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")

    fake_client = MagicMock()
    fake_client.headers = {}
    captured: dict = {}

    def _fake_build(*, host_to_ips, **kwargs):
        captured["host_to_ips"] = host_to_ips
        captured["kwargs"] = kwargs
        return fake_client

    with (
        patch(
            "connectors.rest_connector.resolve_and_validate_outbound_url",
            return_value=(None, [ipaddress.ip_address("203.0.113.10")]),
        ),
        patch(
            "connectors.rest_connector.build_pinned_httpx_client",
            side_effect=_fake_build,
        ),
    ):
        conn = RESTConnector(
            {
                "name": "pin-probe",
                "base_url": "https://api.example.com",
                "paths": ["/x"],
            },
            scanner=None,
            db_manager=_FailureRecorder(),
        )
        conn.connect()

    pins = captured.get("host_to_ips") or {}
    # Dict lookup (not substring-in-URL) — avoids CodeQL py/incomplete-url-substring-sanitization FP.
    pin_host = "api.example.com"
    assert pins.get(pin_host) == ["203.0.113.10"]
    assert captured.get("kwargs", {}).get("base_url") == f"https://{pin_host}"


def test_rest_connector_source_requires_pinned_httpx_client() -> None:
    """#1554 anti-regression: REST must keep the httpx pin constructor."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "connectors" / "rest_connector.py"
    ).read_text(encoding="utf-8")
    assert "build_pinned_httpx_client(" in source
    assert "merge_host_pins(" in source
    assert "resolve_and_validate_outbound_url(" in source


def test_rest_connector_rejects_metadata_base_url() -> None:
    """RESTConnector.run() must save_failure and never request on a guarded URL."""
    from connectors.rest_connector import _HTTPX_AVAILABLE, RESTConnector

    if not _HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")
    db = _FailureRecorder()
    conn = RESTConnector(
        {
            "name": "ssrf-probe",
            "base_url": "http://169.254.169.254/latest",
            "paths": ["/meta-data"],
        },
        scanner=None,
        db_manager=db,
    )
    conn.run()
    assert db.failures, "Expected save_failure for guarded base_url (#832)"
    assert "#832" in db.failures[0][2]


def test_rest_connector_allows_private_with_opt_in() -> None:
    """With opt-in, connect() must pass the guard (no ValueError)."""
    from connectors.rest_connector import _HTTPX_AVAILABLE, RESTConnector

    if not _HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")
    conn = RESTConnector(
        {
            "name": "lab-api",
            "base_url": "http://127.0.0.1:9999",
            "paths": ["/x"],
            OPT_IN_KEY: True,
        },
        scanner=None,
        db_manager=_FailureRecorder(),
    )
    conn.connect()  # must not raise the guard ValueError
    conn.close()


def test_rest_connector_guards_discover_and_token_url() -> None:
    """discover_url and auth.token_url go through the same guard (#832)."""
    from connectors.rest_connector import _HTTPX_AVAILABLE, RESTConnector

    if not _HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")
    for cfg in (
        {
            "name": "d",
            "base_url": "https://example.com",
            "discover_url": "http://192.168.0.1/paths",
        },
        {
            "name": "t",
            "base_url": "https://example.com",
            "auth": {"type": "oauth2_client", "token_url": "http://10.1.1.1/token"},
        },
    ):
        conn = RESTConnector(cfg, scanner=None, db_manager=_FailureRecorder())
        with pytest.raises(ValueError, match="#832"):
            conn.connect()


def test_webdav_connector_rejects_private_base_url() -> None:
    from connectors.webdav_connector import _WEBDAV_AVAILABLE, WebDAVConnector

    if not _WEBDAV_AVAILABLE:
        pytest.skip("webdavclient3 not installed (guard covered by source test)")
    db = _FailureRecorder()
    conn = WebDAVConnector(
        {"name": "dav", "base_url": "http://192.168.1.50/dav"},
        scanner=None,
        db_manager=db,
    )
    conn.run()
    assert db.failures and "#832" in db.failures[-1][2], (
        "WebDAV must save_failure on guarded base_url (#832)"
    )


def test_sharepoint_connector_rejects_private_site_url() -> None:
    from connectors.sharepoint_connector import (
        _REQUESTS_NTLM_AVAILABLE,
        SharePointConnector,
    )

    if not _REQUESTS_NTLM_AVAILABLE:
        pytest.skip("requests_ntlm not installed (guard covered by source test)")
    db = _FailureRecorder()
    conn = SharePointConnector(
        {"name": "sp", "site_url": "http://10.2.3.4/sites/x"},
        scanner=None,
        db_manager=db,
    )
    conn.run()
    failures = [f for f in db.failures if "#832" in f[2]]
    assert failures, (
        f"SharePoint must save_failure on guarded site_url (#832); got: {db.failures}"
    )


@pytest.mark.parametrize(
    "connector_file",
    [
        "connectors/rest_connector.py",
        "connectors/powerbi_connector.py",
        "connectors/hubspot_connector.py",
        "connectors/sharepoint_connector.py",
        "connectors/webdav_connector.py",
        "connectors/dataverse_connector.py",
        "connectors/mongodb_connector.py",
        "connectors/redis_connector.py",
        "connectors/sql_connector.py",
        "core/scan_plan.py",
    ],
)
def test_connector_sources_call_url_guard(connector_file: str) -> None:
    """Dependency-free anti-regression: every outbound HTTP connector must call
    validate_outbound_url (#832) — even when optional deps are absent in CI."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / connector_file).read_text(
        encoding="utf-8"
    )
    has_guard = (
        "validate_outbound_url(" in source
        or "resolve_and_validate_outbound_url(" in source
        or "pinned_httpx_request(" in source
        or "_guard_sql_connection_url(" in source
    )
    assert has_guard, f"{connector_file} lost its SSRF guard call (#832 / #1552)"
    assert "target_allows_private(" in source, (
        f"{connector_file} lost its allow_private_networks opt-in wiring (#832)"
    )


def test_powerbi_token_url_guarded() -> None:
    from connectors.powerbi_connector import _HTTPX_AVAILABLE, _get_access_token

    if not _HTTPX_AVAILABLE:
        pytest.skip("httpx not installed")
    with pytest.raises(ValueError, match="#832"):
        _get_access_token(
            {
                "tenant_id": "t",
                "client_id": "c",
                "client_secret": "s",
                "auth": {"token_url": "http://169.254.169.254/token"},
            }
        )

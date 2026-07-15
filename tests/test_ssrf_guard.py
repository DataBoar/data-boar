"""
Anti-regression tests for the SSRF guard on outbound connector URLs (#832).

Default posture: reject link-local (cloud metadata), loopback, and private
hosts in base_url / discover_url / token_url / site_url. Each target config
may opt in with ``allow_private_networks: true`` — internal scanning is a
legitimate Data Boar use case, but it must be explicit.
"""

from __future__ import annotations

import pytest

from connectors.url_guard import (
    OPT_IN_KEY,
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


def test_guard_allows_empty_and_unresolvable_urls() -> None:
    # Empty: nothing to guard (connector handles missing-url errors itself).
    assert validate_outbound_url("") is None
    # Unresolvable DNS: no availability regression — connection fails later.
    assert (
        validate_outbound_url("https://nonexistent.invalid.example-tld-x/api") is None
    )


def test_target_allows_private_reads_config_flag() -> None:
    assert target_allows_private({OPT_IN_KEY: True}) is True
    assert target_allows_private({OPT_IN_KEY: False}) is False
    assert target_allows_private({}) is False


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
            "base_url": "https://api.example.com",
            "discover_url": "http://192.168.0.1/paths",
        },
        {
            "name": "t",
            "base_url": "https://api.example.com",
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
        "connectors/sharepoint_connector.py",
        "connectors/webdav_connector.py",
        "connectors/dataverse_connector.py",
    ],
)
def test_connector_sources_call_url_guard(connector_file: str) -> None:
    """Dependency-free anti-regression: every outbound HTTP connector must call
    validate_outbound_url (#832) — even when optional deps are absent in CI."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / connector_file).read_text(
        encoding="utf-8"
    )
    assert "validate_outbound_url(" in source, (
        f"{connector_file} lost its SSRF guard call (#832)"
    )
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

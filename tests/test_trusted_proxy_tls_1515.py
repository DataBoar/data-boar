"""Regression: trusted reverse-proxy TLS suppresses false plaintext banner (#1515)."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.dashboard_transport import (
    configure_dashboard_transport,
    effective_dashboard_transport,
    get_dashboard_transport_snapshot,
)

_ENV_KEYS = (
    "DATA_BOAR_DASHBOARD_TRANSPORT",
    "DATA_BOAR_DASHBOARD_INSECURE_OPT_IN",
    "DATA_BOAR_HTTPS_CERT_FILE",
    "DATA_BOAR_HTTPS_KEY_FILE",
)


def _clear_transport_env() -> None:
    for key in _ENV_KEYS:
        os.environ.pop(key, None)


def _request(
    *,
    scheme: str = "http",
    client_host: str = "127.0.0.1",
    forwarded_proto: str | None = None,
):
    headers = {}
    if forwarded_proto is not None:
        headers["x-forwarded-proto"] = forwarded_proto
    return SimpleNamespace(
        headers=headers,
        url=SimpleNamespace(scheme=scheme),
        client=SimpleNamespace(host=client_host),
    )


@pytest.fixture
def http_insecure_transport():
    configure_dashboard_transport(mode="http", insecure_explicit_opt_in=True)
    try:
        yield
    finally:
        _clear_transport_env()


@pytest.fixture
def https_native_transport():
    configure_dashboard_transport(
        mode="https",
        insecure_explicit_opt_in=False,
        cert_path="/tmp/cert.pem",
        key_path="/tmp/key.pem",
    )
    try:
        yield
    finally:
        _clear_transport_env()


def test_direct_http_keeps_insecure_banner(http_insecure_transport):
    cfg = {"api": {}}
    eff = effective_dashboard_transport(_request(), cfg)
    assert eff["show_insecure_banner"] is True
    assert eff["trusted_edge_tls"] is False
    assert eff["effective_external_transport"]["tls_termination"] == "none"


def test_untrusted_forwarded_https_keeps_insecure_banner(http_insecure_transport):
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request(client_host="203.0.113.10", forwarded_proto="https")
    eff = effective_dashboard_transport(req, cfg)
    assert eff["forwarded"]["trusted_proxy_match"] is False
    assert eff["show_insecure_banner"] is True
    assert eff["trusted_edge_tls"] is False


def test_trusted_proxy_without_header_keeps_insecure_banner(http_insecure_transport):
    cfg = {"api": {"trusted_proxy_cidrs": ["127.0.0.1/32"]}}
    eff = effective_dashboard_transport(_request(client_host="127.0.0.1"), cfg)
    assert eff["forwarded"]["trusted_proxy_match"] is True
    assert eff["show_insecure_banner"] is True
    assert eff["trusted_edge_tls"] is False


def test_trusted_proxy_forwarded_http_keeps_insecure_banner(http_insecure_transport):
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request(client_host="10.1.2.3", forwarded_proto="http")
    eff = effective_dashboard_transport(req, cfg)
    assert eff["forwarded"]["forwarded_proto_trusted"] is True
    assert eff["forwarded"]["effective_scheme"] == "http"
    assert eff["show_insecure_banner"] is True
    assert eff["trusted_edge_tls"] is False


def test_trusted_proxy_forwarded_https_suppresses_plaintext_banner(
    http_insecure_transport,
):
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request(client_host="10.1.2.3", forwarded_proto="https")
    eff = effective_dashboard_transport(req, cfg)
    assert eff["trusted_edge_tls"] is True
    assert eff["show_insecure_banner"] is False
    assert eff["show_trusted_proxy_tls_info"] is True
    ext = eff["effective_external_transport"]
    assert ext["scheme"] == "https"
    assert ext["tls_termination"] == "trusted_proxy"
    assert ext["upstream_transport"] == "http"


def test_trusted_proxy_ipv6_forwarded_https_suppresses_banner(http_insecure_transport):
    cfg = {"api": {"trusted_proxy_cidrs": ["fd00::/8"]}}
    req = _request(client_host="fd00::1", forwarded_proto="https")
    eff = effective_dashboard_transport(req, cfg)
    assert eff["trusted_edge_tls"] is True
    assert eff["show_insecure_banner"] is False


def test_native_https_does_not_require_forwarded_header(https_native_transport):
    snap = get_dashboard_transport_snapshot()
    assert snap["tls_active"] is True
    assert snap["show_insecure_banner"] is False
    eff = effective_dashboard_transport(_request(scheme="https"), {"api": {}})
    assert eff["show_insecure_banner"] is False
    assert eff["effective_external_transport"]["tls_termination"] == "native"
    assert eff["show_trusted_proxy_tls_info"] is False


def test_process_snapshot_remains_http_behind_tls_terminating_proxy(
    http_insecure_transport,
):
    cfg = {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    req = _request(client_host="10.1.2.3", forwarded_proto="https")
    eff = effective_dashboard_transport(req, cfg)
    snap = get_dashboard_transport_snapshot()
    assert snap["mode"] == "http"
    assert snap["tls_active"] is False
    assert snap["show_insecure_banner"] is True  # process-level still honest
    assert eff["show_insecure_banner"] is False  # request-scoped suppresses UI
    assert eff["upstream"]["mode"] == "http"


def test_other_governance_banner_is_not_suppressed(http_insecure_transport):
    """Plaintext banner suppression must not clear governance/trust severity UI."""
    from api import routes

    cfg = {
        "api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]},
        "licensing": {},
    }
    req = _request(client_host="10.1.2.3", forwarded_proto="https")

    with (
        patch.object(routes, "_get_config", return_value=cfg),
        patch(
            "api.routes.get_enterprise_surface_posture",
            return_value={
                "severity": "elevated",
                "reasons": ["plaintext_http_explicit", "license_trust_untrusted"],
                "runtime_trust": {"license_state": "untrusted"},
                "access_surface": {"mode": "open_html"},
            },
        ),
    ):
        ctx = routes._template_context({}, req)
    assert ctx["show_insecure_banner"] is False
    assert ctx["show_trusted_proxy_tls_info"] is True
    assert ctx["show_trust_governance_banner"] is True

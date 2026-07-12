"""Tests for trusted-proxy handling of X-Forwarded-Proto."""

from __future__ import annotations

from types import SimpleNamespace

from core.forwarded_headers import forwarded_proto_posture


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


def test_forwarded_proto_ignored_when_no_trusted_proxy_config():
    req = _request(forwarded_proto="https")
    posture = forwarded_proto_posture(req, {"api": {}})
    assert posture["trusted_proxy_configured"] is False
    assert posture["forwarded_proto_trusted"] is False
    assert posture["effective_scheme"] == "http"


def test_forwarded_proto_trusted_when_client_matches_configured_cidr():
    req = _request(forwarded_proto="https", client_host="10.1.2.3")
    posture = forwarded_proto_posture(
        req, {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    )
    assert posture["trusted_proxy_configured"] is True
    assert posture["trusted_proxy_match"] is True
    assert posture["forwarded_proto_trusted"] is True
    assert posture["effective_scheme"] == "https"


def test_forwarded_proto_ignored_when_proxy_not_trusted():
    req = _request(forwarded_proto="https", client_host="203.0.113.10")
    posture = forwarded_proto_posture(
        req, {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}}
    )
    assert posture["trusted_proxy_configured"] is True
    assert posture["trusted_proxy_match"] is False
    assert posture["forwarded_proto_trusted"] is False
    assert posture["effective_scheme"] == "http"

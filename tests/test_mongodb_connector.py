"""MongoDB connector SSRF guard (#1559) and TCP peer pin (#1586)."""

from __future__ import annotations

import importlib.util
import socket
from unittest.mock import MagicMock

import pytest

from connectors.mongodb_connector import MongoDBConnector
from connectors.tcp_pin import HostResolutionPin
from connectors.url_guard import OPT_IN_KEY


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@pytest.mark.skipif(not _has_module("pymongo"), reason="pymongo not installed")
def test_mongodb_connect_rejects_private_host_without_opt_in() -> None:
    conn = MongoDBConnector(
        {"name": "m", "host": "10.0.0.5", "port": 27017},
        scanner=MagicMock(),
        db_manager=MagicMock(),
    )
    with pytest.raises(ValueError, match="#832"):
        conn.connect()


@pytest.mark.skipif(not _has_module("pymongo"), reason="pymongo not installed")
def test_mongodb_connect_allows_private_with_opt_in() -> None:
    conn = MongoDBConnector(
        {
            "name": "m",
            "host": "127.0.0.1",
            "port": 1,
            OPT_IN_KEY: True,
            "connect_timeout_seconds": 1,
            "read_timeout_seconds": 1,
        },
        scanner=MagicMock(),
        db_manager=MagicMock(),
    )
    try:
        conn.connect()
    except ValueError as exc:
        pytest.fail(f"SSRF guard must not reject opted-in private host: {exc}")
    except Exception:
        pass
    finally:
        conn.close()


def test_host_resolution_pin_returns_only_guard_ips() -> None:
    """#1586 — pinned hostname cannot rebind to an unvalidated A record."""
    with HostResolutionPin("db.example.com", ["1.1.1.1"]):
        infos = socket.getaddrinfo("db.example.com", 27017, type=socket.SOCK_STREAM)
        addrs = {info[4][0] for info in infos}
        assert addrs == {"1.1.1.1"}
        # Unrelated hosts still use the real resolver path (literal IP).
        socket.getaddrinfo("1.0.0.1", 80, type=socket.SOCK_STREAM)


def test_host_resolution_pin_noop_for_ip_literal() -> None:
    pin = HostResolutionPin("1.1.1.1", ["1.1.1.1"])
    pin.install()
    try:
        assert pin._key is None
        assert pin._active is False
    finally:
        pin.release()


def test_host_resolution_pin_fails_closed_on_conflicting_active_pins() -> None:
    """#1586 — install must not overwrite a different active pin for the same host."""
    first = HostResolutionPin("shared.example.com", ["1.1.1.1"])
    first.install()
    try:
        second = HostResolutionPin("shared.example.com", ["1.0.0.1"])
        with pytest.raises(ValueError, match="pin conflict|#1586"):
            second.install()
        # Original pin must still be the only peer returned.
        infos = socket.getaddrinfo("shared.example.com", 27017, type=socket.SOCK_STREAM)
        assert {info[4][0] for info in infos} == {"1.1.1.1"}
    finally:
        first.release()


def test_host_resolution_pin_idempotent_same_pins_allowed() -> None:
    """Same pin tuple for the same hostname may install again (no conflict)."""
    a = HostResolutionPin("same.example.com", ["1.1.1.1"])
    b = HostResolutionPin("same.example.com", ["1.1.1.1"])
    a.install()
    try:
        b.install()
        infos = socket.getaddrinfo("same.example.com", 27017, type=socket.SOCK_STREAM)
        assert {info[4][0] for info in infos} == {"1.1.1.1"}
    finally:
        b.release()
        a.release()


def test_host_resolution_pin_allows_new_set_after_release() -> None:
    first = HostResolutionPin("rotate.example.com", ["1.1.1.1"])
    first.install()
    first.release()
    second = HostResolutionPin("rotate.example.com", ["1.0.0.1"])
    second.install()
    try:
        infos = socket.getaddrinfo("rotate.example.com", 27017, type=socket.SOCK_STREAM)
        assert {info[4][0] for info in infos} == {"1.0.0.1"}
    finally:
        second.release()


@pytest.mark.skipif(not _has_module("pymongo"), reason="pymongo not installed")
def test_mongodb_connect_pins_dns_keeps_hostname_in_uri(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — URI keeps hostname (TLS identity); getaddrinfo only returns pin."""
    import ipaddress
    from urllib.parse import urlsplit

    host = "mongo.example.com"

    def fake_resolve(name: str):
        if name == host:
            return [
                ipaddress.ip_address("1.1.1.1"),
                ipaddress.ip_address("2606:4700:4700::1111"),
            ]
        raise OSError(f"unexpected {name}")

    monkeypatch.setattr(
        "connectors.url_guard._resolve_host_ips",
        fake_resolve,
    )

    captured: dict[str, object] = {}

    class FakeMongoClient:
        def __init__(self, uri: str, **kwargs: object) -> None:
            captured["uri"] = uri
            captured["kwargs"] = kwargs
            # While client is "open", pool would call getaddrinfo(hostname).
            infos = socket.getaddrinfo(host, 27017, type=socket.SOCK_STREAM)
            captured["peer_ips"] = {info[4][0] for info in infos}

        def __getitem__(self, name: str) -> MagicMock:
            return MagicMock()

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        "connectors.mongodb_connector.MongoClient",
        FakeMongoClient,
    )

    conn = MongoDBConnector(
        {
            "name": "m",
            "host": host,
            "port": 27017,
            "database": "app",
            "user": "u",
            "pass": "p",
        },
        scanner=MagicMock(),
        db_manager=MagicMock(),
    )
    try:
        conn.connect()
        uri = str(captured["uri"])
        # Authority hostname (not substring) — CodeQL-safe and precise vs pin IP.
        assert urlsplit(uri).hostname == host
        assert captured["peer_ips"] == {"1.1.1.1", "2606:4700:4700::1111"}
    finally:
        conn.close()

    assert conn._dns_pin is None

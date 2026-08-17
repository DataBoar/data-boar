"""Redis connector: WRONGTYPE visibility and sample_limit-derived key classification cap."""

from __future__ import annotations

import importlib.util
import json
from unittest.mock import MagicMock, patch

import pytest

from connectors.redis_connector import (
    REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED,
    RedisConnector,
)
from connectors.url_guard import OPT_IN_KEY


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _mk_scanner():
    scanner = MagicMock()
    scanner.scan_column.return_value = {
        "sensitivity_level": "LOW",
        "pattern_detected": "",
        "norm_tag": "",
        "ml_confidence": 0,
    }
    return scanner


def test_redis_wrongtype_recorded_per_type_not_as_connection_failure():
    if not _has_module("redis"):
        pytest.skip("redis not installed")
    from redis.exceptions import ResponseError

    dbm = MagicMock()
    client = MagicMock()
    client.scan_iter.return_value = iter(["user:1", "session:2"])
    client.get.side_effect = [
        ResponseError(
            "WRONGTYPE Operation against a key holding the wrong kind of value"
        ),
        "plain-string-value",
    ]
    client.type.side_effect = ["hash", "string"]

    conn = RedisConnector(
        {"name": "redis-lab", "host": "127.0.0.1", OPT_IN_KEY: True},
        _mk_scanner(),
        dbm,
        sample_limit=100,
        value_sample_limit=10,
    )
    conn._client = client
    # Bypass connect() — exercise sampling path with the mock client.
    with patch.object(conn, "connect"):
        conn.run()

    unreachable = [
        c for c in dbm.save_failure.call_args_list if c.args[1] == "unreachable"
    ]
    assert not unreachable

    sampled_calls = [
        c
        for c in dbm.save_failure.call_args_list
        if c.args[1] == REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED
    ]
    assert len(sampled_calls) == 1
    payload = json.loads(sampled_calls[0].args[2])
    assert payload["keys_discovered"] == 2
    assert payload["keys_name_classified"] == 2
    assert payload["value_not_sampled_by_type"] == {"hash": 1}
    assert client.get.call_count == 2


def test_redis_per_key_limit_follows_sample_limit():
    if not _has_module("redis"):
        pytest.skip("redis not installed")

    dbm = MagicMock()
    client = MagicMock()
    keys = [f"k{i}" for i in range(120)]
    client.scan_iter.return_value = iter(keys)
    scanner = _mk_scanner()

    conn = RedisConnector(
        {"name": "redis-cap", OPT_IN_KEY: True},
        scanner,
        dbm,
        sample_limit=80,
        value_sample_limit=5,
    )
    conn._client = client
    client.get.return_value = None
    with patch.object(conn, "connect"):
        conn.run()

    assert scanner.scan_column.call_count == 80


def test_redis_connect_rejects_private_host_without_opt_in() -> None:
    # regression-anchor: #1559
    if not _has_module("redis"):
        pytest.skip("redis not installed")
    conn = RedisConnector(
        {"name": "r", "host": "169.254.169.254", "port": 6379},
        scanner=_mk_scanner(),
        db_manager=MagicMock(),
    )
    with pytest.raises(ValueError, match="#832"):
        conn.connect()


def test_redis_connect_allows_private_with_opt_in() -> None:
    # regression-anchor: #1559 — opt-in must pass the guard (may still fail to connect).
    if not _has_module("redis"):
        pytest.skip("redis not installed")
    from connectors.url_guard import OPT_IN_KEY

    conn = RedisConnector(
        {
            "name": "r",
            "host": "127.0.0.1",
            "port": 1,
            OPT_IN_KEY: True,
            "connect_timeout_seconds": 1,
            "read_timeout_seconds": 1,
        },
        scanner=_mk_scanner(),
        db_manager=MagicMock(),
    )
    # Guard must not raise; connection to closed port may raise from redis.
    try:
        conn.connect()
    except ValueError as exc:
        pytest.fail(f"SSRF guard must not reject opted-in private host: {exc}")
    except Exception:
        pass
    finally:
        conn.close()


def test_make_pinned_redis_connection_class_dials_only_pin_ips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — redis connection_class never getaddrinfo(hostname) for TCP peer."""
    if not _has_module("redis"):
        pytest.skip("redis not installed")
    import socket

    from redis.connection import Connection

    from connectors.tcp_pin import make_pinned_redis_connection_class

    host = "redis.example.com"
    seen_connect: list[tuple[str, int]] = []
    real_getaddrinfo = socket.getaddrinfo

    def boom_getaddrinfo(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == host:
            raise AssertionError(
                "pinned class must not resolve hostname via getaddrinfo"
            )
        return real_getaddrinfo(name, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", boom_getaddrinfo)

    class FakeSock:
        def setsockopt(self, *a: object, **k: object) -> None:
            return None

        def settimeout(self, *a: object, **k: object) -> None:
            return None

        def connect(self, address: tuple[object, ...]) -> None:
            seen_connect.append((str(address[0]), int(address[1])))

        def shutdown(self, *a: object, **k: object) -> None:
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr(socket, "socket", lambda *a, **k: FakeSock())

    cls = make_pinned_redis_connection_class(Connection, ["1.1.1.1"])
    conn = cls(host=host, port=6379, socket_connect_timeout=1, socket_timeout=1)
    sock = conn._connect()
    assert sock is not None
    assert seen_connect == [("1.1.1.1", 6379)]
    assert conn.host == host


def test_redis_connect_pins_hostname_keeps_host_for_tls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1586 — pool host stays hostname; connection_class is pin subclass."""
    if not _has_module("redis"):
        pytest.skip("redis not installed")
    import ipaddress

    from redis.connection import Connection, SSLConnection

    host = "redis.example.com"

    def fake_resolve(name: str):
        if name == host:
            return [
                ipaddress.ip_address("1.1.1.1"),
                ipaddress.ip_address("2606:4700:4700::1111"),
            ]
        raise OSError(f"unexpected {name}")

    monkeypatch.setattr("connectors.url_guard._resolve_host_ips", fake_resolve)

    captured: dict[str, object] = {}

    class FakeRedis:
        def __init__(self, *args: object, **kwargs: object) -> None:
            captured["kwargs"] = kwargs
            pool = kwargs.get("connection_pool")
            captured["pool"] = pool

        def close(self) -> None:
            return None

    monkeypatch.setattr("connectors.redis_connector.redis.Redis", FakeRedis)

    conn = RedisConnector(
        {
            "name": "r",
            "host": host,
            "port": 6379,
            "tls": True,
            "ssl_cert_reqs": "required",
            "connect_timeout_seconds": 1,
            "read_timeout_seconds": 1,
        },
        scanner=_mk_scanner(),
        db_manager=MagicMock(),
    )
    conn.connect()
    try:
        pool = captured["pool"]
        assert pool is not None
        assert pool.connection_kwargs["host"] == host  # type: ignore[index]
        assert issubclass(pool.connection_class, SSLConnection)  # type: ignore[union-attr]
        assert pool.connection_class is not SSLConnection  # type: ignore[union-attr]
        assert pool.connection_class is not Connection  # type: ignore[union-attr]
        assert pool.connection_kwargs.get("ssl_cert_reqs") == "required"  # type: ignore[union-attr]
    finally:
        conn.close()

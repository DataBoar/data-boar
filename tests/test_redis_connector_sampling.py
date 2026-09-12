"""Redis connector: TYPE dispatch value sampling (#1348 Part B)."""

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


def _mk_scanner(*, value_hits: bool = False):
    scanner = MagicMock()

    def _scan_column(column: str, content: str) -> dict:
        if value_hits and ":value" in column:
            return {
                "sensitivity_level": "HIGH",
                "pattern_detected": "EMAIL",
                "norm_tag": "LGPD Art. 5",
                "ml_confidence": 0,
            }
        return {
            "sensitivity_level": "LOW",
            "pattern_detected": "",
            "norm_tag": "",
            "ml_confidence": 0,
        }

    scanner.scan_column.side_effect = _scan_column
    return scanner


def _run_with_client(client: MagicMock, scanner: MagicMock, dbm: MagicMock, **kwargs):
    conn = RedisConnector(
        {"name": "redis-lab", "host": "127.0.0.1", OPT_IN_KEY: True},
        scanner,
        dbm,
        sample_limit=kwargs.get("sample_limit", 100),
        value_sample_limit=kwargs.get("value_sample_limit", 10),
    )
    conn._client = client
    with patch.object(conn, "connect"):
        conn.run()
    return conn


def test_redis_unsupported_type_recorded_not_as_connection_failure():
    if not _has_module("redis"):
        pytest.skip("redis not installed")

    dbm = MagicMock()
    client = MagicMock()
    client.scan_iter.return_value = iter(["u:1002", "u:ghost"])
    client.type.side_effect = ["hash", "none"]
    client.hscan.return_value = (
        0,
        {"email": "hash.pii@example.invalid", "cpf": "529.982.247-25"},
    )

    _run_with_client(client, _mk_scanner(value_hits=True), dbm, value_sample_limit=5)

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
    assert payload["value_not_sampled_by_type"] == {"none": 1}
    assert payload["values_sampled"] >= 1
    client.get.assert_not_called()


@pytest.mark.parametrize(
    ("redis_type", "setup_client"),
    [
        (
            "string",
            lambda client: (
                setattr(client, "type", MagicMock(return_value="string")),
                setattr(
                    client,
                    "get",
                    MagicMock(return_value="529.982.247-25 plain@example.invalid"),
                ),
            ),
        ),
        (
            "hash",
            lambda client: (
                setattr(client, "type", MagicMock(return_value="hash")),
                setattr(
                    client,
                    "hscan",
                    MagicMock(
                        return_value=(
                            0,
                            {
                                "email": "hash.pii@example.invalid",
                                "cpf": "529.982.247-25",
                            },
                        )
                    ),
                ),
            ),
        ),
        (
            "list",
            lambda client: (
                setattr(client, "type", MagicMock(return_value="list")),
                setattr(
                    client,
                    "lrange",
                    MagicMock(return_value=["529.982.247-25", "list@example.invalid"]),
                ),
            ),
        ),
        (
            "set",
            lambda client: (
                setattr(client, "type", MagicMock(return_value="set")),
                setattr(
                    client,
                    "sscan",
                    MagicMock(return_value=(0, ["set.member@example.invalid"])),
                ),
            ),
        ),
        (
            "zset",
            lambda client: (
                setattr(client, "type", MagicMock(return_value="zset")),
                setattr(
                    client,
                    "zrange",
                    MagicMock(
                        return_value=["529.982.247-25 zset.member@example.invalid"]
                    ),
                ),
            ),
        ),
        (
            "stream",
            lambda client: (
                setattr(client, "type", MagicMock(return_value="stream")),
                setattr(
                    client,
                    "xrange",
                    MagicMock(
                        return_value=[
                            (
                                "1700000000000-0",
                                {
                                    "email": "stream.pii@example.invalid",
                                    "cpf": "123.456.789-09",
                                },
                            )
                        ]
                    ),
                ),
            ),
        ),
    ],
)
def test_redis_type_dispatch_samples_value_and_finds_pii(redis_type, setup_client):
    if not _has_module("redis"):
        pytest.skip("redis not installed")

    dbm = MagicMock()
    client = MagicMock()
    client.scan_iter.return_value = iter(["u:1001"])
    setup_client(client)

    scanner = _mk_scanner(value_hits=True)
    _run_with_client(client, scanner, dbm, value_sample_limit=5)

    value_scans = [
        c for c in scanner.scan_column.call_args_list if ":value" in c.args[0]
    ]
    assert value_scans
    assert dbm.save_finding.call_count >= 1
    sampled_calls = [
        c
        for c in dbm.save_failure.call_args_list
        if c.args[1] == REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED
    ]
    assert not sampled_calls, f"{redis_type} should not be counted as unsampled"


def test_redis_all_dispatched_types_leave_value_not_sampled_empty():
    if not _has_module("redis"):
        pytest.skip("redis not installed")

    dbm = MagicMock()
    client = MagicMock()
    keys = ["k:string", "k:hash", "k:list", "k:set", "k:zset", "k:stream"]
    client.scan_iter.return_value = iter(keys)

    def _type_side_effect(key: str) -> str:
        return str(key).split(":", 1)[1]

    client.type.side_effect = _type_side_effect
    client.get.return_value = "529.982.247-25"
    client.hscan.return_value = (0, {"cpf": "529.982.247-25"})
    client.lrange.return_value = ["529.982.247-25"]
    client.sscan.return_value = (0, ["529.982.247-25"])
    client.zrange.return_value = ["529.982.247-25"]
    client.xrange.return_value = [("1-0", {"cpf": "529.982.247-25"})]

    scanner = _mk_scanner(value_hits=True)
    _run_with_client(client, scanner, dbm, sample_limit=6, value_sample_limit=6)

    sampled_calls = [
        c
        for c in dbm.save_failure.call_args_list
        if c.args[1] == REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED
    ]
    assert not sampled_calls
    assert dbm.save_finding.call_count == len(keys)


def test_redis_unknown_future_type_still_counted():
    if not _has_module("redis"):
        pytest.skip("redis not installed")

    dbm = MagicMock()
    client = MagicMock()
    client.scan_iter.return_value = iter(["module:key"])
    client.type.return_value = "ReJSON-RL"

    _run_with_client(client, _mk_scanner(), dbm, value_sample_limit=3)

    sampled_calls = [
        c
        for c in dbm.save_failure.call_args_list
        if c.args[1] == REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED
    ]
    assert len(sampled_calls) == 1
    payload = json.loads(sampled_calls[0].args[2])
    assert payload["value_not_sampled_by_type"] == {"ReJSON-RL": 1}


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
    client.type.return_value = "string"
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

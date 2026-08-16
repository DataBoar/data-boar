"""TCP peer pin helpers for DB / NoSQL connectors (#1586).

Closes the validate→connect DNS rebinding window by reusing IPs already
approved by :func:`connectors.url_guard.resolve_and_validate_outbound_url`.

This is **not** an HTTP adapter — each connector applies pins with its own
driver mechanism (libpq ``hostaddr``, redis ``connection_class``,
pymongo via :class:`HostResolutionPin`, etc.).
"""

from __future__ import annotations

import ipaddress
import socket
import threading
from typing import Any

from .url_guard import IpAddr

# pymongo sync pool calls ``socket.getaddrinfo`` on every connect/reconnect
# (#1586). While pins are registered, matching hostnames resolve only to
# guard-validated addresses (hostname string stays in the URI for TLS SNI).
_PIN_LOCK = threading.RLock()
_HOST_PINS: dict[str, tuple[str, ...]] = {}
_ORIG_GETADDRINFO = socket.getaddrinfo
_GETADDRINFO_PATCHED = False


def primary_pin_str(ips: list[IpAddr] | list[str]) -> str:
    """Return the first preferred pin as a canonical IP string.

    Callers pass the ordered list from ``resolve_and_validate_outbound_url``
    (already ``_prefer_pin_order``'d — IPv4 before IPv6).
    """
    if not ips:
        raise ValueError("no pin IPs available for TCP peer pinning (#1586)")
    first = ips[0]
    if isinstance(first, str):
        return str(ipaddress.ip_address(first))
    return str(first)


def format_libpq_hostaddr(ip: IpAddr | str) -> str:
    """Format an address for libpq ``hostaddr`` (no brackets on IPv6)."""
    return str(ipaddress.ip_address(str(ip)))


def normalize_pin_hostname(host: str) -> str:
    """Canonical key for pin maps (lowercase, strip trailing dot)."""
    return (host or "").strip().rstrip(".").lower()


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _synthetic_addrinfo(
    pins: tuple[str, ...],
    port: Any,
    family: int,
    type_: int,
    proto: int,
) -> list[tuple[Any, ...]]:
    """Build ``getaddrinfo``-shaped results for *pins* only."""
    port_i = 0 if port is None else int(port)
    socktype = type_ if type_ else socket.SOCK_STREAM
    out: list[tuple[Any, ...]] = []
    for pin in pins:
        ip = ipaddress.ip_address(pin)
        if family not in (0, socket.AF_UNSPEC):
            if family == socket.AF_INET and ip.version != 4:
                continue
            if family == socket.AF_INET6 and ip.version != 6:
                continue
        if ip.version == 4:
            af = socket.AF_INET
            sockaddr: tuple[Any, ...] = (str(ip), port_i)
        else:
            af = socket.AF_INET6
            sockaddr = (str(ip), port_i, 0, 0)
        out.append((af, socktype, proto or 0, "", sockaddr))
    if not out:
        raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
    return out


def _pinned_getaddrinfo(
    host: Any,
    port: Any,
    family: int = 0,
    type: int = 0,
    proto: int = 0,
    flags: int = 0,
) -> list[tuple[Any, ...]]:
    host_s = host.decode("idna") if isinstance(host, bytes) else str(host)
    key = normalize_pin_hostname(host_s)
    with _PIN_LOCK:
        pins = _HOST_PINS.get(key)
    if pins:
        return _synthetic_addrinfo(pins, port, family, type, proto)
    return _ORIG_GETADDRINFO(host, port, family, type, proto, flags)


def _ensure_getaddrinfo_patched() -> None:
    global _GETADDRINFO_PATCHED
    with _PIN_LOCK:
        if not _GETADDRINFO_PATCHED:
            socket.getaddrinfo = _pinned_getaddrinfo  # type: ignore[assignment]
            _GETADDRINFO_PATCHED = True


def _maybe_unpatch_getaddrinfo() -> None:
    global _GETADDRINFO_PATCHED
    with _PIN_LOCK:
        if _GETADDRINFO_PATCHED and not _HOST_PINS:
            socket.getaddrinfo = _ORIG_GETADDRINFO  # type: ignore[assignment]
            _GETADDRINFO_PATCHED = False


class HostResolutionPin:
    """Pin DNS for one hostname to guard-validated IPs for a client lifetime.

    Used by MongoDB (#1586): pymongo keeps the hostname for TLS
    ``server_hostname`` but resolves TCP peers via ``socket.getaddrinfo``.
    Register before ``MongoClient(...)`` and :meth:`release` on close.
    """

    def __init__(self, hostname: str, pin_ips: list[IpAddr] | list[str]) -> None:
        if not hostname:
            raise ValueError("hostname required for TCP peer pinning (#1586)")
        if _is_ip_literal(hostname.strip().rstrip(".")):
            # Literal peer — no DNS rebinding window; no patch needed.
            self._key: str | None = None
            self._active = False
            return
        if not pin_ips:
            raise ValueError("no pin IPs available for TCP peer pinning (#1586)")
        normalized = tuple(str(ipaddress.ip_address(str(ip))) for ip in pin_ips)
        self._key = normalize_pin_hostname(hostname)
        self._pins = normalized
        self._active = False

    def install(self) -> HostResolutionPin:
        """Register this hostname→IP pin set for the process.

        Fail-closed (#1586 / PR #1591 audit): if another *active* pin already
        holds a **different** IP set for the same hostname, raise instead of
        silently overwriting (concurrent targets / reconnect must not inherit
        another scan's validated peers). Idempotent install of the **same**
        pin tuple is allowed.
        """
        if self._key is None:
            return self
        with _PIN_LOCK:
            existing = _HOST_PINS.get(self._key)
            if existing is not None and existing != self._pins:
                raise ValueError(
                    f"active TCP peer pin conflict for hostname {self._key!r} "
                    "(#1586): another HostResolutionPin already holds a "
                    "different pin set; release it before installing a new one"
                )
            _HOST_PINS[self._key] = self._pins
            self._active = True
        _ensure_getaddrinfo_patched()
        return self

    def release(self) -> None:
        if not self._active or self._key is None:
            return
        with _PIN_LOCK:
            current = _HOST_PINS.get(self._key)
            if current == self._pins:
                _HOST_PINS.pop(self._key, None)
            self._active = False
        _maybe_unpatch_getaddrinfo()

    def __enter__(self) -> HostResolutionPin:
        return self.install()

    def __exit__(self, *exc: object) -> None:
        self.release()

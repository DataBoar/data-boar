"""TCP peer pin helpers for DB / NoSQL connectors (#1586).

Closes the validate→connect DNS rebinding window by reusing IPs already
approved by :func:`connectors.url_guard.resolve_and_validate_outbound_url`.

This is **not** an HTTP adapter — each connector applies pins with its own
driver mechanism (libpq ``hostaddr``, redis ``connection_class``, etc.).
"""

from __future__ import annotations

import ipaddress

from .url_guard import IpAddr


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

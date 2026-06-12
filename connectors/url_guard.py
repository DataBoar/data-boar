"""SSRF guard for outbound connector URLs (#832).

Threat model: operator-supplied (or partner-supplied) target configs steer
HTTP(S) requests from the scanning host. A malicious or mistyped
``base_url`` / ``discover_url`` / ``token_url`` can point the engine at:

- cloud metadata endpoints (``169.254.169.254``, link-local),
- loopback / internal admin services,
- private RFC1918 / ULA ranges the scan host can reach but the config
  author should not target implicitly.

Default posture: **reject non-global addresses** (link-local, loopback,
private, reserved). Scanning internal infrastructure is a legitimate
Data Boar use case, so each target config may opt in explicitly::

    targets:
      - name: internal-api
        type: rest
        base_url: http://10.0.0.5:8080
        allow_private_networks: true   # explicit opt-in (#832)

Shared by: rest_connector, powerbi_connector (token_url),
sharepoint_connector (site_url), webdav_connector (base_url).
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

_ALLOWED_SCHEMES = frozenset(("http", "https"))

# Config key for the per-target opt-in.
OPT_IN_KEY = "allow_private_networks"


def _classify(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str | None:
    """Return a human-readable rejection category for *ip*, or None if global."""
    if ip.is_link_local:
        return "link-local (e.g. cloud metadata 169.254.0.0/16, fe80::/10)"
    if ip.is_loopback:
        return "loopback"
    if ip.is_private:
        return "private (RFC1918 / ULA)"
    if ip.is_unspecified:
        return "unspecified (0.0.0.0 / ::)"
    if ip.is_reserved or ip.is_multicast:
        return "reserved/multicast"
    if not ip.is_global:
        return "non-global"
    return None


def _resolve_host_ips(
    host: str,
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Best-effort resolution of *host* to IP addresses.

    Literal IPs are returned directly. DNS failures return an empty list —
    the connection will fail naturally at request time, so the guard does
    not block on resolver outages (no availability regression).
    """
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except OSError:
        return []
    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for info in infos:
        try:
            ips.append(ipaddress.ip_address(info[4][0]))
        except ValueError:
            continue
    return ips


def validate_outbound_url(
    url: str,
    *,
    allow_private: bool = False,
    label: str = "url",
) -> str | None:
    """Validate *url* against the SSRF allowlist (#832).

    Returns ``None`` when the URL is acceptable, or a human-readable error
    string describing the rejection (scheme not http/https, missing host,
    or host resolving to a non-global address without opt-in).
    """
    if not url:
        return None
    if "://" in url:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in _ALLOWED_SCHEMES:
            return (
                f"{label} rejected: scheme '{scheme}' not allowed "
                f"(only http/https). (#832)"
            )
    else:
        # Bare "host[:port]/path" form (WebDAV configs allow it) — no scheme
        # to enforce, but the host still gets the address checks below.
        parsed = urlparse(f"//{url}")
    host = parsed.hostname
    if not host:
        return f"{label} rejected: no host found in {url!r}. (#832)"
    if allow_private:
        return None
    for ip in _resolve_host_ips(host):
        category = _classify(ip)
        if category:
            return (
                f"{label} rejected: host '{host}' resolves to {ip} "
                f"[{category}]. Scanning internal/private networks requires "
                f"explicit opt-in — add '{OPT_IN_KEY}: true' to this target. (#832)"
            )
    return None


def target_allows_private(target_config: dict[str, Any]) -> bool:
    """Read the per-target opt-in flag (#832)."""
    return bool(target_config.get(OPT_IN_KEY, False))

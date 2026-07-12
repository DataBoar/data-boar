"""
Trusted-proxy handling for forwarded transport headers.

Security posture:
- Ignore X-Forwarded-* headers by default.
- Trust X-Forwarded-Proto only when the direct client IP matches
  api.trusted_proxy_cidrs.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any


def _trusted_proxy_networks(config: dict[str, Any]) -> list[Any]:
    api_cfg = config.get("api") if isinstance(config.get("api"), dict) else {}
    raw = api_cfg.get("trusted_proxy_cidrs")
    if isinstance(raw, str):
        candidates = [raw]
    elif isinstance(raw, list):
        candidates = [str(x) for x in raw]
    else:
        candidates = []
    networks: list[Any] = []
    for item in candidates:
        value = item.strip()
        if not value:
            continue
        try:
            networks.append(ip_network(value, strict=False))
        except ValueError:
            continue
    return networks


def _client_ip_from_request(request: Any):
    client = getattr(request, "client", None)
    host = getattr(client, "host", None) if client is not None else None
    if not host:
        return None
    try:
        return ip_address(str(host))
    except ValueError:
        return None


def forwarded_proto_posture(request: Any, config: dict[str, Any]) -> dict[str, Any]:
    """
    Return trust posture for X-Forwarded-Proto and the effective request scheme.
    """
    networks = _trusted_proxy_networks(config)
    client_ip = _client_ip_from_request(request)
    trusted_proxy_match = bool(
        networks
        and client_ip is not None
        and any(client_ip in network for network in networks)
    )
    raw_header = (request.headers.get("x-forwarded-proto") or "").strip().lower()
    # Proxy chains may send comma-separated values; first entry represents client-facing scheme.
    forwarded_proto = raw_header.split(",", 1)[0].strip() if raw_header else ""
    forwarded_valid = forwarded_proto in {"http", "https"}
    use_forwarded_proto = bool(
        forwarded_proto and forwarded_valid and trusted_proxy_match
    )
    effective_scheme = forwarded_proto if use_forwarded_proto else request.url.scheme
    return {
        "trusted_proxy_configured": bool(networks),
        "trusted_proxy_match": trusted_proxy_match,
        "forwarded_proto_header_present": bool(forwarded_proto),
        "forwarded_proto_header": forwarded_proto or None,
        "forwarded_proto_trusted": use_forwarded_proto,
        "effective_scheme": effective_scheme,
    }

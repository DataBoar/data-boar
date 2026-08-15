"""SSRF guard for outbound connector URLs (#832, #1552).

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

DNS posture (#1552):

- Resolution failure is **fail-closed** (reject the URL) — an empty
  resolve result must not skip address checks.
- httpx clients that use :class:`PinnedIPTransport` connect to the
  IPs validated at guard time (Host / SNI keep the original hostname)
  so a later DNS rebinding cannot steer the TCP peer to a private IP.

Shared by: rest_connector, powerbi_connector (token_url),
sharepoint_connector (site_url), webdav_connector (base_url),
dataverse_connector (org_url / token_url).

#1565: ``PinnedIPHTTPAdapter`` / ``build_pinned_requests_session`` pin
``requests`` peers the same way ``PinnedIPTransport`` pins httpx (SharePoint,
WebDAV).
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse, urlunparse

_ALLOWED_SCHEMES = frozenset(("http", "https"))

# Config key for the per-target opt-in.
OPT_IN_KEY = "allow_private_networks"

IpAddr = ipaddress.IPv4Address | ipaddress.IPv6Address


def _classify(ip: IpAddr) -> str | None:
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


def _prefer_pin_order(ips: list[IpAddr]) -> list[IpAddr]:
    """Prefer IPv4 pins first (simpler URL form / broader NAT paths)."""
    v4 = [i for i in ips if i.version == 4]
    v6 = [i for i in ips if i.version == 6]
    return v4 + v6


def _resolve_host_ips(host: str) -> list[IpAddr]:
    """Resolve *host* to IP addresses.

    Literal IPs are returned directly. DNS / resolver failures raise
    ``OSError`` (callers map that to a fail-closed guard error — #1552).
    """
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass
    infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    ips: list[IpAddr] = []
    seen: set[str] = set()
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        key = str(ip)
        if key not in seen:
            seen.add(key)
            ips.append(ip)
    return ips


def _parse_url_host(url: str) -> tuple[Any, str | None, str | None]:
    """Return (parsed, host, scheme_error)."""
    if "://" in url:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in _ALLOWED_SCHEMES:
            return (
                parsed,
                None,
                (f"scheme '{scheme}' not allowed (only http/https). (#832)"),
            )
    else:
        # Bare "host[:port]/path" form (WebDAV configs allow it) — no scheme
        # to enforce, but the host still gets the address checks below.
        parsed = urlparse(f"//{url}")
    return parsed, parsed.hostname, None


def resolve_and_validate_outbound_url(
    url: str,
    *,
    allow_private: bool = False,
    label: str = "url",
) -> tuple[str | None, list[IpAddr]]:
    """Validate *url* and return ``(error, resolved_ips)``.

    On success ``error`` is ``None`` and ``resolved_ips`` is non-empty
    (except for empty *url*, which returns ``(None, [])``).

    DNS failure or empty resolution → fail-closed error (#1552).
    Non-global addresses without opt-in → rejection (#832).
    """
    if not url:
        return None, []
    parsed, host, scheme_err = _parse_url_host(url)
    if scheme_err:
        return f"{label} rejected: {scheme_err}", []
    if not host:
        return f"{label} rejected: no host found in {url!r}. (#832)", []
    try:
        ips = _resolve_host_ips(host)
    except OSError as exc:
        return (
            f"{label} rejected: DNS resolution failed for host '{host}' "
            f"({exc}). Fail-closed — refusing outbound connect. (#1552)",
            [],
        )
    if not ips:
        return (
            f"{label} rejected: host '{host}' resolved to no addresses. "
            f"Fail-closed — refusing outbound connect. (#1552)",
            [],
        )
    if not allow_private:
        for ip in ips:
            category = _classify(ip)
            if category:
                return (
                    f"{label} rejected: host '{host}' resolves to {ip} "
                    f"[{category}]. Scanning internal/private networks requires "
                    f"explicit opt-in — add '{OPT_IN_KEY}: true' to this target. (#832)",
                    [],
                )
    return None, _prefer_pin_order(ips)


def validate_outbound_url(
    url: str,
    *,
    allow_private: bool = False,
    label: str = "url",
) -> str | None:
    """Validate *url* against the SSRF allowlist (#832 / #1552).

    Returns ``None`` when the URL is acceptable, or a human-readable error
    string describing the rejection.
    """
    err, _ips = resolve_and_validate_outbound_url(
        url, allow_private=allow_private, label=label
    )
    return err


def target_allows_private(target_config: dict[str, Any]) -> bool:
    """Read the per-target opt-in flag (#832)."""
    return bool(target_config.get(OPT_IN_KEY, False))


def host_pins_from_url(url: str, ips: list[IpAddr]) -> dict[str, list[str]]:
    """Build a hostname → pin-IP map entry for *url* (empty if no host)."""
    if not url or not ips:
        return {}
    _parsed, host, _err = _parse_url_host(url)
    if not host:
        return {}
    return {host.lower(): [str(ip) for ip in _prefer_pin_order(ips)]}


def merge_host_pins(pins: dict[str, list[str]], url: str, ips: list[IpAddr]) -> None:
    """Merge pin entries for *url* into *pins* (mutates)."""
    pins.update(host_pins_from_url(url, ips))


class PinnedIPTransport:
    """httpx transport that connects only to pre-validated peer IPs (#1552).

    Rewrites the request URL host to the pinned IP while keeping the original
    ``Host`` header and setting ``sni_hostname`` so TLS cert checks still use
    the configured hostname. Unexpected hosts (not in the pin map) are rejected
    fail-closed — no second DNS lookup on the hot path.
    """

    def __init__(
        self,
        host_to_ips: dict[str, list[str]],
        **transport_kwargs: Any,
    ) -> None:
        import httpx

        self._host_to_ips = {k.lower(): list(v) for k, v in host_to_ips.items() if v}
        self._inner = httpx.HTTPTransport(**transport_kwargs)

    def handle_request(self, request: Any) -> Any:
        import httpx

        host = request.url.host
        if not host:
            raise ValueError("SSRF pin: request has no host (#1552)")
        key = host.lower()
        pins = self._host_to_ips.get(key)
        if not pins:
            raise ValueError(
                f"SSRF pin: host '{host}' was not pre-validated "
                f"(no DNS rebinding path). (#1552)"
            )
        pinned_ip = pins[0]
        # Literal IP already equal to pin — no rewrite needed.
        try:
            if str(ipaddress.ip_address(host)) == pinned_ip:
                return self._inner.handle_request(request)
        except ValueError:
            pass

        port = request.url.port
        if port and port not in (80, 443):
            host_header = f"{host}:{port}"
        else:
            host_header = host

        headers = httpx.Headers(request.headers)
        headers["host"] = host_header
        extensions = dict(request.extensions or {})
        extensions["sni_hostname"] = host
        # httpx.Request has no copy_with (unlike Response) — rebuild with pinned peer.
        pinned_request = httpx.Request(
            method=request.method,
            url=request.url.copy_with(host=pinned_ip),
            headers=headers,
            stream=request.stream,
            extensions=extensions,
        )
        return self._inner.handle_request(pinned_request)

    def close(self) -> None:
        self._inner.close()


def build_pinned_httpx_client(
    *,
    host_to_ips: dict[str, list[str]],
    **client_kwargs: Any,
) -> Any:
    """Construct an ``httpx.Client`` that pins TCP peers to *host_to_ips* (#1552).

    TLS kwargs (``verify`` / ``cert`` / ``trust_env``) must be applied on the
    inner ``HTTPTransport`` — with a custom ``transport=``, httpx does **not**
    forward Client-level ``verify`` into that transport (Bugbot / #1552).
    """
    import httpx

    # Redirects to a new host would bypass the pin map — keep them off.
    client_kwargs.setdefault("follow_redirects", False)
    transport_kwargs: dict[str, Any] = {}
    for key in ("verify", "cert", "trust_env"):
        if key in client_kwargs:
            transport_kwargs[key] = client_kwargs.pop(key)
    transport = PinnedIPTransport(host_to_ips, **transport_kwargs)
    return httpx.Client(transport=transport, **client_kwargs)


def pinned_httpx_request(
    method: str,
    url: str,
    *,
    allow_private: bool = False,
    label: str = "url",
    **request_kwargs: Any,
) -> Any:
    """One-shot httpx request with resolve+validate+pin (#1552)."""
    err, ips = resolve_and_validate_outbound_url(
        url, allow_private=allow_private, label=label
    )
    if err:
        raise ValueError(err)
    pins = host_pins_from_url(url, ips)
    with build_pinned_httpx_client(host_to_ips=pins) as client:
        return client.request(method, url, **request_kwargs)


def _format_pinned_netloc(parsed: Any, pinned_ip: str) -> str:
    """Build netloc for *pinned_ip*, preserving userinfo and port from *parsed*."""
    try:
        ipaddress.IPv6Address(pinned_ip)
        host_part = f"[{pinned_ip}]"
    except ipaddress.AddressValueError:
        host_part = pinned_ip
    userinfo = ""
    if parsed.username is not None:
        from urllib.parse import quote

        user = quote(parsed.username, safe="")
        if parsed.password is not None:
            userinfo = f"{user}:{quote(parsed.password, safe='')}@"
        else:
            userinfo = f"{user}@"
    if parsed.port is not None:
        return f"{userinfo}{host_part}:{parsed.port}"
    return f"{userinfo}{host_part}"


def rewrite_url_host_to_pin(url: str, pinned_ip: str) -> str:
    """Rewrite *url*'s host to *pinned_ip* (IPv6 bracketed); keep path/query/userinfo."""
    parsed = urlparse(url)
    return urlunparse(parsed._replace(netloc=_format_pinned_netloc(parsed, pinned_ip)))


def _make_pinned_ip_http_adapter_class() -> type:
    """Build PinnedIPHTTPAdapter subclass (requests is a hard dependency)."""
    from requests.adapters import HTTPAdapter

    class PinnedIPHTTPAdapter(HTTPAdapter):
        """requests adapter that connects only to pre-validated peer IPs (#1565).

        Rewrites the request URL host to the pinned IP while keeping the original
        ``Host`` header and setting urllib3 ``server_hostname`` / ``assert_hostname``
        so TLS SNI and cert checks still use the configured hostname. Unexpected
        hosts (not in the pin map) are rejected fail-closed — no second DNS lookup
        on the hot path.
        """

        def __init__(
            self,
            host_to_ips: dict[str, list[str]],
            **adapter_kwargs: Any,
        ) -> None:
            self._host_to_ips = {
                k.lower(): list(v) for k, v in host_to_ips.items() if v
            }
            self._pending_tls_hostname: str | None = None
            super().__init__(**adapter_kwargs)

        def send(  # type: ignore[no-untyped-def]
            self,
            request,
            stream=False,
            timeout=None,
            verify=True,
            cert=None,
            proxies=None,
        ):
            parsed = urlparse(request.url)
            host = parsed.hostname
            if not host:
                raise ValueError("SSRF pin: request has no host (#1552)")
            key = host.lower()
            pins = self._host_to_ips.get(key)
            if not pins:
                raise ValueError(
                    f"SSRF pin: host '{host}' was not pre-validated "
                    f"(no DNS rebinding path). (#1552)"
                )
            pinned_ip = pins[0]
            try:
                if str(ipaddress.ip_address(host)) == pinned_ip:
                    return super().send(
                        request,
                        stream=stream,
                        timeout=timeout,
                        verify=verify,
                        cert=cert,
                        proxies=proxies,
                    )
            except ValueError:
                pass

            port = parsed.port
            if "Host" not in request.headers and "host" not in request.headers:
                if port and port not in (80, 443):
                    request.headers["Host"] = f"{host}:{port}"
                else:
                    request.headers["Host"] = host

            request.url = rewrite_url_host_to_pin(request.url, pinned_ip)
            self._pending_tls_hostname = host
            try:
                return super().send(
                    request,
                    stream=stream,
                    timeout=timeout,
                    verify=verify,
                    cert=cert,
                    proxies=proxies,
                )
            finally:
                self._pending_tls_hostname = None

        def get_connection_with_tls_context(  # type: ignore[no-untyped-def]
            self,
            request,
            verify,
            proxies=None,
            cert=None,
        ):
            pool = super().get_connection_with_tls_context(
                request, verify, proxies=proxies, cert=cert
            )
            hostname = self._pending_tls_hostname
            if hostname:
                pool.assert_hostname = hostname
                conn_kw = dict(getattr(pool, "conn_kw", None) or {})
                conn_kw["server_hostname"] = hostname
                pool.conn_kw = conn_kw
            return pool

    return PinnedIPHTTPAdapter


PinnedIPHTTPAdapter = _make_pinned_ip_http_adapter_class()


def build_pinned_requests_session(
    *,
    host_to_ips: dict[str, list[str]],
    **session_kwargs: Any,
) -> Any:
    """Construct a ``requests.Session`` that pins TCP peers to *host_to_ips* (#1565).

    Mounts :class:`PinnedIPHTTPAdapter` for ``http://`` and ``https://``.
    """
    import requests

    session = requests.Session()
    for key, value in session_kwargs.items():
        setattr(session, key, value)
    adapter = PinnedIPHTTPAdapter(host_to_ips)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

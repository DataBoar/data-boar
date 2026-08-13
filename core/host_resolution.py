from __future__ import annotations

import os
from typing import Any

from core.webauthn_rp.settings import resolve_token_secret, webauthn_block

# Effective listen host from ``main.py --web`` (``--host`` / resolved bind).
# Request handlers cannot see uvicorn's bind; without this, CLI ``--host 0.0.0.0``
# while ``api.host`` stays loopback would incorrectly allow key-free bootstrap.
_effective_api_listen_host: str | None = None


def set_effective_api_listen_host(host: str | None) -> None:
    """Record the process listen bind for WebAuthn bootstrap (#1553)."""
    global _effective_api_listen_host
    value = (host or "").strip()
    _effective_api_listen_host = value or None


def get_effective_api_listen_host(
    config: dict[str, Any],
    *,
    cli_host: str | None = None,
) -> str:
    """
    Bind address used for bootstrap trust.

    Prefer the host recorded at ``--web`` startup; else ``resolve_api_host``.
    """
    if _effective_api_listen_host:
        return _effective_api_listen_host
    return resolve_api_host(config, cli_host=cli_host)


def is_loopback_client_host(host: str | None) -> bool:
    """
    True when *host* is a loopback TCP peer (127.0.0.1 / ::1 / localhost).

    Used for WebAuthn first-passkey bootstrap (#1553). Do **not** open
    bootstrap based on ``X-Forwarded-For`` / ``X-Real-IP`` values.
    """
    if not host:
        return False
    h = host.strip().lower()
    # Strip IPv6 zone id if present (e.g. fe80::1%eth0) — loopback has no zone.
    if "%" in h:
        h = h.split("%", 1)[0]
    # Bracketed IPv6 literals from some stacks.
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    return h in ("127.0.0.1", "::1", "localhost")


def http_host_header_hostname(host_header: str | None) -> str | None:
    """
    Hostname from an HTTP ``Host`` header (port stripped).

    Handles ``127.0.0.1:8088`` and ``[::1]:8088``. Empty → ``None``.
    """
    if not host_header:
        return None
    h = host_header.strip().lower()
    if not h:
        return None
    if h.startswith("["):
        end = h.find("]")
        if end == -1:
            return None
        return h[1:end] or None
    # Bare IPv6 without brackets rarely appears in Host; split on last ":" for port.
    if h.count(":") == 1:
        return h.split(":", 1)[0] or None
    return h


def allows_key_free_webauthn_bootstrap(
    peer_host: str | None,
    config: dict[str, Any],
    *,
    cli_host: str | None = None,
    http_host: str | None = None,
) -> bool:
    """
    True when first-passkey registration may proceed without an API key.

    Requires:
    - loopback TCP peer,
    - loopback-only **effective** API listen bind (startup ``--host`` / recorded
      listen host, else ``resolve_api_host``),
    - loopback HTTP ``Host`` hostname when provided (public Host via reverse
      proxy denies key-free even without ``X-Forwarded-*``).

    When the process listens beyond loopback, a loopback peer alone is not
    trusted (#1553 security review).
    """
    if not is_loopback_client_host(peer_host):
        return False
    # Missing or public Host denies key-free (reverse proxy often keeps public Host).
    if not is_loopback_client_host(http_host_header_hostname(http_host)):
        return False
    bind = get_effective_api_listen_host(config, cli_host=cli_host)
    if api_bind_exposes_non_loopback(bind):
        return False
    return True


def request_has_forwarded_client_headers(headers: Any) -> bool:
    """
    True when common reverse-proxy client headers are present.

    Presence only — values are never used to *grant* bootstrap trust.
    Used to deny key-free first-passkey registration when traffic was
    clearly forwarded (local upstream peer can still be loopback).
    """
    if headers is None:
        return False
    get = getattr(headers, "get", None)
    if not callable(get):
        return False
    for name in ("x-forwarded-for", "x-real-ip", "forwarded"):
        if (get(name) or "").strip():
            return True
    return False


def effective_api_key_configured(api_cfg: dict[str, Any] | None) -> bool:
    """
    True when an API key is available after the same rules as ``config.loader``:

    - non-empty ``api.api_key`` in the **normalized** config, or
    - ``api.api_key_from_env`` names a variable that is set to a non-empty value.

    Used for bind warnings and for refusing to start ``--web`` when ``require_api_key``
    is true but no key can be resolved.
    """
    if not isinstance(api_cfg, dict):
        return False
    key = (api_cfg.get("api_key") or "").strip()
    if key:
        return True
    env_name = (api_cfg.get("api_key_from_env") or "").strip()
    if not env_name:
        return False
    return bool((os.environ.get(env_name) or "").strip())


def resolve_api_host(config: dict[str, Any], cli_host: str | None = None) -> str:
    """
    Resolve the host/interface for the API server.

    Resolution order:
    - If cli_host is provided (e.g. main.py --web --host), prefer it.
    - Else, if config.api.host is set, use it.
    - Else, fall back to a safer desktop default: "127.0.0.1".

    Containers and orchestrated deployments (Docker/Kubernetes) should set an
    explicit api.host or use container-level port bindings when they need to
    expose the service on 0.0.0.0.
    """

    if cli_host:
        return cli_host
    api_cfg = config.get("api") or {}
    host = (api_cfg.get("host") or "").strip()
    if host:
        return host

    # Optional environment override: Docker images can set API_HOST=0.0.0.0 so the
    # container is reachable from outside via port bindings, while CLI/desktop
    # remains safely on 127.0.0.1 by default.
    env_host = (os.environ.get("API_HOST") or "").strip()
    if env_host:
        return env_host

    # Safer default for desktop/CLI: bind only to loopback unless explicitly overridden.
    return "127.0.0.1"


def api_bind_exposes_non_loopback(host: str) -> bool:
    """
    True when the API listens beyond loopback (e.g. 0.0.0.0, LAN IP, ::), so clients on
    other hosts can reach the service without SSH port forwarding.
    """
    h = (host or "").strip().lower()
    if not h:
        return False
    if h in ("127.0.0.1", "::1", "localhost"):
        return False
    return True


def should_warn_insecure_api_bind(config: dict[str, Any], host: str) -> bool:
    """
    Corporate-Entity-C / SECURITY: warn when the bind address is reachable beyond loopback but API key
    is not effectively required (open scan/config surface on untrusted networks).
    """
    if not api_bind_exposes_non_loopback(host):
        return False
    api_cfg = config.get("api")
    if not isinstance(api_cfg, dict):
        api_cfg = {}
    if bool(api_cfg.get("require_api_key")):
        if effective_api_key_configured(api_cfg):
            return False
    return True


def auth_boundary_resolved(config: dict[str, Any]) -> bool:
    """
    True when at least one built-in auth mechanism is configured and usable.

    This covers:
    - API key available (literal or *_from_env), and/or
    - WebAuthn enabled with token secret resolved from env.
    """
    api_cfg = config.get("api")
    if not isinstance(api_cfg, dict):
        api_cfg = {}
    if effective_api_key_configured(api_cfg):
        return True
    wa = webauthn_block(config)
    if wa and resolve_token_secret(wa):
        return True
    return False


def should_block_non_loopback_without_auth(config: dict[str, Any], host: str) -> bool:
    """
    Startup hardening gate for issue #1202 confused-deputy exposure.
    """
    if not api_bind_exposes_non_loopback(host):
        return False
    return not auth_boundary_resolved(config)

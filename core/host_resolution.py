from __future__ import annotations

import os
from typing import Any

from core.webauthn_rp.settings import resolve_token_secret, webauthn_block


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

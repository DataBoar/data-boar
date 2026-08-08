"""
Dashboard (uvicorn) transport mode for operator visibility: HTTPS vs explicit insecure HTTP.

Set by ``main.py`` before ``uvicorn.run`` via environment variables so worker processes
and FastAPI see consistent state. :func:`get_dashboard_transport_snapshot` feeds
``GET /status``, ``GET /health``, and dashboard templates.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ENV_MODE = "DATA_BOAR_DASHBOARD_TRANSPORT"
ENV_INSECURE = "DATA_BOAR_DASHBOARD_INSECURE_OPT_IN"
ENV_CERT = "DATA_BOAR_HTTPS_CERT_FILE"
ENV_KEY = "DATA_BOAR_HTTPS_KEY_FILE"


def configure_dashboard_transport(
    *,
    mode: str,
    insecure_explicit_opt_in: bool,
    cert_path: str | None = None,
    key_path: str | None = None,
) -> None:
    """Publish transport posture to the environment (read by API and workers)."""
    os.environ[ENV_MODE] = mode
    os.environ[ENV_INSECURE] = "1" if insecure_explicit_opt_in else "0"
    if cert_path:
        os.environ[ENV_CERT] = cert_path
    else:
        os.environ.pop(ENV_CERT, None)
    if key_path:
        os.environ[ENV_KEY] = key_path
    else:
        os.environ.pop(ENV_KEY, None)


def _not_configured_snapshot() -> dict[str, Any]:
    return {
        "mode": "not_configured",
        "tls_active": False,
        "insecure_http_explicit_opt_in": False,
        "summary": (
            "Dashboard transport not set by CLI entrypoint "
            "(e.g. FastAPI TestClient without main.py)."
        ),
        "show_insecure_banner": False,
    }


def get_dashboard_transport_snapshot() -> dict[str, Any]:
    """Machine-readable transport state for /status, /health, and templates."""
    if ENV_MODE not in os.environ:
        return _not_configured_snapshot()
    mode = os.environ.get(ENV_MODE, "unknown")
    insecure = os.environ.get(ENV_INSECURE) == "1"
    tls_active = mode == "https"
    show_banner = mode == "http" and insecure
    if tls_active:
        summary = "Dashboard transport: HTTPS (TLS >= 1.2)."
    elif mode == "http" and insecure:
        summary = (
            "Dashboard transport: plaintext HTTP with explicit operator opt-in "
            "(interception and sniffing risk; not for untrusted networks)."
        )
    else:
        summary = f"Dashboard transport mode={mode!r}."
    return {
        "mode": mode,
        "tls_active": tls_active,
        "insecure_http_explicit_opt_in": insecure,
        "summary": summary,
        "show_insecure_banner": show_banner,
    }


def resolve_web_listen_options(
    *,
    allow_insecure_http_cli: bool,
    https_cert_file_cli: str | None,
    https_key_file_cli: str | None,
    api_cfg: dict[str, Any] | None,
) -> tuple[str, Path | None, Path | None, bool]:
    """
    Decide listen mode and cert paths from CLI + api config.

    Returns:
        (mode, cert_path, key_path, insecure_explicit)
        mode is ``https`` or ``http``.
    """
    api_cfg = api_cfg or {}
    cert_s = (https_cert_file_cli or api_cfg.get("https_cert_file") or "").strip()
    key_s = (https_key_file_cli or api_cfg.get("https_key_file") or "").strip()
    allow_api = bool(api_cfg.get("allow_insecure_http", False))
    insecure = allow_insecure_http_cli or allow_api

    cert_path = Path(cert_s).expanduser().resolve() if cert_s else None
    key_path = Path(key_s).expanduser().resolve() if key_s else None

    if cert_path or key_path:
        if not cert_path or not key_path:
            raise ValueError(
                "Both https_cert_file and https_key_file are required for HTTPS "
                "(CLI flags or api.https_cert_file / api.https_key_file in config)."
            )
        if not cert_path.is_file():
            raise ValueError(f"HTTPS cert file not found: {cert_path}")
        if not key_path.is_file():
            raise ValueError(f"HTTPS key file not found: {key_path}")
        return "https", cert_path, key_path, False

    if insecure:
        return "http", None, None, True

    raise ValueError(
        "Dashboard transport: choose TLS or explicit insecure HTTP. "
        "Provide --https-cert-file and --https-key-file (or api.https_cert_file "
        "and api.https_key_file), or pass --allow-insecure-http (or "
        "api.allow_insecure_http: true) to accept plaintext."
    )

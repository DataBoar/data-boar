"""Load and validate ``api.webauthn`` settings from normalized config."""

from __future__ import annotations

import os
from typing import Any


def webauthn_block(cfg: dict[str, Any]) -> dict[str, Any] | None:
    """Return normalized ``api.webauthn`` dict, or None when feature is off."""
    api = cfg.get("api") or {}
    wa = api.get("webauthn")
    if not isinstance(wa, dict):
        return None
    if not wa.get("enabled"):
        return None
    return wa


def resolve_token_secret(wa: dict[str, Any]) -> str | None:
    """Secret for signed cookies and server-side state; must be set when WebAuthn is enabled."""
    env_name = str(wa.get("token_secret_from_env") or "").strip() or (
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET"
    )
    return (os.environ.get(env_name) or "").strip() or None


def user_id_bytes(wa: dict[str, Any]) -> bytes:
    """Stable WebAuthn user handle (32 bytes) for single-operator mode."""
    hx = str(wa.get("user_id_hex") or "").strip()
    if len(hx) == 64:
        try:
            out = bytes.fromhex(hx)
            if len(out) == 32:
                return out
        except ValueError:
            pass
    # Default 32-byte handle (not an email; opaque to authenticators).
    raw = b"data-boar-webauthn-v1-operator!!"
    return raw[:32].ljust(32, b"!")[:32]


def expected_origins(wa: dict[str, Any]) -> list[str]:
    """Origins allowed for ``expected_origin`` in verify_* (one or more)."""
    raw = str(wa.get("origin") or "").strip()
    if not raw:
        return ["http://127.0.0.1:8088"]
    extras = wa.get("additional_origins")
    out = [raw]
    if isinstance(extras, list):
        for x in extras:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
    return out

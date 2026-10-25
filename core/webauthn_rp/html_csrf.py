"""Signed CSRF tokens for HTML form POSTs (standalone; not gated on WebAuthn).

Issue #1231: previously CSRF was only enforced when the WebAuthn HTML session gate
was active. Mutating locale forms (``/{locale}/config``, ``/{locale}/assessment``)
must always emit and verify a synchronizer token, fail-closed when missing/invalid.

Secret resolution (first match wins):
1. WebAuthn ``token_secret`` env when ``api.webauthn`` is enabled and the secret resolves.
2. ``DATA_BOAR_HTML_CSRF_SECRET`` for a stable standalone signing key across restarts.
3. Process-ephemeral random secret (tokens invalid after process restart — safe default).
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_CSRF_SALT = "html-csrf-v1"
# Short-lived: forms are submitted soon after page load.
_CSRF_MAX_AGE_SECONDS = 3600

_HTML_CSRF_ENV = "DATA_BOAR_HTML_CSRF_SECRET"
_process_ephemeral_secret: str | None = None


def get_standalone_csrf_secret() -> str:
    """Secret when WebAuthn token secret is unavailable (env or process-ephemeral)."""
    global _process_ephemeral_secret
    env = (os.environ.get(_HTML_CSRF_ENV) or "").strip()
    if env:
        return env
    if _process_ephemeral_secret is None:
        _process_ephemeral_secret = secrets.token_hex(32)
    return _process_ephemeral_secret


def reset_standalone_csrf_secret_for_tests() -> None:
    """Clear process-ephemeral secret (unit tests only)."""
    global _process_ephemeral_secret
    _process_ephemeral_secret = None


def resolve_html_csrf_signing_secret(cfg: dict[str, Any]) -> str:
    """Prefer WebAuthn token secret when present; else standalone HTML CSRF secret."""
    from core.webauthn_rp.settings import resolve_token_secret, webauthn_block

    wa = webauthn_block(cfg)
    if wa is not None:
        wa_secret = resolve_token_secret(wa)
        if wa_secret:
            return wa_secret
    return get_standalone_csrf_secret()


def issue_html_csrf_token(secret: str) -> str:
    ser = URLSafeTimedSerializer(secret, salt=_CSRF_SALT)
    return ser.dumps({"v": 1})


def verify_html_csrf_token(secret: str, token: str | None) -> bool:
    if not token or not isinstance(token, str):
        return False
    ser = URLSafeTimedSerializer(secret, salt=_CSRF_SALT)
    try:
        data = ser.loads(token, max_age=_CSRF_MAX_AGE_SECONDS)
        return isinstance(data, dict) and data.get("v") == 1
    except (BadSignature, SignatureExpired, TypeError, ValueError, KeyError):
        return False

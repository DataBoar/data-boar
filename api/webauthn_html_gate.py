"""
WebAuthn HTML session gate (#86 Phase 1b): require signed session cookie for locale-prefixed
dashboard pages when at least one passkey is registered; public GETs for help, about, login;
CSRF tokens for mutating HTML forms.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from api.locale_i18n import VALID_SLUGS
from core.webauthn_rp import session_cookie
from core.webauthn_rp.html_csrf import issue_html_csrf_token, verify_html_csrf_token
from core.webauthn_rp.settings import resolve_token_secret, webauthn_block

_routes_get_config: Any | None = None
_routes_get_engine: Any | None = None


def configure_routes_context(get_config: Any, get_engine: Any) -> None:
    """Inject route-layer config/engine resolvers without importing api.routes."""
    global _routes_get_config, _routes_get_engine
    _routes_get_config = get_config
    _routes_get_engine = get_engine


def locale_path_segments(path: str) -> tuple[str | None, list[str]]:
    """
    Parse ``/{slug}/...`` where slug is a supported locale segment (``en``, ``pt-br``).
    Returns ``(slug_lower, rest_segments)`` or ``(None, parts)`` if not locale-prefixed.
    """
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None, []
    slug = parts[0].lower()
    if slug not in VALID_SLUGS:
        return None, parts
    return slug, parts[1:]


def webauthn_html_gate_should_enforce(cfg: dict, db_manager: Any) -> bool:
    """True when WebAuthn is enabled, token secret resolves, and at least one credential exists."""
    wa = webauthn_block(cfg)
    if wa is None:
        return False
    if not resolve_token_secret(wa):
        return False
    try:
        return int(db_manager.webauthn_credential_count()) > 0
    except Exception:
        return False


def request_has_webauthn_session(request: Request, token_secret: str) -> bool:
    raw = request.cookies.get(session_cookie.COOKIE_NAME)
    if not raw:
        return False
    return session_cookie.verify_session_cookie(token_secret, raw) is not None


def is_locale_html_public_unauthenticated(method: str, rest: list[str]) -> bool:
    """Pages reachable without WebAuthn session when gate is on (GET only)."""
    return method == "GET" and len(rest) == 1 and rest[0] in ("help", "about", "login")


def safe_next_path(next_q: str | None, fallback: str) -> str:
    """Reject open redirects; allow same-origin path starting with ``/``."""
    if not next_q:
        return fallback
    n = next_q.strip()
    if not n.startswith("/") or "://" in n or "\n" in n or "\r" in n:
        return fallback
    if len(n) > 2048:
        return fallback
    return n


def _routes_config_engine():
    if _routes_get_config is None or _routes_get_engine is None:
        raise RuntimeError("webauthn_html_gate route context was not configured")
    return _routes_get_config(), _routes_get_engine()


def csrf_context_for_request(request: Request) -> dict[str, str]:
    """Issue CSRF token for templates when gate is on and the user has a valid session."""
    cfg, engine = _routes_config_engine()
    if not webauthn_html_gate_should_enforce(cfg, engine.db_manager):
        return {}
    wa = webauthn_block(cfg)
    secret = resolve_token_secret(wa or {})
    if not secret:
        return {}
    if not request_has_webauthn_session(request, secret):
        return {}
    return {"csrf_token": issue_html_csrf_token(secret)}


def verify_html_form_csrf_or_raise(request: Request, form: Any) -> None:
    """
    When the HTML gate is active, require a valid ``csrf_token`` form field.
    Call from POST handlers that mutate state via HTML forms.
    """
    cfg, engine = _routes_config_engine()
    if not webauthn_html_gate_should_enforce(cfg, engine.db_manager):
        return
    wa = webauthn_block(cfg)
    secret = resolve_token_secret(wa or {})
    if not secret:
        return
    if not request_has_webauthn_session(request, secret):
        return
    token = form.get("csrf_token")
    if not verify_html_csrf_token(secret, str(token) if token is not None else None):
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token.")


def is_locale_login_get(path: str, method: str) -> bool:
    if method != "GET":
        return False
    slug, rest = locale_path_segments(path)
    if slug is None:
        return False
    return rest == ["login"]


async def webauthn_html_session_middleware(request: Request, call_next):
    """
    Inner middleware: when WebAuthn gate applies, block unauthenticated access to locale HTML
    (except help, about, login). GET → redirect to ``/{slug}/login``; other methods → 401 JSON.
    """
    cfg, engine = _routes_config_engine()
    dbm = engine.db_manager
    if not webauthn_html_gate_should_enforce(cfg, dbm):
        return await call_next(request)

    path = request.url.path
    slug, rest = locale_path_segments(path)
    if slug is None:
        return await call_next(request)

    wa = webauthn_block(cfg)
    secret = resolve_token_secret(wa or {})
    if not secret:
        return await call_next(request)

    if is_locale_html_public_unauthenticated(request.method, rest):
        return await call_next(request)

    if request_has_webauthn_session(request, secret):
        return await call_next(request)

    if request.method == "GET":
        nxt = quote(path, safe="/")
        return RedirectResponse(url=f"/{slug}/login?next={nxt}", status_code=302)

    return JSONResponse(
        status_code=401,
        content={
            "detail": (
                "Authentication required. Sign in with WebAuthn at "
                f"/{slug}/login (HTML) or use the JSON endpoints under /auth/webauthn/."
            )
        },
    )

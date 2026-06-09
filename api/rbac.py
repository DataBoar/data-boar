"""
Dashboard / API RBAC (GitHub #86 Phase 2).

Opt-in via ``api.rbac.enabled``; requires Pro+ tier (``dashboard_rbac`` in tier_features).
Roles: ``admin`` (all), ``dashboard``, ``scanner``, ``reports_reader``, ``config_admin``.
"""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from api.webauthn_html_gate import locale_path_segments
from core.host_resolution import effective_api_key_configured
from core.rbac_settings import rbac_enforcement_active
from core.webauthn_rp import session_cookie
from core.webauthn_rp.settings import resolve_token_secret, webauthn_block

KNOWN_ROLES = frozenset(
    {"admin", "dashboard", "scanner", "reports_reader", "config_admin"}
)


def _normalize_role_list(raw: list[str] | None, fallback: list[str]) -> list[str]:
    source = raw if raw else fallback
    out: list[str] = []
    for r in source:
        rs = str(r).strip().lower()
        if rs in KNOWN_ROLES:
            out.append(rs)
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def _parse_roles_json(s: str | None) -> list[str] | None:
    if not s or not str(s).strip():
        return None
    try:
        data = json.loads(s)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def resolve_effective_roles_for_request(
    request: Request, cfg: dict[str, Any], db_manager: Any
) -> list[str] | None:
    """
    Return role names for the current principal, or None if unauthenticated.

    Precedence: valid global API key (``api_key_roles``) over WebAuthn session cookie.
    """
    api_cfg = cfg.get("api") if isinstance(cfg.get("api"), dict) else {}
    rbac_cfg = api_cfg.get("rbac") if isinstance(api_cfg.get("rbac"), dict) else {}
    default_roles = list(rbac_cfg.get("default_roles") or [])
    api_key_roles = list(rbac_cfg.get("api_key_roles") or default_roles)

    expected = (api_cfg.get("api_key") or "").strip()
    if expected and effective_api_key_configured(api_cfg):
        provided = (request.headers.get("x-api-key") or "").strip()
        if not provided and request.headers.get("authorization"):
            auth = request.headers.get("authorization", "").strip()
            if auth.lower().startswith("bearer "):
                provided = auth[7:].strip()
        if provided and provided == expected:
            return _normalize_role_list(api_key_roles, default_roles)

    wa = webauthn_block(cfg)
    if wa is None:
        return None
    secret = resolve_token_secret(wa)
    if not secret:
        return None
    raw_c = request.cookies.get(session_cookie.COOKIE_NAME)
    if not raw_c:
        return None
    uid = session_cookie.verify_session_cookie(secret, raw_c)
    if uid is None:
        return None
    rj = db_manager.webauthn_roles_json_for_user_id(uid)
    parsed = _parse_roles_json(rj)
    if parsed is not None:
        return _normalize_role_list(parsed, default_roles)
    return _normalize_role_list(None, default_roles)


def principal_allows(required: frozenset[str], roles: list[str]) -> bool:
    if "admin" in roles:
        return True
    return bool(required.intersection(roles))


def required_roles_for_route(method: str, path: str) -> frozenset[str] | None:
    """
    Return roles that may access this route (any one is enough unless using admin).

    None means this path is not covered by RBAC (public or unknown to policy).
    """
    m = method.upper()
    if path == "/health" or path.startswith("/static/"):
        return None
    if path.startswith("/auth/webauthn"):
        return None
    if path == "/about/json":
        return None

    slug, rest = locale_path_segments(path)
    if (
        slug
        and m in ("GET", "HEAD")
        and len(rest) == 1
        and rest[0] in ("help", "about", "login")
    ):
        return None

    SCAN = frozenset({"scanner", "admin"})
    REP = frozenset({"reports_reader", "admin"})
    DASH = frozenset({"dashboard", "admin"})
    CFG = frozenset({"config_admin", "admin"})

    if path in ("/scan", "/start") and m == "POST":
        return SCAN
    if path == "/scan_database" and m == "POST":
        return SCAN
    if path == "/scan_pdf" and m == "POST":
        return REP
    if path in ("/report", "/heatmap") and m in ("GET", "HEAD"):
        return REP
    if path.startswith("/reports/") and m in ("GET", "HEAD"):
        return REP
    if path.startswith("/heatmap/") and m in ("GET", "HEAD"):
        return REP
    if path in ("/status", "/list") and m in ("GET", "HEAD"):
        return DASH
    if path.startswith("/logs") and m in ("GET", "HEAD"):
        return DASH
    if path.startswith("/sessions/") and m == "PATCH":
        return DASH

    if slug:
        if rest == ["reports"] and m in ("GET", "HEAD"):
            return REP
        if rest == ["config"] and m in ("GET", "HEAD", "POST"):
            return CFG
        if len(rest) == 0 and m in ("GET", "HEAD"):
            return DASH
        if rest == ["assessment"] or rest == ["assessment", "export"]:
            if m in ("GET", "HEAD"):
                return DASH
        if rest == ["assessment"] and m == "POST":
            return DASH

    return None


async def rbac_middleware_handler(
    request: Request,
    call_next: Any,
    get_config: Any,
    get_engine: Any,
) -> Any:
    cfg = get_config()
    if not rbac_enforcement_active(cfg):
        return await call_next(request)
    req_roles = required_roles_for_route(request.method, request.url.path)
    if req_roles is None:
        return await call_next(request)
    engine = get_engine()
    roles = resolve_effective_roles_for_request(request, cfg, engine.db_manager)
    if roles is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required for this resource."},
        )
    if not principal_allows(req_roles, roles):
        return JSONResponse(
            status_code=403,
            content={"detail": "Insufficient role for this resource."},
        )
    return await call_next(request)

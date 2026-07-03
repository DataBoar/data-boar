"""
Dashboard / API RBAC (GitHub #86 Phase 2).

Opt-in via ``api.rbac.enabled``; requires Pro+ tier (``dashboard_rbac`` in tier_features).
Roles: ``admin`` (all), ``dashboard``, ``scanner``, ``reports_reader``, ``config_admin``.

When RBAC is active, policy is **default-deny**: only routes on the public allowlist or the
explicit role map are reachable; unclassified routes return 403.
"""

from __future__ import annotations

import hmac
import json
import re
from enum import Enum
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

SCAN = frozenset({"scanner", "admin"})
REP = frozenset({"reports_reader", "admin"})
DASH = frozenset({"dashboard", "admin"})
CFG = frozenset({"config_admin", "admin"})


class RouteRbacClass(str, Enum):
    """How RBAC classifies a route when enforcement is active."""

    PUBLIC = "public"
    PROTECTED = "protected"
    UNCLASSIFIED = "unclassified"


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


def _concrete_path_for_policy(path: str) -> str:
    """Map FastAPI route templates to a concrete path for policy classification."""
    out = path.replace("{locale_slug}", "en")
    return re.sub(r"\{[^}]+\}", "sample-id", out)


def is_rbac_public_route(method: str, path: str) -> bool:
    """Explicit allowlist: no RBAC check when enforcement is active."""
    m = method.upper()
    concrete = _concrete_path_for_policy(path)
    if concrete == "/health" or concrete.startswith("/static/"):
        return True
    if concrete.startswith("/auth/webauthn"):
        return True
    if concrete == "/about/json":
        return True

    slug, rest = locale_path_segments(concrete)
    if (
        slug
        and m in ("GET", "HEAD")
        and len(rest) == 1
        and rest[0] in ("help", "about", "login")
    ):
        return True
    return False


def required_roles_for_route(method: str, path: str) -> frozenset[str] | None:
    """
    Return roles that may access this protected route (any one is enough unless admin).

    None means the route is public (see ``is_rbac_public_route``) or unclassified when
    used alone — prefer ``classify_route_rbac`` for middleware.
    """
    classification, roles = classify_route_rbac(method, path)
    if classification == RouteRbacClass.PROTECTED:
        assert roles is not None
        return roles
    return None


def classify_route_rbac(
    method: str, path: str
) -> tuple[RouteRbacClass, frozenset[str] | None]:
    """
    Classify a route for RBAC when enforcement is active.

    PUBLIC: allow without role check.
    PROTECTED: requires principal with one of the returned roles (or admin).
    UNCLASSIFIED: deny (403) — route must be added to the policy map.
    """
    if is_rbac_public_route(method, path):
        return RouteRbacClass.PUBLIC, None

    m = method.upper()
    concrete = _concrete_path_for_policy(path)

    if concrete in ("/scan", "/start") and m == "POST":
        return RouteRbacClass.PROTECTED, SCAN
    if concrete == "/scan_database" and m == "POST":
        return RouteRbacClass.PROTECTED, SCAN
    if concrete == "/scan_pdf" and m == "POST":
        return RouteRbacClass.PROTECTED, REP
    if concrete in ("/report", "/heatmap") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, REP
    if concrete.startswith("/reports/") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, REP
    if concrete.startswith("/heatmap/") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, REP
    if concrete in ("/findings", "/findings/csv") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, REP
    if concrete.startswith("/findings/") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, REP
    if concrete in ("/status", "/list") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, DASH
    if concrete in ("/openapi.json", "/docs", "/redoc") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, DASH
    if concrete.startswith("/docs/") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, DASH
    if concrete.startswith("/logs") and m in ("GET", "HEAD"):
        return RouteRbacClass.PROTECTED, DASH
    if concrete.startswith("/sessions/") and m == "PATCH":
        return RouteRbacClass.PROTECTED, DASH

    slug, rest = locale_path_segments(concrete)
    if slug:
        if rest == ["reports"] and m in ("GET", "HEAD"):
            return RouteRbacClass.PROTECTED, REP
        if rest == ["config"] and m in ("GET", "HEAD", "POST"):
            return RouteRbacClass.PROTECTED, CFG
        if len(rest) == 0 and m in ("GET", "HEAD"):
            return RouteRbacClass.PROTECTED, DASH
        if rest == ["assessment"] or rest == ["assessment", "export"]:
            if m in ("GET", "HEAD"):
                return RouteRbacClass.PROTECTED, DASH
        if rest == ["assessment"] and m == "POST":
            return RouteRbacClass.PROTECTED, DASH

    return RouteRbacClass.UNCLASSIFIED, None


def iter_fastapi_route_specs(app: Any) -> list[tuple[str, str]]:
    """(method, path_template) for every HTTP route on the app (for invariant tests)."""
    from starlette.routing import BaseRoute

    specs: list[tuple[str, str]] = []
    for route in app.routes:
        if not isinstance(route, BaseRoute):
            continue
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", None)
        if not path:
            continue
        for method in sorted(methods):
            if method in ("OPTIONS",):
                continue
            specs.append((method, path))
    return specs


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
        if provided and hmac.compare_digest(
            provided.encode("utf-8"), expected.encode("utf-8")
        ):
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


async def rbac_middleware_handler(
    request: Request,
    call_next: Any,
    get_config: Any,
    get_engine: Any,
) -> Any:
    cfg = get_config()
    if not rbac_enforcement_active(cfg):
        return await call_next(request)

    classification, req_roles = classify_route_rbac(request.method, request.url.path)
    if classification == RouteRbacClass.PUBLIC:
        return await call_next(request)
    if classification == RouteRbacClass.UNCLASSIFIED:
        return JSONResponse(
            status_code=403,
            content={"detail": "Route not classified in RBAC policy."},
        )
    assert req_roles is not None

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

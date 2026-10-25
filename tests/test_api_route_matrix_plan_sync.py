"""
Keep `docs/plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md` § *HTTP routes* aligned with `api/routes.py`.

When this test fails: update the Phase 0 route table in that plan (and pt-BR pointers if any), then refresh
EXPECTED_HTTP_ROUTES below to match `api.routes.app`.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from starlette.routing import Mount

from api.routes import app
from fastapi.routing import APIRoute


def _nested_route_list(route: Any) -> Sequence[Any] | None:
    """Child routes for nested/include_router wrappers (version-agnostic).

    FastAPI 0.139+ stores ``include_router`` as ``_IncludedRouter`` with
    ``original_router.routes`` instead of flattening ``APIRoute`` onto ``app.routes``.
    Older FastAPI already flattens; those nodes have no nested list here.
    """
    if isinstance(route, (APIRoute, Mount)):
        return None
    original = getattr(route, "original_router", None)
    if original is not None:
        nested = getattr(original, "routes", None)
        if nested is not None:
            return nested
    nested = getattr(route, "routes", None)
    if nested is not None:
        return nested
    return None


def _collect_http_routes(routes: Iterable[Any], rows: list[str]) -> None:
    for route in routes:
        if isinstance(route, APIRoute):
            for method in sorted(route.methods):
                if method == "HEAD":
                    continue
                rows.append(f"{method} {route.path}")
        elif isinstance(route, Mount):
            rows.append(f"MOUNT {route.path}")
        else:
            nested = _nested_route_list(route)
            if nested is not None:
                _collect_http_routes(nested, rows)


def _registered_http_routes() -> list[str]:
    rows: list[str] = []
    _collect_http_routes(app.routes, rows)
    return sorted(rows)


# Update this tuple when adding/removing/changing routes in api/routes.py (same PR as doc table).
EXPECTED_HTTP_ROUTES: tuple[str, ...] = (
    "GET /about/json",
    "GET /auth/webauthn/status",
    "GET /findings",
    "GET /findings/csv",
    "GET /findings/{session_id}",
    "GET /findings/{session_id}/csv",
    "GET /health",
    "GET /heatmap",
    "GET /heatmap/{session_id}",
    "GET /list",
    "GET /logs",
    "GET /logs/{session_id}",
    "GET /report",
    "GET /reports/{session_id}",
    "GET /status",
    "GET /{locale_slug}",
    "GET /{locale_slug}/",
    "GET /{locale_slug}/about",
    "GET /{locale_slug}/assessment",
    "GET /{locale_slug}/assessment/export",
    "GET /{locale_slug}/config",
    "GET /{locale_slug}/help",
    "GET /{locale_slug}/login",
    "GET /{locale_slug}/reports",
    "MOUNT /static",
    "PATCH /sessions/{session_id}",
    "PATCH /sessions/{session_id}/technician",
    "POST /auth/webauthn/authentication/options",
    "POST /auth/webauthn/authentication/verify",
    "POST /auth/webauthn/logout",
    "POST /auth/webauthn/registration/options",
    "POST /auth/webauthn/registration/verify",
    "POST /scan",
    "POST /scan_database",
    "POST /scan_pdf",
    "POST /start",
    "POST /{locale_slug}/assessment",
    "POST /{locale_slug}/config",
)


def test_api_routes_match_plan_matrix_snapshot():
    actual = tuple(_registered_http_routes())
    assert actual == EXPECTED_HTTP_ROUTES, (
        "Route set changed — update EXPECTED_HTTP_ROUTES in this file and the § Phase 0 route table in "
        "docs/plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md in the same PR.\n"
        f"Actual:\n{actual!r}"
    )

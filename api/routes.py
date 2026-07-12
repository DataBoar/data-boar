"""
FastAPI app: dashboard HTML under GET /{locale_slug}/ (e.g. /en/, /pt-br/), config, reports, help, about,
GET /{locale_slug}/login (WebAuthn browser sign-in when enabled),
optional POST /{locale_slug}/assessment and GET /{locale_slug}/assessment/export (gated maturity POC);
optional JSON /auth/webauthn/* when ``api.webauthn.enabled`` (Phase 1 passkeys); optional HTML session gate
when at least one passkey exists (Phase 1b, GitHub #86); optional per-route RBAC when ``api.rbac.enabled``
(Phase 2, Pro+ ``dashboard_rbac``);
unprefixed /, /config, … redirect to the
negotiated locale prefix. API: POST /scan and /start (optional tenant/technician tags), GET /status
(JSON includes ``audit_log`` sampling posture), /report, /list, GET /reports/{session_id},
POST /scan_database (optional tenant/technician),
PATCH /sessions/{session_id} and /sessions/{session_id}/technician for metadata updates.
Findings export (unified JSON/CSV): GET /findings (latest session), GET /findings/csv,
GET /findings/{session_id}, GET /findings/{session_id}/csv — async StreamingResponse, unified schema
with ``source_type`` discriminator and Phase 1 identity fields (``source_mtime_ns``, ``source_size``,
``content_fingerprint``). On startup load
config (config.yaml or CONFIG_PATH) and create a singleton AuditEngine.

Path safety: session_id is validated before use in file paths. Report paths use
``_real_file_under_out_dir_str`` / ``_resolved_existing_file_under_out_dir``: CodeQL's
documented ``normpath(join(base, filename))`` + ``startswith(base)`` + ``isfile``, with
basename allowlists. Heatmap GET handlers return PNG bytes via ``_heatmap_png_response`` to
avoid ``FileResponse(path=...)`` as an extra sink. See ``tests/test_report_path_safety.py``.

Cache: static assets get long-lived Cache-Control; API/HTML get no-store. Sessions list is cached
in-memory for a short TTL when no scan is running to reduce SQLite reads on repeated dashboard loads.

Security: default middleware adds X-Content-Type-Options, X-Frame-Options, Content-Security-Policy,
Referrer-Policy, Permissions-Policy, and Strict-Transport-Security (only when served over HTTPS).
"""

import hmac
import io
import os
import re
import secrets
import sys
import time
from urllib.parse import quote
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.about import get_about_info
from core.dashboard_transport import get_dashboard_transport_snapshot
from core.enterprise_surface_posture import get_enterprise_surface_posture
from core.forwarded_headers import forwarded_proto_posture
from core.host_resolution import effective_api_key_configured
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import is_feature_available
from core.runtime_trust import get_runtime_trust_snapshot
from core.maturity_assessment.integrity import (
    load_integrity_secret_from_config,
    verify_maturity_assessment_rows,
)
from core.maturity_assessment.export_render import (
    render_maturity_export_csv,
    render_maturity_export_markdown,
    score_for_export,
)
from core.maturity_assessment.pack import load_maturity_pack
from core.maturity_assessment.scoring import rubric_result_to_summary_dict
from core.webauthn_rp.settings import webauthn_block

from api.locale_i18n import (
    LOCALE_SLUG_BY_TAG,
    LOCALE_TAG_BY_SLUG,
    VALID_SLUGS,
    html_base_path,
    make_t,
    negotiate_locale_tag,
)
from api.webauthn_html_gate import (
    configure_routes_context as configure_webauthn_html_gate_context,
    csrf_context_for_request,
    is_locale_login_get,
    safe_next_path,
    verify_html_form_csrf_or_raise,
    webauthn_html_session_middleware as webauthn_html_session_gate,
)
from api.webauthn_routes import register_webauthn_routes


class AssessmentExportFormat(str, Enum):
    """Query ``format`` for GET /{locale}/assessment/export (download)."""

    csv = "csv"
    md = "md"


class LocaleSlug(str, Enum):
    """URL path segment for dashboard HTML (maps to BCP 47 in locale negotiation)."""

    en = "en"
    pt_br = "pt-br"


def _integrity_snapshot() -> dict:
    """#856: integrity anchor snapshot for /health and /status (ensure once, lazily)."""
    from core.integrity_anchor import ensure_integrity_anchor, get_integrity_snapshot

    snap = get_integrity_snapshot()
    if snap.get("integrity_state") == "unknown" and "error" not in snap:
        try:
            snap = ensure_integrity_anchor(_get_config())
        except Exception:  # noqa: BLE001 - fail-soft surface, never break probes
            pass
    return snap


def _about_info() -> dict:
    """Application name, version, author and license (from core.about, matches LICENSE and README)."""
    return get_about_info()


def _template_context(base: dict) -> dict:
    """Merge dashboard transport snapshot into Jinja context (banner, /status parity)."""
    snap = get_dashboard_transport_snapshot()
    esp = get_enterprise_surface_posture(_get_config())
    ctx = dict(base)
    ctx["dashboard_transport"] = snap
    ctx["enterprise_surface"] = esp
    ctx["show_insecure_banner"] = bool(snap.get("show_insecure_banner"))
    reasons = list(esp.get("reasons") or [])
    only_plaintext = reasons == ["plaintext_http_explicit"]
    ctx["show_trust_governance_banner"] = (
        esp.get("severity") in ("caution", "elevated") and not only_plaintext
    )
    return ctx


def _html_lang_attr(locale_tag: str) -> str:
    return "pt-BR" if locale_tag == "pt-BR" else "en"


def _locale_tag_from_slug(slug: str) -> str:
    return LOCALE_TAG_BY_SLUG.get(slug.lower(), "en")


def _display_prog(argv0: str | None = None) -> str:
    """Return the operator-facing command form for this runtime."""
    name = Path(argv0 or sys.argv[0] or "").name.lower()
    if name in {"data-boar", "data-boar.exe"}:
        return "data-boar"
    return "python main.py"


def _maturity_self_assessment_poc_allowed(cfg: dict) -> bool:
    """POC route + nav: ``api.maturity_self_assessment_poc_enabled`` and tier feature map."""
    api = cfg.get("api") if isinstance(cfg.get("api"), dict) else {}
    if not api.get("maturity_self_assessment_poc_enabled"):
        return False
    return is_feature_available(
        "maturity_self_assessment_poc",
        get_runtime_tier_for_features(cfg),
    )


def _valid_maturity_assessment_batch_id(batch_id: str) -> bool:
    """Same validation as POST ``assessment_batch_id`` (hex, length cap)."""
    if not batch_id or len(batch_id) > 64:
        return False
    return bool(re.fullmatch(r"[0-9a-fA-F]+", batch_id))


def _format_maturity_submitted_at(dt: object | None) -> str:
    """UTC display string for batch submit time (SQLite may return naive datetime)."""
    if dt is None:
        return ""
    if not isinstance(dt, datetime):
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _assessment_batch_history_for_template(dbm) -> list[dict[str, object]]:
    """Rows for assessment HTML: distinct batches, newest first.

    When GitHub #86 (RBAC) adds per-subject identity, filter summaries by tenant or
    subject instead of listing every batch in the shared SQLite file — same query
    shape, narrower WHERE. See ADR 0032 and PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.
    """
    rows_out: list[dict[str, object]] = []
    for r in dbm.maturity_assessment_batch_summaries(limit=50):
        bid = str(r.get("batch_id") or "")
        short = bid if len(bid) <= 16 else f"{bid[:16]}…"
        rows_out.append(
            {
                "batch_id": bid,
                "batch_id_short": short,
                "submitted_at_display": _format_maturity_submitted_at(
                    r.get("submitted_at")
                ),
                "answer_count": int(r.get("answer_count") or 0),
                "locale_slug": str(r.get("locale_slug") or ""),
                "pack_version": int(r.get("pack_version") or 0),
            }
        )
    return rows_out


def _switcher_entries(request: Request, current_slug: str, t) -> list[dict]:
    cfg = _get_config()
    supported = (cfg.get("locale") or {}).get("supported_locales") or ["en", "pt-BR"]
    segs = [p for p in request.url.path.split("/") if p]
    if segs and segs[0].lower() in VALID_SLUGS:
        tail_path = "/" + "/".join(segs[1:]) if len(segs) > 1 else "/"
    else:
        tail_path = "/"
    entries: list[dict] = []
    for tag in supported:
        s = LOCALE_SLUG_BY_TAG[tag]
        if tail_path == "/":
            url = f"/{s}/"
        else:
            url = f"/{s}{tail_path}"
        if request.url.query:
            url += f"?{request.url.query}"
        label_key = "nav.locale_en" if tag == "en" else "nav.locale_pt"
        entries.append(
            {
                "slug": s,
                "url": url,
                "label": t(label_key),
                "current": s == current_slug,
            }
        )
    return entries


def _i18n_template_context(
    request: Request, locale_slug: str, locale_tag: str, base: dict
) -> dict:
    cfg = _get_config()
    loc = cfg.get("locale") or {}
    supported = loc.get("supported_locales") or ["en", "pt-BR"]
    default = loc.get("default_locale") or "en"
    catalogs: dict = {}
    t_call = make_t(locale_tag, supported, default, catalogs)
    ctx = _template_context(base)
    ctx["t"] = t_call
    ctx["locale_slug"] = locale_slug
    ctx["locale_tag"] = locale_tag
    ctx["html_lang"] = _html_lang_attr(locale_tag)
    ctx["base_path"] = html_base_path(locale_slug)
    ctx["locale_switcher"] = _switcher_entries(request, locale_slug, t_call)
    js_keys = (
        "chart_total",
        "chart_risk",
        "chart_y_total",
        "chart_y_risk",
        "status_running",
        "status_idle",
        "starting",
        "started_prefix",
        "err_scan_progress",
        "err_scan_progress_guide",
        "err_rate",
        "err_rate_guide",
        "err_auth",
        "err_auth_guide",
        "err_network_guide",
        "err_server_guide",
        "err_what",
        "err_prefix",
        "retry_after",
    )
    ctx["dashboard_js_i18n"] = {k: t_call(f"js.{k}") for k in js_keys}
    ctx["show_maturity_assessment_nav"] = _maturity_self_assessment_poc_allowed(cfg)
    return ctx


# In-memory cache for list_sessions (TTL seconds). Bypassed when a scan is running.
_SESSIONS_CACHE_TTL = 2.0
_sessions_cache: list[dict] | None = None
_sessions_cache_time: float = 0.0

# Cached maturity assessment pack (path key, mtime, pack).
_maturity_pack_cache: tuple[str, float, object] | None = None


def _maturity_pack_question_ids(cfg: dict) -> set[str]:
    """Question ids from the configured YAML pack; empty if unset or invalid."""
    pack = _get_maturity_pack_cached(cfg)
    if pack is None:
        return set()
    out: set[str] = set()
    for sec in pack.sections:
        for q in sec.questions:
            out.add(q.id)
    return out


def _get_maturity_pack_cached(cfg: dict) -> object | None:
    """Load ``api.maturity_assessment_pack_path`` once per path mtime; None if unset or invalid."""
    global _maturity_pack_cache

    api = cfg.get("api") if isinstance(cfg.get("api"), dict) else {}
    path = str(api.get("maturity_assessment_pack_path") or "").strip()
    if not path:
        return None
    p = Path(path)
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return None
    key = str(p.resolve())
    if (
        _maturity_pack_cache is not None
        and _maturity_pack_cache[0] == key
        and _maturity_pack_cache[1] == mtime
    ):
        return _maturity_pack_cache[2]
    try:
        pack = load_maturity_pack(p)
    except (OSError, ValueError, yaml.YAMLError):
        return None
    _maturity_pack_cache = (key, mtime, pack)
    return pack


_api_dir = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_api_dir / "templates"))

# Template names (avoid duplicating string literals).
_TEMPLATE_CONFIG = "config.html"

# Session IDs are generated by core.session (e.g. 12 hex + _ + timestamp). Used in path segments.
_SESSION_ID_PATTERN = re.compile(r"^\w{12,64}$", re.ASCII)
_SESSION_ID_UTC_DAY_SUFFIX_PATTERN = re.compile(r"^[A-Za-z0-9]{12,56}_(\d{8})_\d{6}$")
_REPORT_FILENAME_PATTERN = re.compile(r"^Relatorio_Auditoria_[A-Za-z0-9_]{4,64}\.xlsx$")
_HEATMAP_FILENAME_PATTERN = re.compile(r"^heatmap_[A-Za-z0-9_]{4,64}\.png$")


def _report_output_dir_resolved(engine) -> Path:
    """Configured ``report.output_dir`` only (never a path derived from report files)."""
    return Path(engine.config.get("report", {}).get("output_dir", ".")).resolve()


def _real_file_under_out_dir_str(out_dir: Path, filename: str) -> str | None:
    """
    Return ``fullpath`` for ``(out_dir / filename)`` if it exists as a file under ``out_dir``.

    Matches CodeQL's documented safe pattern: ``normpath(join(base_path, filename))`` then
    ``fullpath.startswith(base_path)`` with the **same** ``base_path`` string, then
    ``os.path.isfile(fullpath)``. We avoid an extra ``realpath`` between the prefix check
    and file checks so the analyzer's path-injection barrier still applies. ``base_path``
    is ``realpath(abspath(out_dir))`` so the root is canonical.
    """
    if not filename or "/" in filename or "\\" in filename:
        return None
    if filename in (".", "..") or filename.startswith(".."):
        return None
    try:
        base_path = os.path.realpath(os.path.abspath(os.fspath(out_dir)))
    except OSError:
        return None
    fullpath = os.path.normpath(os.path.join(base_path, filename))
    if not fullpath.startswith(base_path):
        return None
    if not os.path.isfile(fullpath):
        return None
    return fullpath


def _resolved_existing_file_under_out_dir(out_dir: Path, filename: str) -> Path | None:
    """``Path`` wrapper for :func:`_real_file_under_out_dir_str` (reports / shared logic)."""
    s = _real_file_under_out_dir_str(out_dir, filename)
    return Path(s) if s else None


def _validated_output_basename(
    path: str | Path, pattern: re.Pattern[str]
) -> str | None:
    """
    Last path segment only, validated against an allowlist pattern.

    Uses ``os.path.basename`` (not ``Path(path)``) so static analysis does not treat
    the stored report path as controlling a path expression before we restrict to
    ``out_dir / basename`` only. ``path`` comes from engine state (last report path),
    not raw HTTP input, but we still normalize to a single filename segment.
    """
    raw = os.fspath(path)
    name = os.path.basename(raw.replace("\\", "/"))
    if not name or pattern.fullmatch(name) is None:
        return None
    return name


def _validate_session_id(session_id: str) -> None:
    """Reject session_id that could be used in path traversal. Raises HTTPException if invalid."""
    if not session_id or not isinstance(session_id, str):
        raise HTTPException(status_code=400, detail="Invalid session_id.")
    if not _SESSION_ID_PATTERN.fullmatch(session_id.strip()):
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id: only alphanumeric and underscore, 12–64 characters.",
        )


def _safe_report_output_path(path: str | Path, engine) -> Path | None:
    """
    Resolve and validate a report/heatmap path against configured report.output_dir.

    Returns the resolved candidate when it is inside output_dir and exists.
    Returns None when missing, invalid, outside output_dir, or non-existent.
    """
    if not path:
        return None
    filename = _validated_output_basename(path, _REPORT_FILENAME_PATTERN)
    if filename is None:
        return None
    return _resolved_existing_file_under_out_dir(
        _report_output_dir_resolved(engine), filename
    )


def _safe_report_path_for_heatmap(engine) -> tuple[Path, str] | None:
    """
    Resolve a report path under ``report.output_dir`` and a session key for heatmap naming.

    Returns ``(safe_report_path, session_key)`` or ``None`` when no report is available.
    """
    path = engine.get_last_report_path()
    sid: str | None = None
    safe_report_path = _safe_report_output_path(path, engine) if path else None
    if not safe_report_path:
        sid = engine.db_manager.current_session_id or None
        if not sid:
            sessions = engine.db_manager.list_sessions()
            if sessions:
                sid = sessions[0]["session_id"]
        if not sid:
            return None
        path = engine.generate_final_reports(sid)
        safe_report_path = _safe_report_output_path(path, engine) if path else None
    if not safe_report_path:
        return None
    if not sid:
        name = safe_report_path.name
        prefix = name.removeprefix("Relatorio_Auditoria_").removesuffix(".xlsx")
        sid = prefix
    return safe_report_path, sid or ""


def _heatmap_png_path_for_download(engine, session_key: str) -> Path | None:
    """
    Resolve ``heatmap_<first 12 chars of session_key>.png`` under configured output_dir.

    Uses only ``engine.config`` for the base directory (not ``report_path.parent``).
    """
    heatmap_filename = f"heatmap_{session_key[:12]}.png"
    if not _HEATMAP_FILENAME_PATTERN.fullmatch(heatmap_filename):
        return None
    return _resolved_existing_file_under_out_dir(
        _report_output_dir_resolved(engine), heatmap_filename
    )


def _heatmap_png_response(engine, session_key: str):
    """
    Heatmap download without ``FileResponse(path=...)`` (CodeQL path sink).

    Opens the file only after :func:`_real_file_under_out_dir_str` (normpath + startswith
    + realpath), matching the documented safe ``open(fullpath)`` pattern.
    """
    from starlette.responses import Response

    heatmap_filename = f"heatmap_{session_key[:12]}.png"
    if not _HEATMAP_FILENAME_PATTERN.fullmatch(heatmap_filename):
        return None
    safe_path = _real_file_under_out_dir_str(
        _report_output_dir_resolved(engine), heatmap_filename
    )
    if not safe_path:
        return None
    try:
        with open(safe_path, "rb") as fh:
            body = fh.read()
    except OSError:
        return None
    fname = os.path.basename(safe_path)
    return Response(
        content=body,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{fname}"'},
    )


class DatabaseConfig(BaseModel):
    """Single database target for one-off scan via POST /scan_database."""

    name: str
    host: str
    port: int
    user: str
    password: str
    database: str
    driver: str = "postgresql+psycopg2"
    tenant: str | None = None  # optional customer/tenant name for this scan
    technician: str | None = None  # optional technician/operator name for this scan
    jurisdiction_hint: bool | None = (
        None  # when True, heuristic jurisdiction Report info rows for this session
    )


class ScanStartBody(BaseModel):
    """Optional body for POST /scan: tenant/customer, technician/operator, run-local scan toggles."""

    tenant: str | None = None
    technician: str | None = None
    scan_compressed: bool | None = (
        None  # when True, merge into file_scan for this run only
    )
    content_type_check: bool | None = (
        None  # when True, set file_scan.use_content_type for this run only (magic-byte format sniffing)
    )
    jurisdiction_hint: bool | None = (
        None  # when True, opt-in to heuristic jurisdiction notes on Report info for this session
    )
    scan_for_stego: bool | None = (
        None  # when True, merge into file_scan for this run only (entropy hints on rich media)
    )
    scheduled: bool | None = (
        None  # when True, treat as a scheduled/cron-triggered scan (Pro+ ``scheduled_scans``)
    )


# Load config and create engine at import time (or on startup event)
_config_path = os.environ.get("CONFIG_PATH", "config.yaml")
if not Path(_config_path).exists():
    _config_path = "config.yaml"
_config = None
_audit_engine = None


def _get_config_path() -> str:
    """Return path to config file (for dashboard display and save)."""
    return _config_path


def _get_config_raw() -> str:
    """Return raw config file content (YAML) for editing. If file missing, return default YAML."""
    p = Path(_config_path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return _default_config_yaml()


def _get_config_yaml_for_display() -> str:
    """Return config YAML safe for display: secret values redacted so the UI never shows them."""
    from config.redact_config import redact_config_for_display

    raw = _get_config_raw()
    try:
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            redacted = redact_config_for_display(data)
            return yaml.dump(
                redacted, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
    except Exception:
        pass
    return raw


def _default_config_yaml() -> str:
    return """# LGPD Audit configuration
targets: []
file_scan:
  extensions: [.txt, .csv, .pdf, .docx, .xlsx]
  recursive: true
  scan_sqlite_as_db: true
  sample_limit: 5
report:
  output_dir: .
api:
  port: 8088
locale:
  default_locale: en
  supported_locales: [en, pt-BR]
  cookie_name: db_locale
  cookie_max_age_seconds: 31536000
sqlite_path: audit_results.db
scan:
  max_workers: 1
"""


def _save_config_yaml(yaml_content: str) -> None:
    """Validate and save config file; reset in-memory config and engine so next request reloads."""
    from config.loader import normalize_config
    from core.licensing.guard import reset_license_guard_for_tests

    p = Path(_config_path)
    try:
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError("Config must be a YAML object")
        normalize_config(data, config_path=p)
    except Exception as e:
        raise ValueError(f"Invalid YAML or config: {e}") from e
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml_content, encoding="utf-8")
    global _config, _audit_engine
    _config = None
    _audit_engine = None
    reset_license_guard_for_tests()


def _merge_and_save_config_yaml(submitted_yaml: str) -> None:
    """Merge submitted YAML with current config so redacted/placeholder secret values do not overwrite real secrets, then save."""
    from config.redact_config import merge_config_on_save

    current_raw = _get_config_raw()
    try:
        current_data = yaml.safe_load(current_raw)
    except Exception:
        current_data = {}
    if not isinstance(current_data, dict):
        current_data = {}
    try:
        submitted_data = yaml.safe_load(submitted_yaml)
    except Exception as e:
        raise ValueError(f"Invalid YAML: {e}") from e
    if not isinstance(submitted_data, dict):
        raise ValueError("Config must be a YAML object")
    merged = merge_config_on_save(submitted_data, current_data)
    merged_yaml = yaml.dump(
        merged, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    _save_config_yaml(merged_yaml)


def _get_config():
    global _config
    if _config is None:
        from config.loader import load_config

        if Path(_config_path).exists():
            _config = load_config(_config_path)
        else:
            _config = {
                "targets": [],
                "sqlite_path": "audit_results.db",
                "report": {"output_dir": "."},
                "api": {"port": 8088},
                "locale": {
                    "default_locale": "en",
                    "supported_locales": ["en", "pt-BR"],
                    "cookie_name": "db_locale",
                    "cookie_max_age_seconds": 31536000,
                },
            }
    return _config


def _get_engine():
    global _audit_engine
    if _audit_engine is None:
        from core.engine import AuditEngine
        from core.licensing.guard import get_license_guard

        cfg = _get_config()
        _audit_engine = AuditEngine(cfg, config_path=_config_path)
        get_license_guard(cfg)
    return _audit_engine


configure_webauthn_html_gate_context(_get_config, _get_engine)


def _license_public_dict() -> dict:
    """License status for API/UI (open mode shows OPEN)."""
    try:
        from core.licensing.guard import get_license_guard

        return get_license_guard(_get_config()).context.to_public_dict()
    except Exception:
        return {"license_state": "UNKNOWN", "license_mode": "open"}


def _raise_if_license_blocks_scan() -> None:
    """403 when enforcement blocks ingest/digest."""
    from core.licensing.guard import get_license_guard

    g = get_license_guard(_get_config())
    if g.allows_scan():
        return
    c = g.context
    raise HTTPException(
        status_code=403,
        detail={
            "error": "license_blocked",
            "license_state": c.state,
            "message": "Scan blocked by licensing policy. See /health and /about for status.",
            "detail": c.detail,
        },
    )


def _raise_if_feature_blocked(feature: str) -> None:
    """403 when the runtime tier denies a Pro/Enterprise feature."""
    from core.licensing.errors import FeatureTierBlockedError
    from core.licensing.feature_gate import require_feature

    try:
        require_feature(_get_config(), feature)
    except FeatureTierBlockedError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_tier_blocked",
                "feature": exc.feature,
                "message": exc.reason,
                "required_tier": exc.required_tier,
                "current_tier": exc.current_tier,
            },
        ) from exc


def _validate_webauthn_startup(cfg: dict) -> None:
    """Fail fast when WebAuthn is enabled but no token secret is available."""
    from core.webauthn_rp.settings import resolve_token_secret, webauthn_block

    wa = webauthn_block(cfg)
    if wa is None:
        return
    if not resolve_token_secret(wa):
        raise RuntimeError(
            "api.webauthn.enabled is true but no token secret was resolved. "
            "Set the environment variable named in api.webauthn.token_secret_from_env "
            "(default DATA_BOAR_WEBAUTHN_TOKEN_SECRET) before starting the API."
        )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Load config and create AuditEngine on startup (replaces deprecated on_event)."""
    cfg = _get_config()
    _validate_webauthn_startup(cfg)
    _get_engine()
    yield
    # shutdown: nothing to tear down


app = FastAPI(
    title="LGPD/GDPR/CCPA Audit API",
    version=get_about_info()["version"],
    lifespan=_lifespan,
)


def _list_sessions_cached() -> list[dict]:
    """Return list of sessions; use short-TTL in-memory cache when no scan is running to reduce DB reads."""
    global _sessions_cache, _sessions_cache_time
    engine = _get_engine()
    if engine.is_running:
        _sessions_cache = None
        return engine.db_manager.list_sessions()
    now = time.monotonic()
    if (
        _sessions_cache is not None
        and (now - _sessions_cache_time) < _SESSIONS_CACHE_TTL
    ):
        return _sessions_cache
    _sessions_cache = engine.db_manager.list_sessions()
    _sessions_cache_time = now
    return _sessions_cache


def _invalidate_sessions_cache() -> None:
    """Clear sessions cache so next read gets fresh data (e.g. after scan start or session PATCH)."""
    global _sessions_cache
    _sessions_cache = None


def _raise_if_concurrent_limit_exceeded(dbm, max_concurrent: int, source: str) -> None:
    """Raise HTTPException(429) when running sessions count >= max_concurrent."""
    running = dbm.get_running_sessions_count()
    if running < max_concurrent:
        return
    raise HTTPException(
        status_code=429,
        detail={
            "error": "rate_limited",
            "reason": "Too many scans running at the same time. Wait for existing scans to finish before starting a new one.",
            "max_concurrent_scans": max_concurrent,
            "running_scans": running,
            "source": source,
        },
    )


def _raise_if_interval_limit_exceeded(
    dbm, min_interval: int, grace: int, source: str
) -> None:
    """Raise HTTPException(429) when last scan started too recently (min_interval or grace)."""
    if min_interval <= 0:
        return
    last = dbm.get_last_session()
    if not last or not last.get("started_at"):
        return
    started_at = last["started_at"]
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if started_at > now:
        return
    delta = (now - started_at).total_seconds()
    effective_min = float(min_interval)
    if grace > 0 and float(grace) > effective_min:
        effective_min = float(grace)
    if delta >= effective_min:
        return
    retry_after = max(0, int(effective_min - delta))
    raise HTTPException(
        status_code=429,
        detail={
            "error": "rate_limited",
            "reason": "Scans are being started too frequently. Wait before starting another scan.",
            "min_interval_seconds": int(effective_min),
            "seconds_since_last_scan": int(delta),
            "retry_after_seconds": retry_after,
            "source": source,
        },
    )


def _check_rate_limit(source: str) -> None:
    """
    Enforce basic rate limiting for scan-triggering endpoints.
    Uses normalized config (rate_limit block) plus session metadata from SQLite.
    Raises HTTPException(429) when limits are exceeded.
    """
    cfg = _get_config()
    rl = cfg.get("rate_limit") or {}
    if not rl.get("enabled"):
        return
    engine = _get_engine()
    dbm = engine.db_manager
    max_concurrent = int(rl.get("max_concurrent_scans", 1))
    min_interval = int(rl.get("min_interval_seconds", 0))
    grace = int(rl.get("grace_for_running_status", 0))
    _raise_if_concurrent_limit_exceeded(dbm, max_concurrent, source)
    _raise_if_interval_limit_exceeded(dbm, min_interval, grace, source)


_AUDIT_LOGS_READ_PERMISSION = "audit_logs.read"
_resolve_effective_roles_for_request_fn = None


def _audit_logs_settings(cfg: dict | None = None) -> dict[str, object]:
    """Return normalized audit-log download settings from config."""
    config = cfg or _get_config()
    api_cfg = config.get("api") if isinstance(config.get("api"), dict) else {}
    raw = api_cfg.get("audit_logs")
    if not isinstance(raw, dict):
        raw = {}
    directory = str(raw.get("directory") or "").strip() or None
    return {
        "enabled": bool(raw.get("enabled", False)),
        "directory": directory,
    }


def _resolve_audit_logs_directory(settings: dict[str, object]) -> Path:
    """Resolve configured audit log directory (relative paths anchored to config dir)."""
    directory = settings.get("directory")
    if not isinstance(directory, str) or not directory.strip():
        raise HTTPException(
            status_code=503,
            detail=(
                "Audit log downloads are enabled but api.audit_logs.directory is not configured."
            ),
        )
    root = Path(directory)
    if not root.is_absolute():
        root = (Path(_config_path).resolve().parent / root).resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(
            status_code=503,
            detail=f"Configured api.audit_logs.directory does not exist: {root}",
        )
    return root


def _authorize_audit_log_download(request: Request) -> list[str]:
    """Require authenticated principal with audit_logs.read or admin role."""
    cfg = _get_config()
    resolve_roles = _resolve_effective_roles_for_request_fn
    if resolve_roles is None:
        raise HTTPException(
            status_code=503,
            detail="RBAC resolver unavailable for audit log download.",
        )
    roles = resolve_roles(request, cfg, _get_engine().db_manager)
    if roles is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for audit log downloads.",
        )
    if "admin" in roles or _AUDIT_LOGS_READ_PERMISSION in roles:
        return roles
    raise HTTPException(
        status_code=403,
        detail=f"Missing required permission: {_AUDIT_LOGS_READ_PERMISSION}",
    )


def _audit_log_candidates(log_dir: Path) -> list[Path]:
    return sorted(
        log_dir.glob("audit_*.log"), key=lambda p: p.stat().st_mtime, reverse=True
    )


def _session_exists_for_audit_log_lookup(session_id: str) -> bool:
    """
    Best-effort existence check before date-based fallback.

    Prevents returning daily logs for fabricated-but-valid session IDs.
    """
    dbm = _get_engine().db_manager
    fast_check = getattr(dbm, "_session_exists", None)
    if callable(fast_check):
        try:
            return bool(fast_check(session_id))
        except Exception:
            pass
    try:
        sessions = dbm.list_sessions()
    except Exception:
        return False
    return any((s.get("session_id") or "") == session_id for s in sessions)


def _session_day_from_session_id(session_id: str) -> str | None:
    """
    Extract UTC YYYYMMDD day from ``new_session_id`` format.

    Session IDs are generated as ``<12-hex>_YYYYMMDD_HHMMSS`` in ``core.session``.
    """
    m = _SESSION_ID_UTC_DAY_SUFFIX_PATTERN.fullmatch(session_id.strip())
    if m is None:
        return None
    return m.group(1)


def _date_fallback_log_for_session(log_dir: Path, session_id: str) -> Path | None:
    """
    Return ``audit_YYYYMMDD.log`` fallback for a known session, when available.
    """
    if not _session_exists_for_audit_log_lookup(session_id):
        return None
    day = _session_day_from_session_id(session_id)
    if day is None:
        return None
    wanted_name = f"audit_{day}.log"
    for candidate in _audit_log_candidates(log_dir):
        if candidate.name == wanted_name:
            return candidate
    return None


def _emit_audit_log_download_event(
    request: Request, *, filename: str, session_id: str | None, roles: list[str]
) -> None:
    """Best-effort audit event for /logs downloads."""
    try:
        from utils.logger import get_logger

        client_host = request.client.host if request.client else "unknown"
        session_filter = "session" if session_id else "latest"
        # Avoid log injection and avoid recording path/user-controlled artifacts verbatim.
        safe_client = str(client_host).replace("\n", "").replace("\r", "").strip()
        safe_filename = str(filename).replace("\n", "").replace("\r", "").strip()
        _ = roles
        get_logger().info(
            "AuditLogDownload: file=%s mode=%s client=%s",
            safe_filename,
            session_filter,
            safe_client,
        )
    except Exception:
        # Download path must stay resilient if logger transport is unavailable.
        return


def _audit_log_file_response(path: Path) -> Response:
    """
    Return audit log file content as attachment without FileResponse(path) sink.
    """
    try:
        body = path.read_bytes()
    except OSError as e:
        raise HTTPException(
            status_code=404, detail=f"Audit log file is not readable: {path.name}"
        ) from e
    return Response(
        content=body,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{quote(path.name)}"'},
    )


# Max request body size (1 MB) for JSON/config and scan start body to reduce DoS via huge payloads
MAX_REQUEST_BODY_BYTES = 1_000_000


def _is_secure_request(request: Request) -> bool:
    """True if request is HTTPS after trusted-proxy evaluation."""
    posture = forwarded_proto_posture(request, _get_config())
    return posture.get("effective_scheme") == "https"


@app.middleware("http")
async def rbac_middleware(request: Request, call_next):
    """
    When ``api.rbac.enabled`` and tier allows ``dashboard_rbac``, enforce role checks on API and
    locale HTML routes (Phase 2, GitHub #86). Registered before the WebAuthn HTML gate so it runs
    **after** session authentication on the inner stack (closest to the route handler).
    """
    from api.rbac import rbac_middleware_handler, resolve_effective_roles_for_request

    global _resolve_effective_roles_for_request_fn
    _resolve_effective_roles_for_request_fn = resolve_effective_roles_for_request

    return await rbac_middleware_handler(request, call_next, _get_config, _get_engine)


@app.middleware("http")
async def webauthn_html_session_middleware(request: Request, call_next):
    """
    When WebAuthn is enabled and at least one passkey exists, require a valid session cookie
    for locale-prefixed HTML except ``help``, ``about``, and ``login`` (GET). Registered first
    so this layer is innermost (runs last before the route handler). See PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL Phase 1b.
    """
    return await webauthn_html_session_gate(request, call_next)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Add current best-practice security headers to all responses.
    HSTS is set only when the request is over HTTPS to avoid locking out HTTP users.
    CSP allows 'self' and the Chart.js CDN for scripts, plus 'unsafe-inline' for existing inline styles.
    """
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), interest-cohort=(), payment=(), usb=(), "
        "magnetometer=(), gyroscope=(), accelerometer=()",
    )
    # CSP: script-src 'self' only — Chart.js is vendored in api/static/ (#825).
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; "
        "base-uri 'self'; object-src 'none'",
    )
    if _is_secure_request(request):
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains; preload",
        )
    return response


@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    """Set Cache-Control: long-lived for static assets, no-store for API and HTML."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers.setdefault("Cache-Control", "public, max-age=86400")
    else:
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.middleware("http")
async def optional_api_key_middleware(request: Request, call_next):
    """
    When ``api.require_api_key`` is true and a key is available (literal or resolved from
    ``api_key_from_env`` at config load), require **X-API-Key** or **Authorization: Bearer**
    for every path except **GET /health** (liveness: must stay unauthenticated).

    Responses: **401** if the key is missing or wrong; **503** if the operator enabled
    ``require_api_key`` but no key could be resolved (misconfiguration).
    """
    if request.url.path == "/health":
        return await call_next(request)
    if request.url.path.startswith("/auth/webauthn"):
        return await call_next(request)
    if is_locale_login_get(request.url.path, request.method):
        return await call_next(request)
    cfg = _get_config()
    api_cfg = cfg.get("api") or {}
    if not api_cfg.get("require_api_key"):
        return await call_next(request)
    if not effective_api_key_configured(api_cfg):
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "api.require_api_key is true but no API key is configured. "
                    "Set api.api_key or api.api_key_from_env (with the env var at process start). "
                    "See docs/ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md."
                )
            },
        )
    expected = api_cfg.get("api_key") or ""
    provided = (request.headers.get("x-api-key") or "").strip()
    if not provided and request.headers.get("authorization"):
        auth = request.headers.get("authorization", "").strip()
        if auth.lower().startswith("bearer "):
            provided = auth[7:].strip()
    if not provided or not hmac.compare_digest(provided, expected):
        return JSONResponse(
            status_code=401, content={"detail": "Missing or invalid API key"}
        )
    return await call_next(request)


@app.middleware("http")
async def request_body_size_middleware(request: Request, call_next):
    """
    Reject requests with Content-Length exceeding MAX_REQUEST_BODY_BYTES (1 MB) to prevent
    DoS via huge JSON or form bodies (e.g. POST /config, POST /scan, POST /scan_database).
    Added last so it runs first (outermost) in the middleware stack.
    """
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large. Maximum size is 1 MB."},
                )
        except ValueError:
            pass  # Invalid Content-Length; let the server handle it
    return await call_next(request)


_UNPREFIXED_HTML_PATHS = frozenset({"/", "/config", "/reports", "/help", "/about"})


def _is_api_or_asset_path(path: str) -> bool:
    """Paths that must not receive locale prefix redirects (API, static, OpenAPI)."""
    if path.startswith("/static"):
        return True
    if path.startswith("/auth/"):
        return True
    if path == "/health":
        return True
    if path in ("/status", "/list", "/report", "/heatmap", "/logs"):
        return True
    if path in ("/scan", "/start", "/scan_database"):
        return True
    if path.startswith("/sessions/"):
        return True
    if path.startswith("/heatmap/") or path.startswith("/logs/"):
        return True
    if path.startswith("/reports/") and path != "/reports":
        return True
    if path.startswith("/about/json"):
        return True
    if path == "/findings" or path == "/findings/csv":
        return True
    if path.startswith("/findings/"):
        return True
    if path.startswith("/openapi") or path in ("/docs", "/redoc"):
        return True
    return False


@app.middleware("http")
async def locale_html_middleware(request: Request, call_next):
    """
    Redirect unprefixed dashboard HTML paths to /{slug}/…; fix invalid locale prefix;
    set locale preference cookie on successful HTML responses.
    Registered last so it runs first on incoming requests (outermost).
    """
    if "application/json" in request.headers.get("accept", ""):
        return await call_next(request)
    path = request.url.path
    if _is_api_or_asset_path(path):
        return await call_next(request)
    cfg = _get_config()
    loc_cfg = cfg.get("locale") or {}
    cookie_name = str(loc_cfg.get("cookie_name") or "db_locale")
    try:
        cookie_max_age = int(loc_cfg.get("cookie_max_age_seconds") or 31536000)
    except (TypeError, ValueError):
        cookie_max_age = 31536000

    tag = negotiate_locale_tag(request, cfg)
    slug = LOCALE_SLUG_BY_TAG[tag]

    if path in _UNPREFIXED_HTML_PATHS or (
        request.method == "POST" and path == "/config"
    ):
        dest = f"/{slug}/" if path == "/" else f"/{slug}{path}"
        if request.url.query:
            dest += f"?{request.url.query}"
        code = 307 if request.method in ("POST", "PUT", "PATCH", "DELETE") else 302
        return RedirectResponse(url=dest, status_code=code)

    segments = [p for p in path.split("/") if p]
    if segments and segments[0].lower() not in VALID_SLUGS:
        rest = "/" + "/".join(segments[1:]) if len(segments) > 1 else "/"
        dest = f"/{slug}{rest}" if rest != "/" else f"/{slug}/"
        if request.url.query:
            dest += f"?{request.url.query}"
        return RedirectResponse(url=dest, status_code=302)

    response = await call_next(request)
    if (
        200 <= response.status_code < 400
        and segments
        and segments[0].lower() in VALID_SLUGS
    ):
        lt = LOCALE_TAG_BY_SLUG[segments[0].lower()]
        response.set_cookie(
            cookie_name,
            lt,
            max_age=cookie_max_age,
            path="/",
            samesite="lax",
        )
    return response


app.mount("/static", StaticFiles(directory=str(_api_dir / "static")), name="static")


@app.get("/health")
async def health():
    """
    Liveness/readiness probe for Docker, Swarm and Kubernetes.

    Semantics: **always unauthenticated** (no API key). Returns minimal JSON for
    orchestrators; see SECURITY.md / USAGE.md for difference vs protected routes.
    """
    body: dict = {"status": "ok"}
    body["license"] = _license_public_dict()
    body["dashboard_transport"] = get_dashboard_transport_snapshot()
    body["enterprise_surface"] = get_enterprise_surface_posture(_get_config())
    body["integrity"] = _integrity_snapshot()
    return body


@app.get("/about/json")
async def about_json():
    """Machine-readable about info (name, version, author, license) for API consumers."""
    info = _about_info()
    info["license"] = _license_public_dict()
    return info


def _build_chart_data(sessions: list[dict]) -> list[dict]:
    """
    Build progress chart data: one point per session (oldest first) with total findings and risk score.
    Score formula: min(100, total_findings * 2 + scan_failures * 5). Used for dashboard "Progress over time" chart.
    """
    ordered = list(reversed(sessions))  # chronological order for time axis
    out = []
    for s in ordered:
        total = s["database_findings"] + s["filesystem_findings"]
        score = min(100, total * 2 + s["scan_failures"] * 5)
        started = s.get("started_at") or ""
        # Short label for axis (date only if ISO format)
        label = started[:10] if len(started) >= 10 else started or "—"
        out.append(
            {
                "label": label,
                "started_at": started,
                "total_findings": total,
                "score": round(score, 1),
            }
        )
    return out


_RATE_LIMIT_429 = {
    429: {
        "description": "Rate limit exceeded (too many concurrent scans or scans started too frequently)."
    }
}
_NOT_FOUND_404 = {404: {"description": "Resource not found."}}
_SESSION_RESPONSES = {
    400: {"description": "Invalid session_id (empty or invalid format)."},
    404: {"description": "Session or resource not found."},
}


@app.post("/scan", responses=_RATE_LIMIT_429)
@app.post("/start", responses=_RATE_LIMIT_429)
async def start_scan(
    background_tasks: BackgroundTasks, body: ScanStartBody | None = None
):
    """Start audit in background. Optional body: tenant, technician, scan_compressed, content_type_check, scan_for_stego, scheduled, jurisdiction_hint. Returns session_id."""
    _raise_if_license_blocks_scan()
    if body and getattr(body, "scheduled", None) is True:
        _raise_if_feature_blocked("scheduled_scans")
    engine = _get_engine()
    if engine.is_running:
        raise HTTPException(status_code=409, detail="Audit already in progress.")
    # Global rate limiting (DB-backed) to avoid accidental DoS from repeated scans
    _check_rate_limit(source="scan")
    from core.session import new_session_id
    from core.validation import sanitize_tenant_technician

    session_id = new_session_id()
    tenant = sanitize_tenant_technician((body.tenant if body else None) or None)
    technician = sanitize_tenant_technician((body.technician if body else None) or None)
    jh = bool(body and body.jurisdiction_hint)
    engine.db_manager.set_current_session_id(session_id)
    engine.db_manager.create_session_record(
        session_id,
        tenant_name=tenant,
        technician_name=technician,
        jurisdiction_hint=jh,
    )

    # Run-local overrides: merge into file_scan for this run only; restore after (same pattern as scan_compressed).
    fs = engine.config.get("file_scan") or {}
    prev_scan_compressed = fs.get("scan_compressed")
    prev_use_content_type = fs.get("use_content_type")
    prev_scan_for_stego = fs.get("scan_for_stego")
    _rep_prev = engine.config.get("report") or {}
    _jh_prev = _rep_prev.get("jurisdiction_hints")
    prev_jurisdiction_hints_enabled = (
        bool(_jh_prev.get("enabled")) if isinstance(_jh_prev, dict) else False
    )

    if body and getattr(body, "scan_compressed", None) is True:
        engine.config.setdefault("file_scan", {})["scan_compressed"] = True
    if body and getattr(body, "content_type_check", None) is True:
        engine.config.setdefault("file_scan", {})["use_content_type"] = True
    if body and getattr(body, "scan_for_stego", None) is True:
        engine.config.setdefault("file_scan", {})["scan_for_stego"] = True
    if jh:
        engine.config.setdefault("report", {}).setdefault("jurisdiction_hints", {})
        engine.config["report"]["jurisdiction_hints"]["enabled"] = True

    def run_targets():
        try:
            engine._run_audit_targets()
        finally:
            if "file_scan" in engine.config:
                if prev_scan_compressed is None:
                    engine.config["file_scan"].pop("scan_compressed", None)
                else:
                    engine.config["file_scan"]["scan_compressed"] = prev_scan_compressed
                if prev_use_content_type is None:
                    engine.config["file_scan"].pop("use_content_type", None)
                else:
                    engine.config["file_scan"]["use_content_type"] = (
                        prev_use_content_type
                    )
                if prev_scan_for_stego is None:
                    engine.config["file_scan"].pop("scan_for_stego", None)
                else:
                    engine.config["file_scan"]["scan_for_stego"] = prev_scan_for_stego
            if jh:
                engine.config.setdefault("report", {}).setdefault(
                    "jurisdiction_hints", {}
                )["enabled"] = prev_jurisdiction_hints_enabled
        from utils.notify import notify_scan_complete_background

        notify_scan_complete_background(engine.config, engine.db_manager, session_id)

    background_tasks.add_task(run_targets)
    _invalidate_sessions_cache()
    return {"status": "started", "session_id": session_id}


@app.post("/scan_pdf", responses=_RATE_LIMIT_429)
async def scan_pdf():
    """Pro+ tier gate for executive PDF export (Maestro licensing-matrix smoke)."""
    _raise_if_license_blocks_scan()
    _raise_if_feature_blocked("report_pdf")
    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "feature": "report_pdf"},
    )


@app.get("/status")
async def get_status(request: Request):
    """Return running, current_session_id, findings_count, and declarative ``audit_log`` (sampling posture)."""
    engine = _get_engine()
    runtime_trust = get_runtime_trust_snapshot(_get_config())
    cfg = _get_config()
    sec = load_integrity_secret_from_config(cfg)
    maturity_integrity = engine.db_manager.verify_maturity_assessment_integrity(sec)
    return {
        "running": engine.is_running,
        "current_session_id": engine.db_manager.current_session_id,
        "findings_count": engine.get_current_findings_count(),
        "audit_log": engine.get_scan_audit_log(),
        "forwarded_headers": forwarded_proto_posture(request, cfg),
        "runtime_trust": runtime_trust,
        "dashboard_transport": get_dashboard_transport_snapshot(),
        "enterprise_surface": get_enterprise_surface_posture(cfg),
        "maturity_assessment_integrity": maturity_integrity,
        "integrity": _integrity_snapshot(),
    }


@app.get("/report", responses=_NOT_FOUND_404)
async def download_report():
    """Download last generated report file (Excel)."""
    engine = _get_engine()
    path = engine.get_last_report_path()
    safe_path = _safe_report_output_path(path, engine) if path else None
    if not safe_path:
        # Try to generate from last session (avoid Path(raw_user_path) for CodeQL path-injection).
        sid = engine.db_manager.current_session_id
        if sid:
            path = engine.generate_final_reports(sid)
        else:
            sessions = engine.db_manager.list_sessions()
            if sessions:
                path = engine.generate_final_reports(sessions[0]["session_id"])
            else:
                path = None
        safe_path = _safe_report_output_path(path, engine) if path else None
    if safe_path:
        return FileResponse(
            safe_path,
            filename=safe_path.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    raise HTTPException(
        status_code=404, detail="Report not available. Run a scan first."
    )


@app.get("/heatmap", responses=_NOT_FOUND_404)
async def download_heatmap():
    """Download last generated heatmap PNG (sensitivity/risk heatmap for the most recent session)."""
    engine = _get_engine()
    resolved = _safe_report_path_for_heatmap(engine)
    if not resolved:
        raise HTTPException(
            status_code=404, detail="Heatmap not available. Run a scan first."
        )
    _, sid = resolved
    heatmap_resp = _heatmap_png_response(engine, sid)
    if heatmap_resp:
        return heatmap_resp
    raise HTTPException(
        status_code=404,
        detail="Heatmap not available. Run a scan first or ensure the report was generated.",
    )


@app.get("/list")
async def list_sessions_api(sort: str = "date_desc"):
    """List past scan sessions (session_id, timestamp, tenant_name, counts) for report recreation (JSON API). Query: sort=date_desc (newest first, default) or sort=date_asc (oldest first)."""
    sessions = _list_sessions_cached()
    if (sort or "").strip().lower() == "date_asc":
        sessions = list(reversed(sessions))
    return {"sessions": sessions}


# ---------------------------------------------------------------------------
# Findings export endpoints (JSON + CSV) — unified schema, async
# GET /findings               → last session findings as JSON
# GET /findings/csv           → last session findings as CSV download
# GET /findings/{session_id}  → specific session findings as JSON
# GET /findings/{session_id}/csv → specific session findings as CSV download
# ---------------------------------------------------------------------------

_FINDINGS_UNIFIED_FIELDS = [
    "id",
    "session_id",
    "source_type",
    "target_name",
    "path",
    "file_name",
    "data_type",
    "schema_name",
    "table_name",
    "column_name",
    "sensitivity_level",
    "pattern_detected",
    "norm_tag",
    "ml_confidence",
    "source_mtime_ns",
    "source_size",
    "content_fingerprint",
    "created_at",
]


_FINDINGS_CSV_MEDIA_TYPE = "text/csv; charset=utf-8"


def _findings_to_unified(
    db_findings: list[dict], fs_findings: list[dict]
) -> list[dict]:
    """Merge database + filesystem findings into the unified schema for export.

    Fields present only in one source type are filled with None in the other.
    ``source_type`` is added so consumers can distinguish origin.
    ``created_at`` is serialised to ISO-8601 string when it is a datetime object.
    """
    rows: list[dict] = []
    for f in db_findings:
        row = dict.fromkeys(_FINDINGS_UNIFIED_FIELDS)
        row.update(f)
        row["source_type"] = "database"
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
        rows.append({k: row.get(k) for k in _FINDINGS_UNIFIED_FIELDS})
    for f in fs_findings:
        row = dict.fromkeys(_FINDINGS_UNIFIED_FIELDS)
        row.update(f)
        row["source_type"] = "filesystem"
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
        rows.append({k: row.get(k) for k in _FINDINGS_UNIFIED_FIELDS})
    return rows


def _resolve_session_for_findings(engine, session_id: str | None) -> str | None:
    """Return the session_id to use for a findings export (explicit or latest)."""
    if session_id:
        _validate_session_id(session_id)
        return session_id
    sid = getattr(engine.db_manager, "current_session_id", None)
    if sid:
        return sid
    sessions = engine.db_manager.list_sessions()
    return sessions[0]["session_id"] if sessions else None


def _build_findings_csv(rows: list[dict]) -> str:
    """Serialise a list of unified finding dicts to a CSV string (UTF-8)."""
    import csv as _csv

    buf = io.StringIO()
    writer = _csv.DictWriter(
        buf,
        fieldnames=_FINDINGS_UNIFIED_FIELDS,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    if rows:
        writer.writerows(rows)
    return buf.getvalue()


@app.get("/findings", responses=_NOT_FOUND_404)
async def get_findings_latest():
    """Return all findings for the most recent scan session as a unified JSON array.

    Each item contains ``source_type`` (``database`` or ``filesystem``),
    common fields (``sensitivity_level``, ``pattern_detected``, ``norm_tag``,
    ``ml_confidence``) and source-specific fields (``path``/``file_name`` for
    filesystem; ``schema_name``/``table_name``/``column_name`` for database).
    Fields not applicable to a source type are ``null``.
    """
    engine = _get_engine()
    sid = _resolve_session_for_findings(engine, None)
    if not sid:
        raise HTTPException(status_code=404, detail="No scan sessions found.")
    db_f, fs_f, _ = engine.db_manager.get_findings(sid)
    rows = _findings_to_unified(db_f, fs_f)
    return {"session_id": sid, "count": len(rows), "findings": rows}


@app.get("/findings/csv", responses=_NOT_FOUND_404)
async def get_findings_latest_csv():
    """Download all findings for the most recent session as a UTF-8 CSV attachment."""
    engine = _get_engine()
    sid = _resolve_session_for_findings(engine, None)
    if not sid:
        raise HTTPException(status_code=404, detail="No scan sessions found.")
    db_f, fs_f, _ = engine.db_manager.get_findings(sid)
    rows = _findings_to_unified(db_f, fs_f)
    csv_content = _build_findings_csv(rows)
    safe_sid = re.sub(r"[^\w-]", "_", sid)[:64]
    filename = f"findings_{safe_sid}.csv"
    return StreamingResponse(
        iter([csv_content.encode("utf-8")]),
        media_type=_FINDINGS_CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/findings/{session_id}", responses=_SESSION_RESPONSES)
async def get_findings_by_session(session_id: str):
    """Return all findings for ``session_id`` as a unified JSON array.

    See ``GET /findings`` for the schema description.
    """
    _validate_session_id(session_id)
    engine = _get_engine()
    db_f, fs_f, _ = engine.db_manager.get_findings(session_id)
    if not db_f and not fs_f:
        raise HTTPException(
            status_code=404,
            detail=f"No findings for session {session_id}.",
        )
    rows = _findings_to_unified(db_f, fs_f)
    return {"session_id": session_id, "count": len(rows), "findings": rows}


@app.get("/findings/{session_id}/csv", responses=_SESSION_RESPONSES)
async def get_findings_by_session_csv(session_id: str):
    """Download all findings for ``session_id`` as a UTF-8 CSV attachment."""
    _validate_session_id(session_id)
    engine = _get_engine()
    db_f, fs_f, _ = engine.db_manager.get_findings(session_id)
    rows = _findings_to_unified(db_f, fs_f)
    csv_content = _build_findings_csv(rows)
    safe_sid = re.sub(r"[^\w-]", "_", session_id)[:64]
    filename = f"findings_{safe_sid}.csv"
    return StreamingResponse(
        iter([csv_content.encode("utf-8")]),
        media_type=_FINDINGS_CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class SessionTenantUpdate(BaseModel):
    """Body for PATCH /sessions/{session_id}: set tenant/customer name for a session."""

    tenant: str | None = None


class SessionTechnicianUpdate(BaseModel):
    """Body for PATCH /sessions/{session_id}/technician: set technician/operator name for a session."""

    technician: str | None = None


@app.patch("/sessions/{session_id}", responses=_SESSION_RESPONSES)
async def update_session_tenant(session_id: str, body: SessionTenantUpdate):
    """Set or clear the tenant/customer name for an existing scan session."""
    _validate_session_id(session_id)
    engine = _get_engine()
    sessions = [
        s
        for s in engine.db_manager.list_sessions()
        if s.get("session_id") == session_id
    ]
    if not sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    from core.validation import sanitize_tenant_technician

    tenant = sanitize_tenant_technician(body.tenant)
    engine.db_manager.update_session_tenant(session_id, tenant)
    _invalidate_sessions_cache()
    return {"session_id": session_id, "tenant": tenant}


@app.patch("/sessions/{session_id}/technician", responses=_SESSION_RESPONSES)
async def update_session_technician(session_id: str, body: SessionTechnicianUpdate):
    """Set or clear the technician/operator name for an existing scan session."""
    _validate_session_id(session_id)
    engine = _get_engine()
    sessions = [
        s
        for s in engine.db_manager.list_sessions()
        if s.get("session_id") == session_id
    ]
    if not sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    from core.validation import sanitize_tenant_technician

    technician = sanitize_tenant_technician(body.technician)
    engine.db_manager.update_session_technician(session_id, technician)
    _invalidate_sessions_cache()
    return {"session_id": session_id, "technician": technician}


@app.get("/reports/{session_id}", responses=_SESSION_RESPONSES)
async def download_report_by_session(session_id: str):
    """Regenerate and download Excel report for the given session_id."""
    _validate_session_id(session_id)
    engine = _get_engine()
    path = engine.generate_final_reports(session_id)
    if path:
        candidate = _safe_report_output_path(path, engine)
        if candidate is None:
            # Path is outside configured report directory or does not exist.
            raise HTTPException(
                status_code=403,
                detail="Report path is outside the configured report directory.",
            )
        return FileResponse(
            candidate,
            filename=candidate.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    raise HTTPException(
        status_code=404,
        detail=f"No data for session {session_id} or report generation failed.",
    )


@app.get("/heatmap/{session_id}", responses=_SESSION_RESPONSES)
async def download_heatmap_by_session(session_id: str):
    """Regenerate report (if needed) and download heatmap PNG for the given session_id."""
    _validate_session_id(session_id)
    engine = _get_engine()
    path = engine.generate_final_reports(session_id)
    if not path or _safe_report_output_path(path, engine) is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data for session {session_id} or report generation failed.",
        )
    # Heatmap file is resolved under config output_dir only; body response avoids FileResponse path sink.
    heatmap_resp = _heatmap_png_response(engine, session_id)
    if heatmap_resp:
        return heatmap_resp
    raise HTTPException(
        status_code=404,
        detail=f"Heatmap not available for session {session_id}. Run a scan and ensure findings exist.",
    )


@app.get("/logs", responses=_NOT_FOUND_404)
async def download_latest_log(request: Request):
    """
    Download the most recent audit_YYYYMMDD.log from the configured audit-log directory.
    """
    settings = _audit_logs_settings()
    if not settings.get("enabled"):
        raise HTTPException(status_code=403, detail="Audit log download is disabled.")
    roles = _authorize_audit_log_download(request)
    log_dir = _resolve_audit_logs_directory(settings)
    candidates = _audit_log_candidates(log_dir)
    if not candidates:
        raise HTTPException(status_code=404, detail="No log files found.")
    latest = candidates[0]
    _emit_audit_log_download_event(
        request,
        filename=latest.name,
        session_id=None,
        roles=roles,
    )
    return _audit_log_file_response(latest)


@app.get("/logs/{session_id}", responses=_SESSION_RESPONSES)
async def download_log_for_session(session_id: str, request: Request):
    """
    Download audit log for session_id.

    Lookup order:
    1) first audit_YYYYMMDD.log containing the explicit session_id text;
    2) fallback to audit_YYYYMMDD.log derived from the session UTC day suffix.
    """
    _validate_session_id(session_id)
    settings = _audit_logs_settings()
    if not settings.get("enabled"):
        raise HTTPException(status_code=403, detail="Audit log download is disabled.")
    roles = _authorize_audit_log_download(request)
    log_dir = _resolve_audit_logs_directory(settings)
    candidates = _audit_log_candidates(log_dir)
    if not candidates:
        raise HTTPException(status_code=404, detail="No log files found.")
    for p in candidates:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if session_id in text:
            _emit_audit_log_download_event(
                request,
                filename=p.name,
                session_id=session_id,
                roles=roles,
            )
            return _audit_log_file_response(p)
    by_day = _date_fallback_log_for_session(log_dir, session_id)
    if by_day is not None:
        _emit_audit_log_download_event(
            request,
            filename=by_day.name,
            session_id=session_id,
            roles=roles,
        )
        return _audit_log_file_response(by_day)
    raise HTTPException(
        status_code=404, detail=f"No log file contains session_id {session_id}."
    )


def _normalized_db_driver(value: str | None) -> str:
    return (str(value or "").split("+")[0]).strip().lower()


def _scan_database_matches_configured_target(request_body: DatabaseConfig) -> bool:
    """
    True when POST /scan_database payload exactly matches a configured DB target.

    Matching fields: name, driver family, host, port, user, password, database.
    """
    cfg = _get_config()
    targets = cfg.get("targets") if isinstance(cfg.get("targets"), list) else []
    for target in targets:
        if not isinstance(target, dict):
            continue
        if str(target.get("type") or "").strip().lower() != "database":
            continue
        if str(target.get("name") or "").strip() != request_body.name:
            continue
        if _normalized_db_driver(target.get("driver")) != _normalized_db_driver(
            request_body.driver
        ):
            continue
        if (
            str(target.get("host") or "").strip().lower()
            != request_body.host.strip().lower()
        ):
            continue
        try:
            target_port = int(target.get("port"))
        except (TypeError, ValueError):
            continue
        if target_port != int(request_body.port):
            continue
        if str(target.get("user") or "").strip() != request_body.user:
            continue
        target_password = str(
            target.get("pass") or target.get("password") or ""
        ).strip()
        if target_password != request_body.password:
            continue
        if str(target.get("database") or "").strip() != request_body.database:
            continue
        return True
    return False


@app.post("/scan_database", responses=_RATE_LIMIT_429)
async def scan_database(config: DatabaseConfig, background_tasks: BackgroundTasks):
    """One-off scan of a single database (body: name, host, port, user, password, database, optional driver). Starts in background; returns session_id."""
    _raise_if_license_blocks_scan()
    driver_key = (config.driver or "").split("+")[0].strip().lower()
    if driver_key == "snowflake":
        _raise_if_feature_blocked("connector_snowflake")
    engine = _get_engine()
    if engine.is_running:
        raise HTTPException(status_code=409, detail="Audit already in progress.")
    # Apply same rate limiting as for full scans
    _check_rate_limit(source="scan_database")
    api_cfg = (
        _get_config().get("api") if isinstance(_get_config().get("api"), dict) else {}
    )
    if not bool(api_cfg.get("allow_adhoc_targets", False)):
        if not _scan_database_matches_configured_target(config):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Ad-hoc scan_database target is disabled. "
                    "Set api.allow_adhoc_targets: true or use a pre-configured target."
                ),
            )
    target = {
        "name": config.name,
        "type": "database",
        "driver": config.driver,
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "pass": config.password,
        "database": config.database,
    }
    from core.session import new_session_id
    from core.validation import sanitize_tenant_technician

    session_id = new_session_id()
    tenant = sanitize_tenant_technician(config.tenant)
    technician = sanitize_tenant_technician(config.technician)
    jh_db = bool(config.jurisdiction_hint)
    _rep_prev = engine.config.get("report") or {}
    _jh_prev = _rep_prev.get("jurisdiction_hints")
    prev_jurisdiction_hints_enabled_db = (
        bool(_jh_prev.get("enabled")) if isinstance(_jh_prev, dict) else False
    )
    if jh_db:
        engine.config.setdefault("report", {}).setdefault("jurisdiction_hints", {})
        engine.config["report"]["jurisdiction_hints"]["enabled"] = True
    engine.db_manager.set_current_session_id(session_id)
    engine.db_manager.create_session_record(
        session_id,
        tenant_name=tenant,
        technician_name=technician,
        jurisdiction_hint=jh_db,
    )

    def run_one_target():
        engine._is_running = True
        try:
            engine._run_target(target)
        finally:
            engine._is_running = False
            engine.db_manager.finish_session(session_id, "completed")
            if jh_db:
                engine.config.setdefault("report", {}).setdefault(
                    "jurisdiction_hints", {}
                )["enabled"] = prev_jurisdiction_hints_enabled_db
        from utils.notify import notify_scan_complete_background

        notify_scan_complete_background(engine.config, engine.db_manager, session_id)

    background_tasks.add_task(run_one_target)
    _invalidate_sessions_cache()
    return {"status": "started", "session_id": session_id}


# --- Dashboard HTML (locale-prefixed). Registered after API routes so /status, /list, … are not
# captured by /{locale_slug}.


@app.get("/{locale_slug}/help", response_class=HTMLResponse)
async def help_page(request: Request, locale_slug: LocaleSlug):
    """Help and documentation page: quickstart, config example, links to README/USAGE docs."""
    tag = _locale_tag_from_slug(locale_slug.value)
    home = Path.home()
    return templates.TemplateResponse(
        request=request,
        name="help.html",
        context=_i18n_template_context(
            request,
            locale_slug.value,
            tag,
            {
                "prog": _display_prog(),
                "home_example": str(home),
                "home_docs_example": str(home / "Documents" / "LGPD"),
            },
        ),
    )


@app.get("/{locale_slug}/about", response_class=HTMLResponse)
async def about_page(request: Request, locale_slug: LocaleSlug):
    """About: application name, version, author and license (same as established in the project LICENSE)."""
    tag = _locale_tag_from_slug(locale_slug.value)
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context=_i18n_template_context(
            request,
            locale_slug.value,
            tag,
            {"about": _about_info(), "license": _license_public_dict()},
        ),
    )


@app.get("/{locale_slug}/login", response_class=HTMLResponse)
async def webauthn_login_page(request: Request, locale_slug: LocaleSlug):
    """Browser WebAuthn sign-in / passkey registration (Phase 1b). Public when HTML gate is off; with gate on, always reachable (see middleware)."""
    tag = _locale_tag_from_slug(locale_slug.value)
    fb = f"/{locale_slug.value}/"
    next_path = safe_next_path(request.query_params.get("next"), fb)
    ctx = {
        "login_next": next_path,
        "webauthn_enabled": webauthn_block(_get_config()) is not None,
    }
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=_i18n_template_context(request, locale_slug.value, tag, ctx),
    )


@app.get("/{locale_slug}", response_class=HTMLResponse)
async def dashboard_locale_root_redirect(locale_slug: LocaleSlug):
    """Normalize /en -> /en/ for the dashboard."""
    return RedirectResponse(url=f"/{locale_slug.value}/", status_code=302)


@app.get("/{locale_slug}/", response_class=HTMLResponse)
async def dashboard(request: Request, locale_slug: LocaleSlug):
    """Dashboard: scan status, discovery stats, progress chart, recent sessions, start scan."""
    tag = _locale_tag_from_slug(locale_slug.value)
    engine = _get_engine()
    status = {
        "running": engine.is_running,
        "current_session_id": engine.db_manager.current_session_id,
        "findings_count": engine.get_current_findings_count(),
    }
    sessions = _list_sessions_cached()
    last_session = sessions[0] if sessions else None
    chart_data = _build_chart_data(sessions)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=_i18n_template_context(
            request,
            locale_slug.value,
            tag,
            {
                "status": status,
                "sessions": sessions,
                "last_session": last_session,
                "chart_data": chart_data,
                "about": _about_info(),
                "license": _license_public_dict(),
            },
        ),
    )


@app.get("/{locale_slug}/config", response_class=HTMLResponse)
async def config_page(request: Request, locale_slug: LocaleSlug):
    """Configuration editor (YAML). Secret values are redacted so the UI never displays them. Query: saved=1 or error=... for feedback after POST."""
    tag = _locale_tag_from_slug(locale_slug.value)
    saved = request.query_params.get("saved") == "1"
    error = request.query_params.get("error")
    cfg_ctx = {
        "config_path": _get_config_path(),
        "config_yaml": _get_config_yaml_for_display(),
        "config_saved": saved,
        "config_save_error": error,
    }
    cfg_ctx.update(csrf_context_for_request(request))
    return templates.TemplateResponse(
        request=request,
        name=_TEMPLATE_CONFIG,
        context=_i18n_template_context(request, locale_slug.value, tag, cfg_ctx),
    )


@app.post("/{locale_slug}/config", response_class=HTMLResponse)
async def config_save(request: Request, locale_slug: LocaleSlug):
    """Save configuration (form body: yaml=...). Redirects back to GET .../config with success or error."""
    tag = _locale_tag_from_slug(locale_slug.value)
    ls = locale_slug.value
    form = await request.form()
    verify_html_form_csrf_or_raise(request, form)
    yaml_content = form.get("yaml", "")
    if not yaml_content:
        t_call = make_t(
            tag,
            (_get_config().get("locale") or {}).get("supported_locales")
            or ["en", "pt-BR"],
            (_get_config().get("locale") or {}).get("default_locale") or "en",
            {},
        )
        err_ctx = {
            "config_path": _get_config_path(),
            "config_yaml": _get_config_yaml_for_display(),
            "config_saved": False,
            "config_save_error": t_call("config.no_yaml_error"),
        }
        err_ctx.update(csrf_context_for_request(request))
        return templates.TemplateResponse(
            request=request,
            name=_TEMPLATE_CONFIG,
            context=_i18n_template_context(request, ls, tag, err_ctx),
        )
    try:
        _merge_and_save_config_yaml(yaml_content)
        return RedirectResponse(url=f"/{ls}/config?saved=1", status_code=303)
    except ValueError as e:
        from core.validation import clean_error

        ve_ctx = {
            "config_path": _get_config_path(),
            "config_yaml": yaml_content,
            "config_saved": False,
            "config_save_error": clean_error(e),
        }
        ve_ctx.update(csrf_context_for_request(request))
        return templates.TemplateResponse(
            request=request,
            name=_TEMPLATE_CONFIG,
            context=_i18n_template_context(request, ls, tag, ve_ctx),
        )


@app.get("/{locale_slug}/assessment", response_class=HTMLResponse)
async def maturity_self_assessment_placeholder(
    request: Request, locale_slug: LocaleSlug
):
    """Optional POC: organizational self-assessment placeholder (gated; no bundled questionnaire text)."""
    cfg = _get_config()
    if not _maturity_self_assessment_poc_allowed(cfg):
        raise HTTPException(status_code=404, detail="Not found")
    tag = _locale_tag_from_slug(locale_slug.value)
    pack = _get_maturity_pack_cached(cfg)
    pack_sections: list[dict] | None = None
    pack_version = 1
    if pack is not None:
        pack_version = int(pack.version)
        pack_sections = [
            {
                "id": s.id,
                "title": s.title,
                "questions": [{"id": q.id, "prompt": q.prompt} for q in s.questions],
            }
            for s in pack.sections
        ]
    eng = _get_engine()
    assessment_batch_history = _assessment_batch_history_for_template(eng.db_manager)
    saved = (request.query_params.get("saved") or "").strip() == "1"
    batch_q = (request.query_params.get("batch") or "").strip()
    assessment_summary: dict | None = None
    if saved and batch_q and _valid_maturity_assessment_batch_id(batch_q):
        rows = eng.db_manager.maturity_assessment_rows_for_integrity_batch(batch_q)
        sec = load_integrity_secret_from_config(cfg)
        integrity = verify_maturity_assessment_rows(secret=sec, rows=rows)
        score_dict: dict[str, object] | None = None
        if pack is not None and rows:
            rubric = score_for_export(pack, rows)
            score_dict = rubric_result_to_summary_dict(rubric)
        assessment_summary = {
            "answer_count": len(rows),
            "integrity": integrity,
            "batch_id": batch_q,
            "score": score_dict,
        }
    assess_ctx = {
        "maturity_pack_sections": pack_sections,
        "assessment_batch_id": secrets.token_hex(16),
        "maturity_pack_version": pack_version,
        "assessment_saved": saved,
        "assessment_summary": assessment_summary,
        "assessment_batch_history": assessment_batch_history,
    }
    assess_ctx.update(csrf_context_for_request(request))
    return templates.TemplateResponse(
        request=request,
        name="assessment_placeholder.html",
        context=_i18n_template_context(
            request,
            locale_slug.value,
            tag,
            assess_ctx,
        ),
    )


@app.post("/{locale_slug}/assessment")
async def maturity_self_assessment_submit(request: Request, locale_slug: LocaleSlug):
    """Persist assessment answers to SQLite when a YAML pack is configured (POC)."""
    cfg = _get_config()
    if not _maturity_self_assessment_poc_allowed(cfg):
        raise HTTPException(status_code=404, detail="Not found")
    valid_ids = _maturity_pack_question_ids(cfg)
    if not valid_ids:
        raise HTTPException(
            status_code=400,
            detail="No maturity pack configured (api.maturity_assessment_pack_path)",
        )
    form = await request.form()
    verify_html_form_csrf_or_raise(request, form)
    batch_id = str(form.get("assessment_batch_id") or "").strip()
    if not _valid_maturity_assessment_batch_id(batch_id):
        raise HTTPException(status_code=400, detail="Invalid assessment_batch_id")
    pack = _get_maturity_pack_cached(cfg)
    pack_version = int(pack.version) if pack is not None else 1
    answers: dict[str, str] = {}
    prefix = "answer__"
    for k, v in form.multi_items():
        if not isinstance(k, str) or not k.startswith(prefix):
            continue
        qid = k[len(prefix) :].strip()
        if qid not in valid_ids:
            continue
        answers[qid] = str(v).strip()[:4000]
    eng = _get_engine()
    sec = load_integrity_secret_from_config(cfg)
    eng.db_manager.save_maturity_assessment_answers(
        batch_id=batch_id,
        locale_slug=locale_slug.value,
        pack_version=pack_version,
        answers=answers,
        integrity_secret=sec,
    )
    slug = locale_slug.value
    batch_enc = quote(batch_id, safe="")
    return RedirectResponse(
        url=f"/{slug}/assessment?saved=1&batch={batch_enc}",
        status_code=303,
    )


@app.get("/{locale_slug}/assessment/export")
async def maturity_assessment_export(
    locale_slug: LocaleSlug,
    batch: str = Query(..., min_length=1, max_length=64),
    export_format: AssessmentExportFormat = Query(
        AssessmentExportFormat.csv, alias="format"
    ),
):
    """
    Download CSV or Markdown for one submit batch (same POC gate as GET /assessment).

    This is an **HTTP attachment** response (``Content-Disposition: attachment``), not a
    server-side path under ``report.output_dir``. When ``api.require_api_key`` is true, use
    ``X-API-Key`` or ``Authorization: Bearer`` like other dashboard routes.
    """
    del locale_slug  # locale reserved for future localized filenames / parity with UI
    cfg = _get_config()
    if not _maturity_self_assessment_poc_allowed(cfg):
        raise HTTPException(status_code=404, detail="Not found")
    if not _valid_maturity_assessment_batch_id(batch):
        raise HTTPException(status_code=404, detail="Not found")
    pack = _get_maturity_pack_cached(cfg)
    if pack is None:
        raise HTTPException(status_code=404, detail="Not found")
    eng = _get_engine()
    rows = eng.db_manager.maturity_assessment_rows_for_integrity_batch(batch)
    if not rows:
        raise HTTPException(status_code=404, detail="Not found")
    score = score_for_export(pack, rows)
    if export_format == AssessmentExportFormat.csv:
        body = render_maturity_export_csv(pack=pack, batch_id=batch, score=score)
        media = "text/csv; charset=utf-8"
        ext = "csv"
    else:
        body = render_maturity_export_markdown(pack=pack, batch_id=batch, score=score)
        media = "text/markdown; charset=utf-8"
        ext = "md"
    safe_batch = batch[:24] if len(batch) > 24 else batch
    filename = f"maturity_assessment_{safe_batch}.{ext}"
    return Response(
        content=body.encode("utf-8"),
        media_type=media,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@app.get("/{locale_slug}/reports", response_class=HTMLResponse)
async def reports_page(request: Request, locale_slug: LocaleSlug):
    """Reports list page with download links. Query: sort=date_desc (newest first, default) or sort=date_asc (oldest first)."""
    tag = _locale_tag_from_slug(locale_slug.value)
    sessions = _list_sessions_cached()
    sort = (request.query_params.get("sort") or "date_desc").strip().lower()
    if sort == "date_asc":
        sessions = list(reversed(sessions))
        sort = "date_asc"
    else:
        sort = "date_desc"
    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context=_i18n_template_context(
            request,
            locale_slug.value,
            tag,
            {"sessions": sessions, "sort": sort, "about": _about_info()},
        ),
    )


register_webauthn_routes(app)

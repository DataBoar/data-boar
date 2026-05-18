"""
Unified configuration loader for the LGPD/GDPR/CCPA audit application.
Loads YAML or JSON config; validates required keys; returns normalized dict.
Used by both CLI (main.py) and API.

Encoding: config file is read with auto-detection (UTF-8, UTF-8-sig, cp1252, latin_1)
so it works in multilingual and legacy Windows environments. Pattern files
(regex_overrides_file, ml_patterns_file, dl_patterns_file) use the optional
pattern_files_encoding key (default utf-8) with errors=replace to avoid crashes.
"""

import logging
import warnings
from pathlib import Path
from typing import Any

import yaml

from config.scan_defaults import clamp_file_sample_max_chars
from utils.audit_log_display import assign_unique_audit_log_names
from utils.file_encoding import read_text_auto_encoding

# Optional JSON support without requiring top-level json for YAML-first flow
try:
    import json
except ImportError:
    json = None

import os

_logger = logging.getLogger(__name__)


def _warn_if_env_from_key_unset_or_empty(
    env_var_name: str, config_descriptor: str
) -> None:
    """
    Emit UserWarning when a config *_from_env key is set but the env var is missing or blank.

    Operators still get non-fatal fallback to inline ``pass``, ``user``, ``token``, etc. (issue #508).
    """
    if (os.environ.get(env_var_name) or "").strip():
        return
    warnings.warn(
        (
            f"Environment variable {env_var_name!r} is unset or empty; "
            f"{config_descriptor} falls back to inline or default values when present."
        ),
        UserWarning,
        stacklevel=3,
    )


def _notification_env_value(val: Any) -> str | None:
    """
    Resolve optional notification secrets: inline string or ${ENV_VAR} from the environment.
    """
    if val is None:
        return None
    if not isinstance(val, str):
        return None
    t = val.strip()
    if not t:
        return None
    if t.startswith("${") and t.endswith("}"):
        var = t[2:-1].strip()
        return (os.environ.get(var) or "").strip() or None
    return t


def _normalize_sql_sampling(raw: Any) -> dict[str, Any]:
    """
    Optional ``sql_sampling`` block: hierarchical ``sample_limit`` overrides for SQL targets.

    Shape::

        sql_sampling:
          overrides:
            targets:
              <target_name>:
                sample_limit: 5
                tables:
                  "schema.table": 50
                  bare_table: 20
            patterns:
              "*_audit": 100
    """
    if not isinstance(raw, dict):
        return {"overrides": {"targets": {}, "patterns": {}}}
    ov = raw.get("overrides") or {}
    if not isinstance(ov, dict):
        return {"overrides": {"targets": {}, "patterns": {}}}
    targets_raw = ov.get("targets") or {}
    if not isinstance(targets_raw, dict):
        targets_raw = {}
    patterns_raw = ov.get("patterns") or {}
    if not isinstance(patterns_raw, dict):
        patterns_raw = {}

    def _lim(val: Any) -> int | None:
        try:
            n = int(val)
        except (TypeError, ValueError):
            return None
        if n < 1:
            return None
        return min(n, 10_000)

    targets_norm: dict[str, dict[str, Any]] = {}
    for tname, tcfg in targets_raw.items():
        if not isinstance(tcfg, dict):
            continue
        name = str(tname).strip()
        if not name:
            continue
        entry: dict[str, Any] = {}
        sl = _lim(tcfg.get("sample_limit"))
        if sl is not None:
            entry["sample_limit"] = sl
        tbls = tcfg.get("tables") or {}
        if isinstance(tbls, dict):
            te: dict[str, int] = {}
            for k, v in tbls.items():
                key = str(k).strip()
                if not key:
                    continue
                lim = _lim(v)
                if lim is not None:
                    te[key] = lim
            if te:
                entry["tables"] = te
        if entry:
            targets_norm[name] = entry

    patterns_norm: dict[str, int] = {}
    for pat, v in patterns_raw.items():
        p = str(pat).strip()
        if not p:
            continue
        lim = _lim(v)
        if lim is not None:
            patterns_norm[p] = lim

    return {"overrides": {"targets": targets_norm, "patterns": patterns_norm}}


def _resolve_path_relative_to_config(base_dir: Path, rel: str) -> Path:
    """Resolve a config-relative path; reject ``..`` escapes for relative paths."""
    raw = Path(rel.strip())
    if raw.is_absolute():
        return raw.resolve()
    combined = (base_dir / raw).resolve()
    try:
        combined.relative_to(base_dir.resolve())
    except ValueError as e:
        raise ValueError(f"sql_sampling path escapes config directory: {rel!r}") from e
    return combined


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    text = read_text_auto_encoding(path)
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        loaded = yaml.safe_load(text)
    elif suffix == ".json":
        if json is None:
            raise RuntimeError("JSON fragment requires stdlib json")
        loaded = json.loads(text)
    else:
        raise ValueError(f"Unsupported sql_sampling fragment format: {path}")
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"sql_sampling fragment must be a mapping: {path}")
    return loaded


def _extract_sql_sampling_fragment(root: dict[str, Any]) -> dict[str, Any]:
    """Accept ``sql_sampling:`` wrapper or bare ``overrides:`` at file root."""
    if "sql_sampling" in root and isinstance(root["sql_sampling"], dict):
        return dict(root["sql_sampling"])
    if "overrides" in root and isinstance(root["overrides"], dict):
        return {"overrides": dict(root["overrides"])}
    return {}


def _merge_target_override_blocks(
    base: dict[str, Any], overlay: dict[str, Any]
) -> dict[str, Any]:
    """Deep-merge one target overrides block; ``overlay`` wins on conflicts."""
    out = dict(base)
    for k, v in overlay.items():
        if k == "tables" and isinstance(v, dict):
            prev = out.get("tables")
            if isinstance(prev, dict):
                out["tables"] = {**prev, **v}
            else:
                out["tables"] = dict(v)
        else:
            out[k] = v
    return out


def _deep_merge_sql_sampling_blocks(
    base: dict[str, Any], overlay: dict[str, Any]
) -> dict[str, Any]:
    """Merge two raw ``sql_sampling`` dicts (pre-``_normalize_sql_sampling``); ``overlay`` wins."""
    if not base:
        return dict(overlay) if overlay else {}
    if not overlay:
        return dict(base)
    bo = base.get("overrides") or {}
    oo = overlay.get("overrides") or {}
    if not isinstance(bo, dict):
        bo = {}
    if not isinstance(oo, dict):
        oo = {}
    bt = bo.get("targets") or {}
    ot = oo.get("targets") or {}
    if not isinstance(bt, dict):
        bt = {}
    if not isinstance(ot, dict):
        ot = {}
    merged_targets: dict[str, Any] = dict(bt)
    for name, tcfg in ot.items():
        if not isinstance(tcfg, dict):
            merged_targets[name] = tcfg
            continue
        if name in merged_targets and isinstance(merged_targets[name], dict):
            merged_targets[name] = _merge_target_override_blocks(
                merged_targets[name], tcfg
            )
        else:
            merged_targets[name] = dict(tcfg)
    bp = bo.get("patterns") or {}
    op = oo.get("patterns") or {}
    if not isinstance(bp, dict):
        bp = {}
    if not isinstance(op, dict):
        op = {}
    merged_patterns = {**bp, **op}
    return {"overrides": {"targets": merged_targets, "patterns": merged_patterns}}


def _merge_sql_sampling_from_files(data: dict[str, Any], config_path: Path) -> None:
    """
    Merge optional ``sql_sampling_file`` / ``sql_sampling_files`` fragments into ``data['sql_sampling']``.

    Later sources win: files in order, then inline ``sql_sampling`` in the root config.
    Mutates ``data`` in place.
    """
    paths: list[str] = []
    s1 = data.get("sql_sampling_file")
    if isinstance(s1, str) and s1.strip():
        paths.append(s1.strip())
    s2 = data.get("sql_sampling_files")
    if isinstance(s2, list):
        for x in s2:
            if isinstance(x, str) and x.strip():
                paths.append(x.strip())
    if not paths:
        return
    base_dir = config_path.parent
    merged: dict[str, Any] = {}
    for rel in paths:
        frag_path = _resolve_path_relative_to_config(base_dir, rel)
        frag_root = _load_yaml_mapping(frag_path)
        block = _extract_sql_sampling_fragment(frag_root)
        if block:
            merged = _deep_merge_sql_sampling_blocks(merged, block)
    existing = data.get("sql_sampling")
    if isinstance(existing, dict) and existing:
        data["sql_sampling"] = _deep_merge_sql_sampling_blocks(merged, existing)
    elif merged:
        data["sql_sampling"] = merged


def _normalize_operator_channel_block(d: dict[str, Any]) -> dict[str, Any]:
    """One webhook target: Slack, Teams, Telegram pair, or generic URL."""
    return {
        "generic_webhook_url": _notification_env_value(d.get("generic_webhook_url")),
        "slack_webhook_url": _notification_env_value(d.get("slack_webhook_url")),
        "teams_webhook_url": _notification_env_value(d.get("teams_webhook_url")),
        "telegram_bot_token": _notification_env_value(d.get("telegram_bot_token")),
        "telegram_chat_id": _notification_env_value(d.get("telegram_chat_id")),
    }


def load_config(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from a YAML or JSON file.
    Supports unified schema: targets[], file_scan, report, api, sqlite_path, scan, ml_patterns_file, dl_patterns_file, regex_overrides_file, sensitivity_detection, learned_patterns, optional sql_sampling_file / sql_sampling_files (YAML fragments merged into sql_sampling before normalize).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = read_text_auto_encoding(path)
    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        data = yaml.safe_load(raw)
    elif suffix == ".json":
        if json is None:
            raise RuntimeError("JSON config requires stdlib json")
        data = json.loads(raw)
    else:
        raise ValueError(f"Unsupported config format: {suffix}. Use .yaml or .json")

    if not isinstance(data, dict):
        raise ValueError("Config root must be a dict")

    return normalize_config(data, config_path=path)


def normalize_config(
    data: dict[str, Any], *, config_path: str | Path | None = None
) -> dict[str, Any]:
    """
    Normalize config to unified schema. Accepts legacy shapes (e.g. databases[] from config.json).

    When ``config_path`` is set, optional ``sql_sampling_file`` / ``sql_sampling_files`` entries
    are loaded relative to that file's directory and merged into ``sql_sampling`` (inline wins).

    Emits a logging WARNING (and stderr via default/lastResort handlers) when the obsolete
    ``scan_scope:`` key is detected (produces no targets). The canonical key is ``targets:``
    — see workspace fact in AGENTS.md.
    """
    if "scan_scope" in data:
        _logger.warning(
            "[data-boar] config key 'scan_scope:' is obsolete and will be ignored. "
            "Use 'targets:' instead. See docs/USAGE.md for the canonical config format."
        )

    if not isinstance(data, dict):
        raise ValueError("Config root must be a dict")
    data = dict(data)
    if config_path is not None:
        _merge_sql_sampling_from_files(data, Path(config_path))

    out: dict[str, Any] = {}

    # Targets: prefer 'targets'; fallback: build from 'databases' + file_scan
    if "targets" in data:
        out["targets"] = list(data["targets"])
    else:
        out["targets"] = []
        for db in data.get("databases", []):
            out["targets"].append(
                {
                    "name": db.get("name", "unknown"),
                    "type": "database",
                    "driver": db.get("driver", "postgresql+psycopg2"),
                    "host": db.get("host", "localhost"),
                    "port": int(db.get("port", 5432)),
                    "user": db.get("user", ""),
                    "pass": db.get("password", db.get("pass", "")),
                    "database": db.get("database", ""),
                }
            )
        fs = data.get("file_scan", {})
        for directory in fs.get("directories", []):
            out["targets"].append(
                {
                    "name": Path(directory).name or "filesystem",
                    "type": "filesystem",
                    "path": directory,
                    "recursive": fs.get("recursive", True),
                }
            )

    # File scan defaults: all compatible extensions when not specified (see connectors.filesystem_connector.SUPPORTED_EXTENSIONS)
    def _normalize_file_passwords(pw: Any) -> dict[str, str]:
        """Normalize file_passwords to dict mapping extension or 'default' to password string. Used for password-protected PDF/ZIP/PPTX."""
        if not pw or not isinstance(pw, dict):
            return {}
        out: dict[str, str] = {}
        for k, v in pw.items():
            if v is None or not isinstance(v, str):
                continue
            key = (k or "").strip().lower()
            if key == "default":
                out["default"] = v
            elif key.startswith("."):
                out[key] = v
            else:
                out[f".{key}"] = v
        return out

    # Per-archive inner size cap: valid range 1 MB–500 MB; invalid/missing -> None.
    _MIN_MAX_INNER = 1_000_000
    _MAX_MAX_INNER = 500_000_000

    def _normalize_max_inner_size(val: Any) -> int | None:
        if val is None:
            return None
        try:
            n = int(val)
        except (TypeError, ValueError):
            return None
        if n < _MIN_MAX_INNER:
            return _MIN_MAX_INNER
        if n > _MAX_MAX_INNER:
            return _MAX_MAX_INNER
        return n

    _default_extensions = [
        ".txt",
        ".csv",
        ".pdf",
        ".doc",
        ".docx",
        ".odt",
        ".ods",
        ".odp",
        ".xls",
        ".xlsx",
        ".xlsm",
        ".ppt",
        ".pptx",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".json",
        ".jsonl",
        ".xml",
        ".html",
        ".htm",
        ".md",
        ".yml",
        ".yaml",
        ".log",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".sql",
        ".rtf",
        ".eml",
        ".msg",
        ".tex",
        ".bib",
        ".srt",
        ".vtt",
        ".ass",
        ".ssa",
        ".epub",
        ".parquet",
        ".feather",
        ".orc",
        ".avro",
        ".dbf",
    ]
    fs_cfg = data.get("file_scan", {}) or {}
    out["file_scan"] = {
        "extensions": fs_cfg.get("extensions", _default_extensions),
        "recursive": fs_cfg.get("recursive", True),
        "scan_sqlite_as_db": fs_cfg.get("scan_sqlite_as_db", True),
        "sample_limit": fs_cfg.get("sample_limit", 5),
        # Max UTF-8 characters read per plain-text file (.txt, .md, …) on filesystem/shares.
        # Separate from sample_limit (rows / TOPN for DBs and Power BI / Dataverse).
        "file_sample_max_chars": clamp_file_sample_max_chars(
            fs_cfg.get("file_sample_max_chars")
        ),
        # Optional: scan inside compressed files (zip, tar, gz, bz2, xz, 7z, …)
        # This flag is deliberately conservative: default False so existing configs
        # keep current behaviour until explicitly opted-in.
        "scan_compressed": bool(fs_cfg.get("scan_compressed", False)),
        # Optional: per-archive inner-bytes safety cap (bytes). Valid range 1 MB–500 MB;
        # invalid or missing -> None (connector uses default).
        "max_inner_size": _normalize_max_inner_size(
            fs_cfg.get("max_inner_size") or fs_cfg.get("scan_compressed_max_inner_size")
        ),
        # Optional: restrict which archive types to open; if omitted, engine/connector
        # will use a sensible default Tier 1 + Tier 2 list (see PLAN_COMPRESSED_FILES.md).
        "compressed_extensions": fs_cfg.get("compressed_extensions"),
        "file_passwords": _normalize_file_passwords(fs_cfg.get("file_passwords")),
        # Optional: magic-byte inference for renamed/cloaked files (PDF + rich media)
        # when filesystem/share connectors enable it. See docs/USAGE.md.
        "use_content_type": bool(fs_cfg.get("use_content_type", False)),
        # Rich media: optional EXIF / ID3 / ffprobe metadata and optional image OCR (see docs/USAGE.md).
        "scan_rich_media_metadata": bool(fs_cfg.get("scan_rich_media_metadata", False)),
        "scan_image_ocr": bool(fs_cfg.get("scan_image_ocr", False)),
        "ocr_lang": str(fs_cfg.get("ocr_lang") or "eng").strip() or "eng",
    }
    try:
        _ocr_md = int(fs_cfg.get("ocr_max_dimension", 2000))
    except (TypeError, ValueError):
        _ocr_md = 2000
    out["file_scan"]["ocr_max_dimension"] = max(256, min(8000, _ocr_md))
    out["file_scan"]["scan_for_stego"] = bool(fs_cfg.get("scan_for_stego", False))
    # Normalize extensions to list of suffixes (e.g. "*.pdf" -> ".pdf")
    exts = out["file_scan"]["extensions"]
    out["file_scan"]["extensions"] = [
        e if e.startswith(".") else f".{e.lstrip('*')}" for e in exts
    ]

    out["sql_sampling"] = _normalize_sql_sampling(data.get("sql_sampling"))

    # Resolve credential-from-env for targets (Phase A: secrets in env, not in config)
    for t in out.get("targets") or []:
        if not isinstance(t, dict):
            continue
        env_pass_key = (
            t.get("pass_from_env") or t.get("password_from_env") or ""
        ).strip()
        if env_pass_key:
            _warn_if_env_from_key_unset_or_empty(
                env_pass_key,
                ("pass_from_env" if t.get("pass_from_env") else "password_from_env"),
            )
            t["pass"] = (
                (os.environ.get(env_pass_key) or "").strip()
                or t.get("pass")
                or t.get("password")
                or ""
            )
        env_user_key = (t.get("user_from_env") or "").strip()
        if env_user_key:
            _warn_if_env_from_key_unset_or_empty(env_user_key, "user_from_env")
            t["user"] = (
                (os.environ.get(env_user_key) or "").strip()
                or t.get("user")
                or t.get("username")
                or ""
            )
        auth = t.get("auth")
        if isinstance(auth, dict):
            token_env = (auth.get("token_from_env") or "").strip()
            if token_env:
                _warn_if_env_from_key_unset_or_empty(token_env, "auth.token_from_env")
                auth["token"] = (
                    (os.environ.get(token_env) or "").strip() or auth.get("token") or ""
                )
            cs_env = (auth.get("client_secret_from_env") or "").strip()
            if cs_env:
                _warn_if_env_from_key_unset_or_empty(
                    cs_env, "auth.client_secret_from_env"
                )
                auth["client_secret"] = (
                    (os.environ.get(cs_env) or "").strip()
                    or auth.get("client_secret")
                    or ""
                )
        env_cs_key = (t.get("client_secret_from_env") or "").strip()
        if env_cs_key:
            _warn_if_env_from_key_unset_or_empty(env_cs_key, "client_secret_from_env")
            t["client_secret"] = (
                (os.environ.get(env_cs_key) or "").strip()
                or t.get("client_secret")
                or ""
            )

    # Detection: configuration toggles for detector behaviour (regex/ML/DL options)
    det_cfg = data.get("detection", {}) or {}
    # CNPJ alphanumeric: when true, the detector keeps LGPD_CNPJ_ALNUM active as a built-in pattern.
    # When false or omitted, only the legacy numeric LGPD_CNPJ pattern is used unless re-enabled via
    # regex_overrides_file. This avoids surprising behaviour changes when operators have not yet
    # reviewed or agreed with the newer format.
    out["detection"] = {
        **det_cfg,
        "cnpj_alphanumeric": bool(det_cfg.get("cnpj_alphanumeric", False)),
    }

    # Report
    out["report"] = data.get("report", {})
    if "output_dir" not in out["report"]:
        out["report"]["output_dir"] = "."
    # Optional: list of { norm_tag_pattern, base_legal, risk, recommendation, priority, relevant_for } for recommendations
    overrides = out["report"].get("recommendation_overrides")
    out["report"]["recommendation_overrides"] = (
        list(overrides) if isinstance(overrides, list) else []
    )
    if "include_executive_summary" not in out["report"]:
        out["report"]["include_executive_summary"] = False
    else:
        out["report"]["include_executive_summary"] = bool(
            out["report"]["include_executive_summary"]
        )
    if "min_sensitivity" not in out["report"]:
        out["report"]["min_sensitivity"] = "LOW"
    else:
        v = (out["report"].get("min_sensitivity") or "LOW").upper()
        out["report"]["min_sensitivity"] = (
            v if v in ("HIGH", "MEDIUM", "LOW") else "LOW"
        )
    if "include_suggested_review_sheet" not in out["report"]:
        out["report"]["include_suggested_review_sheet"] = True
    else:
        out["report"]["include_suggested_review_sheet"] = bool(
            out["report"]["include_suggested_review_sheet"]
        )

    # Optional heuristic jurisdiction hints (Report info sheet; not legal conclusions)
    jh_raw = out["report"].get("jurisdiction_hints")
    if not isinstance(jh_raw, dict):
        jh_raw = {}

    def _jh_int(key: str, default: int) -> int:
        try:
            return int(jh_raw.get(key, default))
        except (TypeError, ValueError):
            return default

    out["report"]["jurisdiction_hints"] = {
        "enabled": bool(jh_raw.get("enabled", False)),
        "us_ca": bool(jh_raw.get("us_ca", True)),
        "us_co": bool(jh_raw.get("us_co", True)),
        "jp": bool(jh_raw.get("jp", True)),
        "min_score_us_ca": _jh_int("min_score_us_ca", 4),
        "min_score_us_co": _jh_int("min_score_us_co", 4),
        "min_score_jp": _jh_int("min_score_jp", 3),
    }

    # API
    out["api"] = data.get("api", {})
    if "port" not in out["api"]:
        out["api"]["port"] = 8088
    if "workers" not in out["api"]:
        out["api"]["workers"] = (
            1  # 1 = minimal footprint; 2+ for concurrent API traffic
        )
    # Optional API key (enterprise): when require_api_key is true, API checks X-API-Key or Authorization: Bearer
    out["api"]["require_api_key"] = bool(out["api"].get("require_api_key", False))
    out["api"]["api_key"] = (out["api"].get("api_key") or "").strip() or None
    api_key_env = (out["api"].get("api_key_from_env") or "").strip()
    if api_key_env and not out["api"]["api_key"]:
        out["api"]["api_key"] = (os.environ.get(api_key_env) or "").strip() or None
    out["api"]["api_key_from_env"] = api_key_env or None
    out["api"]["maturity_self_assessment_poc_enabled"] = bool(
        out["api"].get("maturity_self_assessment_poc_enabled", False)
    )
    out["api"]["maturity_assessment_pack_path"] = str(
        out["api"].get("maturity_assessment_pack_path") or ""
    ).strip()
    out["api"]["maturity_integrity_secret_from_env"] = (
        str(out["api"].get("maturity_integrity_secret_from_env") or "").strip() or None
    )

    wa_raw = out["api"].get("webauthn")
    if not isinstance(wa_raw, dict):
        wa_raw = {}
    out["api"]["webauthn"] = {
        "enabled": bool(wa_raw.get("enabled", False)),
        "rp_id": str(wa_raw.get("rp_id") or "localhost").strip() or "localhost",
        "rp_name": str(wa_raw.get("rp_name") or "Data Boar").strip() or "Data Boar",
        "origin": str(wa_raw.get("origin") or "http://127.0.0.1:8088").strip(),
        "user_display_name": str(wa_raw.get("user_display_name") or "operator").strip()
        or "operator",
        "token_secret_from_env": str(
            wa_raw.get("token_secret_from_env") or "DATA_BOAR_WEBAUTHN_TOKEN_SECRET"
        ).strip()
        or "DATA_BOAR_WEBAUTHN_TOKEN_SECRET",
        "user_id_hex": str(wa_raw.get("user_id_hex") or "").strip(),
        "additional_origins": wa_raw.get("additional_origins"),
    }

    rb_raw = out["api"].get("rbac")
    if not isinstance(rb_raw, dict):
        rb_raw = {}
    _default_rbac_roles = [
        "dashboard",
        "scanner",
        "reports_reader",
        "config_admin",
    ]
    out["api"]["rbac"] = {
        "enabled": bool(rb_raw.get("enabled", False)),
        "default_roles": list(rb_raw.get("default_roles") or _default_rbac_roles),
        "api_key_roles": list(rb_raw.get("api_key_roles") or _default_rbac_roles),
    }

    # Optional external pattern files (ML/DL training terms: list of { text, label } with label "sensitive"|1 or "non_sensitive"|0)
    out["ml_patterns_file"] = data.get("ml_patterns_file") or ""
    out["regex_overrides_file"] = data.get("regex_overrides_file") or ""
    out["dl_patterns_file"] = data.get("dl_patterns_file") or ""

    # Unified plugin file (ADR-0052): a single YAML with optional sections
    # regex_patterns, ml_patterns, dl_patterns.  Takes precedence over the
    # corresponding legacy keys when both are non-empty.
    _ppf = (data.get("patterns_plugin_file") or "").strip()
    out["patterns_plugin_file"] = _ppf
    if _ppf:
        import warnings

        from config.plugin_validator import (
            PluginValidationWarning,
            validate_plugin_file,
        )

        pv = validate_plugin_file(_ppf, plugin_type="unified_plugin_file")
        for issue in pv.issues:
            warnings.warn(
                f"patterns_plugin_file '{_ppf}': {issue}",
                PluginValidationWarning,
                stacklevel=2,
            )
        # If valid, override the matching legacy keys so callers need not repeat paths.
        if pv.valid:
            import yaml
            from pathlib import Path as _Path

            try:
                _unified_raw = (
                    yaml.safe_load(_Path(_ppf).read_text(encoding="utf-8")) or {}
                )
            except Exception:  # noqa: BLE001
                _unified_raw = {}
            if "regex_patterns" in _unified_raw and not out["regex_overrides_file"]:
                out["regex_overrides_file"] = _ppf
            if "ml_patterns" in _unified_raw and not out["ml_patterns_file"]:
                out["ml_patterns_file"] = _ppf
            if "dl_patterns" in _unified_raw and not out["dl_patterns_file"]:
                out["dl_patterns_file"] = _ppf
    _raw_sf = data.get("sql_sampling_file")
    out["sql_sampling_file"] = _raw_sf.strip() if isinstance(_raw_sf, str) else ""
    _sfl = data.get("sql_sampling_files")
    out["sql_sampling_files"] = (
        [str(x).strip() for x in _sfl if isinstance(x, str) and str(x).strip()]
        if isinstance(_sfl, list)
        else []
    )

    # Encoding for pattern files (regex_overrides_file, ml_patterns_file, dl_patterns_file). Default utf-8.
    # Use utf-8, utf-8-sig, cp1252, latin_1, or iso-8859-1 for legacy/multilingual environments.
    _enc = (
        (data.get("pattern_files_encoding") or data.get("file_encoding") or "utf-8")
        .strip()
        .lower()
    )
    out["pattern_files_encoding"] = _enc if _enc else "utf-8"

    # Inline sensitivity-detection terms (override or supplement file-based terms when provided)
    sens = data.get("sensitivity_detection") or {}
    mct = sens.get("medium_confidence_threshold", 40)
    try:
        mct_int = int(mct)
    except (TypeError, ValueError):
        mct_int = 40
    # MEDIUM band must stay strictly below HIGH (70) in the detector.
    mct_int = max(1, min(69, mct_int))
    fcm_min = sens.get("fuzzy_column_match_min_confidence", 25)
    fcm_max = sens.get("fuzzy_column_match_max_confidence", 45)
    fcm_ratio = sens.get("fuzzy_column_match_min_ratio", 85)
    try:
        fcm_min_i = int(fcm_min)
    except (TypeError, ValueError):
        fcm_min_i = 25
    try:
        fcm_max_i = int(fcm_max)
    except (TypeError, ValueError):
        fcm_max_i = 45
    try:
        fcm_ratio_i = int(fcm_ratio)
    except (TypeError, ValueError):
        fcm_ratio_i = 85
    fcm_min_i = max(0, min(100, fcm_min_i))
    fcm_max_i = max(0, min(100, fcm_max_i))
    fcm_ratio_i = max(50, min(100, fcm_ratio_i))

    out["sensitivity_detection"] = {
        "ml_terms": sens.get("ml_terms") or [],
        "dl_terms": sens.get("dl_terms") or [],
        "medium_confidence_threshold": mct_int,
        # When true, fold accents and normalize separators on column names for ML/DL input only.
        "column_name_normalize_for_ml": bool(
            sens.get("column_name_normalize_for_ml", False)
        ),
        # Optional typo-tolerant column name vs sensitive terms (requires rapidfuzz).
        "fuzzy_column_match": bool(sens.get("fuzzy_column_match", False)),
        "fuzzy_column_match_min_confidence": fcm_min_i,
        "fuzzy_column_match_max_confidence": fcm_max_i,
        "fuzzy_column_match_min_ratio": fcm_ratio_i,
    }

    # Detection options (e.g. possible minor data)
    detection_cfg = data.get("detection") or {}
    minor_age = detection_cfg.get("minor_age_threshold", 18)
    try:
        minor_age_int = int(minor_age)
    except (TypeError, ValueError):
        minor_age_int = 18
    minor_full_scan_limit = detection_cfg.get("minor_full_scan_limit", 100)
    try:
        minor_full_scan_limit = max(1, int(minor_full_scan_limit))
    except (TypeError, ValueError):
        minor_full_scan_limit = 100
    agg_min = detection_cfg.get("aggregated_min_categories", 2)
    try:
        agg_min = max(1, int(agg_min))
    except (TypeError, ValueError):
        agg_min = 2
    quasi = detection_cfg.get("quasi_identifier_mapping")
    # Merge onto earlier detection dict (preserves cnpj_alphanumeric and any passthrough keys).
    out["detection"] = {
        **(out.get("detection") or {}),
        "minor_age_threshold": minor_age_int,
        "minor_full_scan": bool(detection_cfg.get("minor_full_scan", False)),
        "minor_full_scan_limit": minor_full_scan_limit,
        "minor_cross_reference": bool(detection_cfg.get("minor_cross_reference", True)),
        "aggregated_identification_enabled": bool(
            detection_cfg.get("aggregated_identification_enabled", True)
        ),
        "aggregated_min_categories": agg_min,
        "quasi_identifier_mapping": list(quasi) if isinstance(quasi, list) else [],
        # When true, SQL connector persists LOW columns whose names look like identifiers
        # (see core.suggested_review) for the "Suggested review (LOW)" report sheet.
        "persist_low_id_like_for_review": bool(
            detection_cfg.get("persist_low_id_like_for_review", False)
        ),
    }

    # Rate limiting / safety
    rate_cfg = data.get("rate_limit") or {}
    # Enabled default: True, but with conservative defaults so existing behaviour is effectively unchanged
    enabled_default = True
    enabled = rate_cfg.get("enabled", enabled_default)
    env_enabled = os.environ.get("RATE_LIMIT_ENABLED")
    if env_enabled is not None:
        enabled = env_enabled.strip().lower() in ("1", "true", "yes", "on")

    max_concurrent = rate_cfg.get("max_concurrent_scans", 1)
    env_max = os.environ.get("RATE_LIMIT_MAX_CONCURRENT_SCANS")
    if env_max is not None:
        try:
            max_concurrent = int(env_max)
        except ValueError:
            pass
    try:
        max_concurrent = max(1, int(max_concurrent))
    except (TypeError, ValueError):
        max_concurrent = 1

    min_interval = rate_cfg.get("min_interval_seconds", 0)
    env_min = os.environ.get("RATE_LIMIT_MIN_INTERVAL_SECONDS")
    if env_min is not None:
        try:
            min_interval = int(env_min)
        except ValueError:
            pass
    try:
        min_interval = max(0, int(min_interval))
    except (TypeError, ValueError):
        min_interval = 0

    grace = rate_cfg.get("grace_for_running_status", 0)
    env_grace = os.environ.get("RATE_LIMIT_GRACE_FOR_RUNNING_STATUS")
    if env_grace is not None:
        try:
            grace = int(env_grace)
        except ValueError:
            pass
    try:
        grace = max(0, int(grace))
    except (TypeError, ValueError):
        grace = 0

    out["rate_limit"] = {
        "enabled": bool(enabled),
        "max_concurrent_scans": max_concurrent,
        "min_interval_seconds": min_interval,
        "grace_for_running_status": grace,
    }

    # Timeouts for data source connections (global defaults; per-target overrides applied below)
    timeout_cfg = data.get("timeouts") or {}
    _connect = timeout_cfg.get("connect_seconds", 25)
    _read = timeout_cfg.get("read_seconds", 90)
    try:
        _connect = max(1, int(_connect))
    except (TypeError, ValueError):
        _connect = 25
    try:
        _read = max(1, int(_read))
    except (TypeError, ValueError):
        _read = 90
    out["timeouts"] = {"connect_seconds": _connect, "read_seconds": _read}

    # Per-target timeout overrides: merge global timeouts with optional target.connect_timeout,
    # target.read_timeout, or target.timeout (single value for both). Target overrides global when set.
    global_connect = out["timeouts"]["connect_seconds"]
    global_read = out["timeouts"]["read_seconds"]
    for t in out.get("targets") or []:
        if not isinstance(t, dict):
            continue
        target_connect = t.get("connect_timeout_seconds") or t.get("connect_timeout")
        target_read = t.get("read_timeout_seconds") or t.get("read_timeout")
        single = t.get("timeout")
        if single is not None:
            try:
                single = max(1, int(single))
            except (TypeError, ValueError):
                single = None
        if single is not None:
            if target_connect is None:
                target_connect = single
            if target_read is None:
                target_read = single
        for _name, _val in (
            ("connect_timeout_seconds", target_connect),
            ("read_timeout_seconds", target_read),
        ):
            if _val is not None:
                try:
                    _val = max(1, int(_val))
                except (TypeError, ValueError):
                    _val = (
                        global_connect
                        if _name == "connect_timeout_seconds"
                        else global_read
                    )
            else:
                _val = (
                    global_connect
                    if _name == "connect_timeout_seconds"
                    else global_read
                )
            t[_name] = _val

    # Parallel/sequential
    out["scan"] = data.get("scan", {})
    if "max_workers" not in out["scan"]:
        out["scan"]["max_workers"] = 1  # 1 = sequential; >1 = parallel
    # Clamp max_workers to a safe range to avoid accidental huge parallelism
    raw_max_workers = out["scan"].get("max_workers", 1)
    try:
        mw = int(raw_max_workers)
    except (TypeError, ValueError):
        mw = 1
    if mw < 1:
        mw = 1
    # Hard upper cap to avoid runaway parallelism from misconfiguration
    if mw > 32:
        mw = 32
    out["scan"]["max_workers"] = mw

    # SQLite path for audit results
    out["sqlite_path"] = data.get("sqlite_path", "audit_results.db")

    # Learned patterns (optional): write terms classified sensitive to a file for merging into ml_patterns_file
    out["learned_patterns"] = data.get("learned_patterns") or {}
    lp = out["learned_patterns"]
    if "enabled" not in lp:
        lp["enabled"] = False
    if "output_file" not in lp:
        lp["output_file"] = "learned_patterns.yaml"
    if "min_sensitivity" not in lp:
        lp["min_sensitivity"] = "HIGH"
    if "min_confidence" not in lp:
        lp["min_confidence"] = 70
    if "min_term_length" not in lp:
        lp["min_term_length"] = 3
    if "require_pattern" not in lp:
        lp["require_pattern"] = True
    if "append" not in lp:
        lp["append"] = True
    if "exclude_if_in_ml_patterns" not in lp:
        lp["exclude_if_in_ml_patterns"] = True

    # Optional commercial licensing (default: open — no enforcement). See docs/LICENSING_SPEC.md.
    lic = data.get("licensing") or {}
    if not isinstance(lic, dict):
        lic = {}
    mode = str(lic.get("mode", "open")).strip().lower()
    if mode not in ("open", "enforced"):
        mode = "open"
    out["licensing"] = {
        "mode": mode,
        "public_key_path": str(lic.get("public_key_path") or "").strip(),
        "license_path": str(lic.get("license_path") or "").strip(),
        "revocation_list_path": str(lic.get("revocation_list_path") or "").strip(),
        "manifest_path": str(lic.get("manifest_path") or "").strip(),
        "machine_bind_strict": bool(lic.get("machine_bind_strict", False)),
        # Dev/lab: simulate tier for feature gates (community | pro | enterprise). Not a JWT claim.
        "effective_tier": str(lic.get("effective_tier") or "").strip().lower(),
    }

    # Optional operator notifications (webhooks; default off). Secrets via ${VAR} or env-only docs.
    n_raw = data.get("notifications")
    if not isinstance(n_raw, dict):
        n_raw = {}
    op_raw = n_raw.get("operator")
    if not isinstance(op_raw, dict):
        op_raw = {}
    channels_list: list[dict[str, Any]] = []
    raw_ch = op_raw.get("channels")
    if isinstance(raw_ch, list):
        for item in raw_ch:
            if isinstance(item, dict):
                channels_list.append(_normalize_operator_channel_block(item))

    t_raw = n_raw.get("tenant")
    if not isinstance(t_raw, dict):
        t_raw = {}
    by_tenant: dict[str, dict[str, Any]] = {}
    raw_map = t_raw.get("by_tenant") or t_raw.get("tenants")
    if isinstance(raw_map, dict):
        for k, v in raw_map.items():
            if not isinstance(k, str):
                continue
            key = k.strip().lower()
            if not key:
                continue
            if isinstance(v, str):
                u = _notification_env_value(v)
                if u:
                    by_tenant[key] = {"generic_webhook_url": u}
            elif isinstance(v, dict):
                by_tenant[key] = _normalize_operator_channel_block(v)

    default_tenant_generic = _notification_env_value(
        t_raw.get("default_generic_webhook_url") or t_raw.get("default_webhook_url")
    )
    default_tenant_slack = _notification_env_value(
        t_raw.get("default_slack_webhook_url")
    )

    out["notifications"] = {
        "enabled": bool(n_raw.get("enabled", False)),
        "on_scan_complete": bool(n_raw.get("on_scan_complete", True)),
        "notify_only_if_high_or_critical": bool(
            n_raw.get("notify_only_if_high_or_critical", False)
        ),
        "notify_on_failure": bool(n_raw.get("notify_on_failure", True)),
        "public_base_url": _notification_env_value(n_raw.get("public_base_url")),
        "dedupe_scan_complete_per_session": bool(
            n_raw.get("dedupe_scan_complete_per_session", True)
        ),
        "notify_audit_log": bool(n_raw.get("notify_audit_log", True)),
        "operator": {
            "channels": channels_list,
            "generic_webhook_url": _notification_env_value(
                op_raw.get("generic_webhook_url")
            ),
            "slack_webhook_url": _notification_env_value(
                op_raw.get("slack_webhook_url")
            ),
            "teams_webhook_url": _notification_env_value(
                op_raw.get("teams_webhook_url")
            ),
            "telegram_bot_token": _notification_env_value(
                op_raw.get("telegram_bot_token")
            ),
            "telegram_chat_id": _notification_env_value(op_raw.get("telegram_chat_id")),
        },
        "tenant": {
            "default_generic_webhook_url": default_tenant_generic,
            "default_slack_webhook_url": default_tenant_slack,
            "by_tenant": by_tenant,
        },
    }

    # Unique, sanitized audit log labels per target (text logs only; DB keeps config ``name``).
    assign_unique_audit_log_names(out.get("targets") or [])

    # Dashboard HTML locale (path-prefixed UI; see docs/plans/completed/PLAN_DASHBOARD_I18N.md)
    loc_raw = data.get("locale") or {}
    if not isinstance(loc_raw, dict):
        loc_raw = {}
    default_loc = str(loc_raw.get("default_locale") or "en").strip()
    if default_loc.lower() in ("pt-br", "pt_br"):
        default_loc = "pt-BR"
    supported_raw = loc_raw.get("supported_locales")
    if not isinstance(supported_raw, list) or not supported_raw:
        supported_norm = ["en", "pt-BR"]
    else:
        supported_norm = []
        for x in supported_raw:
            s = str(x).strip()
            if s.lower() in ("pt-br", "pt_br"):
                s = "pt-BR"
            supported_norm.append(s)
    if default_loc not in supported_norm:
        default_loc = supported_norm[0]
    cookie_name = str(loc_raw.get("cookie_name") or "db_locale").strip() or "db_locale"
    try:
        cookie_max_age = int(loc_raw.get("cookie_max_age_seconds", 31536000))
    except (TypeError, ValueError):
        cookie_max_age = 31536000
    cookie_max_age = max(60, min(cookie_max_age, 63072000))
    out["locale"] = {
        "default_locale": default_loc,
        "supported_locales": supported_norm,
        "cookie_name": cookie_name,
        "cookie_max_age_seconds": cookie_max_age,
    }

    return out

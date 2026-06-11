"""
SQLite integrity anchor + startup re-verify + TINTED/-alpha trust level (#856, Phase E).

Tamper-EVIDENT, not tamper-PROOF (E.6 — see docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md
and SECURITY.md threat model): an attacker with write access to both code AND the
SQLite anchor can re-baseline. The local anchor catches casual edits, forks with
gates removed, and drifted deploys; the SIGNED manifest (Sigstore / CI OIDC,
PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY Phase C.4) is the next hardening layer.

Flow (E.1–E.5):

1. First run: hash the behaviour-critical allowlist (CRITICAL_MODULES) →
   persist ``build_integrity_anchor`` (release_label, per-file hashes,
   manifest_content_hash, validated_at, signature_ok, validator_version) in the
   SAME SQLite file as scan data — ``wipe_all_data()`` / ``--reset-data`` only
   delete ORM scan tables, so the anchor SURVIVES a data wipe by design.
2. Every later startup (ANY mode, including ``open``): recompute hashes,
   compare to the anchor. Mismatch → ``integrity_state=tampered`` /
   ``trust_level=adulterated`` and every user-visible surface (report Info
   sheet, dashboard footer, GET /about, GET /status, /health, startup logs)
   shows the ``-alpha`` label ("development / not CI-validated").
3. ``integrity_events`` is append-only (validation / re-verify / tamper) for
   forensics and is also preserved by ``wipe_all_data()``.

The open-mode worker clamp (OPEN_MODE_WORKER_CAP, enforced in core/engine.py)
is part of the hashed allowlist: removing the clamp changes ``core/engine.py``
(or this module) → the build self-marks ``-alpha``.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ANCHOR_VERSION = 1
VALIDATOR_VERSION = "1"

# Behaviour-critical modules (#856): gates, clamps, detection, API surface.
# Paths are repo-root-relative. Changing ANY of these after the first
# validated run marks the runtime as adulterated (-alpha).
CRITICAL_MODULES: tuple[str, ...] = (
    "main.py",
    "core/detector.py",
    "core/engine.py",
    "core/integrity_anchor.py",
    "core/licensing/guard.py",
    "api/routes.py",
)

# Open-mode worker clamp (#856): in ``licensing.mode: open`` the engine runs at
# most this many parallel scan workers. Behaviour-critical — part of the
# integrity manifest above (enforced in core/engine.py).
OPEN_MODE_WORKER_CAP = 2

ALPHA_LABEL = "-alpha"
ALPHA_NOTE = "development / not CI-validated"

_LOCK = threading.Lock()
_SNAPSHOT: dict[str, Any] | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def compute_module_hashes() -> dict[str, str]:
    """SHA-256 hex per CRITICAL_MODULES path; missing files hash as 'missing'."""
    root = _repo_root()
    out: dict[str, str] = {}
    for rel in CRITICAL_MODULES:
        p = root / rel
        if not p.is_file():
            out[rel] = "missing"
            continue
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        out[rel] = h.hexdigest()
    return out


def _manifest_content_hash(hashes: dict[str, str]) -> str:
    canonical = json.dumps(hashes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _db_path_from_config(config: dict[str, Any] | None) -> str:
    cfg = config or {}
    return str(cfg.get("sqlite_path", "audit_results.db"))


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS build_integrity_anchor (
            anchor_version INTEGER PRIMARY KEY,
            release_label TEXT NOT NULL,
            manifest_content_hash TEXT NOT NULL,
            file_hashes_json TEXT NOT NULL,
            validated_at TEXT NOT NULL,
            signature_ok INTEGER NOT NULL,
            validator_version TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS integrity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            detail TEXT NOT NULL
        )
        """
    )


def _record_event(conn: sqlite3.Connection, event_type: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO integrity_events (created_at, event_type, detail) VALUES (?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), event_type, detail[:4000]),
    )


def _release_label() -> str:
    try:
        # Raw package version (not get_about_info) — the about surface may carry
        # the -alpha tamper suffix, which must never leak into the anchor label.
        from core.about import _package_version

        return _package_version()
    except Exception:  # pragma: no cover - about must never break the anchor
        return "unknown"


def _signature_ok() -> bool:
    """Best-effort release signature signal (build digest + optional manifest)."""
    try:
        from core.licensing.integrity import check_build_digest_expected

        ok, _detail = check_build_digest_expected()
        return bool(ok)
    except Exception:  # pragma: no cover
        return False


def ensure_integrity_anchor(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Validate or create the SQLite integrity anchor and cache the snapshot.

    Runs in ANY licensing mode (including ``open``). Fail-soft on storage
    errors: a broken anchor DB yields ``integrity_state=unknown`` (logged),
    never an aborted startup.
    """
    global _SNAPSHOT
    current = compute_module_hashes()
    db_path = _db_path_from_config(config)
    snapshot: dict[str, Any]
    try:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # contextlib.closing: sqlite3's own context manager commits but does
        # NOT close the connection (ResourceWarning under pytest -W error).
        with (
            _LOCK,
            contextlib.closing(sqlite3.connect(db_path, timeout=10)) as conn,
        ):
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT release_label, manifest_content_hash, file_hashes_json, "
                "validated_at, signature_ok FROM build_integrity_anchor "
                "WHERE anchor_version = ?",
                (ANCHOR_VERSION,),
            ).fetchone()
            now_iso = datetime.now(timezone.utc).isoformat()
            if row is None:
                # E.1/E.2 — first-run validation: persist the anchor baseline.
                label = _release_label()
                sig_ok = _signature_ok()
                conn.execute(
                    "INSERT INTO build_integrity_anchor (anchor_version, "
                    "release_label, manifest_content_hash, file_hashes_json, "
                    "validated_at, signature_ok, validator_version) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        ANCHOR_VERSION,
                        label,
                        _manifest_content_hash(current),
                        json.dumps(current, sort_keys=True),
                        now_iso,
                        1 if sig_ok else 0,
                        VALIDATOR_VERSION,
                    ),
                )
                _record_event(
                    conn,
                    "validation",
                    f"first-run anchor created: release_label={label} "
                    f"files={len(current)} signature_ok={sig_ok}",
                )
                snapshot = {
                    "integrity_state": "validated",
                    "trust_level": "expected",
                    "release_label": label,
                    "validated_at": now_iso,
                    "signature_ok": sig_ok,
                    "mismatched_files": [],
                }
            else:
                # E.3 — startup re-verify against the stored anchor.
                label, _stored_manifest, stored_json, validated_at, sig_ok = row
                stored: dict[str, str] = json.loads(stored_json)
                mismatched = sorted(
                    set(stored) | set(current),
                )
                mismatched = [
                    rel for rel in mismatched if stored.get(rel) != current.get(rel)
                ]
                if mismatched:
                    _record_event(
                        conn,
                        "tamper",
                        "startup re-verify mismatch: " + ", ".join(mismatched),
                    )
                    snapshot = {
                        "integrity_state": "tampered",
                        "trust_level": "adulterated",
                        "release_label": label,
                        "validated_at": validated_at,
                        "signature_ok": bool(sig_ok),
                        "mismatched_files": mismatched,
                    }
                else:
                    _record_event(conn, "re-verify", "startup re-verify ok")
                    snapshot = {
                        "integrity_state": "validated",
                        "trust_level": "expected",
                        "release_label": label,
                        "validated_at": validated_at,
                        "signature_ok": bool(sig_ok),
                        "mismatched_files": [],
                    }
            conn.commit()
    except (sqlite3.Error, OSError, json.JSONDecodeError) as e:
        logger.warning("Integrity anchor unavailable (state=unknown): %s", e)
        snapshot = {
            "integrity_state": "unknown",
            "trust_level": "unknown",
            "release_label": "unknown",
            "validated_at": "",
            "signature_ok": False,
            "mismatched_files": [],
            "error": str(e),
        }
    if snapshot["integrity_state"] == "tampered":
        logger.critical(
            "INTEGRITY TAMPER DETECTED: behaviour-critical modules diverge from "
            "the validated anchor (%s). Runtime self-marked %s (%s).",
            ", ".join(snapshot["mismatched_files"]),
            ALPHA_LABEL,
            ALPHA_NOTE,
        )
    else:
        logger.info(
            "Integrity anchor: state=%s release_label=%s validated_at=%s",
            snapshot["integrity_state"],
            snapshot["release_label"],
            snapshot["validated_at"],
        )
    _SNAPSHOT = snapshot
    return dict(snapshot)


def get_integrity_snapshot() -> dict[str, Any]:
    """Cached snapshot from the last ensure_integrity_anchor(); 'unknown' if never run."""
    if _SNAPSHOT is None:
        return {
            "integrity_state": "unknown",
            "trust_level": "unknown",
            "release_label": "unknown",
            "validated_at": "",
            "signature_ok": False,
            "mismatched_files": [],
        }
    return dict(_SNAPSHOT)


def is_tampered() -> bool:
    return get_integrity_snapshot()["integrity_state"] == "tampered"


def alpha_version_suffix() -> str:
    """``-alpha`` suffix for user-visible version strings when adulterated."""
    return ALPHA_LABEL if is_tampered() else ""


def list_integrity_events(
    config: dict[str, Any] | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    """Read-only view of the append-only ``integrity_events`` table (forensics)."""
    db_path = _db_path_from_config(config)
    try:
        with contextlib.closing(sqlite3.connect(db_path, timeout=10)) as conn:
            _ensure_tables(conn)
            rows = conn.execute(
                "SELECT id, created_at, event_type, detail FROM integrity_events "
                "ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            conn.commit()
    except (sqlite3.Error, OSError):
        return []
    return [
        {"id": r[0], "created_at": r[1], "event_type": r[2], "detail": r[3]}
        for r in rows
    ]


def reset_integrity_anchor_for_tests() -> None:
    """Clear the cached snapshot (tests only)."""
    global _SNAPSHOT
    _SNAPSHOT = None

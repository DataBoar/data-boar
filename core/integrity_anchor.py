"""
SQLite integrity forensics + signed-manifest trust (#856 / #2168).

``validated`` / ``expected`` only when installed CRITICAL_MODULES match a
manifest whose Ed25519 signature verifies with the packaged license public
key. SQLite stores events and a last-seen signed label. It is not the
arbiter. ``--reconcile-integrity-anchor`` records an event and re-evaluates
the same signed manifest. See docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md.
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


class IntegrityReconcileError(ValueError):
    """``--confirm-upgrade-to`` does not match the installed package version."""


ANCHOR_VERSION = 1
VALIDATOR_VERSION = "1"

# Behaviour-critical spine (#856) — always hashed.
_CRITICAL_MODULE_SPINE: tuple[str, ...] = (
    "main.py",
    "core/detector.py",
    "core/engine.py",
    "core/integrity_anchor.py",
    "api/routes.py",
)

# Auto-protect new connectors/licensing modules (#1298) — glob at resolve time.
_CRITICAL_MODULE_GLOBS: tuple[str, ...] = (
    "connectors/*.py",
    "core/licensing/*.py",
)

# Explicit paths outside globs (#1298).
_CRITICAL_MODULE_EXTRAS: tuple[str, ...] = (
    "core/connector_registry.py",
    "core/validation.py",
    "utils/logger.py",
    "api/webauthn_routes.py",
    "api/webauthn_html_gate.py",
    "core/integrity_signed_manifest.py",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_critical_modules() -> tuple[str, ...]:
    """Repo-root-relative paths in the behaviour-critical allowlist (sorted, deduped)."""
    root = _repo_root()
    paths: set[str] = set(_CRITICAL_MODULE_SPINE)
    paths.update(_CRITICAL_MODULE_EXTRAS)
    for pattern in _CRITICAL_MODULE_GLOBS:
        for p in sorted(root.glob(pattern)):
            if p.is_file():
                paths.add(p.relative_to(root).as_posix())
    return tuple(sorted(paths))


# Resolved once at import; operator re-baseline is explicit (#1262 CLI).
CRITICAL_MODULES: tuple[str, ...] = resolve_critical_modules()

# Open-mode worker clamp (#856): in ``licensing.mode: open`` the engine runs at
# most this many parallel scan workers. Behaviour-critical — part of the
# integrity manifest above (enforced in core/engine.py).
OPEN_MODE_WORKER_CAP = 2

ALPHA_LABEL = "-alpha"
ALPHA_NOTE = "development / not CI-validated"

_LOCK = threading.Lock()
_SNAPSHOT: dict[str, Any] | None = None


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


def _migrate_legacy_signature_ok_column(conn: sqlite3.Connection) -> None:
    """#1211 — rename signature_ok → build_digest_matched on legacy DBs (SQLite 3.25+)."""
    cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(build_integrity_anchor)").fetchall()
    }
    if "signature_ok" in cols and "build_digest_matched" not in cols:
        conn.execute(
            "ALTER TABLE build_integrity_anchor "
            "RENAME COLUMN signature_ok TO build_digest_matched"
        )
        # Legacy values were written under the old default-true overclaim
        # (nothing verified ≠ matched). One-time reset to 0 (under-claim);
        # module-hash baseline rows stay intact; next honest baseline uses
        # _build_digest_matched().
        conn.execute("UPDATE build_integrity_anchor SET build_digest_matched = 0")


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS build_integrity_anchor (
            anchor_version INTEGER PRIMARY KEY,
            release_label TEXT NOT NULL,
            manifest_content_hash TEXT NOT NULL,
            file_hashes_json TEXT NOT NULL,
            validated_at TEXT NOT NULL,
            build_digest_matched INTEGER NOT NULL,
            validator_version TEXT NOT NULL,
            signed_release_label TEXT
        )
        """
    )
    _migrate_legacy_signature_ok_column(conn)
    cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(build_integrity_anchor)").fetchall()
    }
    if "signed_release_label" not in cols:
        conn.execute(
            "ALTER TABLE build_integrity_anchor ADD COLUMN signed_release_label TEXT"
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


def _persist_forensic(
    conn: sqlite3.Connection,
    *,
    current: dict[str, str],
    label: str,
    now_iso: str,
    digest_matched: bool,
    signed_release_label: str | None,
    first_row: bool,
) -> None:
    if first_row:
        conn.execute(
            "INSERT INTO build_integrity_anchor (anchor_version, "
            "release_label, manifest_content_hash, file_hashes_json, "
            "validated_at, build_digest_matched, validator_version, "
            "signed_release_label) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ANCHOR_VERSION,
                label,
                _manifest_content_hash(current),
                json.dumps(current, sort_keys=True),
                now_iso,
                1 if digest_matched else 0,
                VALIDATOR_VERSION,
                signed_release_label,
            ),
        )
        return
    conn.execute(
        "UPDATE build_integrity_anchor SET release_label=?, "
        "manifest_content_hash=?, file_hashes_json=?, "
        "validated_at=?, build_digest_matched=?, signed_release_label=? "
        "WHERE anchor_version=?",
        (
            label,
            _manifest_content_hash(current),
            json.dumps(current, sort_keys=True),
            now_iso,
            1 if digest_matched else 0,
            signed_release_label,
            ANCHOR_VERSION,
        ),
    )


def _build_digest_matched() -> bool:
    """True only when an expected build digest was configured and matched (#1211).

    This is a **digest compare**, not a cryptographic signature verification.
    ``no_expected_digest`` (env unset) returns False — nothing verified ≠ matched.
    """
    try:
        from core.licensing.integrity import check_build_digest_expected

        ok, detail = check_build_digest_expected()
        return bool(ok) and detail == "digest_match"
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
                "SELECT signed_release_label FROM build_integrity_anchor "
                "WHERE anchor_version = ?",
                (ANCHOR_VERSION,),
            ).fetchone()
            now_iso = datetime.now(timezone.utc).isoformat()
            label = _release_label()
            digest_matched = _build_digest_matched()
            previous_signed = (row[0] if row else None) or None
            from core.integrity_signed_manifest import evaluate_signed_manifest

            verdict = evaluate_signed_manifest(current, label, previous_signed)
            keep_signed = verdict["signed_release_label"] or previous_signed
            _persist_forensic(
                conn,
                current=current,
                label=label,
                now_iso=now_iso,
                digest_matched=digest_matched,
                signed_release_label=keep_signed,
                first_row=row is None,
            )
            if verdict["integrity_state"] == "validated":
                event_type = "validation" if row is None else "re-verify"
            else:
                event_type = "tamper"
            mismatch = ",".join(verdict["mismatched_files"])
            _record_event(
                conn,
                event_type,
                f"{verdict['detail']}: release_label={label} "
                f"files={len(current)} build_digest_matched={digest_matched}"
                + (f" mismatched={mismatch}" if mismatch else ""),
            )
            snapshot = {
                "integrity_state": verdict["integrity_state"],
                "trust_level": verdict["trust_level"],
                "release_label": label,
                "validated_at": now_iso,
                "build_digest_matched": digest_matched,
                "mismatched_files": verdict["mismatched_files"],
            }
            conn.commit()
    except (sqlite3.Error, OSError, json.JSONDecodeError) as e:
        logger.warning("Integrity anchor unavailable (state=unknown): %s", e)
        snapshot = {
            "integrity_state": "unknown",
            "trust_level": "unknown",
            "release_label": "unknown",
            "validated_at": "",
            "build_digest_matched": False,
            "mismatched_files": [],
            # Public JSON (/health, /status) — class name only. str(e) can
            # embed sqlite/OS paths or JSON parse context (CodeQL
            # py/stack-trace-exposure; #1721 / alerts #300, #287).
            "error": type(e).__name__,
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


def reconcile_integrity_anchor(
    config: dict[str, Any] | None,
    confirm_upgrade_to: str,
) -> dict[str, Any]:
    """Record a reconcile event and re-evaluate the signed manifest (#2168).

    ``confirm_upgrade_to`` must equal the installed ``_package_version()``.
    This path cannot produce ``validated`` by itself.
    """
    wanted = (confirm_upgrade_to or "").strip()
    current_label = _release_label()
    if not wanted:
        raise IntegrityReconcileError(
            "--confirm-upgrade-to is required with --reconcile-integrity-anchor"
        )
    if wanted != current_label:
        raise IntegrityReconcileError(
            f"--confirm-upgrade-to={wanted!r} does not match installed "
            f"release_label={current_label!r}"
        )
    db_path = _db_path_from_config(config)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with (
        _LOCK,
        contextlib.closing(sqlite3.connect(db_path, timeout=10)) as conn,
    ):
        _ensure_tables(conn)
        _record_event(
            conn,
            "reconcile",
            f"operator confirmed upgrade to {current_label}; "
            "re-evaluating signed manifest",
        )
        conn.commit()
    logger.info("Integrity reconcile event recorded for %s", current_label)
    return ensure_integrity_anchor(config)


def get_integrity_snapshot() -> dict[str, Any]:
    """Cached snapshot from the last ensure_integrity_anchor(); 'unknown' if never run."""
    if _SNAPSHOT is None:
        return {
            "integrity_state": "unknown",
            "trust_level": "unknown",
            "release_label": "unknown",
            "validated_at": "",
            "build_digest_matched": False,
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

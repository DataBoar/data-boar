"""Shared, metadata-only view of one scan session's findings (#837 / #838).

Used by the RoPA export (``core/ropa_export.py``), the SARIF export
(``core/sarif_export.py``) and the post-scan findings push
(``core/findings_push.py``) so all three describe the same rows the same way.

Nothing here reads or returns sample content: finding rows in SQLite are
metadata-only (location, detector label, sensitivity, norm tag).

The identity key of a finding is the SAME tuple ``LocalDBManager.diff_sessions``
uses (``--diff``), so ``new_findings_count`` / ``resolved_count`` here always
agree with ``--diff`` output for the same two sessions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

SENSITIVITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# Session statuses that make a good baseline for a delta (a run that was
# interrupted or is still going would report phantom "new" findings).
_BASELINE_STATUSES = frozenset({"completed", "completed_errors"})

_KINDS = ("database", "filesystem", "application")


class UnknownSessionError(ValueError):
    """The session id is not present in the local SQLite store."""


@dataclass(frozen=True)
class FindingRecord:
    """One finding row, normalized across database/filesystem/application."""

    kind: str  # database | filesystem | application
    target: str
    sensitivity: str  # HIGH | MEDIUM | LOW | "" (upper-cased)
    pattern: str  # pattern_detected exactly as stored (may be "A, B")
    norm_tag: str
    schema: str | None
    table: str | None
    column: str | None
    path: str | None
    file_name: str | None
    key: tuple[Any, ...]  # identical to diff_sessions' per-kind key

    @property
    def patterns(self) -> list[str]:
        """Detector labels in ``pattern`` (the detector joins hits with ", ")."""
        parts = [p.strip() for p in (self.pattern or "").split(",")]
        out = [p for p in parts if p]
        return out or ["UNSPECIFIED"]

    @property
    def location(self) -> str:
        """Human-readable, metadata-only location string."""
        if self.kind == "database":
            parts = [self.schema, self.table, self.column]
            return ".".join(str(p) for p in parts if p)
        pieces = [p for p in (self.path, self.file_name) if p]
        if len(pieces) == 2:
            sep = "\\" if "\\" in pieces[0] and "/" not in pieces[0] else "/"
            return pieces[0].rstrip("/\\") + sep + pieces[1]
        return pieces[0] if pieces else ""

    def fingerprint(self, token: str = "") -> str:
        """Stable opaque id (SHA-256 prefix) of the diff key (+ optional detector)."""
        raw = "\x1f".join(
            [self.kind, *("" if v is None else str(v) for v in self.key), token]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class SessionDelta:
    """Delta between a session and its baseline (previous comparable session)."""

    previous_session_id: str | None
    new_findings_count: int | None
    resolved_count: int | None
    new_keys: frozenset[tuple[str, tuple[Any, ...]]]

    @property
    def available(self) -> bool:
        return self.previous_session_id is not None

    def is_new(self, rec: FindingRecord) -> bool:
        return (rec.kind, rec.key) in self.new_keys


NO_DELTA = SessionDelta(None, None, None, frozenset())


def _row_to_record(kind: str, row: dict[str, Any]) -> FindingRecord:
    target = row.get("target_name")
    pattern = row.get("pattern_detected")
    if kind == "database":
        key: tuple[Any, ...] = (
            target,
            row.get("schema_name"),
            row.get("table_name"),
            row.get("column_name"),
            pattern,
        )
    else:
        key = (target, row.get("path"), row.get("file_name"), pattern)
    return FindingRecord(
        kind=kind,
        target=str(target or "unknown"),
        sensitivity=str(row.get("sensitivity_level") or "").strip().upper(),
        pattern=str(pattern or ""),
        norm_tag=str(row.get("norm_tag") or ""),
        schema=row.get("schema_name") if kind == "database" else None,
        table=row.get("table_name") if kind == "database" else None,
        column=row.get("column_name") if kind == "database" else None,
        path=row.get("path") if kind != "database" else None,
        file_name=row.get("file_name") if kind != "database" else None,
        key=key,
    )


def session_meta(db_manager: Any, session_id: str) -> dict[str, Any]:
    """Return the ``list_sessions`` row for ``session_id`` or raise."""
    sid = (session_id or "").strip()
    for row in db_manager.list_sessions() or []:
        if row.get("session_id") == sid:
            return dict(row)
    raise UnknownSessionError(f"Unknown session: {sid or '<empty>'}")


def sort_key(rec: FindingRecord) -> tuple[Any, ...]:
    """Deterministic order: most sensitive first, then target and location."""
    return (
        -SENSITIVITY_RANK.get(rec.sensitivity, 0),
        rec.target,
        rec.kind,
        rec.location,
        rec.pattern,
    )


def collect_session_findings(
    db_manager: Any, session_id: str
) -> tuple[list[FindingRecord], int]:
    """Return ``(records, scan_failure_count)`` for ``session_id``, sorted."""
    sid = (session_id or "").strip()
    db_rows, fs_rows, app_rows, fail_rows = db_manager.get_findings(sid)
    records: list[FindingRecord] = []
    for kind, rows in (
        ("database", db_rows),
        ("filesystem", fs_rows),
        ("application", app_rows),
    ):
        records.extend(_row_to_record(kind, r) for r in rows)
    records.sort(key=sort_key)
    return records, len(fail_rows)


def select_baseline_session(db_manager: Any, session_id: str) -> str | None:
    """Most recent earlier, finished session with the same scan scope (if known)."""
    sessions = db_manager.list_sessions() or []
    current = next((s for s in sessions if s.get("session_id") == session_id), None)
    if current is None:
        return None
    scope = current.get("config_scope_hash")
    idx = sessions.index(current)
    # list_sessions is newest-first (started_at desc): earlier runs follow.
    for cand in sessions[idx + 1 :]:
        if (cand.get("status") or "") not in _BASELINE_STATUSES:
            continue
        cand_scope = cand.get("config_scope_hash")
        if scope and cand_scope and scope != cand_scope:
            continue
        return str(cand["session_id"])
    return None


def compute_session_delta(db_manager: Any, session_id: str) -> SessionDelta:
    """Delta vs the baseline session using ``diff_sessions`` (same keys as ``--diff``)."""
    prev = select_baseline_session(db_manager, session_id)
    if prev is None:
        return NO_DELTA
    result = db_manager.diff_sessions(prev, session_id)
    new_keys: set[tuple[str, tuple[Any, ...]]] = set()
    resolved = 0
    for kind in _KINDS:
        block = result.get(kind) or {}
        new_keys.update((kind, k) for k in (block.get("new") or {}))
        resolved += len(block.get("resolved") or {})
    return SessionDelta(
        previous_session_id=prev,
        new_findings_count=len(new_keys),
        resolved_count=resolved,
        new_keys=frozenset(new_keys),
    )

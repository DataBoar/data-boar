"""
Sanitized labels and path fragments for plaintext audit logs (G-26-01 / SECURITY.md).

Keeps ``target`` row ``name`` unchanged in SQLite/Excel; ``audit_log_name`` is derived at
normalize_config time and used in log lines so labels stay unique and paths avoid raw
host disclosure where possible.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Any

_ILLEGAL = re.compile(r'[|\\/*?"<>:\x00-\x1f]+')


def _short_hash(text: str, n: int) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:n]


def _base_audit_slug(raw: str) -> str:
    s = (raw or "").strip()
    s = _ILLEGAL.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "target"


def assign_unique_audit_log_names(targets: list[dict[str, Any]]) -> None:
    """Mutate each target dict: set ``audit_log_name`` unique among siblings (slug from ``name``)."""
    if not targets:
        return
    slugs = [_base_audit_slug(str(t.get("name", "") or "")) for t in targets]
    dup_counts: dict[str, int] = {}
    for t, slug in zip(targets, slugs, strict=True):
        dup_counts[slug] = dup_counts.get(slug, 0) + 1

    ordinal: dict[str, int] = {}
    for t, slug in zip(targets, slugs, strict=True):
        if dup_counts.get(slug, 0) <= 1:
            t["audit_log_name"] = slug
            continue
        ordinal[slug] = ordinal.get(slug, 0) + 1
        n = ordinal[slug]
        if n == 1:
            t["audit_log_name"] = slug
        else:
            t["audit_log_name"] = f"{slug}__{n}"


def audit_log_target_label(config: dict[str, Any], *, default: str) -> str:
    """Label for log lines: explicit ``audit_log_name`` or slug from ``name``."""
    explicit = config.get("audit_log_name")
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    return _base_audit_slug(str(config.get("name", "") or default))


def sanitize_target_name_for_audit_log(
    name: str | None, *, default: str = "target"
) -> str:
    """Collapse dangerous/verbose characters for a single-line audit log field."""
    if name is None or not str(name).strip():
        return default
    s = str(name).strip().replace("\r", " ").replace("\n", " ")
    if len(s) > 500:
        s = f"{s[:497]}..."
    return s


def format_filesystem_scan_root_for_audit_log(scan_root: Path) -> str:
    """Scan root as ``folder?8hex`` (hash of resolved path; avoids raw full path in logs)."""
    try:
        resolved = str(scan_root.resolve())
    except OSError:
        resolved = str(scan_root)
    label = scan_root.name or "scan_root"
    return f"{label}?{_short_hash(resolved, 8)}"


def format_filesystem_finding_location_for_audit_log(
    scan_root: Path,
    file_path: Path,
    audit_log_name: str,
    file_name: str,
) -> str:
    """
    Relative POSIX path from resolved scan root when possible; otherwise
    ``audit_log_name?12hex`` (symlink escapes root).
    """
    try:
        rroot = scan_root.resolve()
        rfile = file_path.resolve()
    except OSError:
        return file_name
    try:
        rel = rfile.relative_to(rroot)
    except ValueError:
        return f"{audit_log_name}?{_short_hash(str(rfile), 12)}"
    return str(PurePosixPath(rel)).replace("\\", "/")

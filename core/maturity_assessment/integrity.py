"""
Tamper-evident sealing for maturity self-assessment POC rows (SQLite).

Uses HMAC-SHA256 over a canonical UTF-8 payload. The secret must live outside the DB
(env or config indirection) so direct SQLite edits break the MAC without the key.

This is **not** a substitute for filesystem encryption or TEE; it limits casual DB edits
and supports operator demos of integrity expectations. See PLAN_MATURITY_*.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any


HMAC_VERSION = "maturity-answer-hmac-v1"


def load_integrity_secret_from_config(cfg: dict) -> bytes | None:
    """
    Resolve HMAC key: ``api.maturity_integrity_secret_from_env`` (env var name), then
    ``DATA_BOAR_MATURITY_INTEGRITY_SECRET``. Returns None if unset (rows stored unsealed).
    """
    api = cfg.get("api") if isinstance(cfg.get("api"), dict) else {}
    env_name = (api.get("maturity_integrity_secret_from_env") or "").strip()
    if env_name:
        raw = (os.environ.get(env_name) or "").strip()
        if raw:
            return raw.encode("utf-8")
    raw = (os.environ.get("DATA_BOAR_MATURITY_INTEGRITY_SECRET") or "").strip()
    if raw:
        return raw.encode("utf-8")
    return None


def canonical_answer_message(
    *,
    batch_id: str,
    locale_slug: str,
    pack_version: int,
    question_id: str,
    answer_text: str,
) -> bytes:
    """Stable byte sequence for HMAC (newline-separated, UTF-8)."""
    parts = (
        HMAC_VERSION,
        batch_id,
        locale_slug,
        str(int(pack_version)),
        question_id,
        answer_text,
    )
    return ("\n".join(parts)).encode("utf-8")


def compute_answer_hmac(
    secret: bytes,
    *,
    batch_id: str,
    locale_slug: str,
    pack_version: int,
    question_id: str,
    answer_text: str,
) -> str:
    """Return 64-char hex HMAC-SHA256."""
    msg = canonical_answer_message(
        batch_id=batch_id,
        locale_slug=locale_slug,
        pack_version=pack_version,
        question_id=question_id,
        answer_text=answer_text,
    )
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def verify_maturity_assessment_rows(
    *,
    secret: bytes | None,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Verify stored rows against recomputed HMACs.

    ``rows`` dicts must include: batch_id, locale_slug, pack_version, question_id,
    answer_text, row_hmac (str, may be empty).

    If ``secret`` is None: cannot verify sealed rows; returns counts only.
    """
    out: dict[str, Any] = {
        "secret_configured": bool(secret),
        "rows_checked": len(rows),
        "rows_ok": 0,
        "rows_mismatch": 0,
        "rows_unsealed": 0,  # empty MAC (written when no secret was configured)
        "rows_unknown_sealed": 0,  # MAC present but secret not available now
    }
    if not rows:
        return out
    for r in rows:
        mac = (r.get("row_hmac") or "").strip().lower()
        if not mac:
            out["rows_unsealed"] += 1
            continue
        if not secret:
            out["rows_unknown_sealed"] += 1
            continue
        got = compute_answer_hmac(
            secret,
            batch_id=str(r.get("batch_id") or ""),
            locale_slug=str(r.get("locale_slug") or ""),
            pack_version=int(r.get("pack_version") or 0),
            question_id=str(r.get("question_id") or ""),
            answer_text=str(r.get("answer_text") or ""),
        ).lower()
        if hmac.compare_digest(mac, got):
            out["rows_ok"] += 1
        else:
            out["rows_mismatch"] += 1
    return out

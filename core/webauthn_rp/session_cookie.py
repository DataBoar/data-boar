"""Signed cookie for WebAuthn session (optional Phase 1; no Starlette SessionMiddleware)."""

from __future__ import annotations

import logging
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

COOKIE_NAME = "db_webauthn"
MAX_AGE_SECONDS = 12 * 3600
SAMESITE = "strict"


def sign_session(secret: str, user_id: bytes, epoch: int = 0) -> str:
    ser = URLSafeTimedSerializer(secret, salt="webauthn-session-v1")
    return ser.dumps({"u": user_id.hex(), "ep": int(epoch)})


def session_payload(
    secret: str, token: str, max_age: int = MAX_AGE_SECONDS
) -> tuple[bytes, int] | None:
    """Signature and expiry. A cookie with no epoch counts as 0."""
    ser = URLSafeTimedSerializer(secret, salt="webauthn-session-v1")
    try:
        data = ser.loads(token, max_age=max_age)
        hx = data.get("u")
        raw_ep = data.get("ep", 0)
        if not isinstance(hx, str):
            return None
        if isinstance(raw_ep, bool) or not isinstance(raw_ep, int) or raw_ep < 0:
            return None
        return bytes.fromhex(hx), raw_ep
    except (BadSignature, SignatureExpired, ValueError, TypeError, KeyError):
        return None


def verify_session_cookie(
    secret: str,
    token: str,
    max_age: int = MAX_AGE_SECONDS,
    *,
    current_epoch: int,
) -> bytes | None:
    """Accept the cookie only when its signed epoch matches the stored one."""
    parsed = session_payload(secret, token, max_age=max_age)
    if parsed is None:
        return None
    uid, token_epoch = parsed
    if token_epoch != int(current_epoch):
        return None
    return uid


def accepted_session_user_id(secret: str, token: str, db_manager: Any) -> bytes | None:
    """User id when signature and stored epoch match. A read error refuses."""
    parsed = session_payload(secret, token)
    if parsed is None:
        return None
    uid, _token_epoch = parsed
    try:
        current = db_manager.webauthn_session_epoch_for_user_id(uid)
    except Exception as exc:
        logging.getLogger(__name__).debug(
            "WebAuthn session epoch read failed (%s)", type(exc).__name__
        )
        return None
    if current is None:
        return None
    return verify_session_cookie(secret, token, current_epoch=current)

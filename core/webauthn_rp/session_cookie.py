"""Signed cookie for WebAuthn session (optional Phase 1; no Starlette SessionMiddleware)."""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

COOKIE_NAME = "db_webauthn"
MAX_AGE_SECONDS = 12 * 3600
SAMESITE = "strict"


def sign_session(secret: str, user_id: bytes) -> str:
    ser = URLSafeTimedSerializer(secret, salt="webauthn-session-v1")
    return ser.dumps({"u": user_id.hex()})


def verify_session_cookie(
    secret: str, token: str, max_age: int = MAX_AGE_SECONDS
) -> bytes | None:
    ser = URLSafeTimedSerializer(secret, salt="webauthn-session-v1")
    try:
        data = ser.loads(token, max_age=max_age)
        hx = data.get("u")
        if not isinstance(hx, str):
            return None
        return bytes.fromhex(hx)
    except (BadSignature, SignatureExpired, ValueError, TypeError, KeyError):
        return None

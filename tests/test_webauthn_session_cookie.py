"""Signed session cookie helpers for WebAuthn Phase 1."""

from core.webauthn_rp.session_cookie import (
    MAX_AGE_SECONDS,
    sign_session,
    verify_session_cookie,
)


def test_sign_verify_roundtrip():
    secret = "test-secret-at-least-16-chars!!"
    uid = b"x" * 32
    tok = sign_session(secret, uid)
    assert verify_session_cookie(secret, tok, max_age=MAX_AGE_SECONDS) == uid


def test_session_max_age_is_twelve_hours():
    assert MAX_AGE_SECONDS == 12 * 3600


def test_verify_rejects_wrong_secret():
    tok = sign_session("secret-a_________________", b"y" * 32)
    assert verify_session_cookie("secret-b_________________", tok) is None

"""Unit tests for HTML CSRF tokens (standalone + WebAuthn signing)."""

from core.webauthn_rp.html_csrf import (
    get_standalone_csrf_secret,
    issue_html_csrf_token,
    reset_standalone_csrf_secret_for_tests,
    resolve_html_csrf_signing_secret,
    verify_html_csrf_token,
)


def test_issue_and_verify_roundtrip():
    secret = "test-secret-minimum-16-chars"
    tok = issue_html_csrf_token(secret)
    assert verify_html_csrf_token(secret, tok) is True


def test_verify_rejects_tampered():
    secret = "test-secret-minimum-16-chars"
    tok = issue_html_csrf_token(secret)
    assert verify_html_csrf_token(secret, tok[:-3] + "xxx") is False


def test_verify_rejects_wrong_secret():
    tok = issue_html_csrf_token("secret-a______________")
    assert verify_html_csrf_token("secret-b______________", tok) is False


def test_verify_rejects_missing_token():
    assert verify_html_csrf_token("test-secret-minimum-16-chars", None) is False
    assert verify_html_csrf_token("test-secret-minimum-16-chars", "") is False


def test_standalone_secret_stable_within_process(monkeypatch):
    reset_standalone_csrf_secret_for_tests()
    monkeypatch.delenv("DATA_BOAR_HTML_CSRF_SECRET", raising=False)
    a = get_standalone_csrf_secret()
    b = get_standalone_csrf_secret()
    assert a == b
    assert len(a) >= 32


def test_standalone_secret_prefers_env(monkeypatch):
    reset_standalone_csrf_secret_for_tests()
    monkeypatch.setenv("DATA_BOAR_HTML_CSRF_SECRET", "env-csrf-secret-16chars")
    assert get_standalone_csrf_secret() == "env-csrf-secret-16chars"


def test_resolve_prefers_webauthn_token_secret(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "webauthn-secret-16ch")
    monkeypatch.setenv("DATA_BOAR_HTML_CSRF_SECRET", "env-csrf-secret-16chars")
    cfg = {"api": {"webauthn": {"enabled": True}}}
    assert resolve_html_csrf_signing_secret(cfg) == "webauthn-secret-16ch"


def test_resolve_falls_back_to_standalone_when_webauthn_off(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_HTML_CSRF_SECRET", "env-csrf-secret-16chars")
    cfg = {"api": {}}
    assert resolve_html_csrf_signing_secret(cfg) == "env-csrf-secret-16chars"

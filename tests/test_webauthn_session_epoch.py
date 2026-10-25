"""WebAuthn session epoch revocation (#2079)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import create_engine, text

from core.database import LocalDBManager, WebAuthnCredential
from core.webauthn_rp.session_cookie import (
    COOKIE_NAME,
    session_payload,
    sign_session,
    verify_session_cookie,
)
from core.webauthn_rp.settings import user_id_bytes, webauthn_block

_SECRET = "unit-test-webauthn-secret-min-16"
_ORIGIN = {"Origin": "http://testserver"}


def _legacy_cookie(uid: bytes) -> str:
    ser = URLSafeTimedSerializer(_SECRET, salt="webauthn-session-v1")
    return ser.dumps({"u": uid.hex()})


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATA_BOAR_WEBAUTHN_TOKEN_SECRET", _SECRET)
    key = "k" * 32
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {tmp_path}/audit.db
api:
  port: 8088
  require_api_key: true
  api_key: "{key}"
  webauthn:
    enabled: true
    rp_id: localhost
    rp_name: Data Boar Test
    origin: http://testserver
    user_display_name: tester
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    import api.routes as routes

    saved = (routes._config_path, routes._config, routes._audit_engine)
    routes._config_path = str(cfg)
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app)
    loaded = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    uid = user_id_bytes(webauthn_block(loaded))
    dbm = routes._get_engine().db_manager
    dbm.webauthn_save_credential(
        user_id=uid,
        credential_id=b"unit-test-credential-id-32bytes!!",
        public_key=b"k" * 64,
        sign_count=0,
    )
    return client, routes, dbm, uid, saved


def _restore(routes, saved) -> None:
    routes._config_path, routes._config, routes._audit_engine = saved


def _scan(client: TestClient, cookie: str):
    client.cookies.set(COOKIE_NAME, cookie)
    return client.post("/scan", json={}, headers=_ORIGIN)


def test_logout_rejects_old_cookie_and_accepts_a_new_one(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        old = sign_session(_SECRET, uid, 0)
        assert _scan(client, old).status_code != 401
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 1
        assert _scan(client, old).status_code == 401
        fresh = sign_session(_SECRET, uid, 1)
        assert _scan(client, fresh).status_code != 401
    finally:
        _restore(routes, saved)


def test_logout_of_one_user_leaves_the_other_cookie(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        other = b"o" * 32
        dbm.webauthn_save_credential(
            user_id=other,
            credential_id=b"other-credential-id-32bytes!!!!!",
            public_key=b"p" * 64,
            sign_count=0,
        )
        other_cookie = sign_session(_SECRET, other, 0)
        mine = sign_session(_SECRET, uid, 0)
        client.cookies.set(COOKIE_NAME, mine)
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        assert _scan(client, other_cookie).status_code != 401
        assert dbm.webauthn_session_epoch_for_user_id(other) == 0
    finally:
        _restore(routes, saved)


def test_second_credential_after_logout_still_signs_in(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        old = sign_session(_SECRET, uid, 0)
        client.cookies.set(COOKIE_NAME, old)
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        dbm.webauthn_save_credential(
            user_id=uid,
            credential_id=b"second-credential-id-32bytes!!!!",
            public_key=b"q" * 64,
            sign_count=1,
        )
        current = dbm.webauthn_session_epoch_for_user_id(uid)
        assert current == 1
        fresh = sign_session(_SECRET, uid, current)
        assert _scan(client, fresh).status_code != 401
        assert _scan(client, old).status_code == 401
    finally:
        _restore(routes, saved)


def test_revoked_cookie_logout_does_not_bump_again(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        old = sign_session(_SECRET, uid, 0)
        client.cookies.set(COOKIE_NAME, old)
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 1
        client.cookies.set(COOKIE_NAME, old)
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 1
        fresh = sign_session(_SECRET, uid, 1)
        client.cookies.set(COOKIE_NAME, fresh)
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 2
        assert _scan(client, fresh).status_code == 401
    finally:
        _restore(routes, saved)


def test_legacy_cookie_without_epoch_dies_after_logout(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        legacy = _legacy_cookie(uid)
        assert session_payload(_SECRET, legacy) == (uid, 0)
        assert _scan(client, legacy).status_code != 401
        client.cookies.set(COOKIE_NAME, legacy)
        assert client.post("/auth/webauthn/logout", headers=_ORIGIN).status_code == 200
        assert _scan(client, legacy).status_code == 401
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 1
    finally:
        _restore(routes, saved)


def test_boolean_epoch_is_refused():
    uid = b"u" * 32
    ser = URLSafeTimedSerializer(_SECRET, salt="webauthn-session-v1")
    token = ser.dumps({"u": uid.hex(), "ep": True})
    assert session_payload(_SECRET, token) is None
    assert verify_session_cookie(_SECRET, token, current_epoch=1) is None
    negative = ser.dumps({"u": uid.hex(), "ep": -1})
    assert session_payload(_SECRET, negative) is None
    missing_user = ser.dumps({"ep": 0})
    assert session_payload(_SECRET, missing_user) is None


def test_forged_epoch_fails_the_signature():
    uid = b"u" * 32
    token = sign_session(_SECRET, uid, 0)
    forged = token[:-4] + ("a" if token[-4] != "a" else "b") + token[-3:]
    assert session_payload(_SECRET, forged) is None
    assert verify_session_cookie(_SECRET, forged, current_epoch=0) is None


def test_epoch_read_error_refuses_the_cookie(tmp_path, monkeypatch):
    client, routes, _dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:

        def _boom(self, user_id: bytes) -> int | None:
            raise RuntimeError("db down")

        monkeypatch.setattr(LocalDBManager, "webauthn_session_epoch_for_user_id", _boom)
        response = _scan(client, sign_session(_SECRET, uid, 0))
        assert response.status_code == 401
    finally:
        _restore(routes, saved)


def test_session_epoch_column_migration_is_idempotent(tmp_path: Path):
    path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE webauthn_credentials ("
                "id INTEGER PRIMARY KEY, user_id BLOB NOT NULL, "
                "credential_id BLOB NOT NULL UNIQUE, public_key BLOB NOT NULL, "
                "sign_count INTEGER NOT NULL, created_at DATETIME, "
                "roles_json VARCHAR(512))"
            )
        )
        conn.execute(
            text(
                "INSERT INTO webauthn_credentials "
                "(user_id, credential_id, public_key, sign_count, roles_json) "
                "VALUES (:u, :c, :p, 3, :r)"
            ),
            {
                "u": b"u" * 32,
                "c": b"cred-id",
                "p": b"k" * 8,
                "r": '["dashboard"]',
            },
        )
    engine.dispose()
    first = LocalDBManager(str(path))
    second = LocalDBManager(str(path))
    session = second._session_factory()
    try:
        row = session.query(WebAuthnCredential).one()
        assert row.session_epoch == 0
        assert int(row.sign_count) == 3
        assert bytes(row.public_key) == b"k" * 8
        assert row.roles_json == '["dashboard"]'
        assert bytes(row.user_id) == b"u" * 32
    finally:
        session.close()
        first.engine.dispose()
        second.engine.dispose()


def test_logout_wrong_origin_does_not_revoke(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        old = sign_session(_SECRET, uid, 0)
        client.cookies.set(COOKIE_NAME, old)
        missing = client.post("/auth/webauthn/logout")
        assert missing.status_code == 403
        wrong = client.post(
            "/auth/webauthn/logout",
            headers={"Origin": "http://sibling.testserver"},
        )
        assert wrong.status_code == 403
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 0
        assert _scan(client, old).status_code != 401
        accepted = client.post("/auth/webauthn/logout", headers=_ORIGIN)
        assert accepted.status_code == 200
        assert dbm.webauthn_session_epoch_for_user_id(uid) == 1
        assert _scan(client, old).status_code == 401
    finally:
        _restore(routes, saved)


def test_sibling_origin_on_scan_is_forbidden(tmp_path, monkeypatch):
    client, routes, _dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        client.cookies.set(COOKIE_NAME, sign_session(_SECRET, uid, 0))
        response = client.post(
            "/scan",
            json={},
            headers={"Origin": "http://sibling.testserver"},
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"] == "Cookie session requires the dashboard origin"
        )
    finally:
        _restore(routes, saved)


def test_user_with_no_credential_rows_is_refused(tmp_path, monkeypatch):
    client, routes, dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        session = dbm._session_factory()
        try:
            session.query(WebAuthnCredential).delete()
            session.commit()
        finally:
            session.close()
        assert dbm.webauthn_session_epoch_for_user_id(uid) is None
        assert _scan(client, sign_session(_SECRET, uid, 0)).status_code == 401
    finally:
        _restore(routes, saved)


def test_cookie_only_request_is_not_limited(tmp_path, monkeypatch):
    client, routes, _dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        for _i in range(5):
            denied = client.get("/status", headers={"X-API-Key": "wrong-secret"})
            assert denied.status_code == 401
        blocked = client.get("/status", headers={"X-API-Key": "k" * 32})
        assert blocked.status_code == 429
        client.cookies.set(COOKIE_NAME, sign_session(_SECRET, uid, 0))
        allowed = client.get("/status")
        assert allowed.status_code != 429
        assert allowed.status_code != 401
    finally:
        _restore(routes, saved)


def test_cookie_and_correct_key_without_origin_is_not_forbidden(tmp_path, monkeypatch):
    client, routes, _dbm, uid, saved = _client(tmp_path, monkeypatch)
    try:
        client.cookies.set(COOKIE_NAME, sign_session(_SECRET, uid, 0))
        response = client.post("/scan", json={}, headers={"X-API-Key": "k" * 32})
        assert response.status_code != 403
    finally:
        _restore(routes, saved)

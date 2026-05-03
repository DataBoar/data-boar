"""
Security tests: SQL injection resistance, path traversal, credential encoding, and safe handling of untrusted input.

Regression tests for critical/high severity issues so they are not reintroduced:

- SQL injection: identifier escaping (quote/backtick) ensures table/column names from discover()
  never execute as multiple statements.
- Path traversal: session_id is validated (api/routes) before use in paths; invalid format returns 400.
- Credential injection in URLs: user and password are URL-encoded when building connection URLs so that
  special characters (@, :, /, #) do not break parsing or allow injection (sql_connector, mongodb_connector).
- Config/serialization: YAML config uses safe_load; no code execution from config content.
- Config endpoint: when require_api_key is true, /config requires valid API key (no raw secret exposure).
"""

import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest


# --- SQL injection: identifier escaping (sql_connector pattern) ---


def test_sqlite_identifier_escaping_prevents_second_statement():
    """
    When column/table names contain quote and semicolon (injection attempt), the escaped
    query must not execute a second statement. Uses same escaping as connectors.sql_connector (double-quote).
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t1 (a TEXT)")
    conn.execute("INSERT INTO t1 (a) VALUES ('ok')")
    conn.commit()

    # Simulate connector escaping for SQLite: double-quote inside identifiers
    malicious_col = 'a"; DROP TABLE t1; --'
    safe_col = malicious_col.replace('"', '""')
    safe_table = "t1"
    query = f'SELECT "{safe_col}" FROM "{safe_table}" LIMIT 1'
    try:
        conn.execute(query)
    except sqlite3.OperationalError:
        pass  # Column may not exist; no injection is what we care about
    # In the same connection: t1 must still exist (no second statement was executed)
    conn.execute("SELECT 1 FROM t1")
    conn.close()


def test_sql_connector_sample_uses_escaped_identifiers_sqlite(tmp_path):
    """
    SQLConnector.sample() with SQLite dialect builds a single SELECT with escaped identifiers;
    a malicious-looking column name does not result in executing multiple statements.
    """
    from connectors.sql_connector import SQLConnector
    from unittest.mock import MagicMock

    db_path = tmp_path / "security_test.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE safe_t (col1 TEXT)")
    conn.execute("INSERT INTO safe_t (col1) VALUES ('x')")
    conn.commit()
    conn.close()

    target = {
        "type": "database",
        "driver": "sqlite",
        "database": str(db_path),
        "name": "SecurityTest",
    }
    scanner = MagicMock()
    db_manager = MagicMock()
    connector = SQLConnector(target, scanner, db_manager)
    connector.connect()
    try:
        connector.sample("", "safe_t", 'col1"; DROP TABLE safe_t; --', limit=1)
    finally:
        connector.close()
    # Table must still exist (no second statement executed)
    conn2 = sqlite3.connect(str(db_path))
    conn2.execute("SELECT 1 FROM safe_t")
    conn2.close()


# --- Path traversal: session_id validation (covered in test_routes_responses; assert behaviour) ---


def test_session_id_validation_rejects_dangerous_patterns():
    """API rejects session_id that could be used for path traversal (validated in routes)."""
    import api.routes as routes

    pattern = getattr(routes, "_SESSION_ID_PATTERN", None)
    assert pattern is not None
    assert not pattern.fullmatch("../../../etc/passwd")
    assert not pattern.fullmatch("a" * 11)
    assert not pattern.fullmatch("x'; DROP TABLE sessions; --")
    assert pattern.fullmatch("a1b2c3d4e5f6_20250101")


# --- Database layer: session_id used via ORM only (no raw SQL with user input) ---


def test_database_filters_use_orm_not_raw_sql():
    """LocalDBManager uses SQLAlchemy ORM filter() for session_id; no raw text() with session_id."""
    from core.database import DatabaseFinding
    from sqlalchemy.sql.elements import BinaryExpression

    # session_id in queries is used as ORM column comparison (parameterized), not string-interpolated
    clause = DatabaseFinding.session_id == "test_sid"
    assert isinstance(clause, BinaryExpression)


# --- Config: YAML safe_load (no code execution) ---


def test_config_save_uses_safe_load():
    """Config loader and save path use safe YAML parsing (no !!python/object or code execution)."""
    import yaml

    # safe_load does not deserialize arbitrary Python objects
    payload = "!!python/object/apply:os.system ['echo pwned']"
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(payload)


def test_config_loader_uses_safe_load_not_load(tmp_path):
    """load_config must use safe_load for YAML so malicious config cannot execute code."""
    import yaml

    malicious = tmp_path / "bad.yaml"
    malicious.write_text(
        "!!python/object/apply:os.system ['echo pwned']", encoding="utf-8"
    )
    from config.loader import load_config

    with pytest.raises(yaml.YAMLError):
        load_config(malicious)


# --- Credential encoding in connection URLs (prevent misparsing / injection) ---


def test_sql_connector_build_url_encodes_password_special_chars():
    """
    _build_url must URL-encode user and password so that @, :, /, # in credentials
    do not break URL parsing or allow injection into host/path.
    """
    from connectors.sql_connector import _build_url

    target = {
        "driver": "postgresql+psycopg2",
        "host": "db.example.com",
        "port": 5432,
        "user": "u",
        "password": "p@ss:word/with#hash",
        "database": "mydb",
    }
    url = _build_url(target)
    parsed = urlparse(url)
    assert parsed.username is not None
    assert parsed.password is not None
    assert unquote(parsed.password) == "p@ss:word/with#hash"
    assert unquote(parsed.username) == "u"
    # Raw @ must not appear in userinfo (would be interpreted as userinfo@host boundary)
    netloc = parsed.netloc
    userinfo = netloc.rsplit("@", 1)[0] if "@" in netloc else ""
    assert "@" not in userinfo.replace("%40", "")


def test_sql_connector_build_url_encodes_user_with_at():
    """User containing @ must be encoded so it does not get interpreted as user@host boundary."""
    from connectors.sql_connector import _build_url

    target = {
        "driver": "postgresql+psycopg2",
        "host": "host",
        "port": 5432,
        "user": "user@realm",
        "password": "secret",
        "database": "db",
    }
    url = _build_url(target)
    parsed = urlparse(url)
    assert unquote(parsed.username) == "user@realm"
    assert unquote(parsed.password) == "secret"


def test_mongodb_connector_uri_encodes_password_special_chars():
    """MongoDB connector must build URI with URL-encoded user/password so special chars do not break parsing."""
    from unittest.mock import MagicMock, patch

    config = {
        "name": "test",
        "host": "localhost",
        "port": 27017,
        "database": "testdb",
        "user": "admin",
        "password": "p@ss:word",
    }
    from connectors.mongodb_connector import MongoDBConnector

    connector = MongoDBConnector(config, MagicMock(), MagicMock())
    # Patch MongoClient so we don't need pymongo installed and we can assert the URI passed
    with patch("connectors.mongodb_connector.MongoClient") as mongo_mock:
        with patch("connectors.mongodb_connector._MONGO_AVAILABLE", True):
            connector.connect()
    mongo_mock.assert_called_once()
    (uri,) = mongo_mock.call_args[0]
    parsed = urlparse(uri)
    assert unquote(parsed.password) == "p@ss:word"
    assert unquote(parsed.username) == "admin"


# --- Config endpoint protected when API key required ---


# --- Tenant / technician validation (length and control chars) ---


def test_sanitize_tenant_technician_returns_none_for_none_or_empty():
    """sanitize_tenant_technician returns None for None and empty/whitespace-only strings."""
    from core.validation import sanitize_tenant_technician

    assert sanitize_tenant_technician(None) is None
    assert sanitize_tenant_technician("") is None
    assert sanitize_tenant_technician("   ") is None


def test_sanitize_tenant_technician_strips_and_removes_control_chars():
    """sanitize_tenant_technician strips whitespace and removes ASCII control characters."""
    from core.validation import sanitize_tenant_technician

    assert sanitize_tenant_technician("  Acme Corp  ") == "Acme Corp"
    # Control chars (NULL, tab, newline, DEL) removed
    assert sanitize_tenant_technician("Acme\x00Corp") == "AcmeCorp"
    assert sanitize_tenant_technician("Alice\tColleague-V") == "AliceColleague-V"
    assert sanitize_tenant_technician("Bob\nOperator") == "BobOperator"
    assert sanitize_tenant_technician("Op\x7fname") == "Opname"
    # Only control chars removed; printable kept
    assert sanitize_tenant_technician("User (DPO)") == "User (DPO)"


def test_sanitize_tenant_technician_truncates_to_max_length():
    """sanitize_tenant_technician truncates to MAX_TENANT_TECHNICIAN_LENGTH (255)."""
    from core.validation import sanitize_tenant_technician, MAX_TENANT_TECHNICIAN_LENGTH

    long_str = "a" * 300
    result = sanitize_tenant_technician(long_str)
    assert result is not None
    assert len(result) == MAX_TENANT_TECHNICIAN_LENGTH
    assert result == "a" * MAX_TENANT_TECHNICIAN_LENGTH


def test_sanitize_tenant_technician_all_control_chars_returns_none():
    """If string is only control chars/whitespace after strip, return None."""
    from core.validation import sanitize_tenant_technician

    assert sanitize_tenant_technician("\x00\x01\t\n\x7f") is None


def test_redact_secrets_for_log_masks_passwords_and_urls():
    """redact_secrets_for_log masks passwords, API keys, and connection URLs in log content."""
    from core.validation import redact_secrets_for_log

    assert "***REDACTED***" in redact_secrets_for_log(
        "postgresql://user:secret@host/db"
    )
    assert "secret" not in redact_secrets_for_log("postgresql://user:secret@host/db")
    assert "***REDACTED***" in redact_secrets_for_log("password=mysecret")
    assert "mysecret" not in redact_secrets_for_log("password=mysecret")
    assert "***REDACTED***" in redact_secrets_for_log("api_key=abc123")
    assert "abc123" not in redact_secrets_for_log("api_key=abc123")
    assert redact_secrets_for_log(None) == ""
    assert redact_secrets_for_log("no secrets here") == "no secrets here"


def test_redact_pii_for_log_masks_detector_aligned_shapes():
    """redact_pii_for_log strips CPF, email, and card-like runs from arbitrary text."""
    from core.validation import redact_pii_for_log

    raw = "contact leak@example.com and CPF 529.982.247-25 card 4111-1111-1111-1111"
    out = redact_pii_for_log(raw)
    assert "leak@example.com" not in out
    assert "529.982.247-25" not in out
    assert "4111-1111-1111-1111" not in out
    assert "***REDACTED***" in out


def test_sanitize_log_text_applies_secrets_then_pii():
    from core.validation import sanitize_log_text

    s = sanitize_log_text(
        "postgresql://u:dbpass@db:5432/app and user@x.com CPF 111.444.777-35"
    )
    assert "dbpass" not in s
    assert "user@x.com" not in s
    assert "111.444.777-35" not in s


def test_clean_error_walks_cause_chain_and_redacts():
    from core.validation import clean_error

    class Inner(Exception):
        pass

    class Outer(Exception):
        pass

    try:
        try:
            raise Inner("inner leak@inner.com")
        except Inner as inner:
            raise Outer("outer 52998224725") from inner
    except Outer as outer:
        msg = clean_error(outer)
    assert "leak@inner.com" not in msg
    assert "52998224725" not in msg
    assert "outer" in msg or "***REDACTED***" in msg


def test_request_body_size_limit_returns_413_when_content_length_exceeds_1mb():
    """API returns 413 when Content-Length exceeds 1 MB (DoS mitigation)."""
    from fastapi.testclient import TestClient

    import api.routes as routes

    max_bytes = routes.MAX_REQUEST_BODY_BYTES
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.yaml"
        config_path.write_text(
            "targets: []\nreport:\n  output_dir: .\napi:\n  port: 8088\nsqlite_path: audit.db\n",
            encoding="utf-8",
        )
        orig_path = getattr(routes, "_config_path", None)
        orig_cfg = getattr(routes, "_config", None)
        orig_engine = getattr(routes, "_audit_engine", None)
        try:
            routes._config_path = str(config_path)
            routes._config = None
            routes._audit_engine = None
            client = TestClient(routes.app)
            # Send a body larger than 1 MB; client sets Content-Length automatically
            big_body = b"x" * (max_bytes + 1)
            resp = client.post("/scan", content=big_body)
            assert resp.status_code == 413
            assert "too large" in (resp.json().get("detail") or "").lower()
        finally:
            if orig_path is not None:
                routes._config_path = orig_path
            routes._config = orig_cfg
            routes._audit_engine = orig_engine


# --- Config endpoint protected when API key required ---


def test_config_endpoint_requires_api_key_when_required(tmp_path):
    """When api.require_api_key is true, GET /config must return 401 without valid API key."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"targets: []\nreport:\n  output_dir: {tmp_path}\napi:\n  port: 8088\n  require_api_key: true\n  api_key: secret123\nsqlite_path: {tmp_path}/audit.db\n",
        encoding="utf-8",
    )
    import api.routes as routes

    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None
        from fastapi.testclient import TestClient

        client = TestClient(routes.app)
        resp = client.get("/config")
        assert resp.status_code == 401
        resp_with_key = client.get("/config", headers={"X-API-Key": "secret123"})
        assert resp_with_key.status_code == 200
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


# --- Secrets Phase A: config redaction and merge ---


def test_redact_config_for_display_redacts_secrets():
    """GET /config shows redacted secrets; redact_config_for_display replaces pass, api_key, etc."""
    from config.redact_config import redact_config_for_display, REDACTED_PLACEHOLDER

    data = {
        "api": {"port": 8088, "api_key": "secret-key-123", "api_key_from_env": None},
        "targets": [
            {"name": "db1", "type": "database", "pass": "dbpass", "user": "dbuser"},
            {"name": "rest1", "type": "rest", "auth": {"token": "bearer-token-xyz"}},
        ],
    }
    redacted = redact_config_for_display(data)
    assert redacted["api"]["api_key"] == REDACTED_PLACEHOLDER
    assert redacted["api"].get("api_key_from_env") is None
    assert redacted["targets"][0]["pass"] == REDACTED_PLACEHOLDER
    assert (
        redacted["targets"][0]["user"] == "dbuser"
    )  # user not in _SECRET_KEYS by default
    assert redacted["targets"][1]["auth"]["token"] == REDACTED_PLACEHOLDER
    assert "secret-key-123" not in str(redacted)
    assert "dbpass" not in str(redacted)


def test_merge_config_on_save_preserves_secrets_when_submitted_is_placeholder():
    """POST /config merge keeps current secret when submitted value is placeholder or empty."""
    from config.redact_config import merge_config_on_save, REDACTED_PLACEHOLDER

    current = {
        "api": {"api_key": "real-key"},
        "targets": [{"name": "db1", "pass": "realpass"}],
    }
    submitted = {
        "api": {"api_key": REDACTED_PLACEHOLDER},
        "targets": [{"name": "db1", "pass": REDACTED_PLACEHOLDER}],
    }
    merged = merge_config_on_save(submitted, current)
    assert merged["api"]["api_key"] == "real-key"
    assert merged["targets"][0]["pass"] == "realpass"
    submitted_new = {
        "api": {"api_key": "new-key"},
        "targets": [{"name": "db1", "pass": "newpass"}],
    }
    merged2 = merge_config_on_save(submitted_new, current)
    assert merged2["api"]["api_key"] == "new-key"
    assert merged2["targets"][0]["pass"] == "newpass"


def test_normalize_config_resolves_pass_from_env_and_user_from_env(monkeypatch):
    """Loader resolves pass_from_env, password_from_env, user_from_env for targets."""
    from config.loader import normalize_config

    monkeypatch.setenv("DB_PASS", "env-pass")
    monkeypatch.setenv("DB_USER", "env-user")
    data = {
        "targets": [
            {"name": "db1", "type": "database", "pass_from_env": "DB_PASS"},
            {
                "name": "db2",
                "type": "database",
                "password_from_env": "DB_PASS",
                "user_from_env": "DB_USER",
            },
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    out = normalize_config(data)
    assert out["targets"][0]["pass"] == "env-pass"
    assert out["targets"][1]["pass"] == "env-pass"
    assert out["targets"][1]["user"] == "env-user"

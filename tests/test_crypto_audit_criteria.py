"""Phase 2a: strong-crypto criteria (evaluate_strong_crypto / TLS normalize)."""

from __future__ import annotations

from sqlalchemy import create_engine

from core.crypto_audit import (
    CryptoProbeFacts,
    StrongCryptoResult,
    _canonical_http_scheme,
    _canonical_smb_dialect,
    _canonical_ssl_cert_reqs,
    _canonical_sslmode,
    _normalize_tls_version,
    _safe_httpx_probe_path,
    _sslmode_from_connection_string,
    collect_httpx_crypto_facts,
    collect_mongodb_crypto_facts,
    collect_redis_crypto_facts,
    collect_smb_crypto_facts,
    collect_sql_crypto_facts,
    evaluate_strong_crypto,
    infer_controls_from_identifiers,
    resolve_httpx_tls_connect_options,
    resolve_nosql_tls_connect_options,
    resolve_smb_connect_options,
    summarize_crypto_from_connection_info,
)


def test_normalize_tls_version_common_labels() -> None:
    assert _normalize_tls_version("TLSv1.3") == "TLSv1.3"
    assert _normalize_tls_version("TLS 1.2") == "TLSv1.2"
    assert _normalize_tls_version("1.1") == "TLSv1.1"


def test_sqlite_is_not_applicable() -> None:
    result, details = evaluate_strong_crypto(CryptoProbeFacts(source="sqlite"))
    assert result is StrongCryptoResult.NOT_APPLICABLE
    assert "SQLite" in details


def test_tls13_ok() -> None:
    result, details = evaluate_strong_crypto(
        CryptoProbeFacts(
            tls_in_use=True,
            tls_version="TLSv1.3",
            sslmode="verify-full",
            source="pg_stat_ssl",
        )
    )
    assert result is StrongCryptoResult.OK
    assert "TLSv1.3" in details


def test_tls12_with_require_is_warning() -> None:
    result, _ = evaluate_strong_crypto(
        CryptoProbeFacts(
            tls_in_use=True,
            tls_version="TLSv1.2",
            sslmode="require",
            source="pg_stat_ssl",
        )
    )
    assert result is StrongCryptoResult.WARNING


def test_tls10_is_fail() -> None:
    result, details = evaluate_strong_crypto(
        CryptoProbeFacts(tls_in_use=True, tls_version="TLSv1.0", source="pg_stat_ssl")
    )
    assert result is StrongCryptoResult.FAIL
    assert "below 1.2" in details


def test_tls_disabled_is_fail() -> None:
    result, _ = evaluate_strong_crypto(
        CryptoProbeFacts(tls_in_use=False, source="pg_stat_ssl")
    )
    assert result is StrongCryptoResult.FAIL


def test_sslmode_disable_is_fail() -> None:
    result, _ = evaluate_strong_crypto(
        CryptoProbeFacts(sslmode="disable", source="config_sslmode")
    )
    assert result is StrongCryptoResult.FAIL


def test_config_verify_full_without_live_tls_is_ok() -> None:
    result, details = evaluate_strong_crypto(
        CryptoProbeFacts(sslmode="verify-full", source="config_sslmode")
    )
    assert result is StrongCryptoResult.OK
    assert "verify" in details.lower()


def test_no_facts_is_not_available() -> None:
    result, _ = evaluate_strong_crypto(CryptoProbeFacts(source="unavailable"))
    assert result is StrongCryptoResult.NOT_AVAILABLE


def test_canonical_sslmode_allowlist_never_keeps_dsn_tail() -> None:
    assert _canonical_sslmode("require") == "require"
    assert _canonical_sslmode("verify-full") == "verify-full"
    # Contaminated extract (old &-only split on libpq DSN): first token may
    # match allowlist, but the secret tail must never remain in the value.
    contaminated = "require password=super-secret-value user=app"
    assert _canonical_sslmode(contaminated) == "require"
    assert "secret" not in (_canonical_sslmode(contaminated) or "")
    assert _canonical_sslmode("not-a-real-mode password=super-secret-value") is None
    assert (
        _sslmode_from_connection_string(
            "host=db.example.com sslmode=require password=super-secret-value"
        )
        == "require"
    )


def test_evaluate_drops_contaminated_sslmode_from_details() -> None:
    """Defense in depth: even if CryptoProbeFacts carries a DSN tail, details stay clean."""
    secret = "evaluate-must-not-echo-this-password"
    result, details = evaluate_strong_crypto(
        CryptoProbeFacts(
            sslmode=f"require password={secret}",
            source="config_sslmode",
        )
    )
    assert secret not in details
    assert "password=" not in details.lower()
    assert result is StrongCryptoResult.WARNING  # sslmode canonicalizes to require


def test_libpq_dsn_password_after_sslmode_never_leaks_into_details() -> None:
    """
    Regression: libpq keyword=value DSNs use spaces, not '&'.

    Naive ``split('&')`` after ``sslmode=`` captured ``require password=...``
    and persisted it into strong_crypto_details / the Crypto & controls sheet.
    """
    secret = "super-secret-libpq-password-XYZ"
    dsn = f"host=db.example.com port=5432 user=app sslmode=require password={secret}"
    eng = create_engine("sqlite:///:memory:")
    facts = collect_sql_crypto_facts(eng, {"dsn": dsn, "name": "pg-libpq"})
    assert secret not in (facts.sslmode or "")
    assert "password" not in (facts.sslmode or "").lower()
    # Space-aware + allowlist → clean token (or None); never the DSN tail.
    assert facts.sslmode in (None, "require")
    result, details = evaluate_strong_crypto(facts)
    assert secret not in details
    assert "password=" not in details.lower()
    assert secret not in result.value

    # Phase 1 coarse signals path must not retain the secret either.
    signals = summarize_crypto_from_connection_info(
        {
            "driver": "postgresql+psycopg2",
            "dsn": dsn,
        }
    )
    blob = " ".join(sorted(s.value for s in signals))
    assert secret not in blob
    assert "password=" not in blob


def test_resolve_nosql_tls_from_config_and_uri_scheme() -> None:
    enabled, posture, cert = resolve_nosql_tls_connect_options({"tls": True})
    assert enabled is True
    assert posture == "verify-full"
    assert cert == "required"

    enabled, posture, cert = resolve_nosql_tls_connect_options(
        {"tls": True, "tls_insecure": True}
    )
    assert enabled is True
    assert posture == "require"
    assert cert == "none"

    enabled, posture, _ = resolve_nosql_tls_connect_options(
        {"uri": "mongodb+srv://cluster.example.com"}
    )
    assert enabled is True
    assert posture == "verify-full"

    enabled, posture, cert = resolve_nosql_tls_connect_options(
        {"url": "rediss://localhost:6666"}
    )
    assert enabled is True
    assert posture == "verify-full"
    assert cert == "required"

    enabled, posture, _ = resolve_nosql_tls_connect_options({"tls": False})
    assert enabled is False
    assert posture == "disable"


def test_canonical_ssl_cert_reqs_allowlist() -> None:
    assert _canonical_ssl_cert_reqs("required") == "required"
    assert _canonical_ssl_cert_reqs("none&password=secret") == "none"
    assert _canonical_ssl_cert_reqs("required password=secret") == "required"
    assert _canonical_ssl_cert_reqs("not-a-real-mode") is None


def test_nosql_uri_password_after_tls_never_leaks_into_details() -> None:
    """
    Regression (Phase 2c): space/ampersand-naive URI parse must not put
    password=... into sslmode / strong_crypto_details.
    """
    secret = "nosql-super-secret-password-ABC"
    mongo_uri = (
        f"mongodb://app:{secret}@db.example.com:27017/appdb?tls=true&authSource=admin"
    )
    # Contaminated libpq-style tail after tls= (same class as sslmode bug).
    dirty = f"tls=true password={secret} ssl_cert_reqs=none"

    enabled, posture, cert = resolve_nosql_tls_connect_options({"uri": mongo_uri})
    assert enabled is True
    assert posture in ("verify-full", "require", "prefer")
    assert secret not in (posture or "")
    assert secret not in (cert or "")

    enabled2, posture2, cert2 = resolve_nosql_tls_connect_options({"uri": dirty})
    assert enabled2 is True
    assert secret not in (posture2 or "")
    assert secret not in (cert2 or "")
    assert cert2 in (None, "none", "optional", "required")

    class _BoomClient:
        """Collector must not need a live server; ping may fail."""

        @property
        def options(self):
            raise RuntimeError("no options")

        @property
        def admin(self):
            raise RuntimeError("no admin")

        @property
        def connection_pool(self):
            raise RuntimeError("no pool")

    facts_m = collect_mongodb_crypto_facts(
        _BoomClient(), {"uri": mongo_uri, "tls": True}
    )
    facts_r = collect_redis_crypto_facts(
        _BoomClient(),
        {"url": f"rediss://:{secret}@localhost:6666", "ssl_cert_reqs": "none"},
    )
    for facts in (facts_m, facts_r):
        assert secret not in (facts.sslmode or "")
        assert secret not in (facts.source or "")
        assert secret not in (facts.cipher or "")
        result, details = evaluate_strong_crypto(facts)
        assert secret not in details
        assert "password=" not in details.lower()
        assert secret not in result.value


def test_collect_redis_crypto_facts_from_ssl_socket() -> None:
    class _FakeSSLSock:
        def version(self):
            return "TLSv1.3"

        def cipher(self):
            return ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)

    class _FakeConn:
        _sock = _FakeSSLSock()
        ssl = True

    class _FakePool:
        def __init__(self):
            self._conn = _FakeConn()

        def get_connection(self, *_a, **_k):
            return self._conn

        def release(self, *_a, **_k):
            return None

    class _FakeRedis:
        connection_pool = _FakePool()

    facts = collect_redis_crypto_facts(
        _FakeRedis(), {"tls": True, "ssl_cert_reqs": "required"}
    )
    assert facts.source == "redis_ssl_socket"
    assert facts.tls_in_use is True
    assert facts.tls_version == "TLSv1.3"
    assert facts.cipher == "TLS_AES_256_GCM_SHA384"
    assert facts.sslmode == "verify-full"
    result, details = evaluate_strong_crypto(facts)
    assert result is StrongCryptoResult.OK
    assert "TLSv1.3" in details


def test_canonical_smb_dialect_allowlist() -> None:
    assert _canonical_smb_dialect(0x0311) == "SMB_3_1_1"
    assert _canonical_smb_dialect("SMB_3_0_2") == "SMB_3_0_2"
    assert _canonical_smb_dialect("SMB_3_1_1 password=secret") == "SMB_3_1_1"
    assert _canonical_smb_dialect(0x9999) is None
    assert _canonical_smb_dialect("not-a-dialect") is None


def test_resolve_smb_connect_options() -> None:
    assert resolve_smb_connect_options({}) == (None, None)
    assert resolve_smb_connect_options({"encrypt": True}) == (True, None)
    assert resolve_smb_connect_options(
        {"smb_encrypt": False, "require_signing": False}
    ) == (False, False)


def test_smb_3_signing_encryption_is_ok() -> None:
    result, details = evaluate_strong_crypto(
        CryptoProbeFacts(
            source="smb_session",
            smb_dialect="SMB_3_1_1",
            smb_signing="required",
            smb_encryption="on",
        )
    )
    assert result is StrongCryptoResult.OK
    assert "SMB_3_1_1" in details
    assert "encryption=on" in details


def test_smb_signing_without_encryption_is_warning() -> None:
    result, details = evaluate_strong_crypto(
        CryptoProbeFacts(
            source="smb_session",
            smb_dialect="SMB_3_0_2",
            smb_signing="required",
            smb_encryption="off",
        )
    )
    assert result is StrongCryptoResult.WARNING
    assert "signed without encryption" in details.lower() or "encryption=off" in details


def test_smb_signing_disabled_is_fail() -> None:
    result, _details = evaluate_strong_crypto(
        CryptoProbeFacts(
            source="smb_session",
            smb_dialect="SMB_3_1_1",
            smb_signing="disabled",
            smb_encryption="off",
        )
    )
    assert result is StrongCryptoResult.FAIL


def test_collect_smb_crypto_facts_and_password_never_leaks() -> None:
    secret = "smb-super-secret-password-XYZ"

    class _Conn:
        dialect = 0x0311
        require_signing = True
        supports_encryption = True

    class _Session:
        connection = _Conn()
        signing_required = True
        encrypt_data = True
        username = f"user\\\\with\\\\{secret}"
        password = secret

    facts = collect_smb_crypto_facts(
        _Session(),
        {
            "password": secret,
            "pass": secret,
            "host": "fileserver.example.com",
            "share": "secretshare",
        },
    )
    assert facts.source == "smb_session"
    assert facts.smb_dialect == "SMB_3_1_1"
    assert facts.smb_signing == "required"
    assert facts.smb_encryption == "on"
    result, details = evaluate_strong_crypto(facts)
    assert secret not in details
    assert "password=" not in details.lower()
    assert "fileserver" not in details
    assert "secretshare" not in details
    assert result is StrongCryptoResult.OK


def test_resolve_httpx_tls_and_scheme_allowlist() -> None:
    assert resolve_httpx_tls_connect_options({}) is None
    assert resolve_httpx_tls_connect_options({"verify": True}) is True
    assert resolve_httpx_tls_connect_options({"verify_ssl": False}) is False
    assert _canonical_http_scheme("https://api.example.com/v1") == "https"
    assert _canonical_http_scheme("http://legacy.example.com") == "http"
    assert (
        _canonical_http_scheme("https://api.example.com/?token=secret-value") == "https"
    )
    assert _canonical_http_scheme("ftp://files.example.com") is None
    assert _safe_httpx_probe_path("/users") == "/users"
    assert _safe_httpx_probe_path("/users?token=abc") == "/"
    assert _safe_httpx_probe_path("https://evil.example/path") == "/"


def test_collect_httpx_plaintext_is_fail() -> None:
    class _Client:
        base_url = "http://api.example.com"

        def stream(self, *_a, **_k):  # pragma: no cover - must not be called
            raise AssertionError("plaintext must not open TLS stream")

    facts = collect_httpx_crypto_facts(
        _Client(), {"base_url": "http://api.example.com"}
    )
    assert facts.tls_in_use is False
    assert facts.source == "httpx_plaintext"
    result, details = evaluate_strong_crypto(facts)
    assert result is StrongCryptoResult.FAIL
    assert "httpx_plaintext" in details


def test_collect_httpx_https_and_secrets_never_leak() -> None:
    secret = "Bearer-leak-token-XYZ-9f3a"
    client_secret = "oauth-client-secret-LEAK-42"

    class _Sock:
        def version(self):
            return "TLSv1.3"

        def cipher(self):
            return ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)

    class _Net:
        def get_extra_info(self, name):
            if name == "socket":
                return _Sock()
            return None

    class _Resp:
        extensions = {"network_stream": _Net()}

        def read(self):
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    class _Client:
        base_url = f"https://api.example.com/tenant?token={secret}"

        def stream(self, method, path, params=None):
            assert method == "GET"
            # Contaminated probe must be sanitized before request.
            assert "?" not in path
            assert secret not in path
            assert params is None or secret not in str(params)
            return _Resp()

    facts = collect_httpx_crypto_facts(
        _Client(),
        {
            "base_url": f"https://api.example.com/?token={secret}",
            "client_secret": client_secret,
            "auth": {"type": "bearer", "token": secret},
            "verify": True,
        },
        probe_url=f"/v1/me?access_token={secret}",
    )
    assert facts.source == "httpx_ssl_socket"
    assert facts.tls_version == "TLSv1.3"
    assert facts.sslmode == "verify-full"
    result, details = evaluate_strong_crypto(facts)
    assert result is StrongCryptoResult.OK
    assert secret not in details
    assert client_secret not in details
    assert "Bearer" not in details
    assert "token=" not in details.lower()
    assert "client_secret" not in details.lower()
    assert "api.example.com" not in details
    assert "access_token" not in details


def test_collect_httpx_verify_false_maps_to_require() -> None:
    class _Client:
        base_url = "https://api.example.com"

        def stream(self, *_a, **_k):
            raise OSError("offline")

    facts = collect_httpx_crypto_facts(
        _Client(),
        {"base_url": "https://api.example.com", "verify_ssl": False},
    )
    assert facts.sslmode == "require"
    assert facts.tls_in_use is True
    result, details = evaluate_strong_crypto(facts)
    assert result is StrongCryptoResult.WARNING
    assert "require" in details


def test_collect_httpx_probe_does_not_read_response_body() -> None:
    """Hostile/large bodies must not be drained during the TLS socket probe."""

    class _Sock:
        def version(self):
            return "TLSv1.3"

        def cipher(self):
            return ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)

    class _Net:
        def get_extra_info(self, name):
            return _Sock() if name == "socket" else None

    class _Resp:
        def __init__(self) -> None:
            self.extensions = {"network_stream": _Net()}
            self.read_calls = 0

        def read(self):
            self.read_calls += 1
            return b"x" * (8 * 1024 * 1024)

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    resp = _Resp()

    class _Client:
        base_url = "https://api.example.com"

        def stream(self, *_a, **_k):
            return resp

    facts = collect_httpx_crypto_facts(
        _Client(), {"base_url": "https://api.example.com"}
    )
    assert facts.source == "httpx_ssl_socket"
    assert facts.tls_version == "TLSv1.3"
    assert resp.read_calls == 0


def test_infer_controls_from_identifiers_counts_without_listing_names() -> None:
    sensitive_name = "customer_cpf_hash"
    summary = infer_controls_from_identifiers(
        [
            sensitive_name,
            "email_masked",
            "token_session",
            "anon_user_id",
            "pseudonym_ref",
            "plain_email",
            "id",
            b"hash_payload",
        ]
    )
    assert summary is not None
    assert "3 names suggest hashing" in summary or "2 names suggest hashing" in summary
    # hashing: customer_cpf_hash + hash_payload = 2; masking 1; tokenization 1; anonymization 2
    assert "hashing" in summary
    assert "masking" in summary
    assert "tokenization" in summary
    assert "anonymization" in summary
    assert "human review required" in summary
    assert sensitive_name not in summary
    assert "cpf" not in summary
    assert "email_masked" not in summary
    assert "plain_email" not in summary


def test_infer_controls_from_identifiers_empty_when_no_match() -> None:
    assert infer_controls_from_identifiers(["email", "phone", "created_at"]) is None


def test_infer_controls_metadata_hints_allowlisted_only() -> None:
    summary = infer_controls_from_identifiers(
        ["id"],
        metadata_hints=["masking", "DROP TABLE users; --", "masking"],
    )
    assert summary is not None
    assert "metadata hint" in summary
    assert "DROP" not in summary
    assert "users" not in summary

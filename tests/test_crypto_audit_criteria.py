"""Phase 2a: strong-crypto criteria (evaluate_strong_crypto / TLS normalize)."""

from __future__ import annotations

from sqlalchemy import create_engine

from core.crypto_audit import (
    CryptoProbeFacts,
    StrongCryptoResult,
    _canonical_sslmode,
    _normalize_tls_version,
    _sslmode_from_connection_string,
    collect_sql_crypto_facts,
    evaluate_strong_crypto,
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

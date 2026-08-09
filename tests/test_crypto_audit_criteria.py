"""Phase 2a: strong-crypto criteria (evaluate_strong_crypto / TLS normalize)."""

from __future__ import annotations

from core.crypto_audit import (
    CryptoProbeFacts,
    StrongCryptoResult,
    _normalize_tls_version,
    evaluate_strong_crypto,
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

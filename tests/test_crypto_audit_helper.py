from __future__ import annotations

from core.crypto_audit import StrongCryptoSignal, summarize_crypto_from_connection_info


def test_https_rest_target_emits_transport_tls() -> None:
    info = {"type": "api", "base_url": "https://api.example.com"}
    signals = summarize_crypto_from_connection_info(info)
    assert StrongCryptoSignal.TRANSPORT_TLS in signals
    assert StrongCryptoSignal.TRANSPORT_PLAINTEXT not in signals


def test_http_rest_target_emits_transport_plaintext() -> None:
    info = {"type": "api", "base_url": "http://legacy.example.com"}
    signals = summarize_crypto_from_connection_info(info)
    assert StrongCryptoSignal.TRANSPORT_PLAINTEXT in signals
    assert StrongCryptoSignal.TRANSPORT_TLS not in signals


def test_postgres_dsn_with_sslmode_require_emits_db_tls_required() -> None:
    info = {
        "type": "database",
        "driver": "postgresql+psycopg2",
        "dsn": "postgresql+psycopg2://user:pass@host:5432/dbname?sslmode=require",
    }
    signals = summarize_crypto_from_connection_info(info)
    assert StrongCryptoSignal.DB_TLS_REQUIRED in signals
    assert StrongCryptoSignal.DB_TLS_DISABLED not in signals


def test_postgres_with_sslmode_disable_emits_db_tls_disabled() -> None:
    info = {
        "type": "database",
        "driver": "postgresql+psycopg2",
        "dsn": "postgresql+psycopg2://user:pass@host:5432/dbname?sslmode=disable",
    }
    signals = summarize_crypto_from_connection_info(info)
    assert StrongCryptoSignal.DB_TLS_DISABLED in signals
    assert StrongCryptoSignal.DB_TLS_REQUIRED not in signals

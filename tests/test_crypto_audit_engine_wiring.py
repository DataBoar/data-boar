from __future__ import annotations

from core.crypto_audit import StrongCryptoSignal
from core.engine import AuditEngine


def test_audit_engine_collects_crypto_signals_for_postgres_like_target(
    monkeypatch,
) -> None:
    # Minimal config with one database target; sqlite path is unused thanks to dummy db manager.
    config = {
        "targets": [
            {
                "name": "pg-secure",
                "type": "database",
                "driver": "postgresql+psycopg2",
                "dsn": "postgresql+psycopg2://user:pass@host:5432/db?sslmode=require",
            }
        ],
        "file_scan": {
            "extensions": [".txt"],
        },
        "detection": {},
        # Opt-in: crypto signal collection is gated behind scan.validate_crypto.
        "scan": {"validate_crypto": True},
    }

    # Stub connector_for_target to avoid hitting real connectors or databases.
    class DummyConnector:
        def __init__(self, *args, **kwargs):
            pass

        def run(self) -> None:
            # No-op: we only care about wiring before run() is invoked.
            return None

    def fake_connector_for_target(target):
        return DummyConnector, target

    from core import engine as engine_mod

    monkeypatch.setattr(
        engine_mod, "connector_for_target", fake_connector_for_target, raising=True
    )

    eng = AuditEngine(config)
    eng._run_audit_targets()

    # Internal crypto signals should contain an entry for our target with DB_TLS_REQUIRED.
    names_and_signals = {name: sigs for name, sigs in eng.crypto_signals}
    assert "pg-secure" in names_and_signals
    assert StrongCryptoSignal.DB_TLS_REQUIRED in names_and_signals["pg-secure"]

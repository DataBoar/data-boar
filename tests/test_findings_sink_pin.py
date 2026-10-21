"""Findings sink must connect to the IP the SSRF guard already accepted (#2097)."""

from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError


def test_sql_sink_connect_uses_validated_ip(tmp_path, monkeypatch) -> None:
    from core.database import LocalDBManager
    from core.findings_sink import push_session_to_sink

    db = tmp_path / "audit.db"
    mgr = LocalDBManager(str(db))
    sid = "sink-pin-01"
    mgr.create_session_record(sid)
    monkeypatch.setattr(
        "connectors.url_guard.resolve_and_validate_outbound_url",
        lambda *_a, **_k: (None, ["203.0.113.10"]),
    )
    monkeypatch.setattr("core.findings_sink._require_sink_tier", lambda *_a, **_k: None)
    captured: dict = {}

    def _engine(url, **kwargs):
        captured["url"] = str(url)
        captured["kwargs"] = kwargs
        engine = MagicMock()
        engine.begin.side_effect = SQLAlchemyError("stop-after-capture")
        return engine

    monkeypatch.setattr("core.findings_sink.create_engine", _engine)
    try:
        push_session_to_sink(
            {
                "licensing": {"effective_tier": "pro"},
                "findings_sink": {
                    "enabled": True,
                    "type": "postgresql",
                    "host": "sink.example.test",
                    "port": 5432,
                    "database": "findings",
                    "user": "sink",
                    "pass": "dummy",
                },
            },
            mgr,
            sid,
        )
    except Exception:
        pass
    blob = captured["url"] + str(captured["kwargs"])
    assert "203.0.113.10" in blob
    assert "sink.example.test" not in captured["url"] or "203.0.113.10" in blob


def test_mongodb_connector_uses_direct_connection(monkeypatch) -> None:
    import connectors.mongodb_connector as mongo

    monkeypatch.setattr(mongo, "_MONGO_AVAILABLE", True)
    captured: dict = {}

    def _client(uri, **kwargs):
        captured["uri"] = uri
        captured["kwargs"] = kwargs
        client = MagicMock()
        client.__getitem__.return_value = MagicMock()
        return client

    monkeypatch.setattr(mongo, "MongoClient", _client)
    monkeypatch.setattr(
        "connectors.url_guard.resolve_and_validate_outbound_url",
        lambda *_a, **_k: (None, ["203.0.113.10"]),
    )
    connector = mongo.MongoDBConnector(
        {"host": "seed.test", "port": 27017, "database": "app"},
        scanner=None,
        db_manager=None,
    )
    connector.connect()
    try:
        assert captured["kwargs"].get("directConnection") is True
    finally:
        connector.close()

"""Tests for utils/notify.py (webhook POST; no real network)."""

from __future__ import annotations

import json
import urllib.error

import pytest

from utils.notify import (
    _SCAN_COMPLETE_OK_SESSIONS,
    build_scan_complete_message,
    notify_scan_complete_sync,
    send_all_operator_notifications,
    send_manual_operator_message,
    send_slack_webhook,
    send_to_first_configured_operator_channel,
    should_send_scan_complete_notification,
)


def test_send_slack_rejects_http_url():
    with pytest.raises(ValueError, match="https"):
        send_slack_webhook("http://hooks.example/hook", "nope")


def test_build_scan_complete_message_includes_session_and_counts():
    text = build_scan_complete_message(
        {
            "session_id": "sess_abc",
            "status": "completed",
            "high": 1,
            "medium": 2,
            "low": 3,
            "total_findings": 6,
            "dob_possible_minor": 0,
            "scan_failures": 0,
            "tenant_name": "T1",
            "technician_name": None,
        },
        public_base_url="https://example.test:8088",
    )
    assert "sess_abc" in text
    assert "HIGH: 1" in text
    assert "Base URL (se configurada):" in text
    assert "example.test:8088" in text


def test_should_send_respects_enabled_and_filters():
    cfg = {"notifications": {"enabled": False, "on_scan_complete": True}}
    summary = {"status": "completed", "high": 5, "dob_possible_minor": 0}
    assert should_send_scan_complete_notification(cfg, summary) is False

    cfg2 = {
        "notifications": {
            "enabled": True,
            "on_scan_complete": True,
            "notify_only_if_high_or_critical": True,
        }
    }
    assert (
        should_send_scan_complete_notification(
            cfg2, {"status": "completed", "high": 0, "dob_possible_minor": 0}
        )
        is False
    )
    assert (
        should_send_scan_complete_notification(
            cfg2, {"status": "completed", "high": 1, "dob_possible_minor": 0}
        )
        is True
    )


def test_should_send_completed_errors():
    cfg = {
        "notifications": {
            "enabled": True,
            "on_scan_complete": False,
            "notify_on_failure": True,
        }
    }
    assert (
        should_send_scan_complete_notification(
            cfg, {"status": "completed_errors", "high": 0, "dob_possible_minor": 0}
        )
        is True
    )
    cfg["notifications"]["notify_on_failure"] = False
    assert (
        should_send_scan_complete_notification(
            cfg, {"status": "completed_errors", "high": 0, "dob_possible_minor": 0}
        )
        is False
    )


def test_send_slack_uses_json_post(monkeypatch):
    captured: dict[str, bytes] = {}

    def fake_urlopen(req, timeout=None):
        captured["body"] = req.data

        class R:
            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    n = {
        "operator": {
            "slack_webhook_url": "https://hooks.slack.example/services/XXX",
        }
    }
    ch, ok, err = send_to_first_configured_operator_channel(n, "hello")
    assert ok is True
    assert ch == "slack"
    assert captured["body"] is not None
    payload = json.loads(captured["body"].decode())
    assert payload.get("text") == "hello"


def test_send_no_channel_returns_error():
    ch, ok, err = send_to_first_configured_operator_channel({}, "x")
    assert ok is False
    assert ch is None
    assert "no operator" in (err or "").lower()


def test_send_slack_retries_once_on_502(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise urllib.error.HTTPError("http://hook", 502, "Bad", {}, None)

        class R:
            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("utils.notify.time.sleep", lambda *_a, **_k: None)
    send_slack_webhook("https://hooks.example/hook", "hi")
    assert calls["n"] == 2


def test_send_all_operator_channels_two_slacks(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1

        class R:
            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    n = {
        "operator": {
            "channels": [
                {"slack_webhook_url": "https://hooks.slack.example/a"},
                {"slack_webhook_url": "https://hooks.slack.example/b"},
            ]
        }
    }
    results = send_all_operator_notifications(n, "hello")
    assert len(results) == 2
    assert all(r[1] for r in results)
    assert calls["n"] == 2


def test_notify_scan_complete_dedupe_skips_second_post(monkeypatch):
    _SCAN_COMPLETE_OK_SESSIONS.clear()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1

        class R:
            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    class FakeDB:
        def get_session_scan_summary_for_notification(self, sid):
            return {
                "session_id": sid,
                "status": "completed",
                "high": 1,
                "medium": 0,
                "low": 0,
                "total_findings": 1,
                "dob_possible_minor": 0,
                "scan_failures": 0,
                "tenant_name": None,
                "technician_name": None,
            }

    cfg = {
        "notifications": {
            "enabled": True,
            "dedupe_scan_complete_per_session": True,
            "operator": {"slack_webhook_url": "https://hooks.example/h"},
        }
    }
    notify_scan_complete_sync(cfg, FakeDB(), "sess_dedupe_1")
    notify_scan_complete_sync(cfg, FakeDB(), "sess_dedupe_1")
    assert calls["n"] == 1


def test_send_manual_operator_message_records_audit(monkeypatch):
    """Manual Part-A sends append notification_send_log rows when db_manager is set."""
    audit_rows: list[dict] = []

    class FakeDB:
        def record_notification_send_log(self, **kwargs):
            audit_rows.append(kwargs)

    def fake_urlopen(req, timeout=None):
        class R:
            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    cfg = {
        "notifications": {
            "enabled": True,
            "notify_audit_log": True,
            "operator": {"slack_webhook_url": "https://hooks.example/manual"},
        }
    }
    ch, ok, err = send_manual_operator_message(cfg, "hello op", db_manager=FakeDB())
    assert ok is True
    assert ch == "slack"
    assert err is None
    assert len(audit_rows) == 1
    assert audit_rows[0]["trigger"] == "manual"
    assert audit_rows[0]["recipient"] == "operator"
    assert audit_rows[0]["channel"] == "slack"
    assert audit_rows[0]["session_id"] is None
    assert audit_rows[0]["success"] is True


def test_notify_scan_complete_tenant_channel(monkeypatch):
    _SCAN_COMPLETE_OK_SESSIONS.clear()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1

        class R:
            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    class FakeDB:
        def get_session_scan_summary_for_notification(self, sid):
            return {
                "session_id": sid,
                "status": "completed",
                "high": 1,
                "medium": 0,
                "low": 0,
                "total_findings": 1,
                "dob_possible_minor": 0,
                "scan_failures": 0,
                "tenant_name": "ACME Corp",
                "technician_name": None,
            }

    cfg = {
        "notifications": {
            "enabled": True,
            "dedupe_scan_complete_per_session": False,
            "operator": {"slack_webhook_url": "https://hooks.example/op"},
            "tenant": {
                "by_tenant": {
                    "acme corp": {
                        "slack_webhook_url": "https://hooks.example/tenant-acme"
                    },
                },
            },
        }
    }
    notify_scan_complete_sync(cfg, FakeDB(), "sess_tenant_1")
    assert calls["n"] == 2

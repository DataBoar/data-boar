import core.runtime_trust as runtime_trust


def test_runtime_trust_snapshot_trusted_for_open_mode():
    snap = runtime_trust.get_runtime_trust_snapshot({})
    assert snap["license_state"] == "OPEN"
    assert snap["trust_state"] == "trusted"
    assert snap["trust_level"] == "expected"
    assert snap["is_unexpected"] is False


def test_runtime_trust_snapshot_untrusted_for_unlicensed_mode(monkeypatch):
    class _Ctx:
        state = "UNLICENSED"
        mode = "enforced"
        detail = "missing token"
        watermark = "UNLICENSED"

    class _Guard:
        context = _Ctx()

    monkeypatch.setattr(runtime_trust, "get_license_guard", lambda _cfg: _Guard())
    snap = runtime_trust.get_runtime_trust_snapshot({})
    assert snap["license_state"] == "UNLICENSED"
    assert snap["trust_state"] == "untrusted"
    assert snap["trust_level"] == "unexpected"
    assert snap["is_unexpected"] is True

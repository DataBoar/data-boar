"""SSRF-style URL guard on scripts/poll_dashboard_scan.py (#529)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO = Path(__file__).resolve().parents[1]
_POLL = _REPO / "scripts" / "poll_dashboard_scan.py"


def _load_poll():
    spec = importlib.util.spec_from_file_location("poll_dashboard_scan", _POLL)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_get_json_rejects_file_scheme() -> None:
    poll = _load_poll()
    with pytest.raises(ValueError):
        poll.get_json("file:///etc/passwd", "/status")


def test_get_json_allows_loopback_and_calls_urlopen() -> None:
    poll = _load_poll()
    payload = json.dumps({"running": False}).encode()
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = payload
    cm.__exit__.return_value = None
    with patch.object(poll.urllib.request, "urlopen", return_value=cm) as opener:
        out = poll.get_json("http://127.0.0.1:8088", "/status")
    assert out["running"] is False
    opener.assert_called_once()
    req = opener.call_args[0][0]
    assert req.full_url == "http://127.0.0.1:8088/status"


def test_assert_dashboard_url_rejects_file() -> None:
    poll = _load_poll()
    with pytest.raises(ValueError):
        poll._assert_dashboard_url("file:///tmp/x")

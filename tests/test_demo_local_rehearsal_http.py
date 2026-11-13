"""The rehearsal helper talks only to the local Boar (#1447): http(s) on loopback."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_PATH = Path(__file__).resolve().parents[1] / "deploy" / "demo-local" / "rehearsal.py"


def _load():
    spec = importlib.util.spec_from_file_location("demo_local_rehearsal", _PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses resolve the module by name
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://127.0.0.1/x",
        "http://example.com/status",
        "https://10.0.0.5:8089/status",
    ],
)
def test_http_refuses_non_loopback_or_non_http_urls(url):
    mod = _load()
    with patch.object(mod.urllib.request, "urlopen") as urlopen:
        with pytest.raises(ValueError):
            mod._http(url)
    urlopen.assert_not_called()


@pytest.mark.parametrize("url", ["http://127.0.0.1:8089/status", "https://localhost/s"])
def test_http_allows_loopback(url):
    mod = _load()
    with patch.object(mod.urllib.request, "urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = b"{}"
        assert mod._http(url) == {}

"""Hermetic HOME / XDG for licensing path tests (#1940)."""

from __future__ import annotations

from pathlib import Path

import pytest


def isolate_user_config_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point HOME (and unset XDG/APPDATA) so canonical license.jwt is absent."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    return home

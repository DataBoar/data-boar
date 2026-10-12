"""Hermetic HOME / XDG / Windows profile dirs for licensing path tests (#1940)."""

from __future__ import annotations

from pathlib import Path

import pytest


def isolate_user_config_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolate user config resolution under ``tmp_path`` on any OS."""
    home = tmp_path / "home"
    roaming = home / "AppData" / "Roaming"
    home.mkdir(parents=True)
    roaming.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return home

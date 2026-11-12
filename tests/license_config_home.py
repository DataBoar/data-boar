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


# Environment that can change the outcome of a "no token" evaluation (#2226).
LICENSE_ENV_VARS_CLEARED: tuple[str, ...] = (
    "DATA_BOAR_LICENSE_PATH",
    "DATA_BOAR_LICENSE_MODE",
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_REVOCATION_PATH",
    "DATA_BOAR_TIER_OVERRIDE",
)


def isolate_license_environment(monkeypatch: pytest.MonkeyPatch, sandbox: Path) -> Path:
    """Make "no token" independent of the machine running the test (#2226).

    Points ``HOME`` / ``USERPROFILE`` / ``APPDATA`` / ``XDG_CONFIG_HOME`` at ``sandbox`` (so
    ``<user config dir>/databoar/license.jwt`` is never the developer's) and drops the license
    and tier environment variables. Explicit ``licensing.license_path`` config values still work.
    Returns the simulated home.
    """
    from core.licensing import reset_license_guard_for_tests

    home = sandbox / "home"
    xdg = sandbox / "xdg"
    roaming = home / "AppData" / "Roaming"
    for d in (home, xdg, roaming):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    for name in LICENSE_ENV_VARS_CLEARED:
        monkeypatch.delenv(name, raising=False)
    reset_license_guard_for_tests()
    return home

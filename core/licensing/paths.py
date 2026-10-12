"""
Org-wide canonical license JWT path resolution (#1940).

Precedence is implemented in ``resolve_license_path``; ``LicenseGuard`` consumes it.
No platformdirs dependency — XDG / Darwin / Windows rules match license-studio deploy.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ORG_CONFIG_DIR_NAME = "databoar"
LICENSE_JWT_FILENAME = "license.jwt"


def user_config_dir() -> Path:
    """Return the OS user configuration directory (no trailing org segment)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata and appdata.strip():
            return Path(appdata.strip())
        profile = os.environ.get("USERPROFILE", "").strip()
        base = Path(profile) if profile else Path.home()
        return base / "AppData" / "Roaming"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def canonical_org_license_jwt_path() -> Path:
    """``<user_config_dir>/databoar/license.jwt`` (org name, not repo slug)."""
    return user_config_dir() / ORG_CONFIG_DIR_NAME / LICENSE_JWT_FILENAME


def resolve_license_path(config_license_path: str | None) -> str:
    """
    Resolve which license file path to use.

    Order: ``DATA_BOAR_LICENSE_PATH`` (if non-empty after strip) →
    ``licensing.license_path`` from config (if non-empty after strip) →
    canonical path only when both are unset/blank **and** the canonical file exists.

    Explicit env/config values are returned even when the file is missing (fail closed).
    """
    env_raw = os.environ.get("DATA_BOAR_LICENSE_PATH")
    if env_raw is not None:
        env_stripped = env_raw.strip()
        if env_stripped:
            return env_stripped
    cfg_stripped = (config_license_path or "").strip()
    if cfg_stripped:
        return cfg_stripped
    canonical = canonical_org_license_jwt_path()
    if canonical.is_file():
        return str(canonical)
    return ""

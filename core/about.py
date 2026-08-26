"""
Application about information (name, version, author, license) for reports, API and UI.
Single source of truth aligned with LICENSE and README in the repository.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# docs/VERSIONING.md checklist §2 — keep identical to pyproject.toml ``[project].version``.
_FALLBACK_VERSION = "1.8.0-beta"


def _package_version() -> str:
    """Return ``[project].version`` from ``pyproject.toml`` (VERSIONING.md source of truth)."""
    path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        with path.open("rb") as handle:
            ver = tomllib.load(handle).get("project", {}).get("version")
        if ver:
            return str(ver)
    except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError):
        pass
    return _FALLBACK_VERSION


def format_release_advisory(payload: object | None) -> str:
    """Format the Report info Advisory line. Never empty; never raises.

    ``None`` / unloadable → ``unknown`` (air-gap). No ``sev`` → ``none``.
    Pending ``sev`` is loud text only — not a command (#1765).
    """
    try:
        if not isinstance(payload, dict):
            return "unknown"
        sev = payload.get("sev")
        if sev is None or str(sev).strip() == "" or str(sev).strip().lower() == "none":
            return "none"
        parts = [f"sev={sev}"]
        current = payload.get("current") or payload.get("from")
        target = payload.get("target") or payload.get("to")
        if current and target:
            parts.append(f"{current} → {target}")
        parts.append("fix disponível")
        seen = payload.get("seen_at") or payload.get("observed_at")
        if seen:
            parts.append(f"visto em {seen}")
        text = " · ".join(str(p) for p in parts if p)
        return text if text.strip() else "unknown"
    except Exception:
        return "unknown"


def _release_advisory_payload() -> dict | None:
    """Optional beacon/cache payload. Fail-open: never raise into reports."""
    return None


def get_http_user_agent() -> str:
    """
    Default User-Agent for outbound HTTP(S) from Data Boar (REST/API discovery, OAuth token
    requests, SharePoint, Power BI, Dataverse). Operators may override per-target via config headers.
    """
    return f"DataBoar-Prospector/{_package_version()}"


def get_about_info() -> dict:
    """
    Return application name, version, author and license (same as LICENSE and README).
    Used by the API /about page, Excel report "Report info" sheet, heatmap image footer,
    and dashboard/reports web pages.

    #856 (Phase E): when the integrity anchor flags tampering, the version is
    forced to the ``-alpha`` label ("development / not CI-validated") so every
    surface that renders about info shows the TINTED state.
    """
    from core.integrity_anchor import ALPHA_NOTE, get_integrity_snapshot

    snap = get_integrity_snapshot()
    tampered = snap.get("integrity_state") == "tampered"
    ver = _package_version()
    if tampered:
        ver = f"{ver}-alpha ({ALPHA_NOTE})"
    return {
        "name": "Data Boar",
        "version": ver,
        "integrity_state": snap.get("integrity_state", "unknown"),
        "build_trust": snap.get("trust_level", "unknown"),
        "advisory": format_release_advisory(_release_advisory_payload()),
        # Note: the template already prints `about.name` before `about.description`,
        # so `description` must not repeat the product name.
        "description": "Audits personal and sensitive data across databases and filesystems, aligned with LGPD, GDPR, CCPA, HIPAA, and GLBA.",
        "author": "Fabio Leitao",
        "license": "BSD 3-Clause License",
        "license_url": "https://opensource.org/licenses/BSD-3-Clause",
        "copyright": "Copyright (c) 2025-2026, Fabio Leitao",
    }

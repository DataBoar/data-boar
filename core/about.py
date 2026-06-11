"""
Application about information (name, version, author, license) for reports, API and UI.
Single source of truth aligned with LICENSE and README in the repository.
"""


def _package_version() -> str:
    """Installed distribution version, or the same fallback string as get_about_info."""
    try:
        from importlib.metadata import version

        return version("data-boar")
    except Exception:
        return "1.7.4"


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
    """
    ver = _package_version()
    return {
        "name": "Data Boar",
        "version": ver,
        # Note: the template already prints `about.name` before `about.description`,
        # so `description` must not repeat the product name.
        "description": "Audits personal and sensitive data across databases and filesystems, aligned with LGPD, GDPR, CCPA, HIPAA, and GLBA.",
        "author": "Fabio Leitao",
        "license": "BSD 3-Clause License",
        "license_url": "https://opensource.org/licenses/BSD-3-Clause",
        "copyright": "Copyright (c) 2025-2026, Fabio Leitao",
    }

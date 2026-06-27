"""Regression: runtime version string matches pyproject.toml (single source of truth)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
from packaging.version import Version


def _project_version_from_pyproject() -> str:
    root = Path(__file__).resolve().parent.parent
    with (root / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    return str(data["project"]["version"])


def _fallback_version_in_about_source() -> str:
    """String used when importlib.metadata has no distribution (see docs/VERSIONING.md)."""
    root = Path(__file__).resolve().parent.parent
    text = (root / "core" / "about.py").read_text(encoding="utf-8")
    m = re.search(r"except Exception:\s*\n\s*return \"([^\"]+)\"", text)
    assert m is not None, (
        'expected fallback `return "..."` after `except Exception:` in core/about.py '
        "(_package_version)"
    )
    return m.group(1)


def test_about_version_matches_pyproject() -> None:
    """Installed/metadata path must agree with repo `version =` (see docs/VERSIONING.md)."""
    from core.about import get_about_info

    expected = _project_version_from_pyproject()
    # importlib.metadata returns PEP 440-normalized strings (e.g. 1.7.2b0 vs 1.7.2-beta in pyproject).
    assert Version(get_about_info()["version"]) == Version(expected)


def test_about_fallback_string_matches_pyproject() -> None:
    """Bump checklist: `core/about.py` except-branch must track `pyproject.toml`."""
    assert _fallback_version_in_about_source() == _project_version_from_pyproject()


def test_http_user_agent_is_data_boar_prospector() -> None:
    """Outbound HTTP(S) from connectors identifies as DataBoar-Prospector/<version>."""
    from core.about import get_about_info, get_http_user_agent

    ua = get_http_user_agent()
    assert ua.startswith("DataBoar-Prospector/")
    assert get_about_info()["version"] in ua


@pytest.mark.parametrize(
    "path,label",
    [
        ("docs/data_boar.1", "man section 1"),
        ("docs/data_boar.5", "man section 5"),
    ],
)
def test_man_th_line_contains_project_version(path: str, label: str) -> None:
    """`.TH` fourth argument uses the marketing string (for example ``Data Boar 1.7.2-beta``).

    While ``pyproject.toml`` carries a PEP 440 pre-release suffix (for example ``1.7.4-rc``),
    the man pages may already advertise the final **minor.patch** semver on ``main``
    preparatory commits (release checklist: ``docs/releases/1.7.4.md``, issue **#641**).
    """
    root = Path(__file__).resolve().parent.parent
    pv = Version(_project_version_from_pyproject())
    text = (root / path).read_text(encoding="utf-8")
    first = next((ln for ln in text.splitlines() if ln.startswith(".TH")), "")
    m = re.search(r'"Data Boar\s+([^"]+)"', first)
    assert m is not None, (
        f"{label}: expected a fourth-argument marketing string matching "
        f'\\"Data Boar <version>\\" in {first!r}'
    )
    marketing = Version(m.group(1))
    allowed_prep = pv.is_prerelease and marketing == Version(pv.base_version)
    allowed_post = pv.is_postrelease and marketing == Version(pv.base_version)
    assert marketing == pv or allowed_prep or allowed_post, (
        f"{label}: man marketing {marketing!r} disagrees with pyproject {pv!r} "
        "(no GA prep/post exemption)"
    )

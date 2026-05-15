"""Regression guards for transitive deps that must stay upper-bounded by upstream caps.

These tests do not run the resolver and do not hit the network. They read
``pyproject.toml`` and ``.github/dependabot.yml`` as text and assert that the
operator-agreed contract is still present.

- ADR 0053: ``ebcdic`` cap (``extract-msg`` chain).
- ADR 0054: ``chardet`` cap (``cyclonedx-bom`` / SBOM chain).

When an upstream package relaxes its transitive cap, remove the matching
assertions in the same PR that drops the pin, the ``ignore`` rule, and updates
this module.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
DEPENDABOT_YML = REPO_ROOT / ".github" / "dependabot.yml"


def _pyproject_text() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def _dependabot_text() -> str:
    return DEPENDABOT_YML.read_text(encoding="utf-8")


def test_ebcdic_upper_bound_present_in_pyproject() -> None:
    """``ebcdic`` must be capped ``<2`` while extract-msg 0.55.x requires it."""
    text = _pyproject_text()
    pattern = re.compile(r'"ebcdic\s*>=\s*1\.1\.1\s*,\s*<\s*2"')
    assert pattern.search(text) is not None, (
        "pyproject.toml must declare 'ebcdic>=1.1.1,<2' as a direct dependency. "
        "If extract-msg upstream has relaxed its 'ebcdic<2' constraint, update "
        "pyproject.toml, .github/dependabot.yml ignore rule, and this test together. "
        "See docs/adr/ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md."
    )


def test_ebcdic_dependabot_ignore_present() -> None:
    """Dependabot must ignore ``ebcdic`` semver-major version-update PRs."""
    text = _dependabot_text()
    has_dependency = re.search(r'dependency-name:\s*"ebcdic"', text) is not None
    has_major_block = re.search(r"version-update:\s*semver-major", text) is not None
    assert has_dependency and has_major_block, (
        ".github/dependabot.yml must keep the ignore entry for 'ebcdic' major "
        "version-update PRs while extract-msg 0.55.x caps it. "
        "See docs/adr/ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md."
    )


def test_extract_msg_still_pinned_at_or_above_0_55() -> None:
    """If extract-msg drops below 0.55 the ebcdic cap may no longer be needed."""
    text = _pyproject_text()
    assert '"extract-msg>=0.55.0"' in text, (
        "pyproject.toml must keep 'extract-msg>=0.55.0' aligned with the "
        "ebcdic<2 cap. If you are bumping extract-msg, check the new release's "
        "requires_dist on PyPI before touching docs/adr/ADR-0053."
    )


def test_chardet_dev_upper_bound_present_in_pyproject() -> None:
    """``chardet`` must stay ``<6`` in the dev group while cyclonedx-bom requires it."""
    text = _pyproject_text()
    pattern = re.compile(r'"chardet\s*>=\s*5\.1\s*,\s*<\s*6\.0"')
    assert pattern.search(text) is not None, (
        "pyproject.toml dev group must declare 'chardet>=5.1,<6.0'. "
        "See docs/adr/ADR-0054-chardet-pinned-by-cyclonedx-bom.md."
    )


def test_chardet_dependabot_ignore_present() -> None:
    """Dependabot must ignore ``chardet`` semver-major bumps."""
    text = _dependabot_text()
    has_chardet = re.search(r'dependency-name:\s*"chardet"', text) is not None
    assert has_chardet, (
        ".github/dependabot.yml must keep the ignore entry for 'chardet'. "
        "See docs/adr/ADR-0054-chardet-pinned-by-cyclonedx-bom.md."
    )

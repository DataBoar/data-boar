"""Regression guards for transitive deps that must stay upper-bounded by upstream caps.

These tests do not run the resolver and do not hit the network. They read
``pyproject.toml`` and ``.github/dependabot.yml`` as text and assert that the
operator-agreed contract is still present. See
``docs/adr/ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md`` for the
motivating incident (SBOM red on PR #346, GitHub Actions run 25879925361).

When an upstream package relaxes its transitive cap, remove the corresponding
entry from this file in the same PR that drops the pin from ``pyproject.toml``
and the ``ignore`` rule from ``dependabot.yml`` — keeping the three artefacts
in lock-step is the durable closure (ADR 0030 + ADR 0044 + ADR 0053).
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
    """``ebcdic`` must be capped ``<2`` while extract-msg 0.55.x requires it.

    extract-msg 0.55.0 requires_dist declares ``ebcdic<2 and >=1.1.1``. Without an
    explicit Data Boar pin, Dependabot keeps proposing ``ebcdic 2.x`` PRs that
    cannot resolve (ResolutionImpossible at image build time — see ADR 0053).
    """
    text = _pyproject_text()
    pattern = re.compile(r'"ebcdic\s*>=\s*1\.1\.1\s*,\s*<\s*2"')
    assert pattern.search(text) is not None, (
        "pyproject.toml must declare 'ebcdic>=1.1.1,<2' as a direct dependency. "
        "If extract-msg upstream has relaxed its 'ebcdic<2' constraint, update "
        "pyproject.toml, .github/dependabot.yml ignore rule, and this test together. "
        "See docs/adr/ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md."
    )


def test_ebcdic_dependabot_ignore_present() -> None:
    """Dependabot must ignore ``ebcdic`` semver-major version-update PRs.

    The ``ignore`` directive blocks Dependabot ``version-update`` PRs only;
    security advisories still surface, so this does not silence CVE alerts.
    """
    text = _dependabot_text()
    # The block we look for is intentionally specific to avoid passing on a
    # cosmetic 'ignore:' block that does not actually cover ebcdic.
    has_dependency = re.search(r'dependency-name:\s*"ebcdic"', text) is not None
    has_major_block = re.search(r"version-update:\s*semver-major", text) is not None
    assert has_dependency and has_major_block, (
        ".github/dependabot.yml must keep the ignore entry for 'ebcdic' major "
        "version-update PRs while extract-msg 0.55.x caps it. "
        "See docs/adr/ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md."
    )


def test_extract_msg_still_pinned_at_or_above_0_55() -> None:
    """If extract-msg drops below 0.55 the ebcdic cap may no longer be needed.

    This test exists to make removing the ``ebcdic`` cap a *deliberate* edit:
    the operator must update extract-msg first (verifying the new release also
    relaxes the ``ebcdic`` constraint), then this test will guide the cleanup.
    """
    text = _pyproject_text()
    assert '"extract-msg>=0.55.0"' in text, (
        "pyproject.toml must keep 'extract-msg>=0.55.0' aligned with the "
        "ebcdic<2 cap. If you are bumping extract-msg, check the new release's "
        "requires_dist on PyPI before touching docs/adr/ADR-0053."
    )

"""
Guardrail: real talent pool URLs stay in gitignored JSON; tracked talent.ps1 stays thin.

**Policy:** At most **one** placeholder `example.com/profile/...` URL may appear in **tracked**
`scripts/talent.ps1`. Additional profile URLs belong in **`docs/private/commercial/talent_pool.json`**
(loaded at runtime), not duplicated inline in the script.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TALENT_PS1 = REPO_ROOT / "scripts" / "talent.ps1"

# LinkedIn public profile path (tracked file only — not private JSON).
_LINKEDIN_IN_PATH = re.compile(r"linkedin\.com/in/[^\s\"'`]+", re.IGNORECASE)


def test_talent_ps1_tracked_has_at_most_one_linkedin_in_url() -> None:
    if not TALENT_PS1.is_file():
        pytest.skip("scripts/talent.ps1 not present")
    text = TALENT_PS1.read_text(encoding="utf-8", errors="replace")
    matches = _LINKEDIN_IN_PATH.findall(text)
    assert len(matches) <= 1, (
        "scripts/talent.ps1 must contain at most one example.com/profile/ URL (placeholder). "
        f"Found {len(matches)}: {matches!r}. "
        "Add real profiles to docs/private/commercial/talent_pool.json instead."
    )

"""
Guardrail: tracked talent/session helper scripts must use generic placeholders only.

Real pool aliases, PDF names, and LinkedIn slugs belong in gitignored
``docs/private/commercial/talent_pool.json`` (or equivalent), not in public tree.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

SESSION_COLLECT = REPO_ROOT / "scripts" / "session-collect.ps1"


def test_session_collect_linkedin_examples_use_candidate_placeholders_only() -> None:
    """foreach / Write-Info examples must use candidate_a..d style, not real aliases."""
    if not SESSION_COLLECT.is_file():
        pytest.skip("scripts/session-collect.ps1 not present")
    text = SESSION_COLLECT.read_text(encoding="utf-8", errors="replace")
    # Allow candidate_* tokens only in talent.ps1 hint lines / foreach arrays.
    bad = re.findall(
        r"talent\.ps1\s+linkedin\s+([a-z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )
    for token in bad:
        assert token.startswith("candidate_"), (
            f"session-collect.ps1: public example must use candidate_* placeholder, got {token!r}"
        )


def test_session_collect_foreach_array_only_candidate_placeholders() -> None:
    if not SESSION_COLLECT.is_file():
        pytest.skip("scripts/session-collect.ps1 not present")
    text = SESSION_COLLECT.read_text(encoding="utf-8", errors="replace")
    m = re.search(
        r"foreach\s*\(\s*\$candidato\s+in\s+@\(\s*([^)]+)\s*\)\s*\)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert m, "expected foreach ($candidato in @(...)) block in session-collect.ps1"
    inner = m.group(1)
    entries = re.findall(r'"([^"]+)"', inner)
    assert entries, "foreach array should list quoted placeholders"
    for e in entries:
        assert re.match(r"^candidate_[a-z0-9_]+$", e), (
            f"session-collect.ps1: foreach entry must be candidate_* only, got {e!r}"
        )

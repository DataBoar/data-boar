"""
Regression guard: .cursorrules must not exist in the repository.

The legacy JSON `.cursorrules` file was used by older Cursor versions (pre-0.43).
Modern Cursor uses `.cursor/rules/*.mdc` files exclusively. All content that was
in `.cursorrules` has been migrated to `alwaysApply: true` `.mdc` rules, ADRs,
and skills. Having `.cursorrules` present would create a false impression that
those rules are active when they may be silently ignored by the current Cursor
version.

Migration completed: 2026-05-12. Reference: commit 817cdf5.
See `.cursor/rules/linguistic-rigor-and-performance.mdc`,
`.cursor/rules/operator-notification-channels.mdc`, ADR-0047, ADR-0048, ADR-0049,
and `.cursor/skills/linguistic-rigor-active-voice/SKILL.md`.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_no_legacy_cursorrules_file() -> None:
    """`.cursorrules` must not exist — all content lives in `.cursor/rules/*.mdc`."""
    legacy_path = REPO_ROOT / ".cursorrules"
    assert not legacy_path.exists(), (
        ".cursorrules detected in the repository root. "
        "This legacy JSON file is ignored by Cursor 0.43+. "
        "Migrate any new rules to .cursor/rules/*.mdc (alwaysApply: true for global policy) "
        "and delete .cursorrules. See commit 817cdf5 for the migration history."
    )

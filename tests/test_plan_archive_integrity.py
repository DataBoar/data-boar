"""Guard against overclaim in archived plans (docs/plans/completed/).

An archived plan must not use an unqualified **Status:** (bare "Completed") while
phase tables still show open ⬜ rows. Open rows must be labelled Deferred, N/A, etc.

See PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md phase G and
docs/plans/completed/ audit (2026-06-29).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPLETED_DIR = ROOT / "docs" / "plans" / "completed"

STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.MULTILINE)

# Scope qualifiers that make "Completed" honest when backlog rows remain.
SCOPE_QUALIFIER_RE = re.compile(
    r"(?i)"
    r"(core\s+complete|catalogue|catalog|doc-?only|documentation|"
    r"phase\s*\d|phases\s*\d|poc|pattern|tier\s*1|slice|deferred|ongoing|"
    r"format\s+compatibility|shipped|optional)"
)

# Table/status cells that are not "open work" for overclaim purposes.
OPEN_PENDING_RE = re.compile(r"⬜(?!\s*(?:Deferred|N/A|Optional))")


def _completed_plans() -> list[Path]:
    if not COMPLETED_DIR.is_dir():
        return []
    return sorted(COMPLETED_DIR.glob("PLAN_*.md"))


def _parse_status(text: str) -> str | None:
    match = STATUS_RE.search(text)
    return match.group(1).strip() if match else None


def _has_scope_qualifier(status: str) -> bool:
    if SCOPE_QUALIFIER_RE.search(status):
        return True
    # "Completed (archived under ...)" alone is OK when no open ⬜ rows exist.
    if re.search(r"(?i)completed\s*\(archived", status):
        return True
    return False


def _open_pending_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        if "⬜" not in line:
            continue
        if OPEN_PENDING_RE.search(line):
            lines.append(line.strip()[:120])
    return lines


@pytest.mark.parametrize("plan_path", _completed_plans(), ids=lambda p: p.name)
def test_archived_plan_status_matches_open_rows(plan_path: Path) -> None:
    """Unqualified Completed + open ⬜ ⇒ overclaim risk (fail CI)."""
    text = plan_path.read_text(encoding="utf-8")
    status = _parse_status(text)
    open_rows = _open_pending_lines(text)

    if not open_rows:
        pytest.skip("no open ⬜ rows — bare Completed header is acceptable")

    if status is None:
        pytest.fail(f"{plan_path.name}: open ⬜ rows but missing **Status:** line")

    if _has_scope_qualifier(status):
        return

    pytest.fail(
        f"{plan_path.name}: **Status:** {status!r} lacks scope qualifier "
        f"but has {len(open_rows)} open ⬜ row(s). "
        f"First: {open_rows[0]!r}. "
        "Use Core complete / catalogue / phase N / Deferred (post-archive), etc."
    )

"""Guardrail: docs/adr/README.md Index table lists every numbered ADR file (and only those)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = REPO_ROOT / "docs" / "adr"
README_EN = ADR_DIR / "README.md"
# Canonical index for completeness lives in EN README (see docs/adr/README.pt_BR.md partial table).
_INDEX_START = "## Index"
_INDEX_END = "## Related docs"
_LINK_TARGET = re.compile(
    r"\]\(((?:ADR-)?\d{4}-[a-z0-9._-]+\.md)\)",
    re.IGNORECASE,
)


def _index_table_block(text: str) -> str:
    if _INDEX_START not in text:
        msg = f"{README_EN}: missing {_INDEX_START!r}"
        raise AssertionError(msg)
    after = text.split(_INDEX_START, 1)[1]
    if _INDEX_END not in after:
        msg = f"{README_EN}: missing {_INDEX_END!r} after {_INDEX_START!r}"
        raise AssertionError(msg)
    return after.split(_INDEX_END, 1)[0]


def _indexed_filenames(readme_text: str) -> list[str]:
    block = _index_table_block(readme_text)
    return _LINK_TARGET.findall(block)


def _numbered_adr_filenames() -> set[str]:
    names: set[str] = set()
    names.update(p.name for p in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))
    names.update(p.name for p in ADR_DIR.glob("ADR-[0-9][0-9][0-9][0-9]-*.md"))
    return names


def test_adr_readme_index_lists_every_numbered_adr_file() -> None:
    text = README_EN.read_text(encoding="utf-8")
    indexed = _indexed_filenames(text)
    on_disk = _numbered_adr_filenames()

    missing_in_index = sorted(on_disk - set(indexed))
    assert not missing_in_index, (
        f"{README_EN}: Index table missing row(s) for: {missing_in_index}. "
        "Add a line in the ## Index table (same PR as the new ADR file)."
    )


def test_adr_readme_index_has_no_extra_or_duplicate_links() -> None:
    text = README_EN.read_text(encoding="utf-8")
    indexed = _indexed_filenames(text)
    on_disk = _numbered_adr_filenames()

    extra = sorted(set(indexed) - on_disk)
    assert not extra, (
        f"{README_EN}: Index links to missing file(s): {extra}. "
        "Fix the link target or remove the row."
    )

    if len(indexed) != len(set(indexed)):
        from collections import Counter

        dupes = sorted([k for k, v in Counter(indexed).items() if v > 1])
        assert False, f"{README_EN}: duplicate Index link target(s): {dupes}"

    assert set(indexed) == on_disk

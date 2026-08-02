"""Guardrail: docs/adr README Index tables list every numbered ADR file (EN + pt-BR)."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = REPO_ROOT / "docs" / "adr"
README_EN = ADR_DIR / "README.md"
README_PT = ADR_DIR / "README.pt_BR.md"
_INDEX_MARKERS = {
    README_EN: ("## Index", "## Related docs"),
    README_PT: ("## Índice", "## Docs relacionados"),
}
_LINK_TARGET = re.compile(
    r"\]\(((?:ADR-)?\d{4}-[a-z0-9._-]+\.md)\)",
    re.IGNORECASE,
)


def _index_table_block(readme: Path, text: str) -> str:
    start, end = _INDEX_MARKERS[readme]
    if start not in text:
        msg = f"{readme}: missing {start!r}"
        raise AssertionError(msg)
    after = text.split(start, 1)[1]
    if end not in after:
        msg = f"{readme}: missing {end!r} after {start!r}"
        raise AssertionError(msg)
    return after.split(end, 1)[0]


def _indexed_filenames(readme: Path, readme_text: str) -> list[str]:
    block = _index_table_block(readme, readme_text)
    return _LINK_TARGET.findall(block)


def _numbered_adr_filenames() -> set[str]:
    names: set[str] = set()
    names.update(p.name for p in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))
    names.update(p.name for p in ADR_DIR.glob("ADR-[0-9][0-9][0-9][0-9]-*.md"))
    return names


def _assert_index_complete(readme: Path) -> None:
    text = readme.read_text(encoding="utf-8")
    indexed = _indexed_filenames(readme, text)
    on_disk = _numbered_adr_filenames()

    missing_in_index = sorted(on_disk - set(indexed))
    assert not missing_in_index, (
        f"{readme}: Index table missing row(s) for: {missing_in_index}. "
        "Add a line in the Index table (same PR as the new ADR file)."
    )

    extra = sorted(set(indexed) - on_disk)
    assert not extra, (
        f"{readme}: Index links to missing file(s): {extra}. "
        "Fix the link target or remove the row."
    )

    if len(indexed) != len(set(indexed)):
        dupes = sorted([k for k, v in Counter(indexed).items() if v > 1])
        raise AssertionError(f"{readme}: duplicate Index link target(s): {dupes}")

    assert set(indexed) == on_disk


def test_adr_readme_index_lists_every_numbered_adr_file() -> None:
    _assert_index_complete(README_EN)


def test_adr_readme_pt_br_index_lists_every_numbered_adr_file() -> None:
    _assert_index_complete(README_PT)


def test_adr_readme_en_and_pt_br_index_same_link_set() -> None:
    en = set(_indexed_filenames(README_EN, README_EN.read_text(encoding="utf-8")))
    pt = set(_indexed_filenames(README_PT, README_PT.read_text(encoding="utf-8")))
    assert en == pt, (
        f"EN vs pt-BR Index link set drift: "
        f"only_en={sorted(en - pt)} only_pt={sorted(pt - en)}"
    )

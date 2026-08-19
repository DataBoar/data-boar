"""#645 — root QUICKSTART exists as EN canonical + pt-BR twin with switchers."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_EN = _ROOT / "QUICKSTART.md"
_PT = _ROOT / "QUICKSTART.pt_BR.md"

_EN_HEADINGS = (
    "## Path 0 — Zero-config (`pip` / `pipx` + `--demo`)",
    "## Path A — Docker (less friction for non-developers)",
    "## Path B — Local Python (for developers / technical IT)",
)

_PT_HEADINGS = (
    "## Caminho 0 — Zero-config (`pip` / `pipx` + `--demo`)",
    "## Caminho A — Docker (menos fricção para não desenvolvedores)",
    "## Caminho B — Python local (para desenvolvedor / TI técnico)",
)


def _heading_line_index(lines: list[str], heading: str) -> int:
    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if line == heading or line.startswith(f"{heading} {{#"):
            return idx
    raise AssertionError(f"missing heading line {heading!r}")


def test_quickstart_en_and_pt_br_exist_with_switchers() -> None:
    assert _EN.is_file(), "canonical EN QUICKSTART.md is missing"
    assert _PT.is_file(), "QUICKSTART.pt_BR.md twin is missing"
    en_text = _EN.read_text(encoding="utf-8")
    pt_text = _PT.read_text(encoding="utf-8")
    assert "[QUICKSTART.pt_BR.md](QUICKSTART.pt_BR.md)" in en_text
    assert "[QUICKSTART.md](QUICKSTART.md)" in pt_text
    assert "QUICKSTART.en.md" not in en_text
    assert "QUICKSTART.en.md" not in pt_text


def test_quickstart_en_and_pt_br_have_path_0_a_b_in_order() -> None:
    en_lines = _EN.read_text(encoding="utf-8").splitlines()
    pt_lines = _PT.read_text(encoding="utf-8").splitlines()
    en_indexes = [_heading_line_index(en_lines, heading) for heading in _EN_HEADINGS]
    pt_indexes = [_heading_line_index(pt_lines, heading) for heading in _PT_HEADINGS]
    assert en_indexes == sorted(en_indexes)
    assert pt_indexes == sorted(pt_indexes)

"""Light offline guard for docs/CANONICAL_PRODUCT_FACTS*.md (#1470 slice 1).

Anchors MUST / MUST-NOT on the FACTS surfaces this slice creates and controls.
README / QUICKSTART policing is deferred (coordinate with #1473 and later #1470 slices).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]

# Primary anchor for this slice — do not expand to README/QUICKSTART here.
FACTS_SURFACES = (
    _REPO / "docs" / "CANONICAL_PRODUCT_FACTS.md",
    _REPO / "docs" / "CANONICAL_PRODUCT_FACTS.pt_BR.md",
)

MUST_CONTAIN = (
    "pipx install data-boar",
    "data-boar --demo",
    "https://github.com/DataBoar/data-boar",
    "https://databoar.com.br",
    "fabioleitao/data_boar",  # Docker Hub image (explicitly labeled in FACTS)
)

# Docker-optional: EN and pt-BR phrasing both required across the pair;
# each file must contain at least one of these markers.
DOCKER_OPTIONAL_MARKERS = (
    "Docker is optional",
    "Docker é opcional",
)

MUST_NOT_SUBSTRINGS = (
    "pastas_para_varrer",
    "databoarscan",
    "databoar scan",
    "github.com/FabioLeitao/data-boar",
)

# Allowed only when the same line negates the claim (hallucination table).
_NEGATION_MARKERS = (
    "Does not exist",
    "Não existe",
    "fabricated",
    "fabricada",
    "**False**",
    "**Falso**",
    "**Stale**",
    "Stale",
)

# Canonical prose must not sell Docker as required / only / default for non-tech.
# Same-line negation (hallucination table) is allowed.
MUST_NOT_DOCKER_CANONICAL = (
    re.compile(r"docker\s+is\s+required", re.I),
    re.compile(r"docker\s+obrigat[oó]rio", re.I),
    re.compile(r"docker\s+is\s+the\s+only", re.I),
    re.compile(r"docker\s+(?:é|e)\s+o\s+[uú]nico", re.I),
    re.compile(
        r"docker\s+recommended\s+for\s+non[- ]?(?:tech|technical|developer)",
        re.I,
    ),
    re.compile(
        r"docker\s+recomendad[oa]\s+para\s+(?:n[aã]o[- ]?(?:de[- ]?ti|t[eé]cnic)|quem\s+n[aã]o\s+[eé]\s+de\s+ti)",
        re.I,
    ),
)


def _line_has_negation(line: str) -> bool:
    return any(m in line for m in _NEGATION_MARKERS)


def _unnegated_mentions(text: str, needle: str) -> list[str]:
    bad: list[str] = []
    for line in text.splitlines():
        if needle in line and not _line_has_negation(line):
            bad.append(line.strip())
    return bad


def _unnegated_regex_hits(text: str, rx: re.Pattern[str]) -> list[str]:
    bad: list[str] = []
    for line in text.splitlines():
        if rx.search(line) and not _line_has_negation(line):
            bad.append(line.strip())
    return bad


@pytest.mark.parametrize("path", FACTS_SURFACES, ids=lambda p: p.name)
def test_facts_file_exists(path: Path) -> None:
    assert path.is_file(), f"missing canonical facts surface: {path}"


@pytest.mark.parametrize("path", FACTS_SURFACES, ids=lambda p: p.name)
def test_facts_must_contain_canonical_install_and_identity(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for needle in MUST_CONTAIN:
        assert needle in text, f"{path.name} must contain {needle!r}"
    assert "windows.html" in text, f"{path.name} must link windows.html"
    assert "targets:" in text, f"{path.name} must document real config key targets:"
    assert any(m in text for m in DOCKER_OPTIONAL_MARKERS), (
        f"{path.name} must state Docker is optional / Docker é opcional"
    )


@pytest.mark.parametrize("path", FACTS_SURFACES, ids=lambda p: p.name)
def test_facts_must_not_contain_invented_or_stale_canonicals(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for needle in MUST_NOT_SUBSTRINGS:
        bad = _unnegated_mentions(text, needle)
        assert not bad, (
            f"{path.name}: {needle!r} appears without same-line negation "
            f"(hallucination table may name it only when marked false): {bad!r}"
        )
    for rx in MUST_NOT_DOCKER_CANONICAL:
        bad = _unnegated_regex_hits(text, rx)
        assert not bad, (
            f"{path.name}: Docker required/only/non-tech-default without negation "
            f"(pattern {rx.pattern!r}): {bad!r}"
        )


def test_facts_label_docker_hub_image_distinct_from_github_repo() -> None:
    """fabioleitao/data_boar is allowed only as Docker Hub image, not as GitHub home."""
    en = (_REPO / "docs" / "CANONICAL_PRODUCT_FACTS.md").read_text(encoding="utf-8")
    assert "Docker Hub" in en
    assert "DataBoar/data-boar" in en
    assert "image namespace" in en.lower() or "≠ GitHub" in en or "!= GitHub" in en

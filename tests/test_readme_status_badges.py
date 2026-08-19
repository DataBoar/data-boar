"""README status badges (#457) — GitHub org, Hub image, no premature PyPI/coverage."""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GITHUB = "https://github.com/DataBoar/data-boar"
_HUB_IMAGE = "fabioleitao/data_boar"


@pytest.mark.parametrize("readme_name", ["README.md", "README.pt_BR.md"])
def test_readme_status_badges_after_mascot(readme_name: str) -> None:
    text = (_REPO_ROOT / readme_name).read_text(encoding="utf-8")
    mascot = "![Data Boar mascot]"
    i_mascot = text.find(mascot)
    i_rule = text.find("\n---\n")
    assert i_mascot != -1, f"{readme_name} must include the mascot image"
    assert i_rule != -1, f"{readme_name} must have a --- separator after the intro"
    intro = text[i_mascot:i_rule]
    assert f"{_GITHUB}/actions/workflows/ci.yml/badge.svg" in intro
    assert f"{_GITHUB}/actions/workflows/codeql.yml/badge.svg" in intro
    assert f"img.shields.io/docker/v/{_HUB_IMAGE}" in intro
    assert "hub.docker.com/r/fabioleitao/data_boar" in intro
    assert "img.shields.io/github/license/DataBoar/data-boar" in intro
    assert "(LICENSE)" in intro
    assert "pypi.org" not in intro.lower()
    assert "codecov" not in intro.lower()
    assert "coveralls" not in intro.lower()
    # Issue example used a personal GitHub path; upstream is the org.
    assert "github.com/FabioLeitao/data-boar" not in intro

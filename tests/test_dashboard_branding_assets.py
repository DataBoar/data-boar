"""Branding assets referenced by the dashBOARd layout and READMEs must exist (#1450)."""

from __future__ import annotations

import re
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "api" / "static"
MASCOT = STATIC / "mascot"
TEMPLATES = ROOT / "api" / "templates"
_STATIC_REF = re.compile(r'(?:href|src)="/static/([^"]+)"')


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    return struct.unpack(">II", data[16:24])


@pytest.mark.parametrize("template", ["base.html", "about.html"])
def test_static_references_resolve_to_existing_files(template: str) -> None:
    refs = _STATIC_REF.findall((TEMPLATES / template).read_text(encoding="utf-8"))
    assert refs, f"{template} references no /static assets"
    for ref in refs:
        assert (STATIC / ref).is_file(), f"{template} references missing /static/{ref}"


def test_layout_declares_favicon_set() -> None:
    head = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    for expected in (
        "/static/favicon.ico",
        "/static/mascot/favicon-32.png",
        "/static/mascot/icon-192.png",
        "/static/mascot/apple-touch-icon.png",
    ):
        assert expected in head, f"base.html must link {expected}"


@pytest.mark.parametrize(
    ("name", "size"),
    [
        ("favicon-32.png", (32, 32)),
        ("icon-192.png", (192, 192)),
        ("apple-touch-icon.png", (180, 180)),
    ],
)
def test_icon_png_dimensions(name: str, size: tuple[int, int]) -> None:
    assert _png_size(MASCOT / name) == size


def test_favicon_ico_is_a_valid_icon_resource() -> None:
    header = (STATIC / "favicon.ico").read_bytes()[:6]
    reserved, kind, count = struct.unpack("<HHH", header)
    assert (reserved, kind) == (0, 1)
    assert count >= 1


def test_mascot_pot_is_a_landscape_png() -> None:
    width, height = _png_size(MASCOT / "mascot-pot.png")
    assert width >= 600
    assert width > height


@pytest.mark.parametrize("readme", ["README.md", "README.pt_BR.md"])
def test_readme_banner_is_centered_site_hosted_mascot(readme: str) -> None:
    """The banner keeps the site-hosted URL pinned by tests/test_docs_markdown.py, now centered."""
    text = (ROOT / readme).read_text(encoding="utf-8")
    banner = "![Data Boar mascot](https://databoar.com.br/images/mascot-pot.png)"
    assert banner in text
    assert '<p align="center">' in text.split(banner, 1)[0][-40:]


def test_legacy_mascot_assets_are_preserved() -> None:
    """Lineage: the previous mascot art must not be deleted by the branding refresh."""
    assert (MASCOT / "data_boar_mascote_color.svg").is_file()
    assert (MASCOT / "data_boar_mascote_color_translucent_not_zombie.png").is_file()

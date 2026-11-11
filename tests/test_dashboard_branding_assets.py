"""Branding assets referenced by the dashBOARd layout and READMEs must exist and be placed by rule (#1450)."""

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

ALL_TEMPLATES = sorted(p.name for p in TEMPLATES.glob("*.html"))
# Placement rule: a large illustration appears only on these screens.
LARGE_ART = {
    "about.html": "mascot-pot.png",
    "reports.html": "data-soup-pot.png",
    "dashboard.html": "mascot-hero.png",
}
FACE_MARK = "mascot-mark-face.png"
# Screens that carry the small face anchor in their heading.
SCREENS_WITH_MARK = [
    "about.html",
    "config.html",
    "dashboard.html",
    "help.html",
    "reports.html",
]


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    return struct.unpack(">II", data[16:24])


@pytest.mark.parametrize("template", ALL_TEMPLATES)
def test_static_references_resolve_to_existing_files(template: str) -> None:
    for ref in _STATIC_REF.findall((TEMPLATES / template).read_text(encoding="utf-8")):
        if (
            "{{" in ref
        ):  # dynamic (e.g. per-locale screenshots): not a literal file name
            continue
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
        ("mascot-pot.png", (760, 558)),
        ("mascot-hero.png", (760, 558)),
        ("data-soup-pot.png", (760, 558)),
        (FACE_MARK, (443, 383)),
    ],
)
def test_png_dimensions(name: str, size: tuple[int, int]) -> None:
    assert _png_size(MASCOT / name) == size


def test_favicon_ico_is_a_valid_icon_resource() -> None:
    reserved, kind, count = struct.unpack(
        "<HHH", (STATIC / "favicon.ico").read_bytes()[:6]
    )
    assert (reserved, kind) == (0, 1)
    assert count >= 1


def test_hero_and_soup_pot_are_distinct_alpha_cutouts() -> None:
    """hero = the boar alone, soup-pot = the pot alone: same scene, different transparency."""
    Image = pytest.importorskip("PIL.Image")

    def opaque_fraction(name: str) -> float:
        hist = Image.open(MASCOT / name).convert("RGBA").getchannel("A").histogram()
        return sum(hist[201:]) / sum(hist)

    pot, hero, soup = (
        opaque_fraction(n)
        for n in ("mascot-pot.png", "mascot-hero.png", "data-soup-pot.png")
    )
    assert hero < pot and soup < pot, (
        "hero and soup-pot must each show only part of the pot scene"
    )
    assert hero > soup, "the boar alone covers more of the frame than the pot alone"
    assert abs(hero - soup) > 0.05, "hero and soup-pot must not be the same image"


@pytest.mark.parametrize("template", ALL_TEMPLATES)
def test_large_illustrations_only_where_the_rule_allows(template: str) -> None:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for big in {"mascot-pot.png", "mascot-hero.png", "data-soup-pot.png"}:
        allowed = LARGE_ART.get(template) == big
        assert (big in text) == allowed, (
            f"{template}: {big} {'missing' if allowed else 'not allowed here'}"
        )


@pytest.mark.parametrize("template", SCREENS_WITH_MARK)
def test_every_screen_carries_the_small_face_mark(template: str) -> None:
    assert FACE_MARK in (TEMPLATES / template).read_text(encoding="utf-8")


@pytest.mark.parametrize("template", ALL_TEMPLATES)
def test_no_template_uses_the_legacy_art(template: str) -> None:
    assert "data_boar_mascot" not in (TEMPLATES / template).read_text(encoding="utf-8")


def test_idle_mascot_is_hidden_while_a_scan_runs() -> None:
    assert 'id="idle-mascot"' in (TEMPLATES / "dashboard.html").read_text(
        encoding="utf-8"
    )
    assert "idle-mascot" in (STATIC / "dashboard.js").read_text(encoding="utf-8")


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
    assert (STATIC / "logo-candidates").is_dir()

"""#2163 — wheel and native packages ship the man pages."""

from __future__ import annotations

import tomllib
import zipfile
from pathlib import Path

from core.extras_manifest import build_manifest
from core.man_page_packaging import (
    MAN1_LEGACY_ALIASES,
    MAN5_LEGACY_ALIASES,
    MAN7_LEGACY_ALIASES,
    wheel_shared_man_paths,
)
from core.native_nfpm import generated_dir, render_all_nfpm_docs
from core.void_xbps import render_template

REPO = Path(__file__).resolve().parents[1]


def test_pyproject_wheel_man_shared_data_matches_packaging_module() -> None:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    shared = data["tool"]["hatch"]["build"]["targets"]["wheel"]["shared-data"]
    assert shared == wheel_shared_man_paths()


def test_wheel_and_nfpm_ship_man_pages(tmp_path) -> None:
    import subprocess

    out = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(out)],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(out.glob("*.whl"))
    assert len(wheels) == 1
    names = zipfile.ZipFile(wheels[0]).namelist()
    assert any(n.endswith("share/man/man1/data-boar.1") for n in names)
    assert any(n.endswith("share/man/man5/data-boar.5") for n in names)
    assert any(n.endswith("share/man/man7/data-boar.7") for n in names)
    for alias in MAN1_LEGACY_ALIASES:
        assert any(n.endswith(f"share/man/man1/{alias}") for n in names)
    for alias in MAN5_LEGACY_ALIASES:
        assert any(n.endswith(f"share/man/man5/{alias}") for n in names)
    for alias in MAN7_LEGACY_ALIASES:
        assert any(n.endswith(f"share/man/man7/{alias}") for n in names)

    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    core = render_all_nfpm_docs(manifest=manifest)["data-boar.yaml"]
    dests = [str(item.get("dst") or "") for item in core["contents"]]
    assert "/usr/share/man/man1/data-boar.1" in dests
    assert "/usr/share/man/man5/data-boar.5" in dests
    assert "/usr/share/man/man7/data-boar.7" in dests
    for alias in MAN1_LEGACY_ALIASES:
        assert f"/usr/share/man/man1/{alias}" in dests
    for alias in MAN5_LEGACY_ALIASES:
        assert f"/usr/share/man/man5/{alias}" in dests
    for alias in MAN7_LEGACY_ALIASES:
        assert f"/usr/share/man/man7/{alias}" in dests
    symlink_rows = [item for item in core["contents"] if item.get("type") == "symlink"]
    assert len(symlink_rows) == (
        len(MAN1_LEGACY_ALIASES) + len(MAN5_LEGACY_ALIASES) + len(MAN7_LEGACY_ALIASES)
    )

    yaml_text = (generated_dir() / "data-boar.yaml").read_text(encoding="utf-8")
    assert "/usr/share/man/man1/data-boar.1" in yaml_text
    assert "/usr/share/man/man5/data-boar.5" in yaml_text
    assert "/usr/share/man/man7/data-boar.7" in yaml_text
    for alias in MAN1_LEGACY_ALIASES:
        assert f"/usr/share/man/man1/{alias}" in yaml_text
    for alias in MAN5_LEGACY_ALIASES:
        assert f"/usr/share/man/man5/{alias}" in yaml_text
    for alias in MAN7_LEGACY_ALIASES:
        assert f"/usr/share/man/man7/{alias}" in yaml_text

    template = render_template(manifest=manifest)
    assert "vman" in template
    assert "data-boar.1" in template
    assert "data-boar.5" in template
    assert "data-boar.7" in template
    assert "ln -sf data-boar.1" in template
    assert "ln -sf data-boar.5" in template
    assert "ln -sf data-boar.7" in template


def test_void_srcpkg_ships_man7_files() -> None:
    from core.void_xbps import CORE_PACKAGE, generated_dir as void_generated_dir

    shipped = void_generated_dir() / "srcpkgs" / CORE_PACKAGE / "files" / "data-boar.7"
    assert shipped.read_text(encoding="utf-8") == (
        REPO / "docs" / "data_boar.7"
    ).read_text(encoding="utf-8")


def test_wheel_alias_symlinks_for_man7_resolve_to_the_page() -> None:
    page = (REPO / "docs" / "data_boar.7").resolve()
    for alias in MAN7_LEGACY_ALIASES:
        link = REPO / "packaging" / "wheel-man-aliases" / "man7" / alias
        assert link.is_symlink(), link
        assert link.resolve() == page

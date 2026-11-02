"""Native package license must match [project].license (#2161)."""

from __future__ import annotations

import tomllib
from pathlib import Path

from core.extras_manifest import build_manifest
from core.native_nfpm import generated_dir as nfpm_generated_dir
from core.native_nfpm import render_all_nfpm_docs
from core.void_xbps import generated_srcpkg_dir, render_template

REPO = Path(__file__).resolve().parents[1]


def _pyproject_license() -> str:
    with (REPO / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["license"])


def test_generated_nfpm_and_void_license_match_pyproject() -> None:
    expected = _pyproject_license()
    assert expected == "BSD-3-Clause"

    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    docs = render_all_nfpm_docs(manifest=manifest)
    for name, doc in docs.items():
        assert doc["license"] == expected, name

    for path in sorted(nfpm_generated_dir().glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        assert f"license: {expected}" in text, path.name
        assert "AGPL" not in text, path.name

    template = render_template(manifest=manifest)
    license_line = next(
        line for line in template.splitlines() if line.startswith("license=")
    )
    assert license_line == f'license="{expected}"'

    on_disk = (generated_srcpkg_dir() / "template").read_text(encoding="utf-8")
    disk_license = next(
        line for line in on_disk.splitlines() if line.startswith("license=")
    )
    assert disk_license == f'license="{expected}"'
    assert "AGPL" not in on_disk

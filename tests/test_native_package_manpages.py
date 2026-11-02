"""#2163 — wheel and native packages ship the man pages."""

from __future__ import annotations

import zipfile
from pathlib import Path

from core.extras_manifest import build_manifest
from core.native_nfpm import generated_dir, render_all_nfpm_docs
from core.void_xbps import render_template

REPO = Path(__file__).resolve().parents[1]


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

    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    core = render_all_nfpm_docs(manifest=manifest)["data-boar.yaml"]
    dests = [str(item.get("dst") or "") for item in core["contents"]]
    assert "/usr/share/man/man1/data-boar.1" in dests
    assert "/usr/share/man/man5/data-boar.5" in dests

    yaml_text = (generated_dir() / "data-boar.yaml").read_text(encoding="utf-8")
    assert "/usr/share/man/man1/data-boar.1" in yaml_text
    assert "/usr/share/man/man5/data-boar.5" in yaml_text

    template = render_template(manifest=manifest)
    assert "vman" in template
    assert "data-boar.1" in template
    assert "data-boar.5" in template

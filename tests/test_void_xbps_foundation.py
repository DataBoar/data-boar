"""Void xbps overlay (#1404 / ADR-0084) — generated template + systemd canary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.extras_manifest import (
    EMBEDDED_INTERPRETER_NATIVE,
    build_manifest,
)
from core.integrity_anchor import OPEN_MODE_WORKER_CAP
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
from core.native_nfpm import CORE_PACKAGE, read_subpackage_map
from core.void_xbps import (
    VOID_LAYER2_DEPENDS,
    assert_generated_in_sync,
    generated_dir,
    pep440_to_xbps_version,
    render_template,
    runit_run_source,
)

REPO = Path(__file__).resolve().parents[1]


def test_pep440_to_xbps_version() -> None:
    assert pep440_to_xbps_version("1.8.0") == "1.8.0"
    assert pep440_to_xbps_version("1.8.0-beta") == "1.8.0beta1"
    assert pep440_to_xbps_version("1.8.0-rc1") == "1.8.0rc1"


def test_subpackage_map_matches_nfpm_1403() -> None:
    expected = {
        "data-boar-mssql": "mssql",
        "data-boar-nosql": "nosql",
        "data-boar-shares": "shares",
        "data-boar-compressed": "compressed",
        "data-boar-dataformats": "dataformats",
        "data-boar-richmedia": "richmedia",
    }
    assert read_subpackage_map() == expected


def test_generated_void_in_sync_with_manifest() -> None:
    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    assert_generated_in_sync(manifest=manifest)


def test_template_subpackages_come_from_extras_manifest() -> None:
    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    text = render_template(manifest=manifest)
    extras = manifest["extras"]
    for package_name, extra_name in read_subpackage_map().items():
        assert f"{package_name}_package()" in text
        assert f"vmove usr/lib/data-boar/extras/{extra_name}" in text
        assert "refuse empty subpackage" in text
        for pkg in extras[extra_name]["packages"]:
            stem = pkg.split(">=")[0].split("==")[0]
            assert stem in text


def test_core_has_no_depends_python3_and_void_layer2() -> None:
    text = render_template(
        manifest=build_manifest(probe=False, include_embedded_interpreter=True)
    )
    depends_line = next(
        line for line in text.splitlines() if line.startswith("depends=")
    )
    lowered = depends_line.lower()
    assert "python3" not in lowered
    assert "python" not in lowered
    assert "p7zip" not in lowered
    for dep in VOID_LAYER2_DEPENDS:
        assert dep in depends_line


def test_commercial_notice_and_embed_prefix() -> None:
    text = render_template(
        manifest=build_manifest(probe=False, include_embedded_interpreter=True)
    )
    assert "does NOT unlock Enterprise" in text
    assert "worker caps" in text
    assert "pro_prefilter_accel" in text
    assert EMBEDDED_INTERPRETER_NATIVE["python_bin"] in text
    assert 'archs="x86_64"' in text
    meta = json.loads(
        (generated_dir() / "PACKAGES.meta.json").read_text(encoding="utf-8")
    )
    assert meta["packager"] == "xbps"
    assert meta["validation"] == "podman_void"
    assert meta["init"] == "runit"
    assert meta["upstream_void_packages"] == "out_of_scope"


def test_cp314t_presence_does_not_unlock_enterprise_gates() -> None:
    assert OPEN_MODE_WORKER_CAP == 2
    assert FEATURE_TIER_MAP["pro_prefilter_accel"] == Tier.PRO_PLUS
    assert FEATURE_TIER_MAP["scan_max_workers_enterprise"] == Tier.ENTERPRISE


def test_runit_and_void_paths_never_call_systemctl() -> None:
    """Void is the init-coupling canary — overlay + product launcher stay init-neutral."""
    run_text = runit_run_source().read_text(encoding="utf-8")
    assert (
        "exec /usr/lib/data-boar/python3.14t/bin/python3.14t -m data_boar --web"
        in run_text
    )
    assert "DISABLE_SQLALCHEMY_CEXT" in run_text
    assert "systemctl" not in run_text
    generated_run = (
        generated_dir() / "srcpkgs" / CORE_PACKAGE / "files" / "data-boar" / "run"
    ).read_text(encoding="utf-8")
    assert generated_run == run_text
    template = (generated_dir() / "srcpkgs" / CORE_PACKAGE / "template").read_text(
        encoding="utf-8"
    )
    assert "systemctl" not in template
    assert "vsv data-boar" in template
    product_roots = (REPO / "data_boar", REPO / "main.py")
    for path in product_roots:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "systemctl" not in text
            continue
        for py in path.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            assert "systemctl" not in text, py


def test_podman_script_is_fail_closed() -> None:
    script = (REPO / "scripts" / "void-xbps-podman-validate.sh").read_text(
        encoding="utf-8"
    )
    assert "podman" in script
    assert "ENGINE=docker" in script
    assert "void-glibc" in script
    assert "void-musl" in script
    assert "./xbps-src show" in script
    assert "./xbps-src pkg" in script
    assert "missing embedded interpreter" in script
    assert "do not reuse glibc bytes" in script
    assert "not lab metal" in script.lower() or "No lab metal" in script


def test_void_xbps_scripts_bash_syntax() -> None:
    if sys.platform == "win32":
        return
    for rel in (
        "scripts/void-xbps-podman-validate.sh",
        "packaging/void/files/data-boar/run",
    ):
        proc = subprocess.run(
            ["bash", "-n", str(REPO / rel)],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert proc.returncode == 0, f"{rel}: {proc.stderr or proc.stdout}"

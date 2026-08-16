"""Native nfpm foundation (#1403 / ADR-0084) — generated packages + commercial gate."""

from __future__ import annotations

import yaml

from core.extras_manifest import (
    EMBEDDED_INTERPRETER_NATIVE,
    build_manifest,
)
from core.integrity_anchor import OPEN_MODE_WORKER_CAP
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
from core.native_nfpm import (
    CORE_PACKAGE,
    LAYER2_DEPENDS,
    NFPM_PACKAGERS,
    assert_generated_in_sync,
    generated_dir,
    read_subpackage_map,
    render_all_nfpm_docs,
)


def test_subpackage_map_matches_issue_1403_table() -> None:
    expected = {
        "data-boar-mssql": "mssql",
        "data-boar-nosql": "nosql",
        "data-boar-shares": "shares",
        "data-boar-compressed": "compressed",
        "data-boar-dataformats": "dataformats",
        "data-boar-richmedia": "richmedia",
    }
    assert read_subpackage_map() == expected


def test_generated_nfpm_in_sync_with_manifest() -> None:
    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    assert_generated_in_sync(manifest=manifest)


def test_subpackage_deps_come_from_extras_manifest_not_hand_list() -> None:
    manifest = build_manifest(probe=False, include_embedded_interpreter=True)
    docs = render_all_nfpm_docs(manifest=manifest)
    for package_name, extra_name in read_subpackage_map().items():
        doc = docs[f"{package_name}.yaml"]
        expected_pkgs = list(manifest["extras"][extra_name]["packages"])
        # Description carries the package list from the manifest (audit trail).
        for pkg in expected_pkgs:
            assert pkg.split(">=")[0].split("==")[0] in doc["description"]
        assert CORE_PACKAGE in doc["depends"][0]


def test_core_has_no_depends_python3_and_layer2_overrides() -> None:
    docs = render_all_nfpm_docs(
        manifest=build_manifest(probe=False, include_embedded_interpreter=True)
    )
    core = docs[f"{CORE_PACKAGE}.yaml"]
    flat_depends = " ".join(core.get("depends") or []).lower()
    assert "python3" not in flat_depends
    assert "python" not in flat_depends
    for packager in NFPM_PACKAGERS:
        assert packager in core["overrides"]
        assert core["overrides"][packager]["depends"] == LAYER2_DEPENDS[packager]
    assert set(NFPM_PACKAGERS) == {"deb", "rpm", "apk", "archlinux"}
    assert "xbps" not in NFPM_PACKAGERS


def test_core_layer2_does_not_require_p7zip() -> None:
    """`.7z` uses optional py7zr; p7zip is not a core binary dep (Rocky EPEL trap)."""
    for deps in LAYER2_DEPENDS.values():
        joined = " ".join(deps).lower()
        assert "p7zip" not in joined
    docs = render_all_nfpm_docs(
        manifest=build_manifest(probe=False, include_embedded_interpreter=True)
    )
    core = docs[f"{CORE_PACKAGE}.yaml"]
    for packager in NFPM_PACKAGERS:
        joined = " ".join(core["overrides"][packager]["depends"]).lower()
        assert "p7zip" not in joined


def test_embedded_interpreter_in_native_manifest() -> None:
    m = build_manifest(probe=False, include_embedded_interpreter=True)
    emb = m["embedded_interpreter"]
    assert emb["abi_tag"] == "cp314t"
    assert emb["freethreaded"] is True
    assert emb["prefix"] == "/usr/lib/data-boar"
    assert emb == EMBEDDED_INTERPRETER_NATIVE

    native_path = generated_dir() / "EXTRAS_MANIFEST.native.json"
    assert native_path.is_file()
    text = native_path.read_text(encoding="utf-8")
    assert "cp314t" in text
    assert "embedded_interpreter" in text


def test_cp314t_presence_does_not_unlock_enterprise_gates() -> None:
    """ADR-0084 commercial clause — inventory must not weaken #551 caps."""
    assert OPEN_MODE_WORKER_CAP == 2
    assert FEATURE_TIER_MAP["pro_prefilter_accel"] == Tier.PRO_PLUS
    assert FEATURE_TIER_MAP["scan_max_workers_enterprise"] == Tier.ENTERPRISE
    # Generated packages must restate the commercial clause (not claim unlock).
    for path in generated_dir().glob("*.yaml"):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        desc = str(doc.get("description") or "").lower()
        assert "does not unlock enterprise" in desc
        assert "worker caps" in desc
        assert "pro_prefilter_accel" in desc


def test_committed_generated_yaml_files_exist() -> None:
    names = {
        "data-boar.yaml",
        "data-boar-mssql.yaml",
        "data-boar-nosql.yaml",
        "data-boar-shares.yaml",
        "data-boar-compressed.yaml",
        "data-boar-dataformats.yaml",
        "data-boar-richmedia.yaml",
    }
    on_disk = {p.name for p in generated_dir().glob("*.yaml")}
    assert names == on_disk
    assert (generated_dir() / "PACKAGES.meta.json").is_file()

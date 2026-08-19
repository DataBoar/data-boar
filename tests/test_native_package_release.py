"""Native package release naming, checksums, and manifest merge (#1408)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_release_manifest import apply_preserved_native_packages
from scripts.generate_release_manifest import main as release_manifest_main
from scripts.native_package_release import (
    classify_package_name,
    main as native_release_main,
    maybe_gpg_sign_sums,
    merge_native_packages,
    native_packages_payload,
    reject_reason,
    validate_package_names,
    write_sha256sums,
)


def test_issue_1408_example_names_are_valid() -> None:
    assert classify_package_name("data-boar_1.7.4.post12_amd64.deb") == "deb"
    assert classify_package_name("data-boar-1.7.4.post12-1.x86_64.rpm") == "rpm"
    assert classify_package_name("data-boar-1.7.4.post12-r0.apk") == "apk"
    assert (
        classify_package_name("data-boar-1.7.4.post12-1-x86_64.pkg.tar.zst") == "pacman"
    )


def test_hyphen_only_deb_is_rejected() -> None:
    """Hyphen-only .deb (no arch) breaks apt/reprepro/aptly."""
    bad = "data-boar-1.7.4-post12.deb"
    assert classify_package_name(bad) is None
    assert "reprepro" in reject_reason(bad)


def test_validate_and_checksums(tmp_path: Path) -> None:
    pkg = tmp_path / "data-boar_1.8.0-beta_amd64.deb"
    pkg.write_bytes(b"deb-stub\n")
    assert validate_package_names(tmp_path) == []
    sums = write_sha256sums(tmp_path)
    text = sums.read_text(encoding="utf-8")
    assert pkg.name in text
    assert len(text.split()[0]) == 64
    payload = native_packages_payload(tmp_path)
    assert payload[0]["packager"] == "deb"
    assert payload[0]["name"] == pkg.name


def test_merge_native_packages_leaves_files_intact() -> None:
    manifest = {
        "generated_at": "2026-08-18T00:00:00Z",
        "data_boar_version": "1.8.0-beta",
        "files": [{"path": "main.py", "sha256": "ab" * 32}],
    }
    merged = merge_native_packages(
        manifest,
        [
            {
                "name": "data-boar_1.8.0-beta_amd64.deb",
                "packager": "deb",
                "sha256": "cd" * 32,
            }
        ],
    )
    assert merged["files"] == manifest["files"]
    assert merged["native_packages"][0]["packager"] == "deb"


def test_maybe_gpg_sign_sums_skips_without_key(tmp_path: Path) -> None:
    sums = tmp_path / "SHA256SUMS"
    sums.write_text("deadbeef  data-boar_1.8.0-beta_amd64.deb\n", encoding="utf-8")
    assert maybe_gpg_sign_sums(sums) is None
    assert not (tmp_path / "SHA256SUMS.asc").exists()


def test_merge_manifest_refuses_missing_or_empty_files(tmp_path: Path) -> None:
    pkg = tmp_path / "data-boar_1.8.0-beta_amd64.deb"
    pkg.write_bytes(b"deb-stub\n")
    missing = tmp_path / "no-such-manifest.json"
    assert (
        native_release_main(
            ["--dir", str(tmp_path), "merge-manifest", "--manifest", str(missing)]
        )
        == 1
    )
    stub = tmp_path / "release-manifest.json"
    stub.write_text(
        json.dumps({"data_boar_version": "unknown", "files": []}) + "\n",
        encoding="utf-8",
    )
    assert (
        native_release_main(
            ["--dir", str(tmp_path), "merge-manifest", "--manifest", str(stub)]
        )
        == 1
    )
    assert json.loads(stub.read_text(encoding="utf-8"))["files"] == []


def test_patch_native_into_fails_when_source_missing(tmp_path: Path) -> None:
    dest = tmp_path / "release-manifest.json"
    dest.write_text(
        json.dumps({"files": [{"path": "main.py", "sha256": "aa" * 32}]}) + "\n",
        encoding="utf-8",
    )
    missing = tmp_path / "prior.json"
    assert (
        release_manifest_main(
            [
                "--patch-native-into",
                str(dest),
                "--preserve-native-from",
                str(missing),
            ]
        )
        == 1
    )
    assert "native_packages" not in json.loads(dest.read_text(encoding="utf-8"))


def test_apply_preserved_native_packages(tmp_path: Path) -> None:
    dest = tmp_path / "release-manifest.json"
    dest.write_text(
        json.dumps({"files": [{"path": "main.py", "sha256": "aa" * 32}]}) + "\n",
        encoding="utf-8",
    )
    src = tmp_path / "prior.json"
    src.write_text(
        json.dumps(
            {
                "files": [],
                "native_packages": [
                    {"name": "data-boar_1.8.0-beta_amd64.deb", "sha256": "bb" * 32}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert apply_preserved_native_packages(dest, src) is True
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["files"][0]["path"] == "main.py"
    assert data["native_packages"][0]["name"].endswith(".deb")

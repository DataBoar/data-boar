"""Release manifest generator and licensing tamper detection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.licensing.guard import LicenseGuard, reset_license_guard_for_tests
from core.licensing.integrity import verify_manifest_optional
from scripts.generate_release_manifest import (
    build_manifest_payload,
    collect_release_file_paths,
    verify_manifest_on_disk,
    write_release_manifest,
)


def test_release_manifest_paths_sorted_deterministic() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    first = [item["path"] for item in build_manifest_payload(repo_root)["files"]]
    second = [item["path"] for item in build_manifest_payload(repo_root)["files"]]
    assert first == second
    assert first == sorted(first)
    assert "main.py" in first


def test_release_manifest_writes_schema(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_bytes(b"print('ok')\n")
    out = tmp_path / "dist" / "release-manifest.json"
    write_release_manifest(tmp_path, out, version="9.9.9-test")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["data_boar_version"] == "9.9.9-test"
    assert data["generated_at"].endswith("Z")
    assert data["files"][0]["path"] == "main.py"
    assert len(data["files"][0]["sha256"]) == 64


def test_release_manifest_check_detects_tamper(tmp_path: Path) -> None:
    main = tmp_path / "main.py"
    main.write_bytes(b"stable\n")
    manifest = tmp_path / "manifest.json"
    write_release_manifest(tmp_path, manifest)
    ok, _ = verify_manifest_on_disk(manifest, tmp_path)
    assert ok is True
    main.write_bytes(b"stable!\n")
    ok, msg = verify_manifest_on_disk(manifest, tmp_path)
    assert ok is False
    assert msg.startswith("hash_mismatch:")


def test_manifest_tamper_detection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    main = tmp_path / "main.py"
    main.write_bytes(b"print('ok')\n")
    manifest = tmp_path / "manifest.json"
    write_release_manifest(tmp_path, manifest)

    monkeypatch.setenv("DATA_BOAR_LICENSE_MODE", "enforced")
    monkeypatch.setenv("DATA_BOAR_RELEASE_MANIFEST_PATH", str(manifest))
    reset_license_guard_for_tests()
    guard = LicenseGuard(
        {"licensing": {"mode": "enforced", "manifest_path": str(manifest)}}
    )
    assert guard.context.state != "TAMPERED"

    main.write_bytes(main.read_bytes() + b" ")
    reset_license_guard_for_tests()
    guard = LicenseGuard(
        {"licensing": {"mode": "enforced", "manifest_path": str(manifest)}}
    )
    assert guard.context.state == "TAMPERED"
    assert "hash_mismatch" in guard.context.detail


def test_verify_manifest_optional_matches_generator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    main = tmp_path / "main.py"
    main.write_bytes(b"x\n")
    manifest = tmp_path / "manifest.json"
    write_release_manifest(tmp_path, manifest)
    ok, msg = verify_manifest_optional(str(manifest))
    assert ok is True
    assert msg == "manifest_ok"


def test_collect_release_includes_so_when_present(tmp_path: Path) -> None:
    so_dir = tmp_path / "rust" / "out"
    so_dir.mkdir(parents=True)
    so_file = so_dir / "boar_fast_filter.so"
    so_file.write_bytes(b"\x7fELF-stub\n")
    (tmp_path / "main.py").write_bytes(b"# stub\n")
    paths = collect_release_file_paths(tmp_path)
    keys = {p.name for p in paths}
    assert "main.py" in keys
    assert "boar_fast_filter.so" in keys

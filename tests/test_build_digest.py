"""Build digest generator and licensing tamper mismatch."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.licensing.guard import LicenseGuard, reset_license_guard_for_tests
from core.licensing.integrity import check_build_digest_expected
from scripts.generate_build_digest import (
    collect_source_paths,
    compute_build_digest_hex,
    write_build_digest,
)


def test_generate_build_digest_deterministic() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    paths = collect_source_paths(repo_root)
    assert paths, "expected at least one critical source file"
    first = compute_build_digest_hex(repo_root, paths)
    second = compute_build_digest_hex(repo_root, paths)
    assert first == second
    assert len(first) == 64


def test_generate_build_digest_writes_expected_file(tmp_path: Path) -> None:
    src = tmp_path / "main.py"
    src.write_bytes(b"print('ok')\n")
    (tmp_path / "core" / "licensing").mkdir(parents=True)
    paths = [src]
    digest = compute_build_digest_hex(tmp_path, paths)
    out = write_build_digest(tmp_path, digest)
    assert out.read_text(encoding="utf-8").strip() == digest


def test_build_digest_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_BOAR_EXPECTED_BUILD_DIGEST", "deadbeef" * 8)
    monkeypatch.setattr(
        "core.licensing.integrity._embedded_build_digest",
        lambda: "cafebabe" * 8,
    )
    ok, msg = check_build_digest_expected()
    assert ok is False
    assert msg.startswith("digest_mismatch:")


def test_license_guard_tampered_on_build_digest_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_BOAR_LICENSE_MODE", "enforced")
    monkeypatch.setenv("DATA_BOAR_EXPECTED_BUILD_DIGEST", "aa" * 32)
    monkeypatch.setattr(
        "core.licensing.integrity._embedded_build_digest",
        lambda: "bb" * 32,
    )
    reset_license_guard_for_tests()
    guard = LicenseGuard({"licensing": {"mode": "enforced"}})
    assert guard.context.state == "TAMPERED"
    assert guard.context.watermark == "UNAUTHORIZED_BUILD"
    assert "digest_mismatch" in guard.context.detail

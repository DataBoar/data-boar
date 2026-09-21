"""#1950: local provenance record binds commit/version/SBOMs; never claims SLSA."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.emit_provenance import (
    KIND,
    build_record,
    collect_toolchain,
    main as emit_main,
    verify_record,
)


def _sha_file(path: Path, payload: bytes) -> None:
    path.write_bytes(payload)


def test_emit_and_verify_with_sboms(tmp_path: Path) -> None:
    app = tmp_path / "sbom-python.cdx.json"
    runtime = tmp_path / "sbom-docker-image.cdx.json"
    _sha_file(app, b'{"bomFormat":"CycloneDX"}')
    _sha_file(runtime, b'{"bomFormat":"CycloneDX","specVersion":"1.6"}')
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "data-boar"\nversion = "1.8.0-beta"\n',
        encoding="utf-8",
    )
    commit = "a" * 40
    out = tmp_path / "sbom" / "provenance-local.json"
    rc = emit_main(
        [
            "emit",
            "--root",
            str(tmp_path),
            "--out",
            str(out),
            "--application",
            str(app),
            "--runtime",
            str(runtime),
            "--source-commit",
            commit,
            "--require-sboms",
        ]
    )
    assert rc == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["kind"] == KIND
    assert record["signed_slsa"] is False
    assert record["source_commit"] == commit
    assert record["version"] == "1.8.0-beta"
    assert "application" in record["sbom_digests"]
    assert "runtime" in record["sbom_digests"]
    assert record["signed_attestation"] is None
    rc = emit_main(
        [
            "verify",
            "--root",
            str(tmp_path),
            "--out",
            str(out),
            "--require-sboms",
        ]
    )
    assert rc == 0


def test_require_signed_attestation_fails_without_bundle(tmp_path: Path) -> None:
    app = tmp_path / "a.json"
    runtime = tmp_path / "r.json"
    _sha_file(app, b"app")
    _sha_file(runtime, b"run")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0"\n',
        encoding="utf-8",
    )
    with pytest.raises(FileNotFoundError, match="signed attestation"):
        build_record(
            tmp_path,
            source_commit="b" * 40,
            version="0",
            application=app,
            runtime=runtime,
            attestation=tmp_path / "missing.intoto.jsonl",
            require_sboms=True,
            require_signed_attestation=True,
        )


def test_verify_rejects_signed_slsa_true() -> None:
    record = {
        "kind": KIND,
        "signed_slsa": True,
        "source_commit": "c" * 40,
        "version": "1",
        "toolchain": {"python": "3.13"},
        "workflow_inputs": {},
        "artifact_digests": {},
        "sbom_digests": {"application": "d" * 64, "runtime": "e" * 64},
        "signed_attestation": None,
    }
    with pytest.raises(ValueError, match="signed_slsa"):
        verify_record(record, require_sboms=True, require_signed_attestation=False)


def test_toolchain_collection_is_fail_soft_when_command_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="rustc --version", timeout=15)

    monkeypatch.setattr("scripts.emit_provenance.subprocess.run", timeout)

    toolchain = collect_toolchain(tmp_path)

    assert toolchain["python"]
    assert "uv" not in toolchain
    assert "rustc" not in toolchain

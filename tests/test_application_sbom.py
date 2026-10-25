"""#1950: application CycloneDX must include the Cargo.lock graph; drift fails check."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.application_sbom import (
    CARGO_LOCK_REL,
    check_rust_lock_coverage,
    merge_cargo_into_bom,
    parse_cargo_lock,
)
from scripts.application_sbom import main as application_sbom_main

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture()
def python_stub_bom() -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {"properties": []},
        "components": [
            {
                "type": "library",
                "name": "fastapi",
                "version": "0.0.0",
                "purl": "pkg:pypi/fastapi@0.0.0",
            }
        ],
    }


def test_parse_real_cargo_lock_includes_pyo3_and_regex() -> None:
    packages = parse_cargo_lock(REPO / CARGO_LOCK_REL)
    names = {p["name"] for p in packages}
    assert "pyo3" in names
    assert "regex" in names
    assert "boar_fast_filter" in names
    assert "aho-corasick" in names


def test_merge_adds_lock_crates_without_dropping_python(python_stub_bom: dict) -> None:
    packages = parse_cargo_lock(REPO / CARGO_LOCK_REL)
    merged = merge_cargo_into_bom(
        copy.deepcopy(python_stub_bom),
        packages,
        lock_rel=CARGO_LOCK_REL.as_posix(),
    )
    names = {c["name"] for c in merged["components"]}
    assert "fastapi" in names
    assert "pyo3" in names
    assert check_rust_lock_coverage(merged, packages) == []


def test_check_fails_when_crate_dropped(python_stub_bom: dict) -> None:
    packages = parse_cargo_lock(REPO / CARGO_LOCK_REL)
    merged = merge_cargo_into_bom(
        copy.deepcopy(python_stub_bom),
        packages,
        lock_rel=CARGO_LOCK_REL.as_posix(),
    )
    merged["components"] = [c for c in merged["components"] if c.get("name") != "pyo3"]
    missing = check_rust_lock_coverage(merged, packages)
    assert any(item.startswith("pyo3@") for item in missing)


def test_cli_merge_and_check_roundtrip(python_stub_bom: dict, tmp_path: Path) -> None:
    src = tmp_path / "python.cdx.json"
    src.write_text(json.dumps(copy.deepcopy(python_stub_bom)), encoding="utf-8")
    out = tmp_path / "app.cdx.json"
    rc = application_sbom_main(
        [
            "--repo-root",
            str(REPO),
            "merge",
            "--python-bom",
            str(src),
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert (
        application_sbom_main(
            ["--repo-root", str(REPO), "check", "--application", str(out)]
        )
        == 0
    )
    drifted = json.loads(out.read_text(encoding="utf-8"))
    drifted["components"] = [
        c for c in drifted["components"] if c.get("name") != "regex"
    ]
    bad = tmp_path / "drift.cdx.json"
    bad.write_text(json.dumps(drifted), encoding="utf-8")
    assert (
        application_sbom_main(
            ["--repo-root", str(REPO), "check", "--application", str(bad)]
        )
        == 1
    )

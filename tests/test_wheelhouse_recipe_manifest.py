"""Guards for wheelhouse recipe single-source-of-truth + CI wiring (#1379)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "scripts" / "wheelhouse" / "recipe-manifest.yaml"
PLAN = REPO / "docs" / "plans" / "PLAN_WHEELHOUSE_DISTRIBUTION.md"
WORKFLOW = REPO / ".github" / "workflows" / "wheelhouse-recipe.yml"
RUN_CELL = REPO / "scripts" / "wheelhouse" / "run_cell.sh"
BUILD_MUSL = REPO / "scripts" / "wheelhouse" / "build_musl_incontainer.sh"


def _manifest() -> dict:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_manifest_has_required_pins_and_gates() -> None:
    m = _manifest()
    assert m["schema_version"] == 1
    assert m["gates"]["numpy_popcnt_max"] == 0
    assert m["gates"]["numpy_umath_so_max_bytes"] == 8_000_000
    assert m["gates"]["scipy_forbid_libscipy_openblas"] is True
    assert m["build"]["require_no_build_isolation"] is True
    assert m["build"]["docker_platform"] == "linux/amd64"
    assert "-Dcpu-baseline=none" in m["build"]["numpy_meson_args"]
    assert m["canary"] == {"libc": "musl", "python": "3.12"}
    cc = m["mariadb_connector_c"]
    assert cc["version"] == "3.4.6"
    assert re.fullmatch(r"[0-9a-f]{64}", cc["sha256"])
    assert "v3.4.6.tar.gz" in cc["tarball_url"]
    assert "-DWITH_EXTERNAL_ZLIB=ON" in cc["cmake_flags"]


def test_plan_references_manifest_and_shares_connector_sha256() -> None:
    plan = PLAN.read_text(encoding="utf-8")
    assert "scripts/wheelhouse/recipe-manifest.yaml" in plan
    sha = _manifest()["mariadb_connector_c"]["sha256"]
    assert sha in plan, (
        "PLAN prose must show the same Connector/C sha256 as the manifest"
    )


def test_workflow_does_not_hardcode_connector_sha256() -> None:
    """Two copies diverge — CI must load the pin from the manifest only."""
    sha = _manifest()["mariadb_connector_c"]["sha256"]
    text = WORKFLOW.read_text(encoding="utf-8")
    assert sha not in text
    assert "recipe-manifest.yaml" in text or "verify_connector_c_checksum.sh" in text
    assert "wheelhouse-recipe" in text or "Wheelhouse recipe" in text
    data = yaml.safe_load(text)
    # GitHub Actions key is `on:`; YAML 1.1 may load it as True unless quoted as 'on'.
    on = data.get("on") or data.get(True)
    assert isinstance(on, dict)
    assert "schedule" in on
    assert "workflow_dispatch" in on
    assert "pull_request" in on
    jobs = data["jobs"]
    assert "connector-c-checksum" in jobs
    assert "canary-musl-cp312" in jobs
    assert "matrix-cell" in jobs


def test_export_build_env_composes_package_name_with_spec() -> None:
    """pip rejects a bare '>=2.4.6' — export must be 'numpy>=2.4.6' (#1380 CI)."""
    import subprocess
    import sys

    out = subprocess.check_output(
        [
            sys.executable,
            str(REPO / "scripts" / "wheelhouse" / "load_manifest.py"),
            "--export-build-env",
        ],
        text=True,
    )
    assert "NUMPY_SPEC='numpy>=2.4.6'" in out
    assert "SCIPY_SPEC='scipy>=" in out
    assert "SKLEARN_SPEC='scikit-learn>=" in out
    assert "PANDAS_SPEC='pandas>=" in out
    assert "NUMPY_SPEC='>=2.4.6'" not in out


def test_build_scripts_preserve_grep_c_and_platform_lessons() -> None:
    musl = BUILD_MUSL.read_text(encoding="utf-8")
    assert "grep -c popcnt || true" in musl
    assert "--no-build-isolation" in musl
    assert "libscipy_openblas" in musl
    assert "GATE_UMATH_MAX_BYTES" in musl
    run = RUN_CELL.read_text(encoding="utf-8")
    assert "--platform" in run
    assert "docker_platform" in run

"""EXTRAS_MANIFEST, --check-extras, ABI guard, missing-extra messages (#1400/#1401/#1402)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.extras_manifest import (
    IMAGE_BASE_EXTRAS,
    assert_in_artifact_imports,
    build_manifest,
    check_extras_rows,
    format_check_extras_table,
)
from core.extras_runtime import (
    install_hint_for_extra,
    unresolved_connector_failure,
    verify_extras_abi,
)


REPO = Path(__file__).resolve().parents[1]


def test_manifest_lists_all_pyproject_extras() -> None:
    m = build_manifest(probe=False)
    assert "postgres" in m["extras"]
    assert "nosql" in m["extras"]
    assert "shares" in m["extras"]
    assert set(m["image_base_extras"]) == set(IMAGE_BASE_EXTRAS)
    for name in IMAGE_BASE_EXTRAS:
        assert m["extras"][name]["in_artifact"] is True


def test_assert_in_artifact_imports_fails_when_marked_missing(tmp_path: Path) -> None:
    """Smoke-guard proof: in_artifact true + missing module → RuntimeError (#1401)."""
    bogus = {
        "schema_version": 1,
        "extras": {
            "nosql": {
                "packages": ["pymongo>=4.0"],
                "modules": ["definitely_not_a_real_module_xyz_1401"],
                "in_artifact": True,
            }
        },
    }
    path = tmp_path / "EXTRAS_MANIFEST.json"
    path.write_text(json.dumps(bogus), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    with pytest.raises(RuntimeError, match="in_artifact import failed"):
        assert_in_artifact_imports(loaded)


def test_check_extras_table_names_extras() -> None:
    text = format_check_extras_table(check_extras_rows(build_manifest(probe=True)))
    assert "extra" in text
    assert "nosql" in text
    assert "shares" in text


def test_unresolved_typo_vs_missing_optional() -> None:
    reason, detail = unresolved_connector_failure({"type": "unknowntype_xyz"})
    assert reason == "unknown_connector_type"
    assert "typo" in detail.lower()

    reason2, detail2 = unresolved_connector_failure({"type": "smb"})
    assert reason2 == "missing_optional_dependency"
    assert "shares" in detail2
    assert "/extras" in detail2

    reason3, detail3 = unresolved_connector_failure(
        {"type": "database", "driver": "redis"}
    )
    assert reason3 == "missing_optional_dependency"
    assert "nosql" in detail3


def test_install_hint_names_extra_and_runtime_path() -> None:
    hint = install_hint_for_extra("mssql-pymssql")
    assert "data-boar[mssql-pymssql]" in hint
    assert "/extras" in hint


def test_verify_extras_abi_empty_ok(tmp_path: Path) -> None:
    empty = tmp_path / "extras"
    empty.mkdir()
    verify_extras_abi(empty)  # no raise


def test_verify_extras_abi_rejects_wrong_tag(tmp_path: Path) -> None:
    root = tmp_path / "extras"
    dist = root / "fake-1.0.dist-info"
    dist.mkdir(parents=True)
    (dist / "WHEEL").write_text(
        "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: false\nTag: cp39-cp39-linux_x86_64\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="ABI-incompatible"):
        verify_extras_abi(root)


def test_generate_script_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "EXTRAS_MANIFEST.json"
    r = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "generate_extras_manifest.py"),
            "--no-probe",
            "--write",
            str(out),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "sql-community" in data["extras"]


def test_main_check_extras_exit_zero(tmp_path: Path) -> None:
    r = subprocess.run(
        [sys.executable, str(REPO / "main.py"), "--check-extras"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "nosql" in r.stdout
    assert "estado" in r.stdout.lower() or "OK" in r.stdout or "AUSENTE" in r.stdout


def test_smb_and_redis_always_registered() -> None:
    import connectors.redis_connector  # noqa: F401
    import connectors.smb_connector  # noqa: F401
    from core.connector_registry import list_connector_types

    types = list_connector_types()
    assert "smb" in types
    assert "cifs" in types
    assert "redis" in types


def test_dockerfile_has_extras_runtime_extension() -> None:
    text = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert 'VOLUME ["/extras"]' in text
    assert "ENV PYTHONPATH=/extras" in text
    assert "DATA_BOAR_MACHINE_SEED" in text
    assert '"/app[sql-community,mssql,oracle]"' in text
    assert "generate_extras_manifest.py" in text
    assert "EXTRAS_MANIFEST.json" in text
    nogil = (REPO / "Dockerfile.nogil").read_text(encoding="utf-8")
    assert 'VOLUME ["/extras"]' in nogil
    assert "ENV PYTHONPATH=/extras" in nogil


def test_docker_smoke_scripts_guard_in_artifact() -> None:
    sh = (REPO / "scripts" / "docker" / "docker-image-smoke.sh").read_text(
        encoding="utf-8"
    )
    ps1 = (REPO / "scripts" / "docker" / "docker-image-smoke.ps1").read_text(
        encoding="utf-8"
    )
    assert "assert_in_artifact_imports" in sh
    assert "assert_in_artifact_imports" in ps1

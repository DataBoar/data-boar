"""Regression guards for #1028 release image hardening (PR-A)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = REPO_ROOT / "Dockerfile"
COLLECT_SCRIPT = REPO_ROOT / "scripts" / "docker" / "collect-runtime-rootfs.sh"
SMOKE_SH = REPO_ROOT / "scripts" / "docker" / "docker-image-smoke.sh"
GRYPE_CONFIG = REPO_ROOT / ".grype.yaml"
GRYPE_GATE_SH = REPO_ROOT / "scripts" / "grype-image-gate.sh"
GRYPE_GATE_PS1 = REPO_ROOT / "scripts" / "grype-image-gate.ps1"


def _dockerfile_instructions(text: str) -> str:
    """Dockerfile body excluding comments (so we can forbid shell-form HEALTHCHECK)."""
    return "\n".join(
        ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")
    )


def _dockerfile_from_lines() -> list[str]:
    text = DOCKERFILE.read_text(encoding="utf-8")
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip().upper().startswith("FROM ")
    ]


def test_dockerfile_pins_all_from_images_by_digest() -> None:
    """ADR-0074 / #1028: every stage (builder, assembler, distroless) uses digest-pinned FROM."""
    from_lines = _dockerfile_from_lines()
    assert len(from_lines) >= 3, f"expected 3-stage Dockerfile, got: {from_lines!r}"
    for line in from_lines:
        assert "@sha256:" in line, f"expected digest pin in FROM line: {line!r}"
    joined = "\n".join(from_lines)
    assert "distroless/cc-debian13" in joined
    assert "python:3.14-slim" in joined


def _dockerfile_from_first_from(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("FROM "):
            return "\n".join(lines[i:])
    raise AssertionError("no FROM in Dockerfile")


def test_dockerfile_distroless_nonroot_and_exec_cmd() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "distroless/cc-debian13:nonroot@" in text
    assert "USER 65532:65532" in text
    assert 'ENTRYPOINT ["/usr/local/bin/python3.14t"' in text
    assert "core.licensing.gil_container_gate" in text
    assert 'CMD ["main.py"' in text
    assert "HEALTHCHECK" in text
    assert "CMD-SHELL" not in _dockerfile_instructions(text)
    assert "http://127.0.0.1:8088/health" in text
    assert "urllib.request" in text
    joined_hc = "\n".join(
        ln for ln in text.splitlines() if "HEALTHCHECK" in ln or "urllib.request" in ln
    )
    assert '"/usr/local/bin/python3.14t"' in joined_hc
    assert "0.0.0.0" not in joined_hc


def test_dockerfile_extras_runtime_extension_point() -> None:
    """#1400: lean base + /extras mount; no fat image of all optional extras."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert 'VOLUME ["/extras"]' in text
    assert "ENV PYTHONPATH=/extras:/app" in text
    assert "DATA_BOAR_MACHINE_SEED" in text
    assert '"/app[sql-community,mssql,oracle]"' in text
    assert "generate_extras_manifest.py" in text
    # Must not silently expand to all 18 extras in the image.
    assert "sql-all,nosql,shares" not in text
    smoke = SMOKE_SH.read_text(encoding="utf-8")
    assert "assert_in_artifact_imports" in smoke


def test_collect_runtime_rootfs_script_bundles_tls_and_db_libs() -> None:
    text = COLLECT_SCRIPT.read_text(encoding="utf-8")
    assert "ca-certificates.crt" in text
    assert "libpq.so" in text
    assert "libssl.so" in text or "libcrypto.so" in text
    assert "libmariadb.so" in text
    assert "usrmerge_dest" in text or "copy_lib_path" in text
    assert "refusing usr-merge conflict" in text
    # stdlib extension deps (e.g. _sqlite3 → libsqlite3) live in lib-dynload, not site-packages.
    assert "lib-dynload" in text
    assert "libsqlite3" in text
    assert "sysconfig.get_path" in text  # derive python3.14 / python3.14t
    assert (
        "readlink" in text
    )  # SONAME symlink → real .so (avoid dangling in distroless)


def test_dockerfile_applies_wheelhouse_v1_in_builder() -> None:
    """#1387: release image must force-reinstall ML stack from x86-64-v1 wheelhouse."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "apply_wheelhouse_v1.sh" in text
    assert "WHEELHOUSE_TAG" in text
    assert "binutils" in text  # objdump popcnt gate
    script = REPO_ROOT / "scripts" / "docker" / "apply_wheelhouse_v1.sh"
    assert script.is_file()
    body = script.read_text(encoding="utf-8")
    assert "--force-reinstall" in body
    assert "--no-index" in body
    assert "popcnt" in body
    assert "boar_fast_filter" in body
    assert "wheelhouse-x86-64-v1-2026-07-29" in body
    # ABI must follow the builder interpreter (cp314 / cp314t), not a hardcode.
    assert "Py_GIL_DISABLED" in body or "SOABI" in body
    assert "sys.version_info" in body
    assert "cp314t" in body  # free-threaded wheel cells + EXPECTED_SHA
    assert "mariadb-1.1.14-cp314-cp314t-linux_x86_64.whl" in body
    assert "pymssql-2.3.13-cp314-cp314t-linux_x86_64.whl" in body


def test_dockerfile_nogil_pins_and_uv_freethreaded() -> None:
    """#1409: one image — Dockerfile is cp314t; Dockerfile.nogil is an alias."""
    nogil = REPO_ROOT / "Dockerfile.nogil"
    assert nogil.is_file()
    text = DOCKERFILE.read_text(encoding="utf-8")
    alias = nogil.read_text(encoding="utf-8")
    assert _dockerfile_from_first_from(text) == _dockerfile_from_first_from(alias)
    assert "python:3.14-slim@" in text
    assert "@sha256:" in text
    assert "uv python install" in text
    assert "freethreaded" in text
    assert "python3.14t" in text
    assert "DISABLE_SQLALCHEMY_CEXT=1" in text
    assert "--no-binary sqlalchemy" in text
    assert "freetds-dev" in text  # pymssql source build on cp314t (#1398)
    assert "libkrb5-dev" in text
    assert "assert not sos" in text
    assert "GIL re-enabled after sqlalchemy" in text
    assert "gil_container_gate" in text
    assert "ENV PYTHON_GIL" not in text
    assert "PYTHON_GIL=0" not in [
        ln.strip() for ln in text.splitlines() if not ln.lstrip().startswith("#")
    ]
    assert "distroless/cc-debian13:nonroot@" in text
    assert "HEALTHCHECK" in text
    assert "CMD-SHELL" not in _dockerfile_instructions(text)
    assert "http://127.0.0.1:8088/health" in text
    assert '"/usr/local/bin/python3.14t"' in text
    from_lines = [
        ln.strip() for ln in text.splitlines() if ln.strip().upper().startswith("FROM ")
    ]
    assert all("3.14t-slim" not in ln for ln in from_lines)
    assert all("@sha256:" in ln for ln in from_lines)
    collect = COLLECT_SCRIPT.read_text(encoding="utf-8")
    assert "sysconfig.get_path" in collect  # python3.14t lib dir


def test_boar_fast_filter_releases_gil_on_batch_and_stage() -> None:
    """#1398 / #551: Rust hot paths must use py.detach (PyO3 ≥0.29)."""
    lib = (REPO_ROOT / "rust" / "boar_fast_filter" / "src" / "lib.rs").read_text(
        encoding="utf-8"
    )
    assert "fn filter_batch(&self, py: Python<'_>" in lib
    assert lib.count("py.detach") >= 2
    assert "fn match_names(&self, py: Python<'_>" in lib


def test_compare_gil_nogil_demo_timing_script_exists() -> None:
    """#1398 AC: manifest duration_minutes comparison helper for publish gate."""
    path = REPO_ROOT / "scripts" / "docker" / "compare-gil-nogil-demo-timing.sh"
    measure = REPO_ROOT / "scripts" / "docker" / "measure_demo_scan_manifest_timing.py"
    assert path.is_file()
    assert measure.is_file()
    body = path.read_text(encoding="utf-8")
    assert "duration_minutes" in body
    assert "PUBLISH_GATE" in body


def test_grype_vex_config_has_documented_ignore_rules() -> None:
    """PR-B #1028: .grype.yaml documents wont-fix base classes + CVE VEX with reason."""
    assert GRYPE_CONFIG.is_file()
    data = yaml.safe_load(GRYPE_CONFIG.read_text(encoding="utf-8"))
    rules = data.get("ignore") or []
    assert len(rules) >= 5
    cve_rules = [r for r in rules if r.get("vulnerability")]
    deb_rules = [r for r in rules if not r.get("vulnerability")]
    for rule in rules:
        assert rule.get("reason"), f"ignore rule missing reason: {rule!r}"
        assert rule.get("package", {}).get("name"), (
            f"ignore rule missing package.name: {rule!r}"
        )
    for rule in deb_rules:
        assert rule.get("fix-state") == "wont-fix"
        assert rule.get("package", {}).get("type") == "deb"
    for cve_id in ("CVE-2026-15308", "CVE-2026-11940", "CVE-2026-11972"):
        assert any(r.get("vulnerability") == cve_id for r in cve_rules), cve_id
        cve_pkg = next(r for r in cve_rules if r["vulnerability"] == cve_id)
        assert cve_pkg.get("package", {}).get("type") == "binary"
        assert cve_pkg.get("package", {}).get("name") == "python"
    names = {r["package"]["name"] for r in deb_rules}
    assert "libc6" in names
    assert "mariadb" in names


def test_grype_image_gate_scripts_enforce_only_fixed() -> None:
    """Gate wrappers must not weaken --only-fixed (PLAN_IMAGE_HARDENING PR-B)."""
    sh = GRYPE_GATE_SH.read_text(encoding="utf-8")
    ps1 = GRYPE_GATE_PS1.read_text(encoding="utf-8")
    assert "--only-fixed" in sh
    assert "--fail-on high" in sh
    assert ".grype.yaml" in sh
    assert "--only-fixed" in ps1
    assert "--fail-on" in ps1 and "high" in ps1


@pytest.mark.skipif(
    subprocess.run(["which", "podman"], capture_output=True, check=False).returncode
    != 0,
    reason="podman not available",
)
def test_docker_image_smoke_script_passes_on_built_image() -> None:
    """Integration: requires pre-built image data_boar:hardening-test (local operator/CI optional)."""
    image = "data_boar:hardening-test"
    inspect = subprocess.run(
        ["podman", "image", "exists", image],
        capture_output=True,
        check=False,
    )
    if inspect.returncode != 0:
        pytest.skip(f"image {image!r} not built locally")

    version = None
    pyproject = REPO_ROOT / "pyproject.toml"
    match = re.search(
        r'^version = "([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M
    )
    if match:
        version = match.group(1)

    if version:
        probe = subprocess.run(
            [
                "podman",
                "run",
                "--rm",
                image,
                "/usr/local/bin/python3.14t",
                "-c",
                "from core.about import _package_version; print(_package_version())",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0:
            pytest.skip(f"cannot probe version in image {image!r}")
        installed = (probe.stdout or "").strip()
        if installed != version:
            pytest.skip(
                f"stale image {image!r}: installed {installed!r} != pyproject {version!r}; "
                "rebuild with docker-lab-build.ps1 / podman build"
            )

    cmd = [str(SMOKE_SH), image]
    if version:
        cmd.append(version)
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def test_compose_data_boar_healthcheck_is_exec_form() -> None:
    """#459: Compose must not use CMD-SHELL — distroless has no /bin/sh."""
    compose_path = REPO_ROOT / "deploy" / "docker-compose.yml"
    data = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    test = data["services"]["data-boar"]["healthcheck"]["test"]
    assert test[0] == "CMD"
    assert test[1] == "/usr/local/bin/python3.14t"
    assert any("127.0.0.1:8088/health" in part for part in test)
    assert "CMD-SHELL" not in compose_path.read_text(encoding="utf-8")

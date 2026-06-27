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
    assert "python:3.13-slim" in joined


def test_dockerfile_distroless_nonroot_and_exec_cmd() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "distroless/cc-debian13:nonroot@" in text
    assert "USER 65532:65532" in text
    assert 'CMD ["/usr/local/bin/python3.13"' in text


def test_collect_runtime_rootfs_script_bundles_tls_and_db_libs() -> None:
    text = COLLECT_SCRIPT.read_text(encoding="utf-8")
    assert "ca-certificates.crt" in text
    assert "libpq.so" in text
    assert "libssl.so" in text or "libcrypto.so" in text
    assert "libmariadb.so" in text
    assert "usrmerge_dest" in text or "copy_lib_path" in text
    assert "refusing usr-merge conflict" in text


def test_dockerfile_builds_boar_fast_filter_in_builder() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "maturin build --release" in text
    assert "import boar_fast_filter" in text


def test_grype_vex_config_has_documented_ignore_rules() -> None:
    """PR-B #1028: .grype.yaml documents wont-fix base classes with reason (audit posture)."""
    assert GRYPE_CONFIG.is_file()
    data = yaml.safe_load(GRYPE_CONFIG.read_text(encoding="utf-8"))
    rules = data.get("ignore") or []
    assert len(rules) >= 5
    for rule in rules:
        assert rule.get("reason"), f"ignore rule missing reason: {rule!r}"
        assert rule.get("fix-state") == "wont-fix"
        assert rule.get("package", {}).get("type") == "deb"
    names = {r["package"]["name"] for r in rules}
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
                "/usr/local/bin/python3.13",
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

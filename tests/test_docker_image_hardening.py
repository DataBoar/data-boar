"""Regression guards for #1028 release image hardening (PR-A)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = REPO_ROOT / "Dockerfile"
COLLECT_SCRIPT = REPO_ROOT / "scripts" / "docker" / "collect-runtime-rootfs.sh"
SMOKE_SH = REPO_ROOT / "scripts" / "docker" / "docker-image-smoke.sh"


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

    cmd = [str(SMOKE_SH), image]
    if version:
        cmd.append(version)
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)

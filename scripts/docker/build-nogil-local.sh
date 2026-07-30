#!/usr/bin/env bash
# Build + validate the free-threaded image locally (no Hub push).
#
# Usage (repo root):
#   ./scripts/docker/build-nogil-local.sh
#   ./scripts/docker/build-nogil-local.sh 1.7.4.post12-nogil
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

TAG="${1:-1.7.4.post12-nogil}"
IMAGE="localhost/data_boar:${TAG}"
# Also tag short name used in AC examples.
ALIAS="data_boar:${TAG}"

need_() { command -v "$1" >/dev/null 2>&1 || { echo "FATAL: $1 not in PATH" >&2; exit 127; }; }
need_ podman

echo "=== podman build -f Dockerfile.nogil -t ${IMAGE} ==="
podman build -f Dockerfile.nogil -t "${IMAGE}" .
podman tag "${IMAGE}" "${ALIAS}"

echo "=== AC: sys._is_gil_enabled() is False ==="
podman run --rm "${ALIAS}" python -c 'import sys; v=sys._is_gil_enabled(); print("gil_enabled", v); raise SystemExit(0 if v is False else 1)'

echo "=== AC: ML + boar_fast_filter imports ==="
podman run --rm "${ALIAS}" python -c 'import numpy,scipy,sklearn,pandas,boar_fast_filter; print("imports_ok", numpy.__version__, boar_fast_filter.__file__)'

echo "=== AC: filter .so is cpython-314t (not abi3) ==="
podman run --rm "${ALIAS}" python -c '
import boar_fast_filter, pathlib
pkg = pathlib.Path(boar_fast_filter.__file__).resolve().parent
sos = sorted(pkg.rglob("*.so"))
print("filter_sos", [p.name for p in sos])
assert sos, pkg
assert not any("abi3" in p.name for p in sos), sos
assert any("314t" in p.name for p in sos), sos
print("filter_ok", sos[0].name)
'

echo "=== AC: docker-image-smoke (public version) ==="
VERSION="${TAG%-nogil}"
./scripts/docker/docker-image-smoke.sh "${ALIAS}" "${VERSION}"

echo "=== AC: grype gate ==="
./scripts/grype-image-gate.sh "${ALIAS}"

echo "=== OK local nogil image ${ALIAS} (NOT pushed) ==="

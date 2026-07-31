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

echo "=== AC: sys._is_gil_enabled() is False (boot) ==="
podman run --rm "${ALIAS}" python -c 'import sys; v=sys._is_gil_enabled(); print("gil_enabled", v); raise SystemExit(0 if v is False else 1)'

echo "=== AC: GIL stays False after sqlalchemy import ==="
OUT="$(podman run --rm "${ALIAS}" python -W error::RuntimeWarning -c 'import sqlalchemy, sys; print(sqlalchemy.__version__); print("gil_after_sa", sys._is_gil_enabled()); raise SystemExit(0 if sys._is_gil_enabled() is False else 1)' 2>&1)" || {
  echo "$OUT" >&2
  echo "FATAL: sqlalchemy import re-enabled GIL or raised RuntimeWarning" >&2
  exit 1
}
echo "$OUT"

echo "=== AC: zero sqlalchemy *.so under site-packages ==="
podman run --rm "${ALIAS}" python -c '
import pathlib, site
root = pathlib.Path(site.getsitepackages()[0]) / "sqlalchemy"
sos = sorted(root.rglob("*.so")) if root.is_dir() else []
print("sqlalchemy_sos", len(sos), [str(p.relative_to(root)) for p in sos[:20]])
raise SystemExit(0 if not sos else 1)
'

echo "=== AC: ML + boar_fast_filter imports (GIL still False) ==="
podman run --rm "${ALIAS}" python -c '
import numpy, scipy, sklearn, pandas, boar_fast_filter, sqlalchemy, sys
print("imports_ok", numpy.__version__, boar_fast_filter.__file__)
print("gil_after_stack", sys._is_gil_enabled())
raise SystemExit(0 if sys._is_gil_enabled() is False else 1)
'

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

echo "=== AC: docker-image-smoke (public version; no GIL RuntimeWarning) ==="
VERSION="${TAG%-nogil}"
SMOKE_OUT="$(./scripts/docker/docker-image-smoke.sh "${ALIAS}" "${VERSION}" 2>&1)" || {
  echo "$SMOKE_OUT" >&2
  exit 1
}
echo "$SMOKE_OUT"
if grep -qiE 'RuntimeWarning|GIL has been enabled' <<<"$SMOKE_OUT"; then
  echo "FATAL: smoke emitted GIL RuntimeWarning" >&2
  exit 1
fi

echo "=== AC: data-boar --version without GIL RuntimeWarning ==="
VER_OUT="$(podman run --rm "${ALIAS}" python main.py --version 2>&1)" || {
  echo "$VER_OUT" >&2
  exit 1
}
echo "$VER_OUT"
grep -qw "${VERSION}" <<<"$VER_OUT" || { echo "FATAL: version token missing" >&2; exit 1; }
if grep -qiE 'RuntimeWarning|GIL has been enabled' <<<"$VER_OUT"; then
  echo "FATAL: --version emitted GIL RuntimeWarning" >&2
  exit 1
fi

echo "=== AC: data-boar --demo completes with findings ==="
# Distroless: invoke via python main.py. --demo runs the scan then blocks on uvicorn;
# timeout after scan output is the expected success path (exit 124).
set +e
DEMO_OUT="$(timeout 240 podman run --rm "${ALIAS}" python main.py --demo 2>&1)"
DEMO_RC=$?
set -e
echo "$DEMO_OUT" | tail -60
if ! grep -q '\[demo\] Scan session:' <<<"$DEMO_OUT"; then
  echo "FATAL: --demo did not complete scan (rc=${DEMO_RC})" >&2
  exit 1
fi
if ! grep -qiE '\[demo\] Report written:|finding' <<<"$DEMO_OUT"; then
  echo "FATAL: --demo missing findings/report signal" >&2
  exit 1
fi
# sqlalchemy cext must stay out of the image (module-level import). Report/XLSX may
# still load lxml.etree and warn — that is a separate follow-up, not this AC.
if grep -qiE "sqlalchemy\.cyextension|to load module 'sqlalchemy" <<<"$DEMO_OUT"; then
  echo "FATAL: --demo loaded sqlalchemy cext / re-enabled GIL via sqlalchemy" >&2
  exit 1
fi
# 0 = exited; 124 = timeout (uvicorn still up after scan) — both OK once scan reported.
if [[ "${DEMO_RC}" -ne 0 && "${DEMO_RC}" -ne 124 ]]; then
  echo "FATAL: --demo unexpected exit ${DEMO_RC}" >&2
  exit 1
fi

echo "=== AC: grype gate ==="
./scripts/grype-image-gate.sh "${ALIAS}"

echo "=== OK local nogil image ${ALIAS} (NOT pushed) ==="

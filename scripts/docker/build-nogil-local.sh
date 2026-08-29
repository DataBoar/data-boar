#!/usr/bin/env bash
# Build + validate the free-threaded image locally (no Hub push).
#
# Usage (repo root):
#   ./scripts/docker/build-nogil-local.sh
#   ./scripts/docker/build-nogil-local.sh 1.7.4.post12-nogil
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

APP_VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path
print(tomllib.load(Path("pyproject.toml").open("rb"))["project"]["version"])
PY
)"
TAG="${1:-${APP_VERSION}-nogil}"
IMAGE="localhost/data_boar:${TAG}"
# Also tag short name used in AC examples.
ALIAS="data_boar:${TAG}"
# Smoke/version checks use pyproject semver (tag prefix may differ for Hub pairs).
SMOKE_VERSION="${APP_VERSION}"

need_() { command -v "$1" >/dev/null 2>&1 || { echo "FATAL: $1 not in PATH" >&2; exit 127; }; }
need_ podman

echo "=== podman build -f Dockerfile -t ${IMAGE} ==="
podman build -f Dockerfile -t "${IMAGE}" .
podman tag "${IMAGE}" "${ALIAS}"

# Interpreter contract: skip license ENTRYPOINT (OPEN would set PYTHON_GIL=1).
EP=(podman run --rm --entrypoint /usr/local/bin/python3.14t "${ALIAS}")

echo "=== AC: sys._is_gil_enabled() is False (boot, --entrypoint) ==="
"${EP[@]}" -c 'import sys; v=sys._is_gil_enabled(); print("gil_enabled", v); raise SystemExit(0 if v is False else 1)'

echo "=== AC: GIL stays False after sqlalchemy import ==="
OUT="$("${EP[@]}" -W error::RuntimeWarning -c 'import sqlalchemy, sys; print(sqlalchemy.__version__); print("gil_after_sa", sys._is_gil_enabled()); raise SystemExit(0 if sys._is_gil_enabled() is False else 1)' 2>&1)" || {
  echo "$OUT" >&2
  echo "FATAL: sqlalchemy import re-enabled GIL or raised RuntimeWarning" >&2
  exit 1
}
echo "$OUT"

echo "=== AC: zero sqlalchemy *.so under site-packages ==="
"${EP[@]}" -c '
import pathlib, site
root = pathlib.Path(site.getsitepackages()[0]) / "sqlalchemy"
sos = sorted(root.rglob("*.so")) if root.is_dir() else []
print("sqlalchemy_sos", len(sos), [str(p.relative_to(root)) for p in sos[:20]])
raise SystemExit(0 if not sos else 1)
'

echo "=== AC: ML + boar_fast_filter imports (GIL still False) ==="
"${EP[@]}" -c '
import numpy, scipy, sklearn, pandas, boar_fast_filter, sqlalchemy, sys
print("imports_ok", numpy.__version__, boar_fast_filter.__file__)
print("gil_after_stack", sys._is_gil_enabled())
raise SystemExit(0 if sys._is_gil_enabled() is False else 1)
'

echo "=== AC: filter .so is cpython-314t (not abi3) ==="
"${EP[@]}" -c '
import boar_fast_filter, pathlib
pkg = pathlib.Path(boar_fast_filter.__file__).resolve().parent
sos = sorted(pkg.rglob("*.so"))
print("filter_sos", [p.name for p in sos])
assert sos, pkg
assert not any("abi3" in p.name for p in sos), sos
assert any("314t" in p.name for p in sos), sos
print("filter_ok", sos[0].name)
'

echo "=== AC: license gate — OPEN/default forces PYTHON_GIL=1 ==="
GATE_OUT="$(podman run --rm "${ALIAS}" python -c 'import os,sys; g=os.environ.get("PYTHON_GIL"); e=sys._is_gil_enabled(); print("PYTHON_GIL", g, "gil_enabled", e); raise SystemExit(0 if g=="1" and e is True else 1)' 2>&1)" || {
  echo "$GATE_OUT" >&2
  echo "FATAL: default entrypoint must set PYTHON_GIL=1 and enable GIL" >&2
  exit 1
}
echo "$GATE_OUT"

echo "=== AC: license gate — open + effective_tier enterprise keeps no-GIL ==="
ENT_CFG="$(mktemp)"
trap 'rm -f "${ENT_CFG}"' EXIT
printf '%s\n' 'licensing:' '  mode: open' '  effective_tier: enterprise' > "${ENT_CFG}"
# Distroless nonroot cannot read a 0600 mktemp file bind-mounted at /data.
chmod a+r "${ENT_CFG}"
ENT_OUT="$(podman run --rm -v "${ENT_CFG}:/data/config.yaml:ro" -e CONFIG_PATH=/data/config.yaml "${ALIAS}" python -c 'import os,sys; g=os.environ.get("PYTHON_GIL"); e=sys._is_gil_enabled(); print("PYTHON_GIL", g, "gil_enabled", e); raise SystemExit(0 if not g and e is False else 1)' 2>&1)" || {
  echo "$ENT_OUT" >&2
  echo "FATAL: Enterprise open-mode YAML must leave PYTHON_GIL unset and GIL off" >&2
  exit 1
}
echo "$ENT_OUT"

echo "=== AC: docker-image-smoke (public version; no GIL RuntimeWarning) ==="
SMOKE_OUT="$(./scripts/docker/docker-image-smoke.sh "${ALIAS}" "${SMOKE_VERSION}" 2>&1)" || {
  echo "$SMOKE_OUT" >&2
  exit 1
}
echo "$SMOKE_OUT"
if grep -qiE "sqlalchemy\\.cyextension|to load module 'sqlalchemy" <<<"$SMOKE_OUT"; then
  echo "FATAL: smoke loaded sqlalchemy cext" >&2
  exit 1
fi

echo "=== AC: data-boar --version without GIL RuntimeWarning ==="
VER_OUT="$(podman run --rm "${ALIAS}" python main.py --version 2>&1)" || {
  echo "$VER_OUT" >&2
  exit 1
}
echo "$VER_OUT"
grep -qw "${SMOKE_VERSION}" <<<"$VER_OUT" || { echo "FATAL: version token missing" >&2; exit 1; }
if grep -qiE "sqlalchemy\\.cyextension|to load module 'sqlalchemy" <<<"$VER_OUT"; then
  echo "FATAL: --version loaded sqlalchemy cext" >&2
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

echo "=== AC: cryptography >= 50.0.0 (GHSA-g6cj-pr64-35w5) ==="
podman run --rm --entrypoint /usr/local/bin/python3.14t "${ALIAS}" -c '
import importlib.metadata as m
v = m.version("cryptography")
print("cryptography", v)
parts = tuple(int(p) for p in v.split(".")[:2])
raise SystemExit(0 if parts >= (50, 0) else 1)
'

echo "=== AC: grype gate ==="
./scripts/grype-image-gate.sh "${ALIAS}"

echo "=== AC: optional GIL vs nogil demo timing (manifest duration_minutes) ==="
if podman image exists "localhost/data_boar:1.7.4.post12" 2>/dev/null; then
  if ./scripts/docker/compare-gil-nogil-demo-timing.sh "localhost/data_boar:1.7.4.post12" "${ALIAS}"; then
    echo "  publish_gate: nogil demo faster than local GIL reference — operator may publish after review"
  else
    cmp_rc=$?
    if [[ "${cmp_rc}" -eq 3 ]]; then
      echo "WARN: nogil demo did NOT beat GIL on manifest timing — do NOT publish -nogil (#1398 AC)" >&2
    else
      echo "WARN: compare-gil-nogil-demo-timing failed (rc=${cmp_rc}) — skipped publish gate" >&2
    fi
  fi
else
  echo "  skip: no local GIL reference image localhost/data_boar:1.7.4.post12 (pull/build to run compare)"
fi

echo "=== OK local nogil image ${ALIAS} (NOT pushed) ==="

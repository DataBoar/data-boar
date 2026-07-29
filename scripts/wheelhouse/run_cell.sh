#!/usr/bin/env bash
# run_cell.sh — host driver: load recipe-manifest.yaml, run one scientific cell in Docker.
# Usage: run_cell.sh musl|glibc <pyver>
#   DOCKER=podman run_cell.sh musl 3.12
#
# ALWAYS passes --platform from the manifest (default linux/amd64). Without an
# explicit platform a local tag may be another arch and the job runs emulated
# (measured: 30+ min stuck).
set -euo pipefail
LIBC="${1:?usage: run_cell.sh musl|glibc <pyver>}"
PYVER="${2:?usage: run_cell.sh musl|glibc <pyver>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DOCKER="${DOCKER:-docker}"
OUT="${WHEELHOUSE_OUT:-${TMPDIR:-/tmp}/data-boar-wheelhouse-ci}"
mkdir -p "$OUT/$LIBC" "$OUT/logs"

# Prefer uv-run when available so PyYAML resolves from the project env.
if command -v uv >/dev/null 2>&1 && [ -f "$HERE/../../pyproject.toml" ]; then
  LOAD=(uv run --project "$HERE/../.." python "$HERE/load_manifest.py")
else
  LOAD=(python3 "$HERE/load_manifest.py")
fi

eval "$("${LOAD[@]}" --export-build-env)"
PLATFORM="$("${LOAD[@]}" --get build.docker_platform)"
export NUMPY_SPEC SCIPY_SPEC SKLEARN_SPEC PANDAS_SPEC PURE_WHEELS
export NUMPY_MESON_PIP_ARGS GATE_POPCNT_MAX GATE_UMATH_MAX_BYTES

CP="cp${PYVER//./}"
LOG="$OUT/logs/${LIBC}-${CP}.log"
echo "=== run_cell $LIBC $PYVER platform=$PLATFORM ===" | tee "$LOG"
date | tee -a "$LOG"

ENV_ARGS=(
  -e NUMPY_SPEC -e SCIPY_SPEC -e SKLEARN_SPEC -e PANDAS_SPEC
  -e PURE_WHEELS -e NUMPY_MESON_PIP_ARGS
  -e GATE_POPCNT_MAX -e GATE_UMATH_MAX_BYTES
  -e TMPDIR=/var/tmp/data-boar-build
)

if [ "$LIBC" = musl ]; then
  IMG_TMPL="$("${LOAD[@]}" --get containers.musl.image_template)"
  IMG="${IMG_TMPL/\{pyver\}/$PYVER}"
  AUDIT="$("${LOAD[@]}" --get containers.musl.auditwheel_plat)"
  BUILD="$HERE/build_musl_incontainer.sh"
  "$DOCKER" run --rm --platform "$PLATFORM" \
    "${ENV_ARGS[@]}" -e "AUDITWHEEL_PLAT=$AUDIT" \
    -v "$BUILD:/build.sh:ro" -v "$OUT/$LIBC:/out/repaired" \
    "$IMG" sh /build.sh 2>&1 | tee -a "$LOG"
elif [ "$LIBC" = glibc ]; then
  IMG="$("${LOAD[@]}" --get containers.glibc.image)"
  AUDIT="$("${LOAD[@]}" --get containers.glibc.auditwheel_plat)"
  BUILD="$HERE/build_glibc_incontainer.sh"
  "$DOCKER" run --rm --platform "$PLATFORM" \
    "${ENV_ARGS[@]}" -e "AUDITWHEEL_PLAT=$AUDIT" \
    -v "$BUILD:/build.sh:ro" -v "$OUT/$LIBC:/out/repaired" \
    "$IMG" bash /build.sh "$CP" 2>&1 | tee -a "$LOG"
else
  echo "FATAL: libc must be musl|glibc"; exit 2
fi

# Preserve docker exit through tee (pipefail).
exit "${PIPESTATUS[0]}"

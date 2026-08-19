#!/usr/bin/env bash
# Compare internal demo scan timing: GIL image vs -nogil (#1398 AC).
#
# Usage (repo root):
#   ./scripts/docker/compare-gil-nogil-demo-timing.sh [gil_image] [nogil_image]
#
# Defaults:
#   GIL image   = localhost/data_boar:1.7.4.post12 (build locally or pull Hub tag)
#   nogil image = data_boar:1.7.4.post12-nogil (from build-nogil-local.sh)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

GIL_IMAGE="${1:-localhost/data_boar:1.7.4.post12}"
NOGIL_IMAGE="${2:-data_boar:1.7.4.post12-nogil}"
MEASURE="/app/scripts/docker/measure_demo_scan_manifest_timing.py"
MEASURE_HOST="${REPO_ROOT}/scripts/docker/measure_demo_scan_manifest_timing.py"

need_() { command -v "$1" >/dev/null 2>&1 || { echo "FATAL: $1 not in PATH" >&2; exit 127; }; }
need_ podman
need_ python3

measure_image() {
  local image="$1"
  local variant="$2"
  podman run --rm \
    -v "${MEASURE_HOST}:${MEASURE}:ro" \
    -e "DATA_BOAR_IMAGE_VARIANT=${variant}" \
    "${image}" \
    python "${MEASURE}"
}

echo "=== #1398 demo timing (manifest duration_minutes) ==="
echo "GIL image:   ${GIL_IMAGE}"
echo "nogil image: ${NOGIL_IMAGE}"

if ! podman image exists "${GIL_IMAGE}" 2>/dev/null; then
  echo "WARN: GIL image missing locally — pull/build ${GIL_IMAGE} first" >&2
  echo "  e.g. podman pull docker.io/fabioleitao/data_boar:1.7.4.post12" >&2
  exit 2
fi
if ! podman image exists "${NOGIL_IMAGE}" 2>/dev/null; then
  echo "WARN: nogil image missing — run ./scripts/docker/build-nogil-local.sh first" >&2
  exit 2
fi

# Distroless runs as uid 65532; bind-mount must be world-readable.
chmod a+r "${MEASURE_HOST}"

GIL_JSON="$(measure_image "${GIL_IMAGE}" "gil-cext" | grep '^{' | tail -1)"
NOGIL_JSON="$(measure_image "${NOGIL_IMAGE}" "nogil-pure-python-sa" | grep '^{' | tail -1)"

echo "GIL:   ${GIL_JSON}"
echo "NOGIL: ${NOGIL_JSON}"

python3 - <<'PY' "${GIL_JSON}" "${NOGIL_JSON}"
import json
import sys

gil = json.loads(sys.argv[1])
nogil = json.loads(sys.argv[2])
for label, row in ("GIL", gil), ("NOGIL", nogil):
    if label == "NOGIL" and row.get("gil_after_sqlalchemy") is True:
        print(
            f"FAIL AC: {label} GIL re-enabled after sqlalchemy import",
            file=sys.stderr,
        )
        sys.exit(1)
    if row.get("duration_minutes") is None:
        print(f"FAIL AC: {label} missing duration_minutes in manifest", file=sys.stderr)
        sys.exit(1)
    print(
        f"{label}: duration_minutes={row['duration_minutes']} "
        f"findings_total={row.get('findings_total')} "
        f"gil_after_sa={row.get('gil_after_sqlalchemy')} "
        f"gil_after_scan={row.get('gil_after_scan')}"
    )

g = float(gil["duration_minutes"])
n = float(nogil["duration_minutes"])
if n >= g:
    print(
        "PUBLISH_GATE: nogil is NOT faster than GIL on demo manifest timing "
        f"({n:.4f} >= {g:.4f} min) — do NOT publish -nogil (#1398 AC).",
        file=sys.stderr,
    )
    sys.exit(3)
ratio = g / n if n > 0 else 0.0
print(f"PUBLISH_GATE: nogil faster ({n:.4f} min vs {g:.4f} min, ~{ratio:.2f}x) — eligible for operator publish review.")
PY

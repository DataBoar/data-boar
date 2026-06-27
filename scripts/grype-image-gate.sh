#!/usr/bin/env bash
# Grype release-image gate (#1028 PR-B).
# Contract (mirror docker-scout-critical-gate.ps1 intent):
#   - Fail only on actionable High/Critical (--only-fixed).
#   - Load repo .grype.yaml for documented VEX (audit posture; does not weaken only-fixed).
# Compatible with operator build-push-podman.sh step 4 (same flags; optional --config).
#
# Usage (from repo root):
#   ./scripts/grype-image-gate.sh
#   ./scripts/grype-image-gate.sh fabioleitao/data_boar:1.7.4
#   ./scripts/grype-image-gate.sh podman:localhost/data_boar:hardening-test
#   ./scripts/grype-image-gate.sh -SaveLog docs/ops/evidence/grype-last.txt
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

IMAGE="fabioleitao/data_boar:latest"
SAVE_LOG=""
CONFIG="${GRYPE_CONFIG:-$REPO_ROOT/.grype.yaml}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      echo "Usage: $0 [IMAGE] [-SaveLog PATH]"
      echo "  IMAGE defaults to fabioleitao/data_boar:latest"
      echo "  Policy: grype --fail-on high --only-fixed [--config .grype.yaml]"
      exit 0
      ;;
    -SaveLog)
      SAVE_LOG="${2:-}"
      shift 2
      ;;
    -*)
      echo "grype-image-gate.sh: unknown option: $1" >&2
      exit 2
      ;;
    *)
      IMAGE="$1"
      shift
      ;;
  esac
done

if ! command -v grype >/dev/null 2>&1; then
  echo "grype-image-gate.sh: ABORTED: grype not on PATH." >&2
  exit 2
fi

echo "=== grype image gate (#1028) ==="
echo "Image:  $IMAGE"
echo "Policy: --fail-on high --only-fixed (actionable High/Critical only)"

ARGS=(grype "$IMAGE" --fail-on high --only-fixed)
if [[ -f "$CONFIG" ]]; then
  echo "Config: $CONFIG"
  ARGS+=(--config "$CONFIG")
else
  echo "Config: (none — $CONFIG missing)"
fi

if [[ -n "$SAVE_LOG" ]]; then
  mkdir -p "$(dirname "$SAVE_LOG")"
  echo "Log:    $SAVE_LOG"
  "${ARGS[@]}" | tee "$SAVE_LOG"
  exit "${PIPESTATUS[0]}"
fi

"${ARGS[@]}"

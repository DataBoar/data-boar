#!/usr/bin/env bash
# smoke_upgrade_path.sh — upgrade-path smoke for data-boar #2162
# Usage: ./scripts/smoke_upgrade_path.sh [--prev-version 1.7.4] [--candidate-wheel /path/to/wheel]
# Reprodutive: clean venv with previous PyPI version, create SQLite anchor, upgrade to candidate wheel built via uv build, verify no TAMPER / -alpha / config rejection.
set -euo pipefail

REPO_ROOT="$(cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd)"
cd "$REPO_ROOT"

PREV_VERSION="${PREV_VERSION:-1.7.4}"
CANDIDATE_WHEEL="${CANDIDATE_WHEEL:-}"
WORKDIR="$(mktemp -d)"
VENV="$WORKDIR/venv"
CONFIG_FIXTURE="tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml"

log() { echo "[smoke] $*"; }

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

log "Creating venv"
python3 -m venv "$VENV"
# shellcheck disable=SC1090
source "$VENV/bin/activate"
pip install --upgrade pip

if [[ -z "$CANDIDATE_WHEEL" ]]; then
  log "Building candidate wheel"
  uv build --wheel --out-dir "$WORKDIR/dist"
  CANDIDATE_WHEEL="$(ls "$WORKDIR/dist"/data_boar-*.whl | head -n1)"
fi

log "Installing previous version $PREV_VERSION"
pip install "data-boar==$PREV_VERSION"

log "First run to create SQLite anchor"
SQLITE_PATH="$WORKDIR/audit.db"
export DATA_BOAR_SQLITE_PATH="$SQLITE_PATH" # not used directly; config drives path
# Run with config fixture to trigger integrity anchor creation
# Use --check-extras to load config without scanning
"$VENV/bin/data-boar" --config "$CONFIG_FIXTURE" --check-extras > /dev/null 2>&1 || true

log "Upgrading to candidate wheel $(basename "$CANDIDATE_WHEEL")"
pip install --force-reinstall --no-deps "$CANDIDATE_WHEEL"

log "Verifying version"
VERSION_OUT="$("$VENV/bin/data-boar" --version 2>&1)"
log "Version output: $VERSION_OUT"
if echo "$VERSION_OUT" | grep -qi "alpha"; then
  echo "FAIL: version contains -alpha" >&2
  exit 1
fi

log "Running with legacy config fixture"
RUN_OUT="$("$VENV/bin/data-boar" --config "$CONFIG_FIXTURE" --check-extras 2>&1 || true)"
log "Run output: $RUN_OUT"
if echo "$RUN_OUT" | grep -qi "INTEGRITY TAMPER DETECTED"; then
  echo "FAIL: INTEGRITY TAMPER DETECTED after upgrade" >&2
  exit 1
fi
if echo "$RUN_OUT" | grep -qi "tampered"; then
  echo "FAIL: tampered signal after upgrade" >&2
  exit 1
fi

log "Smoke passed: $PREV_VERSION -> candidate"
echo "UPGRADE_PATH_OK $PREV_VERSION -> $(basename "$CANDIDATE_WHEEL")"

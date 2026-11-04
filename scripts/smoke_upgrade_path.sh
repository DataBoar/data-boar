#!/usr/bin/env bash
# smoke_upgrade_path.sh — upgrade-path smoke for data-boar #2162
# Usage: ./scripts/smoke_upgrade_path.sh [--prev-version 1.7.4] [--candidate-wheel /path/to/wheel]
# Reproducible: clean venv with previous PyPI version, create SQLite anchor, upgrade to candidate wheel built via uv build, verify no TAMPER / -alpha / config rejection.
set -euo pipefail

REPO_ROOT="$(cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd)"
CONFIG_FIXTURE="$REPO_ROOT/tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml"

# Parse command line arguments
PREV_VERSION="1.7.4"
CANDIDATE_WHEEL=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --prev-version)
      PREV_VERSION="$2"
      shift 2
      ;;
    --candidate-wheel)
      CANDIDATE_WHEEL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

WORKDIR="$(mktemp -d -p /tmp)"
VENV="$WORKDIR/venv"

# Isolate user data to avoid contaminating operator HOME and make run reproducible
export HOME="$WORKDIR/home"
export XDG_CONFIG_HOME="$WORKDIR/xdg_config"
export XDG_DATA_HOME="$WORKDIR/xdg_data"
export XDG_CACHE_HOME="$WORKDIR/xdg_cache"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME"

# Provide dummy values for legacy credential env vars used by the fixture
# The fixture uses DATABOAR_* unprefixed names (pre-1.8.0 style)
export DATABOAR_PG_PASSWORD=dummy
export MEU_BANCO_SENHA=dummy
export DATABOAR_MONGO_PASS=dummy
export DATABOAR_REDIS_PASS=dummy

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

# Install optional dependencies for mongodb, redis, and smb connectors
pip install pymongo redis pysmb

# Determine if previous version has integrity anchor feature
HAS_ANCHOR_FEATURE=0
if "$VENV/bin/python" -c "from core.integrity_anchor import ensure_integrity_anchor" 2>/dev/null; then
  HAS_ANCHOR_FEATURE=1
  log "Previous version $PREV_VERSION has integrity anchor feature"
else
  log "Previous version $PREV_VERSION does NOT have integrity anchor feature (expected for 1.7.4)"
fi

ANCHOR_DB="$WORKDIR/audit_legacy_upgrade.db"
cd "$WORKDIR"

if [[ $HAS_ANCHOR_FEATURE -eq 1 ]]; then
  log "First run to create SQLite anchor via previous version (main.py:1593 -> _run_startup_integrity_check)"
  # The real user command that creates the anchor is: data-boar --config <config>
  # This triggers _run_startup_integrity_check at main.py:1593
  # We run it with the original fixture config which has sqlite_path: audit_legacy_upgrade.db
  # Since we cd'd to WORKDIR, the relative path resolves to WORKDIR/audit_legacy_upgrade.db
  set +e
  "$VENV/bin/data-boar" --config "$CONFIG_FIXTURE" --plan > /dev/null 2>&1
  FIRST_EXIT=$?
  set -e
  # --plan exits early but anchor should still be created during startup
  # If command failed, we still check if anchor was created
  if [[ ! -f "$ANCHOR_DB" ]]; then
    # Anchor not created, try with --version which also triggers integrity check
    log "Anchor not created via --plan, trying --version"
    set +e
    "$VENV/bin/data-boar" --version > /dev/null 2>&1
    set -e
    # For --version, sqlite_path is hardcoded to audit_results.db
    # Copy it to expected location
    if [[ -f "$WORKDIR/audit_results.db" ]]; then
      cp "$WORKDIR/audit_results.db" "$ANCHOR_DB"
    fi
  fi
  
  if [[ ! -f "$ANCHOR_DB" ]]; then
    echo "FAIL: integrity anchor DB not created at $ANCHOR_DB" >&2
    exit 1
  fi
  log "Anchor created at $ANCHOR_DB"
else
  log "Skipping anchor creation (previous version lacks feature)"
  # Create empty anchor DB for upgrade test
  "$VENV/bin/python" -c "
import sqlite3
conn = sqlite3.connect('$ANCHOR_DB')
conn.execute('CREATE TABLE IF NOT EXISTS build_integrity_anchor (anchor_version INTEGER PRIMARY KEY, release_label TEXT NOT NULL, manifest_content_hash TEXT NOT NULL, file_hashes_json TEXT NOT NULL, validated_at TEXT NOT NULL, build_digest_matched INTEGER NOT NULL, validator_version TEXT NOT NULL, signed_release_label TEXT)')
conn.commit()
conn.close()
"
fi

log "Upgrading to candidate wheel $(basename "$CANDIDATE_WHEEL")"
# Install candidate WITH dependencies, as a user would
pip install --force-reinstall "$CANDIDATE_WHEEL"

# Reinstall optional dependencies
pip install pymongo redis pysmb

log "Verifying version"
VERSION_OUT="$("$VENV/bin/data-boar" --version 2>&1)"
log "Version output: $VERSION_OUT"

log "Running with legacy config fixture (--plan to verify acceptance)"
# Run with ORIGINAL fixture - all 4 targets. This tests legacy credential names (#2164)
# If candidate rejects it (exit code != 0), that's a regression
set +e
RUN_OUT="$("$VENV/bin/data-boar" --plan --config "$CONFIG_FIXTURE" 2>&1)"
RUN_EXIT=$?
set -e
log "Run output: $RUN_OUT"

if [[ $RUN_EXIT -ne 0 ]]; then
  echo "FAIL: validate-config exited with $RUN_EXIT (legacy config rejected - regression of #2164)" >&2
  exit 1
fi

# Check for TAMPER / -alpha issues
if echo "$VERSION_OUT" | grep -qi "alpha"; then
  echo "FAIL: version contains -alpha" >&2
  exit 1
fi
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

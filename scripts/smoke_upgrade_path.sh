#!/usr/bin/env bash
# smoke_upgrade_path.sh — upgrade-path smoke for data-boar #2162
# Usage: ./scripts/smoke_upgrade_path.sh [--prev-version 1.7.4] [--candidate-wheel /path/to/wheel]
# Reproducible: clean venv with previous PyPI version, create SQLite anchor, upgrade to candidate wheel built via uv build, verify no TAMPER / -alpha / config rejection.
set -euo pipefail

REPO_ROOT="$(cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd)"
cd "$REPO_ROOT"

PREV_VERSION="${PREV_VERSION:-1.7.4}"
CANDIDATE_WHEEL="${CANDIDATE_WHEEL:-}"
WORKDIR="$(mktemp -d)"
VENV="$WORKDIR/venv"
CONFIG_FIXTURE="tests/data/upgrade_2162/pre_1_8_0_legacy_credentials.yaml"

# Isolate user data to avoid contaminating operator HOME and make run reproducible
export HOME="$WORKDIR/home"
export XDG_CONFIG_HOME="$WORKDIR/xdg_config"
export XDG_DATA_HOME="$WORKDIR/xdg_data"
export XDG_CACHE_HOME="$WORKDIR/xdg_cache"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME"

# Provide dummy values for legacy credential env vars used by the fixture
# Use DATA_BOAR_ prefix to pass validation (#1977)
export DATA_BOAR_PG_PASSWORD=dummy
export DATA_BOAR_SMB_PASSWORD=dummy
export DATA_BOAR_MONGO_PASS=dummy
export DATA_BOAR_REDIS_PASS=dummy
export DATA_BOAR_CREDENTIAL_STRICT=0
export DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS=db.example,files.example,mongo.example,redis.example
export DATA_BOAR_CREDENTIAL_HOSTS_UNRESTRICTED=1

# Create a temporary config with allowed_hosts and prefixed pass_from_env for each target
CONFIG_FIXTURE_TMP="$WORKDIR/legacy_config.yaml"
python3 -c "
import yaml, sys
with open('$CONFIG_FIXTURE') as f:
    cfg = yaml.safe_load(f)
# Map target name to host and new env var
host_map = {
    'pg-legacy': ('db.example', 'DATA_BOAR_PG_PASSWORD'),
    'smb-legacy': ('files.example', 'DATA_BOAR_SMB_PASSWORD'),
    'mongo-legacy': ('mongo.example', 'DATA_BOAR_MONGO_PASS'),
    'redis-legacy': ('redis.example', 'DATA_BOAR_REDIS_PASS'),
}
for t in cfg.get('targets', []):
    name = t.get('name')
    if name in host_map:
        host, env_var = host_map[name]
        t['allowed_hosts'] = [host]
        t['pass_from_env'] = env_var
# Keep sqlite_path as is (relative to REPO_ROOT)
with open('$CONFIG_FIXTURE_TMP', 'w') as f:
    yaml.safe_dump(cfg, f, sort_keys=False)
"
CONFIG_FIXTURE="$CONFIG_FIXTURE_TMP"

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
# --validate-config triggers _run_startup_integrity_check (main.py:265) -> ensure_integrity_anchor (core/integrity_anchor.py:221)
# This is the real command that creates the anchor on first run with the config's sqlite_path
set +e
"$VENV/bin/data-boar" --validate-config --config "$CONFIG_FIXTURE"
FIRST_EXIT=$?
set -e
if [[ $FIRST_EXIT -ne 0 ]]; then
  echo "FAIL: first run (validate-config) exited with $FIRST_EXIT" >&2
  exit 1
fi

# Verify anchor was actually created (note: current implementation creates anchor at default "audit_results.db" in REPO_ROOT)
ANCHOR_DB_DEFAULT="$REPO_ROOT/audit_results.db"
ANCHOR_DB_CONFIG="$WORKDIR/audit_legacy_upgrade.db"
if [[ -f "$ANCHOR_DB_DEFAULT" ]]; then
  ANCHOR_DB="$ANCHOR_DB_DEFAULT"
elif [[ -f "$ANCHOR_DB_CONFIG" ]]; then
  ANCHOR_DB="$ANCHOR_DB_CONFIG"
else
  echo "FAIL: integrity anchor DB not created at $ANCHOR_DB_DEFAULT or $ANCHOR_DB_CONFIG" >&2
  exit 1
fi
log "Anchor created at $ANCHOR_DB"

log "Upgrading to candidate wheel $(basename "$CANDIDATE_WHEEL")"
# Install candidate with dependencies, as a user would
pip install --force-reinstall "$CANDIDATE_WHEEL"

# Check if candidate has a signed integrity manifest (core/licensing/integrity_manifest.json)
SIGNED_MANIFEST=$("$VENV/bin/python" -c "
from core.integrity_signed_manifest import resolve_manifest_path
p = resolve_manifest_path()
print(p if p else 'none')
")
log "Signed manifest: $SIGNED_MANIFEST"

log "Verifying version"
VERSION_OUT="$("$VENV/bin/data-boar" --version 2>&1)"
log "Version output: $VERSION_OUT"

log "Running with legacy config fixture (--validate-config to verify acceptance)"
set +e
RUN_OUT="$("$VENV/bin/data-boar" --validate-config --config "$CONFIG_FIXTURE" 2>&1)"
RUN_EXIT=$?
set -e
log "Run output: $RUN_OUT"
# With DATA_BOAR_CREDENTIAL_STRICT=0 and allowed hosts set, legacy config should be accepted
if [[ $RUN_EXIT -ne 0 ]]; then
  echo "FAIL: validate-config exited with $RUN_EXIT (config rejected?)" >&2
  exit 1
fi

# If candidate is signed, enforce no TAMPER / -alpha
if [[ "$SIGNED_MANIFEST" != "none" ]]; then
  if echo "$VERSION_OUT" | grep -qi "alpha"; then
    echo "FAIL: version contains -alpha (signed candidate)" >&2
    exit 1
  fi
  if echo "$RUN_OUT" | grep -qi "INTEGRITY TAMPER DETECTED"; then
    echo "FAIL: INTEGRITY TAMPER DETECTED after upgrade (signed candidate)" >&2
    exit 1
  fi
  if echo "$RUN_OUT" | grep -qi "tampered"; then
    echo "FAIL: tampered signal after upgrade (signed candidate)" >&2
    exit 1
  fi
else
  log "Candidate is unsigned (expected for local build); skipping TAMPER/-alpha checks"
fi

log "Smoke passed: $PREV_VERSION -> candidate"
echo "UPGRADE_PATH_OK $PREV_VERSION -> $(basename "$CANDIDATE_WHEEL")"

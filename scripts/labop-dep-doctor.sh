#!/usr/bin/env bash
# scripts/labop-dep-doctor.sh
# LAB-OP Dependency Doctor -- detects missing optional Python C extensions and attempts OS-level fix.
# Run via narrow sudoers (LABOP_DEP_DOCTOR) from Maestro/completao.
# Scope: additive only -- never removes packages, never upgrades OS.
# Logs every attempt to stdout (captured by Maestro Collect).
#
# Usage: sudo -n bash /path/to/labop-dep-doctor.sh [--check]
#   --check   Probe only, no install (exit 0 if healthy, 1 if fix needed).
#
# Exit codes:
#   0 -- healthy or successfully healed
#   1 -- unhealthy and could not heal
#   2 -- invocation error

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"
if [[ -d "${HOME}/.local/bin" ]]; then export PATH="${HOME}/.local/bin:${PATH}"; fi

CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --help|-h) echo "Usage: $0 [--check]"; exit 0 ;;
    *) echo "[DepDoctor] Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

_log() { echo "[DepDoctor $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[DepDoctor] OK: $*"; }
_warn(){ echo "[DepDoctor] WARN: $*" >&2; }
_fail(){ echo "[DepDoctor] FAIL: $*" >&2; }

HOST=$(hostname -f 2>/dev/null || hostname)
_log "Starting on $HOST (check_only=$CHECK_ONLY)"

# ---------------------------------------------------------------------------
# Phase 1: detect uv + repo root
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
_log "Repo root: $REPO_ROOT"

UV_BIN=""
for candidate in "${HOME}/.local/bin/uv" "/usr/local/bin/uv" "$(command -v uv 2>/dev/null)"; do
  if [[ -x "$candidate" ]]; then UV_BIN="$candidate"; break; fi
done
if [[ -z "$UV_BIN" ]]; then
  _fail "uv not found -- cannot run dependency checks"
  exit 1
fi
_log "uv: $UV_BIN ($("$UV_BIN" --version 2>/dev/null | head -1))"

# ---------------------------------------------------------------------------
# Phase 2: probe for known optional modules
# ---------------------------------------------------------------------------
probe_module() {
  local mod="$1"
  "$UV_BIN" run --project "$REPO_ROOT" python3 -c "import $mod" >/dev/null 2>&1
  return $?
}

probe_lzma() {
  "$UV_BIN" run --project "$REPO_ROOT" python3 -c "import lzma" >/dev/null 2>&1
  return $?
}

NEED_FIX=0
declare -A MISSING

if ! probe_module "py7zr"; then
  _warn "py7zr not importable"
  MISSING["py7zr"]=1
  NEED_FIX=1
fi

if ! probe_lzma; then
  _warn "lzma C extension missing (Python built without liblzma-dev)"
  MISSING["lzma"]=1
  NEED_FIX=1
fi

if [[ $NEED_FIX -eq 0 ]]; then
  _ok "All optional modules healthy. Nothing to do."
  exit 0
fi

if [[ $CHECK_ONLY -eq 1 ]]; then
  _warn "Check-only mode: fixes needed but not applied."
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 3: try uv sync --extra compressed first
# ---------------------------------------------------------------------------
_log "Step 1: uv sync --extra compressed"
if (cd "$REPO_ROOT" && "$UV_BIN" sync --extra compressed 2>&1); then
  _log "uv sync succeeded. Re-probing py7zr..."
  if probe_module "py7zr"; then
    _ok "py7zr now importable after uv sync."
    MISSING["py7zr"]=0
    NEED_FIX=0
  else
    _warn "py7zr still not importable after uv sync -- likely _lzma C extension missing."
  fi
else
  _warn "uv sync --extra compressed failed or partial."
fi

if [[ $NEED_FIX -eq 0 ]]; then exit 0; fi

# ---------------------------------------------------------------------------
# Phase 4: OS-level package manager for liblzma
# ---------------------------------------------------------------------------
_log "Step 2: detecting OS package manager for lzma-dev install"

PM=""
PM_CMD=""
if command -v apt-get >/dev/null 2>&1; then
  PM="apt"; PM_CMD="apt-get install -y liblzma-dev"
elif command -v xbps-install >/dev/null 2>&1; then
  PM="xbps"; PM_CMD="xbps-install -y xz-devel"
elif command -v pacman >/dev/null 2>&1; then
  PM="pacman"; PM_CMD="pacman -S --noconfirm xz"
elif command -v dnf >/dev/null 2>&1; then
  PM="dnf"; PM_CMD="dnf install -y xz-devel"
elif command -v zypper >/dev/null 2>&1; then
  PM="zypper"; PM_CMD="zypper install -y xz-devel"
elif command -v apk >/dev/null 2>&1; then
  PM="apk"; PM_CMD="apk add xz-dev"
else
  _fail "No recognized package manager found (apt/xbps/pacman/dnf/zypper/apk). Cannot install liblzma."
  _warn "Host feature: 7z_UNSUPPORTED reason=no_known_pm"
  exit 1
fi

_log "PM detected: $PM. Running: $PM_CMD"
if eval "$PM_CMD" 2>&1; then
  _ok "OS package installed via $PM."
else
  _fail "OS package install failed via $PM (exit $?)."
  _warn "Host feature: 7z_UNSUPPORTED reason=pm_install_failed pm=$PM"
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 5: reinstall Python via uv so it picks up the new lzma header
# ---------------------------------------------------------------------------
_log "Step 3: reinstalling Python via uv to pick up liblzma"
PY_VER=$("$UV_BIN" run --project "$REPO_ROOT" python3 --version 2>/dev/null | awk '{print $2}')
_log "Current Python: $PY_VER"
if [[ -n "$PY_VER" ]]; then
  if "$UV_BIN" python install "$PY_VER" --reinstall 2>&1; then
    _ok "Python $PY_VER reinstalled via uv."
  else
    _warn "uv python install --reinstall failed. Trying without version pin..."
    "$UV_BIN" python install --reinstall 2>&1 || _warn "Reinstall also failed."
  fi
fi

# ---------------------------------------------------------------------------
# Phase 6: re-sync and final probe
# ---------------------------------------------------------------------------
_log "Step 4: uv sync --extra compressed (post-install)"
(cd "$REPO_ROOT" && "$UV_BIN" sync --extra compressed 2>&1) || _warn "Post-install sync failed."

_log "Final probe..."
if probe_lzma && probe_module "py7zr"; then
  _ok "All optional modules healthy after full remediation."
  exit 0
else
  _fail "Modules still unavailable after all remediation steps."
  _warn "Host feature: 7z_UNSUPPORTED reason=lzma_unavailable_after_all_steps"
  exit 1
fi

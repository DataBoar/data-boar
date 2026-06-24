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
# This script's intended invocation is sudo -n, where $HOME is /root and the operator's
# uv (~/.local/bin) is invisible. Resolve the operator home via getent (same pattern as
# labop-nfs/smb-ensure), preferring SUDO_USER then the current user (#935).
_DD_OPERATOR="${SUDO_USER:-$(id -un 2>/dev/null || echo "${USER:-}")}"
_DD_OP_HOME="$(getent passwd "$_DD_OPERATOR" 2>/dev/null | cut -d: -f6)"
if [[ -z "$_DD_OP_HOME" ]]; then _DD_OP_HOME="${HOME:-/root}"; fi
if [[ -d "${_DD_OP_HOME}/.local/bin" ]]; then export PATH="${_DD_OP_HOME}/.local/bin:${PATH}"; fi

CHECK_ONLY=0
PRIVILEGED=0
APPLY_ONLY=0
PERSONAS_RAW=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)      CHECK_ONLY=1; shift ;;
    --privileged) PRIVILEGED=1; shift ;;
    --apply)      APPLY_ONLY=1; shift ;;  # uv sync only, no OS PM (no root needed)
    --personas=*) PERSONAS_RAW="${1#--personas=}"; shift ;;
    --personas)   PERSONAS_RAW="${2:-}"; shift 2 ;;
    --help|-h) echo "Usage: $0 [--check | --apply | --privileged] [--personas p1,p2,...]
  (no args)     same as --check: probe only, no changes
  --check       probe only, exit 0 if healthy, 1 if fix needed
  --apply       uv sync --extra compressed only (no OS package manager)
  --privileged  full flow: uv sync + OS PM (apt/xbps/...) + Python rebuild
                requires root (sudo -n); the intended LABOP_DEP_DOCTOR invocation
  --personas    Maestro persona list (#958): apk/apt packages for nfs/cifs/io bins
"; exit 0 ;;
    *) echo "[DepDoctor] Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Default: no args = check only (safe accidental invocation)
if [[ $PRIVILEGED -eq 0 && $APPLY_ONLY -eq 0 ]]; then
  CHECK_ONLY=1
fi

_log() { echo "[DepDoctor $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[DepDoctor] OK: $*"; }
_warn(){ echo "[DepDoctor] WARN: $*" >&2; }
_fail(){ echo "[DepDoctor] FAIL: $*" >&2; }

_detect_pm() {
  if command -v apt-get >/dev/null 2>&1; then echo "apt"; return 0; fi
  if command -v xbps-install >/dev/null 2>&1; then echo "xbps"; return 0; fi
  if command -v pacman >/dev/null 2>&1; then echo "pacman"; return 0; fi
  if command -v dnf >/dev/null 2>&1; then echo "dnf"; return 0; fi
  if command -v zypper >/dev/null 2>&1; then echo "zypper"; return 0; fi
  if command -v apk >/dev/null 2>&1; then echo "apk"; return 0; fi
  echo ""
}

_pkg_logical_to_pm() {
  local logical="$1" pm="$2"
  case "$logical" in
    procps)
      case "$pm" in
        xbps) echo "procps-ng" ;;
        apk) echo "procps" ;;
        *) echo "procps" ;;
      esac
      ;;
    iproute2) echo "iproute2" ;;
    samba) echo "samba" ;;
    nfs-utils)
      case "$pm" in
        apt) echo "nfs-kernel-server" ;;
        apk) echo "nfs-utils" ;;
        *) echo "nfs-utils" ;;
      esac
      ;;
    *) echo "$logical" ;;
  esac
}

_pkg_installed() {
  local pkg="$1" pm="$2"
  case "$pm" in
    apt) dpkg -s "$pkg" >/dev/null 2>&1 ;;
    apk) apk info -e "$pkg" >/dev/null 2>&1 ;;
    xbps) xbps-query "$pkg" >/dev/null 2>&1 ;;
    pacman) pacman -Q "$pkg" >/dev/null 2>&1 ;;
    dnf) rpm -q "$pkg" >/dev/null 2>&1 ;;
    zypper) rpm -q "$pkg" >/dev/null 2>&1 ;;
    *) return 1 ;;
  esac
}

_pm_install_cmd() {
  local pkg="$1" pm="$2"
  case "$pm" in
    apt) echo "apt-get install -y $pkg" ;;
    apk) echo "apk add $pkg" ;;
    xbps) echo "xbps-install -y $pkg" ;;
    pacman) echo "pacman -S --noconfirm $pkg" ;;
    dnf) echo "dnf install -y $pkg" ;;
    zypper) echo "zypper install -y $pkg" ;;
    *) return 1 ;;
  esac
}

_persona_logical_pkgs() {
  local persona="${1// /}"
  case "$persona" in
    target_nfs) echo "nfs-utils procps iproute2" ;;
    target_cifs) echo "samba procps iproute2" ;;
    baremetal|web) echo "procps iproute2" ;;
    *) echo "" ;;
  esac
}

_load_personas_from_gate_context() {
  if [[ -n "$PERSONAS_RAW" ]]; then
    return 0
  fi
  local gate_file
  gate_file="$(cd "$(dirname "$0")/.." && pwd)/.labop-gate/PERSONAS"
  if [[ -f "$gate_file" ]]; then
    PERSONAS_RAW="$(tr -d '\n\r' <"$gate_file")"
  fi
}

_run_persona_os_phase() {
  [[ -z "$PERSONAS_RAW" ]] && return 0
  local pm pkgs logical pkg failed=0
  pm="$(_detect_pm)"
  if [[ -z "$pm" ]]; then
    _warn "Persona OS phase: no package manager (ALARM)"
    return 1
  fi
  declare -A WANT=()
  local p blob
  IFS=',' read -ra _PL <<<"$PERSONAS_RAW"
  for p in "${_PL[@]}"; do
    blob="$(_persona_logical_pkgs "$p")"
    for logical in $blob; do
      WANT["$logical"]=1
    done
  done
  for logical in "${!WANT[@]}"; do
    pkg="$(_pkg_logical_to_pm "$logical" "$pm")"
    if _pkg_installed "$pkg" "$pm"; then
      _ok "persona pkg $pkg ($logical) installed"
    else
      _warn "persona pkg $pkg ($logical) missing"
      failed=1
      if [[ $CHECK_ONLY -eq 0 && $PRIVILEGED -eq 1 ]]; then
        local cmd
        cmd="$(_pm_install_cmd "$pkg" "$pm")"
        _log "Installing: $cmd"
        if ! eval "$cmd" 2>&1; then
          _fail "install failed for $pkg via $pm"
        fi
      fi
    fi
  done
  # Re-verify ALL wanted packages; success on one install must not mask another failure (#1020).
  for logical in "${!WANT[@]}"; do
    pkg="$(_pkg_logical_to_pm "$logical" "$pm")"
    if ! _pkg_installed "$pkg" "$pm"; then
      failed=1
      _warn "persona pkg $pkg ($logical) still missing after phase"
    fi
  done
  if [[ $failed -ne 0 ]]; then
    return 1
  fi
  return 0
}

HOST=$(hostname -f 2>/dev/null || hostname)
_load_personas_from_gate_context
_log "Starting on $HOST (check_only=$CHECK_ONLY privileged=$PRIVILEGED apply_only=$APPLY_ONLY personas=${PERSONAS_RAW:-<none>})"

# ---------------------------------------------------------------------------
# Phase 0: persona OS packages (#958) before Python probes
# ---------------------------------------------------------------------------
PERSONA_OS_OK=1
if [[ -n "$PERSONAS_RAW" ]]; then
  if ! _run_persona_os_phase; then
    PERSONA_OS_OK=0
    if [[ $CHECK_ONLY -eq 1 ]]; then
      _warn "Persona OS packages missing (check-only)."
      exit 1
    fi
    if [[ $PRIVILEGED -eq 0 ]]; then
      _warn "Persona OS packages missing; re-run with --privileged"
      exit 1
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Phase 1: detect uv + repo root
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
_log "Repo root: $REPO_ROOT"

UV_BIN=""
for candidate in "${_DD_OP_HOME}/.local/bin/uv" "/usr/local/bin/uv" "$(command -v uv 2>/dev/null)"; do
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
  if [[ -n "$PERSONAS_RAW" && $PERSONA_OS_OK -eq 0 ]]; then
    _fail "Persona OS packages still missing (privileged remediation incomplete)."
    exit 1
  fi
  _ok "All optional modules healthy. Nothing to do."
  exit 0
fi

if [[ $CHECK_ONLY -eq 1 ]]; then
  _warn "Check-only mode: fixes needed but not applied."
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 3: try uv sync --extra compressed (safe, no root needed)
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
# Phase 4: OS-level package manager for liblzma (requires --privileged / root)
# ---------------------------------------------------------------------------
if [[ $PRIVILEGED -eq 0 ]]; then
  _warn "OS-level package manager step skipped: --privileged not set."
  _warn "Re-run as: sudo -n bash $0 --privileged"
  _warn "Host feature: 7z_UNSUPPORTED reason=lzma_unavailable_uvsync_only"
  exit 1
fi
_log "Step 2: detecting OS package manager for lzma-dev install"

PM="$(_detect_pm)"
case "$PM" in
  apt) PM_CMD="apt-get install -y liblzma-dev" ;;
  xbps) PM_CMD="xbps-install -y xz-devel" ;;
  pacman) PM_CMD="pacman -S --noconfirm xz" ;;
  dnf) PM_CMD="dnf install -y xz-devel" ;;
  zypper) PM_CMD="zypper install -y xz-devel" ;;
  apk) PM_CMD="apk add xz-dev" ;;
  *)
    _fail "No recognized package manager found (apt/xbps/pacman/dnf/zypper/apk). Cannot install liblzma."
    _warn "Host feature: 7z_UNSUPPORTED reason=no_known_pm"
    exit 1
    ;;
esac

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
  if [[ -n "$PERSONAS_RAW" && $PERSONA_OS_OK -eq 0 ]]; then
    _fail "Persona OS packages still missing after full remediation."
    exit 1
  fi
  _ok "All optional modules healthy after full remediation."
  exit 0
else
  _fail "Modules still unavailable after all remediation steps."
  _warn "Host feature: 7z_UNSUPPORTED reason=lzma_unavailable_after_all_steps"
  exit 1
fi

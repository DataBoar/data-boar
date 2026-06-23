#!/usr/bin/env bash
# scripts/labop-gate-readiness.sh
# Per-node Maestro pre-flight readiness (#960): ALARM (--check) / REMEDIATE (--apply).
# Parses: lines "GR check=<name> status=<OK|ALARM|REMEDIATE> ..."
#
# Usage:
#   bash labop-gate-readiness.sh --check --personas baremetal,target_nfs,web
#   bash labop-gate-readiness.sh --apply --personas baremetal,target_nfs
# Env: LAB_OP_SUBNET (from inventory via Maestro)

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

APPLY=0
PERSONAS_RAW=""
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --check) APPLY=0 ;;
    --personas=*) PERSONAS_RAW="${arg#--personas=}" ;;
    --personas) ;;
    --help|-h)
      echo "Usage: $0 [--check | --apply] --personas p1,p2,..."
      exit 0
      ;;
    *)
      if [[ "${PREV_ARG:-}" == "--personas" ]]; then
        PERSONAS_RAW="$arg"
      else
        echo "[GateReadiness] Unknown arg: $arg" >&2
        exit 2
      fi
      ;;
  esac
  PREV_ARG="$arg"
done

if [[ -z "$PERSONAS_RAW" ]]; then
  echo "[GateReadiness] FAIL: --personas required" >&2
  exit 2
fi

HOST=$(hostname -s 2>/dev/null || hostname)
OPERATOR="${SUDO_USER:-$(id -un 2>/dev/null || echo "${USER:-}")}"
OP_HOME="$(getent passwd "$OPERATOR" 2>/dev/null | cut -d: -f6)"
[[ -z "$OP_HOME" ]] && OP_HOME="${HOME:-/root}"

_gr() {
  local check="$1" status="$2" detail="${3:-}"
  echo "GR host=$HOST check=$check status=$status${detail:+ detail=$detail}"
}

FAIL=0
MODE_WORD=$([[ $APPLY -eq 1 ]] && echo apply || echo check)

_log() { echo "[GateReadiness $(date -u +%H:%M:%SZ)] $*" >&2; }
_log "mode=$MODE_WORD personas=$PERSONAS_RAW repo=$REPO_ROOT"

_ensure_login_path() {
  if [[ -d "${OP_HOME}/.local/bin" ]]; then
    export PATH="${OP_HOME}/.local/bin:${PATH}"
  fi
  if ! command -v cargo >/dev/null 2>&1 && [[ -f "${OP_HOME}/.cargo/env" ]]; then
    # shellcheck source=/dev/null
    . "${OP_HOME}/.cargo/env"
  fi
}

_ensure_login_path

_persona_needs() {
  local persona="$1" need="$2"
  local p
  IFS=',' read -ra _PL <<<"$PERSONAS_RAW"
  for p in "${_PL[@]}"; do
    p="${p// /}"
    [[ "$p" == "$persona" ]] && return 0
  done
  return 1
}

_any_persona() {
  local want="$1"
  local p
  IFS=',' read -ra _PL <<<"$PERSONAS_RAW"
  for p in "${_PL[@]}"; do
    p="${p// /}"
    case "$p" in
      target_nfs|target_cifs|baremetal|docker|podman|dockerswarm|web)
        case "$want" in
          io) [[ "$p" == "target_nfs" || "$p" == "target_cifs" || "$p" == "baremetal" ]] && return 0 ;;
          nfs) [[ "$p" == "target_nfs" ]] && return 0 ;;
          cifs) [[ "$p" == "target_cifs" ]] && return 0 ;;
          baremetal) [[ "$p" == "baremetal" ]] && return 0 ;;
        esac
        ;;
    esac
  done
  return 1
}

# --- Privilege probe (#954 / #959) ---
PRIV="NO_PRIV"
if command -v doas >/dev/null 2>&1 && doas -n true 2>/dev/null; then
  PRIV="doas-narrow"
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  PRIV="sudo-narrow"
fi
if [[ "$PRIV" == "NO_PRIV" ]]; then
  _gr privilege ALARM "no doas/sudo -n"
  FAIL=1
else
  _gr privilege OK "$PRIV"
fi

# --- Per-persona binaries ---
if _any_persona io; then
  for bin in tmux vmstat ss; do
    if command -v "$bin" >/dev/null 2>&1; then
      _gr "bin:$bin" OK "present"
    else
      _gr "bin:$bin" ALARM "missing"
      FAIL=1
    fi
  done
fi

if _any_persona nfs; then
  if command -v exportfs >/dev/null 2>&1 || command -v showmount >/dev/null 2>&1; then
    _gr bin:nfs-utils OK "exportfs_or_showmount"
  else
    _gr bin:nfs-utils ALARM "missing"
    FAIL=1
  fi
fi

if _any_persona cifs; then
  if command -v smbd >/dev/null 2>&1 || pgrep -x smbd >/dev/null 2>&1; then
    _gr bin:smbd OK "present"
  else
    _gr bin:smbd ALARM "missing"
    FAIL=1
  fi
fi

if _any_persona baremetal; then
  for bin in uv cargo maturin; do
    if command -v "$bin" >/dev/null 2>&1; then
      _gr "login-env:$bin" OK "on_path"
    else
      _gr "login-env:$bin" ALARM "missing_from_path"
      FAIL=1
    fi
  done
  UV_BIN="$(command -v uv 2>/dev/null || true)"
  if [[ -n "$UV_BIN" ]]; then
    if "$UV_BIN" run --project "$REPO_ROOT" python3 -c "import boar_fast_filter" >/dev/null 2>&1; then
      _gr rust-wheel OK "boar_fast_filter_importable"
    else
      _gr rust-wheel ALARM "boar_fast_filter_missing_in_venv"
      FAIL=1
    fi
  fi
fi

# --- fail2ban / sshguard (#957) ---
FW_SCRIPT="$SCRIPT_DIR/labop-fw-guard-ensure.sh"
if [[ -f "$FW_SCRIPT" ]]; then
  FW_MODE=$([[ $APPLY -eq 1 ]] && echo --apply || echo --check)
  if [[ -z "${LAB_OP_SUBNET:-}" ]]; then
    _gr fail2ban ALARM "LAB_OP_SUBNET_unset"
    FAIL=1
  elif [[ "$PRIV" != "NO_PRIV" ]]; then
    PRIV_CMD="sudo -n"
    command -v doas >/dev/null 2>&1 && doas -n true 2>/dev/null && PRIV_CMD="doas -n"
    if $PRIV_CMD env LAB_OP_SUBNET="$LAB_OP_SUBNET" bash "$FW_SCRIPT" $FW_MODE; then
      _gr fail2ban OK "subnet_whitelisted"
    elif [[ $APPLY -eq 1 ]]; then
      _gr fail2ban ALARM "remediation_failed"
      FAIL=1
    else
      _gr fail2ban ALARM "subnet_not_whitelisted"
      FAIL=1
    fi
  else
    _gr fail2ban ALARM "no_priv_for_check"
    FAIL=1
  fi
fi

# --- dep-doctor persona packages (#958) ---
DEP_SCRIPT="$SCRIPT_DIR/labop-dep-doctor.sh"
if [[ -f "$DEP_SCRIPT" ]] && { [[ $APPLY -eq 1 ]] || [[ $FAIL -eq 1 ]]; }; then
  if [[ "$PRIV" != "NO_PRIV" ]]; then
    PRIV_CMD="sudo -n"
    command -v doas >/dev/null 2>&1 && doas -n true 2>/dev/null && PRIV_CMD="doas -n"
    DEP_ARGS=(--personas "$PERSONAS_RAW")
    if [[ $APPLY -eq 1 ]]; then
      DEP_ARGS=(--privileged "${DEP_ARGS[@]}")
    else
      DEP_ARGS=(--check "${DEP_ARGS[@]}")
    fi
    if $PRIV_CMD bash "$DEP_SCRIPT" "${DEP_ARGS[@]}"; then
      _gr dep-doctor OK "persona_packages"
    elif [[ $APPLY -eq 1 ]]; then
      _gr dep-doctor ALARM "remediation_failed"
      FAIL=1
    else
      _gr dep-doctor ALARM "packages_or_modules_missing"
      FAIL=1
    fi
  fi
fi

if [[ $FAIL -eq 0 ]]; then
  _gr summary OK "mode=$MODE_WORD"
  exit 0
fi
_gr summary ALARM "mode=$MODE_WORD"
exit 1

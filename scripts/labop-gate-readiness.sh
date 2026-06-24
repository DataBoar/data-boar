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

# Narrow sudoers/doas grants match a literal bash path (#1021 ROUND 5/6).
# Prefer /usr/bin/bash and /bin/bash (grant-canonical) before command -v bash,
# which may resolve to /usr/sbin/bash via secure_path and miss the grant (#1021 R6 RCA).
_resolve_bash_bin() {
  local candidate resolved
  for candidate in /usr/bin/bash /bin/bash; do
    if [[ -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  candidate="$(command -v bash 2>/dev/null || true)"
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    resolved="$(readlink -f "$candidate" 2>/dev/null || printf '%s' "$candidate")"
    case "$resolved" in
      /usr/bin/bash|/bin/bash)
        printf '%s' "$resolved"
        return 0
        ;;
    esac
    printf '%s' "$candidate"
    return 0
  fi
  return 1
}

LABOP_BASH_BIN=""
if ! LABOP_BASH_BIN="$(_resolve_bash_bin)"; then
  _gr privilege ALARM "bash_bin_unresolved"
  FAIL=1
else
  _gr bootstrap OK "bash_bin=$LABOP_BASH_BIN"
fi
_log "mode=$MODE_WORD personas=$PERSONAS_RAW repo=$REPO_ROOT bash=$LABOP_BASH_BIN"

GATE_CTX_DIR="$REPO_ROOT/.labop-gate"

# shellcheck source=labop-rfc1918-cidr-lib.sh
. "$SCRIPT_DIR/labop-rfc1918-cidr-lib.sh"

_is_rfc1918_lab_subnet() {
  labop_is_rfc1918_cidr "$1"
}

_write_gate_context() {
  mkdir -p "$GATE_CTX_DIR"
  if [[ -n "${LAB_OP_SUBNET:-}" ]]; then
    if ! _is_rfc1918_lab_subnet "$LAB_OP_SUBNET"; then
      echo "[GateReadiness] FAIL: LAB_OP_SUBNET '$LAB_OP_SUBNET' is not a private RFC1918 CIDR - refusing (zero-trust)" >&2
      return 1
    fi
    printf '%s\n' "$LAB_OP_SUBNET" >"$GATE_CTX_DIR/LAB_OP_SUBNET"
  fi
  printf '%s\n' "$PERSONAS_RAW" >"$GATE_CTX_DIR/PERSONAS"
  return 0
}

_priv_cmd() {
  if [[ "$PRIV" == "doas-narrow" ]]; then
    echo "doas -n"
  elif [[ "$PRIV" == "sudo-narrow" ]]; then
    echo "sudo -n"
  else
    echo ""
  fi
}

_priv_denied_output() {
  local out="$1"
  grep -qiE 'not allowed|a password is required|authentication required|doas \(.*\) failed|sorry, user|authentication failures' <<<"$out"
}

_invoke_priv_script() {
  local script="$1"
  shift
  local priv out ec=0
  priv="$(_priv_cmd)"
  [[ -z "$priv" ]] && return 127
  if [[ -z "$LABOP_BASH_BIN" ]]; then
    return 127
  fi
  if ! _write_gate_context; then
    return 125
  fi
  out="$($priv "$LABOP_BASH_BIN" "$script" "$@" 2>&1)" || ec=$?
  printf '%s\n' "$out" >&2
  if [[ $ec -ne 0 ]] && _priv_denied_output "$out"; then
    return 126
  fi
  return $ec
}

_has_persona() {
  local want="$1" p
  IFS=',' read -ra _PL <<<"$PERSONAS_RAW"
  for p in "${_PL[@]}"; do
    p="${p// /}"
    [[ "$p" == "$want" ]] && return 0
  done
  return 1
}

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

_FW_GUARD_SCRIPT="$SCRIPT_DIR/labop-fw-guard-ensure.sh"
_FW_GUARD_PROBE_DONE=0
_FW_GUARD_PROBE_EC=0
_FW_GUARD_PROBE_OUT=""
_PRIV_DETAIL=""

_sudo_l_has_labop_grant() {
  local listing
  listing="$(sudo -n -l 2>/dev/null)" || return 1
  grep -qE 'LABOP_(FW_GUARD|DEP_DOCTOR|NFS_SERVER|SMB_SERVER)|labop-(fw-guard|dep-doctor|nfs-server|smb-server)-ensure\.sh' <<<"$listing"
}

_doas_c_has_labop_grant() {
  local conf
  for conf in /etc/doas.conf /etc/doas.d/*.conf; do
    [[ -f "$conf" ]] || continue
    if doas -C "$conf" "${LABOP_BASH_BIN:-/bin/bash}" "$_FW_GUARD_SCRIPT" --check 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

_probe_fw_guard_priv() {
  local priv="$1"
  local out ec=0
  if [[ ! -f "$_FW_GUARD_SCRIPT" ]]; then
    return 1
  fi
  if ! _write_gate_context; then
    return 1
  fi
  out="$($priv "${LABOP_BASH_BIN:-/bin/bash}" "$_FW_GUARD_SCRIPT" --check 2>&1)" || ec=$?
  _FW_GUARD_PROBE_OUT="$out"
  _FW_GUARD_PROBE_EC=$ec
  _FW_GUARD_PROBE_DONE=1
  if [[ $ec -eq 126 ]] || _priv_denied_output "$out"; then
    return 1
  fi
  return 0
}

_detect_sudo_narrow() {
  if ! command -v sudo >/dev/null 2>&1; then
    return 1
  fi
  if sudo -n true 2>/dev/null; then
    _PRIV_DETAIL="blanket"
    return 0
  fi
  if _sudo_l_has_labop_grant; then
    _PRIV_DETAIL="sudo_l"
    return 0
  fi
  if _probe_fw_guard_priv "sudo -n"; then
    _PRIV_DETAIL="probe_fw_guard"
    return 0
  fi
  return 1
}

_detect_doas_narrow() {
  if ! command -v doas >/dev/null 2>&1; then
    return 1
  fi
  if doas -n true 2>/dev/null; then
    _PRIV_DETAIL="blanket"
    return 0
  fi
  if [[ -f "$_FW_GUARD_SCRIPT" ]] && _doas_c_has_labop_grant; then
    _PRIV_DETAIL="doas_c"
    return 0
  fi
  if _probe_fw_guard_priv "doas -n"; then
    _PRIV_DETAIL="probe_fw_guard"
    return 0
  fi
  return 1
}

# --- Privilege probe (#954 / #959 / #1022: narrow grant != sudo -n true) ---
PRIV="NO_PRIV"
if [[ -n "$LABOP_BASH_BIN" ]]; then
  if _detect_doas_narrow; then
    PRIV="doas-narrow"
  elif _detect_sudo_narrow; then
    PRIV="sudo-narrow"
  fi
  if [[ "$PRIV" == "NO_PRIV" ]]; then
    _gr privilege ALARM "no_narrow_grant"
    FAIL=1
  else
    _gr privilege OK "$PRIV" "${_PRIV_DETAIL:-}"
  fi
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

# --- baremetal Rust accelerator (#1021 R7): optional FFI; pure-Python fallback is OK ---
_rust_toolchain_runnable() {
  local uv_bin mat_ok=0
  if command -v maturin >/dev/null 2>&1; then
    mat_ok=1
  else
    uv_bin="$(command -v uv 2>/dev/null || true)"
    if [[ -n "$uv_bin" ]] && "$uv_bin" run maturin --version >/dev/null 2>&1; then
      mat_ok=1
    fi
  fi
  [[ $mat_ok -eq 1 ]] && command -v rustc >/dev/null 2>&1
}

_boar_fast_filter_importable() {
  local uv_bin="$1"
  [[ -n "$uv_bin" ]] && "$uv_bin" run --project "$REPO_ROOT" python3 -c "import boar_fast_filter" >/dev/null 2>&1
}

_emit_rust_accel_hints() {
  local reason="${1:-optional_degraded}"
  echo "[GateReadiness] WARN: HINT: boar_fast_filter (Rust) is optional; scanner uses pure-Python fallback" >&2
  echo "[GateReadiness] WARN: HINT: install rustc + maturin, then: uv run maturin develop --release (repo root)" >&2
  echo "[GateReadiness] WARN: Host feature: RUST_ACCEL_UNSUPPORTED reason=$reason" >&2
}

if _any_persona baremetal; then
  UV_BIN="$(command -v uv 2>/dev/null || true)"
  if [[ -z "$UV_BIN" ]]; then
    _gr "login-env:uv" ALARM "missing_from_path"
    FAIL=1
  else
    _gr "login-env:uv" OK "on_path"
  fi
  for bin in cargo maturin; do
    if command -v "$bin" >/dev/null 2>&1; then
      _gr "login-env:$bin" OK "on_path"
    elif [[ "$bin" == "maturin" && -n "$UV_BIN" ]] && "$UV_BIN" run maturin --version >/dev/null 2>&1; then
      _gr "login-env:maturin" OK "uv_run"
    else
      _gr "login-env:$bin" ALARM "optional_accelerator_missing"
    fi
  done
  if _boar_fast_filter_importable "$UV_BIN"; then
    _gr rust-wheel OK "boar_fast_filter_importable"
  else
    _emit_rust_accel_hints "boar_fast_filter_missing_in_venv"
    _gr rust-wheel ALARM "pure_python_fallback hint=maturin_develop_release"
    if [[ $APPLY -eq 1 && -n "$UV_BIN" ]]; then
      if _rust_toolchain_runnable; then
        if (cd "$REPO_ROOT" && "$UV_BIN" run maturin develop --release >/dev/null 2>&1); then
          if _boar_fast_filter_importable "$UV_BIN"; then
            _gr rust-wheel REMEDIATE "maturin_develop_ok"
          else
            _emit_rust_accel_hints "import_still_missing_after_maturin"
            _gr rust-wheel ALARM "maturin_develop_no_import hint=pure_python_fallback"
          fi
        else
          _emit_rust_accel_hints "maturin_develop_failed"
          _gr rust-wheel ALARM "maturin_develop_failed hint=pure_python_fallback"
        fi
      else
        _gr rust-wheel ALARM "rust_toolchain_unavailable hint=install_rust_maturin"
      fi
    fi
  fi
fi

# --- fail2ban / sshguard (#957) ---
FW_SCRIPT="$SCRIPT_DIR/labop-fw-guard-ensure.sh"
if [[ -f "$FW_SCRIPT" ]]; then
  if _has_persona maestro; then
    _gr fail2ban OK "maestro_orchestrator_skip"
  elif [[ -z "${LAB_OP_SUBNET:-}" ]]; then
    _gr fail2ban ALARM "LAB_OP_SUBNET_unset"
    FAIL=1
  elif ! _is_rfc1918_lab_subnet "${LAB_OP_SUBNET}"; then
    _gr fail2ban ALARM "LAB_OP_SUBNET_not_rfc1918"
    FAIL=1
  elif [[ "$PRIV" != "NO_PRIV" ]]; then
    FW_MODE=$([[ $APPLY -eq 1 ]] && echo --apply || echo --check)
    FW_EC=0
    if [[ "${_FW_GUARD_PROBE_DONE:-0}" -eq 1 && "$FW_MODE" == "--check" ]]; then
      printf '%s\n' "$_FW_GUARD_PROBE_OUT" >&2
      FW_EC="$_FW_GUARD_PROBE_EC"
    else
      _invoke_priv_script "$FW_SCRIPT" "$FW_MODE"
      FW_EC=$?
    fi
    if [[ $FW_EC -eq 0 ]]; then
      _gr fail2ban OK "subnet_whitelisted"
    elif [[ $FW_EC -eq 125 ]]; then
      _gr fail2ban ALARM "LAB_OP_SUBNET_not_rfc1918"
      FAIL=1
    elif [[ $FW_EC -eq 126 ]]; then
      _gr fail2ban ALARM "privilege_denied"
      FAIL=1
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

# --- dep-doctor (#958): always --check as operator; --privileged via narrow grant only ---
_dep_optional_degraded() {
  grep -qE 'optional_modules_degraded|7z_UNSUPPORTED' <<<"$1"
}

DEP_SCRIPT="$SCRIPT_DIR/labop-dep-doctor.sh"
if [[ -f "$DEP_SCRIPT" ]]; then
  DEP_OUT=""
  DEP_EC=0
  DEP_OUT="$(bash "$DEP_SCRIPT" --check --personas "$PERSONAS_RAW" 2>&1)" || DEP_EC=$?
  printf '%s\n' "$DEP_OUT" >&2
  DEP_ALARM=0
  DEP_OPTIONAL_DEGRADED=0
  if [[ $DEP_EC -ne 0 ]]; then
    DEP_ALARM=1
  elif _dep_optional_degraded "$DEP_OUT"; then
    DEP_OPTIONAL_DEGRADED=1
  fi
  if [[ $APPLY -eq 1 && "$PRIV" != "NO_PRIV" && $DEP_ALARM -eq 1 ]]; then
    # Capture exit directly - `if ! cmd; then EC=$?` records 0 (negation success), not 126 (#1021).
    _invoke_priv_script "$DEP_SCRIPT" --privileged
    PRIV_EC=$?
    DEP_RECHECK_EC=0
    if [[ $PRIV_EC -eq 0 ]]; then
      DEP_RECHECK_OUT="$(bash "$DEP_SCRIPT" --check --personas "$PERSONAS_RAW" 2>&1)" || DEP_RECHECK_EC=$?
      printf '%s\n' "$DEP_RECHECK_OUT" >&2
    fi
    if [[ $PRIV_EC -eq 0 && $DEP_RECHECK_EC -eq 0 ]]; then
      _gr dep-doctor REMEDIATE "privileged_heal_ok"
      DEP_ALARM=0
      if _dep_optional_degraded "${DEP_RECHECK_OUT:-}"; then
        DEP_OPTIONAL_DEGRADED=1
      fi
    elif [[ $PRIV_EC -eq 126 ]]; then
      _gr dep-doctor ALARM "privilege_denied"
    elif [[ $PRIV_EC -ne 0 ]]; then
      _gr dep-doctor ALARM "remediation_failed"
    else
      _gr dep-doctor ALARM "packages_still_missing_after_remediate"
    fi
  fi
  if [[ $DEP_ALARM -eq 0 ]]; then
    if [[ $DEP_OPTIONAL_DEGRADED -eq 1 ]]; then
      _gr dep-doctor ALARM "optional_modules_degraded hint=uv_sync_extra_compressed"
    else
      _gr dep-doctor OK "modules_and_persona_os"
    fi
  else
    _gr dep-doctor ALARM "packages_or_modules_missing"
    FAIL=1
  fi
fi

if [[ $FAIL -eq 0 ]]; then
  _gr summary OK "mode=$MODE_WORD"
  exit 0
fi
_gr summary ALARM "mode=$MODE_WORD"
exit 1

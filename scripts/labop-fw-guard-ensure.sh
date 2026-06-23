#!/usr/bin/env bash
# scripts/labop-fw-guard-ensure.sh
# Validates (and optionally remediates) fail2ban/sshguard ignore lists for lab-op subnet.
# Run via narrow sudoers from labop-gate-readiness.sh / Maestro -Deep (#957).
#
# Usage: sudo -n bash labop-fw-guard-ensure.sh [--check | --apply]
#   Subnet: REPO_ROOT/.labop-gate/LAB_OP_SUBNET (written by labop-gate-readiness.sh before
#   narrow-grant invoke). LAB_OP_SUBNET env is fallback for direct operator testing only.
#
# Exit: 0=healthy or remediated; 1=needs fix (check) or remediation failed; 2=bad args

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --check) APPLY=0 ;;
    --help|-h)
      echo "Usage: $0 [--check | --apply]  (LAB_OP_SUBNET required)"
      exit 0
      ;;
    *) echo "[FW-Guard] Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

SUBNET="${LAB_OP_SUBNET:-}"
GATE_SUBNET_FILE="$(cd "$(dirname "$0")/.." && pwd)/.labop-gate/LAB_OP_SUBNET"
if [[ -f "$GATE_SUBNET_FILE" ]]; then
  SUBNET="$(tr -d '[:space:]' <"$GATE_SUBNET_FILE")"
fi
if [[ -z "$SUBNET" ]]; then
  echo "[FW-Guard] FAIL: LAB_OP_SUBNET unset (write .labop-gate/LAB_OP_SUBNET or set env)" >&2
  exit 2
fi

_log() { echo "[FW-Guard $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[FW-Guard] OK: $*"; }
_warn(){ echo "[FW-Guard] WARN: $*" >&2; }
_fail(){ echo "[FW-Guard] FAIL: $*" >&2; }

HOST=$(hostname -f 2>/dev/null || hostname)
_log "Starting on $HOST (apply=$APPLY subnet=$SUBNET)"

NEED_FIX=0
F2B_PRESENT=0
SG_PRESENT=0

_subnet_in_list() {
  local list="$1"
  [[ -z "$list" ]] && return 1
  # Word-boundary style: subnet appears as token in ignoreip/whitelist string
  grep -qE "(^|[[:space:]])${SUBNET}([[:space:]]|$)" <<<"$list"
}

# --- fail2ban ---
if command -v fail2ban-client >/dev/null 2>&1; then
  F2B_PRESENT=1
  IGNOREIP=""
  if fail2ban-client ping >/dev/null 2>&1; then
    IGNOREIP="$(fail2ban-client get sshd ignoreip 2>/dev/null || true)"
    if [[ -z "$IGNOREIP" ]]; then
      IGNOREIP="$(fail2ban-client status sshd 2>/dev/null | grep -i 'ignore ip list' | sed 's/.*://' || true)"
    fi
  fi
  if _subnet_in_list "$IGNOREIP"; then
    _ok "fail2ban sshd ignoreip includes $SUBNET"
  else
    _warn "fail2ban sshd ignoreip missing lab subnet (have: ${IGNOREIP:-<empty>})"
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      DROPIN="/etc/fail2ban/jail.d/labop-ignoreip.local"
      if [[ -w /etc/fail2ban ]] || [[ -w "$(dirname "$DROPIN")" ]]; then
        MERGED_IPS="$IGNOREIP"
        if [[ -z "$MERGED_IPS" ]]; then
          MERGED_IPS="127.0.0.1/8 ::1"
        fi
        if ! _subnet_in_list "$MERGED_IPS"; then
          MERGED_IPS="$MERGED_IPS $SUBNET"
        fi
        if [[ ! -f "$DROPIN" ]] || ! grep -qF "$SUBNET" "$DROPIN" 2>/dev/null; then
          {
            echo "# labop-fw-guard-ensure.sh (leave-no-trace: remove this file to revert)"
            echo "[sshd]"
            echo "ignoreip = $MERGED_IPS"
          } >"$DROPIN"
          _log "Wrote $DROPIN (merged ignoreip, preserved existing entries)"
        fi
        if fail2ban-client reload >/dev/null 2>&1 || systemctl reload fail2ban >/dev/null 2>&1; then
          _ok "fail2ban reloaded after ignoreip remediation"
          NEED_FIX=0
        else
          _fail "fail2ban reload failed after writing drop-in"
        fi
      else
        _fail "Cannot write fail2ban drop-in (no grant or read-only)"
      fi
    fi
  fi
else
  _log "fail2ban-client absent (skip)"
fi

# --- sshguard ---
if command -v sshguard >/dev/null 2>&1 || [[ -f /etc/sshguard/whitelist ]]; then
  SG_PRESENT=1
  WL=""
  for f in /etc/sshguard/whitelist /etc/sshguard.whitelist; do
    if [[ -f "$f" ]]; then
      WL="$(grep -v '^#' "$f" | tr '\n' ' ')"
      break
    fi
  done
  for d in /etc/sshguard/whitelist.d /etc/sshguard.whitelist.d; do
    if [[ -d "$d" ]]; then
      WL="$WL $(grep -vh '^#' "$d"/* 2>/dev/null | tr '\n' ' ')"
    fi
  done
  if _subnet_in_list "$WL"; then
    _ok "sshguard whitelist includes $SUBNET"
  elif [[ -z "$WL" && $F2B_PRESENT -eq 1 ]]; then
    _log "sshguard whitelist empty/unreadable; fail2ban present - advisory only"
  else
    _warn "sshguard whitelist missing lab subnet (have: ${WL:-<empty>})"
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      SG_DROPIN="/etc/sshguard/whitelist.d/labop-subnet.conf"
      if [[ ! -d "$(dirname "$SG_DROPIN")" ]]; then
        SG_DROPIN="/etc/sshguard.whitelist.d/labop-subnet.conf"
      fi
      if [[ -w "$(dirname "$SG_DROPIN")" ]] || [[ ! -f "$SG_DROPIN" && -w /etc/sshguard ]]; then
        mkdir -p "$(dirname "$SG_DROPIN")" 2>/dev/null || true
        if [[ ! -f "$SG_DROPIN" ]] || ! grep -qF "$SUBNET" "$SG_DROPIN" 2>/dev/null; then
          {
            echo "# labop-fw-guard-ensure.sh (leave-no-trace: remove this file to revert)"
            echo "$SUBNET"
          } >"$SG_DROPIN"
          _log "Wrote reversible drop-in $SG_DROPIN"
        fi
        if command -v rc-service >/dev/null 2>&1; then
          rc-service sshguard restart >/dev/null 2>&1 || true
        elif command -v systemctl >/dev/null 2>&1; then
          systemctl reload sshguard >/dev/null 2>&1 || systemctl restart sshguard >/dev/null 2>&1 || true
        fi
        _ok "sshguard whitelist remediated (best-effort reload)"
        NEED_FIX=0
      else
        _fail "Cannot write sshguard whitelist (no grant)"
      fi
    fi
  fi
fi

if [[ $F2B_PRESENT -eq 0 && $SG_PRESENT -eq 0 ]]; then
  _log "No fail2ban/sshguard detected - skip fw guard"
  exit 0
fi

if [[ $NEED_FIX -eq 0 ]]; then
  exit 0
fi
exit 1

#!/usr/bin/env bash
# Primary Linux dev workstation: persistent tmux for Cursor agent + Claude Code (/rc).
#
# Cursor = executor (agent worker or interactive agent); Claude = auditor/copilot.
# No secrets in this script. Safe for tracked repo — operator paths via env only.
#
# Usage (from repo root or anywhere):
#   ./scripts/primary-linux-agent-sessions.sh start|stop|status|attach|install-systemd|uninstall-systemd
#
# Env (optional):
#   DATA_BOAR_ROOT       default: ~/Projects/dev/data-boar
#   TMUX_SESSION_CURSOR  default: databoar-cursor
#   TMUX_SESSION_CLAUDE  default: databoar-claude
#   CURSOR_AGENT_MODE    worker | interactive  (default: worker)
#   SKIP_CLAUDE=1        skip Claude tmux session on start
#   SKIP_CURSOR=1        skip Cursor tmux session on start
#
# After install-systemd, enable user lingering so sessions survive logout:
#   loginctl enable-linger "$USER"
#
# See: docs/ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md
# Hub: docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DATA_BOAR_ROOT="${DATA_BOAR_ROOT:-${HOME}/Projects/dev/data-boar}"
TMUX_SESSION_CURSOR="${TMUX_SESSION_CURSOR:-databoar-cursor}"
TMUX_SESSION_CLAUDE="${TMUX_SESSION_CLAUDE:-databoar-claude}"
CURSOR_AGENT_MODE="${CURSOR_AGENT_MODE:-worker}"

SYSTEMD_UNIT_NAME="databoar-agent-sessions.service"
SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user"
SYSTEMD_ENV_FILE="${XDG_CONFIG_HOME:-${HOME}/.config}/databoar/agent-sessions.env"

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  echo
  echo "Commands:"
  echo "  start              Create tmux sessions (idempotent unless --force)"
  echo "  stop               Kill tmux sessions"
  echo "  status             Show session / binary readiness"
  echo "  attach <cursor|claude>   Attach to a session"
  echo "  install-systemd    Install + enable user systemd unit"
  echo "  uninstall-systemd  Disable + remove user systemd unit"
  echo
  echo "Options:"
  echo "  --force            Recreate existing tmux sessions on start"
  echo "  -h, --help         Show this help"
}

log() {
  printf '==> %s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_tmux() {
  command -v tmux >/dev/null 2>&1 || die "tmux not found — install tmux (apt install tmux)"
}

warm_path() {
  if [[ -f /etc/profile.d/zz-local-bin.sh ]]; then
    # shellcheck source=/dev/null
    source /etc/profile.d/zz-local-bin.sh
  fi
  export PATH="/usr/local/bin:${HOME}/.local/bin:${PATH}"
  for _d in "${HOME}/.local/share/flatpak/exports/bin" "/var/lib/flatpak/exports/bin"; do
    if [[ -d "${_d}" ]]; then
      case ":${PATH}:" in *:"${_d}":*) ;; *) export PATH="${_d}:${PATH}" ;; esac
    fi
  done
}

resolve_repo_root() {
  if [[ -d "${DATA_BOAR_ROOT}/.git" ]]; then
    printf '%s\n' "${DATA_BOAR_ROOT}"
    return 0
  fi
  if [[ -d "${REPO_ROOT}/.git" ]]; then
    printf '%s\n' "${REPO_ROOT}"
    return 0
  fi
  die "No git repo at DATA_BOAR_ROOT=${DATA_BOAR_ROOT} or script repo ${REPO_ROOT}"
}

cursor_start_cmd() {
  case "${CURSOR_AGENT_MODE}" in
    worker)
      if command -v agent >/dev/null 2>&1; then
        printf '%s\n' "exec agent worker start"
      else
        warn "agent not on PATH — starting shell in ${TMUX_SESSION_CURSOR}; run: agent worker start"
        printf '%s\n' "exec bash -l"
      fi
      ;;
    interactive)
      if command -v agent >/dev/null 2>&1; then
        printf '%s\n' "exec agent"
      else
        warn "agent not on PATH — starting shell; run: agent"
        printf '%s\n' "exec bash -l"
      fi
      ;;
    *)
      die "CURSOR_AGENT_MODE must be worker or interactive (got: ${CURSOR_AGENT_MODE})"
      ;;
  esac
}

claude_start_cmd() {
  if command -v claude >/dev/null 2>&1; then
    printf '%s\n' "exec claude"
  else
    warn "claude not on PATH — starting shell in ${TMUX_SESSION_CLAUDE}; run: claude then /rc"
    printf '%s\n' "exec bash -l"
  fi
}

tmux_session_exists() {
  local name="$1"
  tmux has-session -t "${name}" 2>/dev/null
}

start_session() {
  local name="$1"
  local cmd="$2"
  local force="${3:-0}"

  if tmux_session_exists "${name}"; then
    if [[ "${force}" == "1" ]]; then
      log "Recreating tmux session: ${name}"
      tmux kill-session -t "${name}" 2>/dev/null || true
    else
      log "tmux session already running: ${name} (use --force to recreate)"
      return 0
    fi
  fi

  log "Starting tmux session: ${name}"
  tmux new-session -d -s "${name}" -c "${repo}" "${cmd}"
}

cmd_start() {
  local force=0
  if [[ "${1:-}" == "--force" ]]; then
    force=1
  fi

  require_tmux
  warm_path
  local repo
  repo="$(resolve_repo_root)"

  if [[ "${SKIP_CURSOR:-0}" != "1" ]]; then
    start_session "${TMUX_SESSION_CURSOR}" "$(cursor_start_cmd)" "${force}"
  fi

  if [[ "${SKIP_CLAUDE:-0}" != "1" ]]; then
    start_session "${TMUX_SESSION_CLAUDE}" "$(claude_start_cmd)" "${force}"
  fi

  log "Done. Attach: $0 attach cursor | $0 attach claude"
  log "Claude remote: inside claude session, run /rc (or claude --remote-control)"
  cmd_status
}

cmd_stop() {
  require_tmux
  for name in "${TMUX_SESSION_CURSOR}" "${TMUX_SESSION_CLAUDE}"; do
    if tmux_session_exists "${name}"; then
      log "Killing tmux session: ${name}"
      tmux kill-session -t "${name}"
    else
      log "tmux session not running: ${name}"
    fi
  done
}

cmd_status() {
  require_tmux
  warm_path
  local repo="<missing>"
  if [[ -d "${DATA_BOAR_ROOT}/.git" ]]; then
    repo="${DATA_BOAR_ROOT}"
  elif [[ -d "${REPO_ROOT}/.git" ]]; then
    repo="${REPO_ROOT}"
  fi

  echo "DATA_BOAR_ROOT=${DATA_BOAR_ROOT}"
  echo "Resolved repo: ${repo}"
  echo "CURSOR_AGENT_MODE=${CURSOR_AGENT_MODE}"
  echo

  for name in "${TMUX_SESSION_CURSOR}" "${TMUX_SESSION_CLAUDE}"; do
    if tmux_session_exists "${name}"; then
      echo "tmux ${name}: running"
      tmux list-panes -t "${name}" -F '  pane %{pane_index}: #{pane_current_command}' 2>/dev/null || true
    else
      echo "tmux ${name}: stopped"
    fi
  done

  echo
  for bin in agent claude tmux; do
    if command -v "${bin}" >/dev/null 2>&1; then
      echo "binary ${bin}: $(command -v "${bin}")"
    else
      echo "binary ${bin}: missing"
    fi
  done

  if loginctl show-user "${USER}" -p Linger 2>/dev/null | grep -q 'yes'; then
    echo "systemd linger: enabled"
  else
    echo "systemd linger: disabled (run: loginctl enable-linger \"${USER}\" for boot/logout survival)"
  fi
}

cmd_attach() {
  local which="${1:-}"
  require_tmux
  case "${which}" in
    cursor|c)
      tmux attach -t "${TMUX_SESSION_CURSOR}"
      ;;
    claude|cc)
      tmux attach -t "${TMUX_SESSION_CLAUDE}"
      ;;
    *)
      die "attach requires cursor or claude (got: ${which:-<empty>})"
      ;;
  esac
}

write_systemd_env() {
  mkdir -p "$(dirname "${SYSTEMD_ENV_FILE}")"
  cat >"${SYSTEMD_ENV_FILE}" <<EOF
# Generated by ${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}") install-systemd
DATA_BOAR_ROOT=${DATA_BOAR_ROOT}
TMUX_SESSION_CURSOR=${TMUX_SESSION_CURSOR}
TMUX_SESSION_CLAUDE=${TMUX_SESSION_CLAUDE}
CURSOR_AGENT_MODE=${CURSOR_AGENT_MODE}
EOF
  log "Wrote ${SYSTEMD_ENV_FILE}"
}

write_systemd_unit() {
  local unit_path="${SYSTEMD_USER_DIR}/${SYSTEMD_UNIT_NAME}"
  mkdir -p "${SYSTEMD_USER_DIR}"
  cat >"${unit_path}" <<EOF
[Unit]
Description=Data Boar agent tmux sessions (Cursor + Claude Code)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
EnvironmentFile=-${SYSTEMD_ENV_FILE}
ExecStart=${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}") start
ExecStop=${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}") stop

[Install]
WantedBy=default.target
EOF
  log "Wrote ${unit_path}"
}

cmd_install_systemd() {
  command -v systemctl >/dev/null 2>&1 || die "systemctl not found"
  write_systemd_env
  write_systemd_unit
  systemctl --user daemon-reload
  systemctl --user enable --now "${SYSTEMD_UNIT_NAME}"
  log "Enabled ${SYSTEMD_UNIT_NAME}"
  echo
  echo "Next steps:"
  echo "  1. loginctl enable-linger \"${USER}\"   # survive logout / run at boot"
  echo "  2. ${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}") status"
  echo "  3. tmux attach -t ${TMUX_SESSION_CLAUDE}  →  /rc"
  echo "  4. cursor.com/agents (when CURSOR_AGENT_MODE=worker)"
}

cmd_uninstall_systemd() {
  command -v systemctl >/dev/null 2>&1 || die "systemctl not found"
  local unit_path="${SYSTEMD_USER_DIR}/${SYSTEMD_UNIT_NAME}"
  if systemctl --user is-enabled "${SYSTEMD_UNIT_NAME}" >/dev/null 2>&1; then
    systemctl --user disable --now "${SYSTEMD_UNIT_NAME}" || true
  fi
  rm -f "${unit_path}"
  systemctl --user daemon-reload
  log "Removed ${unit_path} (env file kept: ${SYSTEMD_ENV_FILE})"
}

main() {
  local cmd="${1:-}"
  shift || true

  case "${cmd}" in
    start)
      cmd_start "$@"
      ;;
    stop)
      cmd_stop
      ;;
    status)
      cmd_status
      ;;
    attach)
      cmd_attach "$@"
      ;;
    install-systemd)
      cmd_install_systemd
      ;;
    uninstall-systemd)
      cmd_uninstall_systemd
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      die "Unknown command: ${cmd} (try --help)"
      ;;
  esac
}

main "$@"

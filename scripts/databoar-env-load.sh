#!/usr/bin/env bash
# Load Data Boar runtime secrets from XDG config env files into the current shell.
#
# Product contract (stable over time):
#   YAML → *_from_env names → OS environment at process start.
# Vaults (Bitwarden CLI today; Phase B @vault: / HashiCorp later) inject into
# that same env layer — they do not replace *_from_env in tracked YAML.
#
# Canonical dir (override with DATA_BOAR_ENV_DIR):
#   ${XDG_CONFIG_HOME:-$HOME/.config}/databoar/
# Files: chmod 0600 recommended; never commit live values.
# Prefer vault → env when available; on-disk *.env is an optional bridge.
#
# Usage (must be sourced so exports persist):
#   . ./scripts/databoar-env-load.sh              # all *.env in the dir
#   . ./scripts/databoar-env-load.sh hubspot      # only hubspot.env
#   . ./scripts/databoar-env-load.sh --list       # list files, no export
#
# Docs: docs/ops/OPERATOR_CREDENTIALS_FROM_ENV.md
# See also: docs/ops/OPERATOR_SECRETS_BITWARDEN.md · docs/plans/PLAN_SECRETS_VAULT.md

_DATA_BOAR_ENV_DIR="${DATA_BOAR_ENV_DIR:-${XDG_CONFIG_HOME:-${HOME}/.config}/databoar}"

_databoar_env_is_sourced() {
  [[ "${BASH_SOURCE[0]}" != "${0}" ]]
}

_databoar_env_usage() {
  sed -n '2,22p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

_databoar_env_list() {
  if [[ ! -d "${_DATA_BOAR_ENV_DIR}" ]]; then
    echo "databoar-env-load: directory missing: ${_DATA_BOAR_ENV_DIR}" >&2
    echo "  mkdir -p \"${_DATA_BOAR_ENV_DIR}\" && chmod 700 \"${_DATA_BOAR_ENV_DIR}\"" >&2
    return 1
  fi
  local f found=0
  for f in "${_DATA_BOAR_ENV_DIR}"/*.env; do
    [[ -e "${f}" ]] || continue
    found=1
    ls -l "${f}"
  done
  if [[ "${found}" -eq 0 ]]; then
    echo "databoar-env-load: no *.env under ${_DATA_BOAR_ENV_DIR}" >&2
    return 1
  fi
}

_databoar_env_load_file() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "databoar-env-load: not found: ${path}" >&2
    return 1
  fi
  set -a
  # shellcheck disable=SC1090
  . "${path}"
  set +a
  echo "databoar-env-load: loaded $(basename "${path}")" >&2
}

_databoar_env_main() {
  local arg="${1:-}"
  case "${arg}" in
    -h|--help)
      _databoar_env_usage
      return 0
      ;;
    --list|-l)
      _databoar_env_list
      return $?
      ;;
  esac

  if ! _databoar_env_is_sourced; then
    echo "databoar-env-load: source this script so exports persist in your shell:" >&2
    echo "  . ./scripts/databoar-env-load.sh ${arg}" >&2
    return 2
  fi

  if [[ ! -d "${_DATA_BOAR_ENV_DIR}" ]]; then
    echo "databoar-env-load: directory missing: ${_DATA_BOAR_ENV_DIR}" >&2
    echo "  mkdir -p \"${_DATA_BOAR_ENV_DIR}\" && chmod 700 \"${_DATA_BOAR_ENV_DIR}\"" >&2
    return 1
  fi

  if [[ -n "${arg}" ]]; then
    local stem="${arg%.env}"
    _databoar_env_load_file "${_DATA_BOAR_ENV_DIR}/${stem}.env"
    return $?
  fi

  local f loaded=0
  for f in "${_DATA_BOAR_ENV_DIR}"/*.env; do
    [[ -e "${f}" ]] || continue
    case "$(basename "${f}")" in
      *.example.env|example.env) continue ;;
    esac
    _databoar_env_load_file "${f}" || return $?
    loaded=1
  done
  if [[ "${loaded}" -eq 0 ]]; then
    echo "databoar-env-load: no *.env under ${_DATA_BOAR_ENV_DIR}" >&2
    return 1
  fi
}

_databoar_env_main "$@"

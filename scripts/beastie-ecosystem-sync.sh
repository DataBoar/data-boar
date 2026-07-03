#!/usr/bin/env bash
# Beastie ecosystem — local clone sync / status (DataBoar org).
# Complements operator ~/.local/bin/bestiais-docs-skeleton.sh and bestiais-mirror.sh.
#
# Usage (from data-boar repo root):
#   ./scripts/beastie-ecosystem-sync.sh status          # default — fetch + report
#   ./scripts/beastie-ecosystem-sync.sh fetch           # git fetch on all clones
#   ./scripts/beastie-ecosystem-sync.sh clone-missing   # clone missing repos under DEV_ROOT
#   ./scripts/beastie-ecosystem-sync.sh pull-ff         # ff-only pull on default branch (each clone)
#   ./scripts/beastie-ecosystem-sync.sh set-remote      # point origin at DataBoar/<name> (one or all)
#   ./scripts/beastie-ecosystem-sync.sh status homing-robin quirky-quati   # subset
#
# Env:
#   DATA_BOAR_DEV_ROOT  default: $HOME/Projects/dev
#   BEASTIE_GH_ORG      default: DataBoar
set -euo pipefail

ORG="${BEASTIE_GH_ORG:-DataBoar}"
DEV_ROOT="${DATA_BOAR_DEV_ROOT:-$HOME/Projects/dev}"
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=5 -o ServerAliveCountMax=2}"

# Canonical beastie / satellite repos (DataBoar org). data-boar itself optional — listed last.
ALL_REPOS=(
  quirky-quati
  homing-robin
  carrion-crow
  resolute-rikki
  sage-remora
  tidy-tortoise
  sweeping-squirrel
  building-beaver
  burrowing-badger
  loaded-llama
  mimic-octopus
  observant-otter
  platypus
  picket-prairie-dog
  stealthy-stoat
  polyglot-pangolin
  polyglot-file-detector
  maestro
  license-studio
  data-boar
)

MODE="${1:-status}"
shift || true
if [ $# -gt 0 ]; then
  REPOS=("$@")
else
  REPOS=("${ALL_REPOS[@]}")
fi

_default_branch() {
  local name="$1"
  gh api "repos/${ORG}/${name}" --jq .default_branch 2>/dev/null || echo main
}

_clone_if_missing() {
  local name="$1"
  local d="${DEV_ROOT}/${name}"
  if [ -d "${d}/.git" ]; then
    return 0
  fi
  echo "  cloning ${ORG}/${name} -> ${d}"
  git clone "git@github.com:${ORG}/${name}.git" "${d}"
}

_fetch_one() {
  local d="$1"
  git -C "${d}" fetch origin --prune --quiet 2>/dev/null || git -C "${d}" fetch origin --prune
}

_status_one() {
  local name="$1"
  local d="${DEV_ROOT}/${name}"
  if [ ! -d "${d}/.git" ]; then
    printf "MISSING\t%s\t(no clone at %s)\n" "${name}" "${d}"
    return 0
  fi
  _fetch_one "${d}"
  local branch remote ahead behind dirty def
  branch=$(git -C "${d}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  remote=$(git -C "${d}" remote get-url origin 2>/dev/null || echo "?")
  def=$(_default_branch "${name}")
  local upstream="origin/${def}"
  if git -C "${d}" rev-parse --verify "${upstream}" >/dev/null 2>&1; then
    ahead=$(git -C "${d}" rev-list --count "${upstream}..HEAD" 2>/dev/null || echo "?")
    behind=$(git -C "${d}" rev-list --count "HEAD..${upstream}" 2>/dev/null || echo "?")
  else
    ahead="?"
    behind="?"
  fi
  dirty=$(git -C "${d}" status --porcelain | wc -l | tr -d ' ')
  local sync="OK"
  [ "${ahead}" != "0" ] && [ "${ahead}" != "?" ] && sync="AHEAD+${ahead}"
  [ "${behind}" != "0" ] && [ "${behind}" != "?" ] && sync="${sync},BEHIND+${behind}"
  [ "${dirty}" != "0" ] && sync="${sync},DIRTY+${dirty}"
  if ! echo "${remote}" | grep -q "${ORG}/${name}"; then
    sync="${sync},REMOTE-DRIFT"
  fi
  printf "CLONE\t%s\tbranch=%s\tvs origin/%s\t%s\t%s\n" "${name}" "${branch}" "${def}" "${sync}" "${remote}"
}

_pull_ff_one() {
  local name="$1"
  local d="${DEV_ROOT}/${name}"
  [ -d "${d}/.git" ] || { echo "  skip ${name} (no clone)"; return 0; }
  local def
  def=$(_default_branch "${name}")
  git -C "${d}" fetch origin --prune --quiet
  if ! git -C "${d}" diff --quiet || ! git -C "${d}" diff --cached --quiet; then
    echo "  skip ${name} (dirty working tree)"
    return 0
  fi
  git -C "${d}" checkout "${def}" 2>/dev/null || true
  git -C "${d}" pull --ff-only origin "${def}"
  echo "  pulled ${name} (${def})"
}

_set_remote_one() {
  local name="$1"
  local d="${DEV_ROOT}/${name}"
  local want="git@github.com:${ORG}/${name}.git"
  if [ ! -d "${d}/.git" ]; then
    echo "  skip ${name} (no clone)"
    return 0
  fi
  if ! gh api "repos/${ORG}/${name}" --jq .name >/dev/null 2>&1; then
    echo "  skip ${name} (no ${ORG}/${name} on GitHub)"
    return 1
  fi
  local cur
  cur=$(git -C "${d}" remote get-url origin 2>/dev/null || echo "")
  if [ "${cur}" = "${want}" ]; then
    echo "  ok ${name} (already ${want})"
    return 0
  fi
  git -C "${d}" remote set-url origin "${want}"
  _fetch_one "${d}"
  echo "  set-remote ${name}: ${cur:-?} -> ${want}"
}

echo "beastie-ecosystem-sync: mode=${MODE} org=${ORG} dev_root=${DEV_ROOT} repos=${#REPOS[@]}"
echo "---"

case "${MODE}" in
  status)
    for name in "${REPOS[@]}"; do
      _status_one "${name}"
    done
    ;;
  fetch)
    for name in "${REPOS[@]}"; do
      d="${DEV_ROOT}/${name}"
      if [ -d "${d}/.git" ]; then
        echo "fetch ${name}"
        _fetch_one "${d}"
      else
        echo "skip ${name} (no clone)"
      fi
    done
    ;;
  clone-missing)
    for name in "${REPOS[@]}"; do
      _clone_if_missing "${name}" || echo "  FAIL ${name}"
    done
    ;;
  pull-ff)
    for name in "${REPOS[@]}"; do
      _pull_ff_one "${name}" || echo "  FAIL pull ${name}"
    done
    ;;
  set-remote)
    for name in "${REPOS[@]}"; do
      _set_remote_one "${name}" || echo "  FAIL set-remote ${name}"
    done
    ;;
  *)
    echo "Unknown mode: ${MODE}" >&2
    echo "Modes: status | fetch | clone-missing | pull-ff | set-remote" >&2
    exit 2
    ;;
esac

echo "---"
echo "done"

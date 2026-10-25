#!/usr/bin/env bash
# private-git-sync.sh -- Linux/macOS mirror of scripts/private-git-sync.ps1.
# Stacked private repo (docs/private): feedbacks inbox, commit, optional push mirrors.
# Usage (from repo root): ./scripts/private-git-sync.sh [--push] [--feedbacks-only] [--message "msg"]
# Windows: prefer .\scripts\private-git-sync.ps1
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
PRIVATE_DIR="$REPO_ROOT/docs/private"
INBOX_DIR="$REPO_ROOT/docs/feedbacks, reviews, comments and criticism"
FEEDBACKS_DEST="$PRIVATE_DIR/feedbacks_and_reviews"

PUSH=0
FEEDBACKS_ONLY=0
MESSAGE=""

# Lab bare notes-sync.git mirrors: reliable local disks only.
# pi3b excluded (fragile SD card, limited space).
LAB_BARE_MIRROR_HOSTS=(mini-bt latitude t14 alpine-emachines)

HOMELAB_SECRET_LEAF_NAMES=(".env.bitwarden.local")

usage() {
  echo "Usage: $0 [--push] [--feedbacks-only] [--message \"commit message\"]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --feedbacks-only) FEEDBACKS_ONLY=1; shift ;;
    --message)
      MESSAGE="${2:-}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

header() { echo ""; echo "=== $1 ==="; }
ok() { echo "  OK  $1"; }
info() { echo "  ... $1"; }
warn() { echo " WARN $1"; }

lab_ssh_user() {
  if [[ -n "${LAB_OP_SSH_USER:-}" ]]; then
    echo "$LAB_OP_SSH_USER"
  else
    echo "leitao"
  fi
}

lab_remote_url() {
  local host_short=$1
  local user
  user=$(lab_ssh_user)
  echo "ssh://${user}@${host_short}/home/${user}/Documents/.kb-cache/repos/notes-sync.git"
}

ensure_lab_remote() {
  local remote_name=$1 remote_url=$2 existing
  existing=$(git remote get-url "$remote_name" 2>/dev/null || true)
  if [[ -z "$existing" ]]; then
    git remote add "$remote_name" "$remote_url"
    info "Remote criado: $remote_name"
  elif [[ "$existing" != "$remote_url" ]]; then
    git remote set-url "$remote_name" "$remote_url"
    info "Remote atualizado: $remote_name"
  fi
}

ensure_lab_bare_repo() {
  local host_short=$1 user init_cmd
  user=$(lab_ssh_user)
  init_cmd='mkdir -p ~/Documents/.kb-cache/repos && test -d ~/Documents/.kb-cache/repos/notes-sync.git || git init --bare ~/Documents/.kb-cache/repos/notes-sync.git'
  if ! ssh -o BatchMode=yes -o ConnectTimeout=15 "${user}@${host_short}" "$init_cmd"; then
    warn "Bare init FALHOU em ${host_short}"
    return 1
  fi
  return 0
}

push_lab_bare_mirrors() {
  local host_short remote_name remote_url push_fail=0
  header "Passo 3: Push bare notes-sync.git para lab hosts (lista canonica)"
  info "Hosts: ${LAB_BARE_MIRROR_HOSTS[*]} (pi3b excluido -- SD fragil)"
  for host_short in "${LAB_BARE_MIRROR_HOSTS[@]}"; do
    remote_name="lab-${host_short}"
    remote_url=$(lab_remote_url "$host_short")
    ensure_lab_remote "$remote_name" "$remote_url"
    if ! ensure_lab_bare_repo "$host_short"; then
      push_fail=1
      continue
    fi
    info "Pushing para ${remote_name} ..."
    if git push "$remote_name" main; then
      ok "Push OK: ${remote_name}"
    else
      warn "Push FALHOU: ${remote_name}"
      push_fail=1
    fi
  done
  if git remote 2>/dev/null | grep -qx 'lab-pi3b'; then
    info "lab-pi3b ainda configurado; politica atual nao faz push para pi3b. Remova com: git -C docs/private remote remove lab-pi3b"
  fi
  [[ "$push_fail" -eq 0 ]]
}

push_local_bare_origin() {
  local bare="$HOME/Documents/.kb-cache/repos/notes-sync.git"
  header "Passo 4: Push bare local (origin)"
  if [[ ! -d "$bare" ]]; then
    mkdir -p "$(dirname "$bare")"
    git init --bare "$bare"
    info "Bare local criado: $bare"
  fi
  git -C "$bare" config core.fsync none 2>/dev/null || true
  if git remote get-url origin >/dev/null 2>&1; then
    :
  else
    git remote add origin "$bare"
  fi
  local current_origin
  current_origin=$(git remote get-url origin 2>/dev/null || true)
  if [[ "$current_origin" != "$bare" ]]; then
    git remote set-url origin "$bare"
  fi
  info "Push origin (local bare) ..."
  if git push origin main; then
    ok "Push OK: origin ($bare)"
    return 0
  fi
  warn "Push FALHOU: origin ($bare)"
  return 1
}

push_veracrypt_bare() {
  local bare push_fail=0 found=0
  header "Passo 5: Push bare notes-sync.git (VeraCrypt Z: ou Y: -- se montado)"
  for mount in /media/*/VeraCrypt /mnt/z /mnt/y Z: Y:; do
    [[ -d "$mount" ]] || continue
    bare="${mount%/}/notes-sync.git"
    [[ -d "$bare" ]] || continue
    found=1
    git -C "$bare" config core.fsync none 2>/dev/null || true
    info "Push bare (VC): $bare ..."
    if git push "${bare}" main:main; then
      ok "Push OK (VC bare): $bare"
    else
      warn "Push FALHOU (VC bare): $bare"
      push_fail=1
    fi
    break
  done
  if [[ "$found" -eq 0 ]]; then
    info "VC bare: nenhum notes-sync.git montado -- pulando (esperado no T14 sem VeraCrypt)"
  fi
  [[ "$push_fail" -eq 0 ]]
}

pcloud_mirror() {
  local dest="$HOME/pCloudDrive/lab-private-backup/notes-sync"
  local exclude_args=()
  header "Passo 6: Espelho pCloud (~/pCloudDrive) -- sem secrets homelab"
  if [[ ! -d "$HOME/pCloudDrive" ]]; then
    info "pCloud (~/pCloudDrive) nao montado -- pulando backup pCloud"
    return 0
  fi
  mkdir -p "$dest"
  for leaf in "${HOMELAB_SECRET_LEAF_NAMES[@]}"; do
    exclude_args+=(--exclude="$leaf")
  done
  info "rsync para $dest (sem .git e secrets homelab) ..."
  if rsync -a --delete --exclude='.git' "${exclude_args[@]}" "$PRIVATE_DIR/" "$dest/"; then
    ok "pCloud sync OK: $dest"
    return 0
  fi
  warn "pCloud rsync FALHOU: $dest"
  return 1
}

header "private-git-sync: Stacked Private Repo Sync"

header "Passo 1: Sincronizar feedbacks do inbox para docs/private/feedbacks_and_reviews/"
if [[ -d "$INBOX_DIR" ]]; then
  mkdir -p "$FEEDBACKS_DEST"
  cp -a "$INBOX_DIR"/. "$FEEDBACKS_DEST"/ 2>/dev/null || true
  ok "Feedbacks sincronizados para feedbacks_and_reviews/"
else
  info "Inbox nao encontrado (ok se vazio)"
fi

if [[ "$FEEDBACKS_ONLY" -eq 1 ]]; then
  info "Modo --feedbacks-only: encerrado apos sync de feedbacks."
  exit 0
fi

[[ -d "$PRIVATE_DIR/.git" ]] || { warn "docs/private/.git ausente"; exit 1; }
cd "$PRIVATE_DIR"

lock_file=".git/index.lock"
if [[ -f "$lock_file" ]]; then
  rm -f "$lock_file"
  warn "Removido stale index.lock"
fi

header "Passo 2: Commit no private repo"
pending_count=$(git status --short | wc -l | tr -d ' ')
info "Arquivos pendentes (M/A/?): $pending_count"

if [[ "$pending_count" -eq 0 ]]; then
  ok "Private repo ja esta em dia. Nenhum arquivo pendente."
else
  folders=(feedbacks_and_reviews homelab author_info commercial operator_economics legal_dossier raw_pastes plans pitch security_audit social_drafts employers evidence_catalog scripts)
  for f in "${folders[@]}"; do
    [[ -d "$f" ]] && git add "$f" 2>/dev/null || true
  done
  git add --all -- . 2>/dev/null || true
  staged_count=$(git diff --cached --name-only | wc -l | tr -d ' ')
  info "Staged: $staged_count arquivos"
  if [[ "$staged_count" -eq 0 ]]; then
    warn "Nenhum arquivo staged. Verificar .gitignore interno ou paths."
  else
    if [[ -z "$MESSAGE" ]]; then
      MESSAGE="chore(private): session sync $(date +%Y-%m-%d\ %H:%M)"
    fi
    git commit --trailer "Made-with: Cursor" -m "$MESSAGE"
    ok "Commit realizado: $MESSAGE"
  fi
fi

push_had_failure=0
if [[ "$PUSH" -eq 1 ]]; then
  push_local_bare_origin || push_had_failure=1
  push_lab_bare_mirrors || push_had_failure=1
  push_veracrypt_bare || push_had_failure=1
  pcloud_mirror || push_had_failure=1
  if [[ "$push_had_failure" -ne 0 ]]; then
    warn "private-git-sync: concluido com avisos/falhas em push ou pCloud"
  fi
fi

header "private-git-sync: Concluido"
cd "$REPO_ROOT"
exit "$push_had_failure"

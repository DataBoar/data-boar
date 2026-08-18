#!/usr/bin/env bash
# Install Bitwarden CLI (bw) on Debian/LMDE LAB-NODE-01 without waiting for full Ansible.
# Fixes docker.list noise (Errno 13), installs nodejs/npm, npm -g @bitwarden/cli,
# permissions on /usr/local/lib/node_modules/@bitwarden, and PATH for login + tmux.
#
# Run from repo root:
#   bash scripts/lab-node-01-bitwarden-cli-bootstrap.sh
set -eu

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIX_DOCKER="${REPO_ROOT}/scripts/lab-node-01-fix-docker-list.sh"
if [[ -f "${FIX_DOCKER}" ]]; then
  echo "==> docker.list (if present)"
  bash "${FIX_DOCKER}"
fi

echo "==> apt: build-essential, nodejs, npm (Bitwarden CLI help: Linux npm may need build-essential)"
sudo apt-get update -qq
sudo apt-get install -y build-essential nodejs npm

echo "==> npm: global @bitwarden/cli"
sudo npm install -g @bitwarden/cli

echo "==> permissions: @bitwarden tree + bw.js"
sudo chmod -R go+rX /usr/local/lib/node_modules/@bitwarden 2>/dev/null || true
if [[ -f /usr/local/lib/node_modules/@bitwarden/cli/build/bw.js ]]; then
  sudo chmod 755 /usr/local/lib/node_modules/@bitwarden/cli/build/bw.js
fi

PROFILED="/etc/profile.d/zz-local-bin.sh"
echo "==> ${PROFILED}"
sudo tee "${PROFILED}" > /dev/null <<'EOF'
# Managed by Ansible (lab_node_01_bitwarden_cli) — Bitwarden CLI and other /usr/local/bin tools
case ":${PATH}:" in
  *:/usr/local/bin:*) ;;
  *) export PATH="/usr/local/bin:${PATH}" ;;
esac
EOF
sudo chmod 644 "${PROFILED}"

BASHRC="/etc/bash.bashrc"
MARK_BEGIN="# BEGIN ANSIBLE MANAGED BLOCK lab_node_01_bitwarden_cli_path"
if ! grep -qF "${MARK_BEGIN}" "${BASHRC}" 2>/dev/null; then
  echo "==> append PATH block to ${BASHRC} (tmux / non-login bash)"
  sudo tee -a "${BASHRC}" > /dev/null <<'EOF'

# BEGIN ANSIBLE MANAGED BLOCK lab_node_01_bitwarden_cli_path
# Bitwarden CLI (npm -g) and other /usr/local/bin tools
case ":${PATH}:" in
  *:/usr/local/bin:*) ;;
  *) export PATH="/usr/local/bin:${PATH}" ;;
esac
# END ANSIBLE MANAGED BLOCK lab_node_01_bitwarden_cli_path
EOF
else
  echo "==> ${BASHRC} already has lab_node_01_bitwarden_cli_path block — skip"
fi

case ":${PATH}:" in
  *:/usr/local/bin:*) ;;
  *) export PATH="/usr/local/bin:${PATH}" ;;
esac

echo "==> bw version"
/usr/local/bin/bw --version
echo
echo "OK. In this shell, bw is on PATH. In tmux: new pane or: source /etc/bash.bashrc"
echo "Next: bw login   then: bw unlock"

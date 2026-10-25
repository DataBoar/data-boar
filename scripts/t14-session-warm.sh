#!/usr/bin/env bash
# Optional: PATH for bw (/usr/local/bin, Flatpak exports), sudo timestamp refresh, bw hints.
# No secrets. Run from repo root or anywhere: bash scripts/lab-node-01-session-warm.sh
set -eu

# PATH: profile.d (Ansible), npm global, Flatpak exports (user may get bw symlink here)
if [[ -f /etc/profile.d/zz-local-bin.sh ]]; then
  # shellcheck source=/dev/null
  source /etc/profile.d/zz-local-bin.sh
fi
export PATH="/usr/local/bin:${PATH}"
for _d in "${HOME}/.local/share/flatpak/exports/bin" "/var/lib/flatpak/exports/bin"; do
  if [[ -d "${_d}" ]]; then
    case ":${PATH}:" in *:"${_d}":*) ;; *) export PATH="${_d}:${PATH}" ;; esac
  fi
done

echo "== LAB-NODE-01 session warm (PATH + sudo + bw check) =="
if [[ -n "${TMUX:-}" ]]; then
  echo "NOTE: inside tmux — panes often use non-login bash; if bw is missing, run: source /etc/bash.bashrc"
  echo "      (role lab_node_01_bitwarden_cli adds PATH there.) Flatpak-only: alias bw in ~/.bashrc — see OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md §1.2.2"
fi

_bw_ok=""
if command -v bw >/dev/null 2>&1; then
  echo "OK: bw -> $(command -v bw)"
  bw --version 2>/dev/null | head -n 1 || true
  _bw_ok=1
elif [[ -x /usr/local/bin/bw ]]; then
  echo "OK: bw -> /usr/local/bin/bw"
  /usr/local/bin/bw --version 2>/dev/null | head -n 1 || true
  _bw_ok=1
elif command -v flatpak >/dev/null 2>&1 && flatpak list --app 2>/dev/null | grep -q com.bitwarden.desktop; then
  if flatpak run --command=bw com.bitwarden.desktop --version >/dev/null 2>&1; then
    echo "OK: bw via Flatpak (com.bitwarden.desktop)"
    flatpak run --command=bw com.bitwarden.desktop --version 2>/dev/null | head -n 1 || true
    echo "NOTE: this script has no shell aliases — use flatpak run ... for bw, or alias bw in ~/.bashrc for tmux."
    _bw_ok=1
  fi
fi

if [[ -z "${_bw_ok}" ]]; then
  echo "NOTE: bw not found — options:"
  echo "      - npm: bash scripts/lab-node-01-bitwarden-cli-bootstrap.sh  (or Ansible role lab_node_01_bitwarden_cli)"
  echo "      - Flatpak: flatpak install flathub com.bitwarden.desktop  (+ alias — docs §1.2.2)"
fi

echo "Running sudo -v (refresh sudo timestamp)..."
sudo -v
echo "OK: sudo -v succeeded."
echo "Next: bw login / bw unlock  (then export BW_SESSION=... per Bitwarden docs)"
echo "      VeraCrypt: see docs/private/homelab/VERACRYPT_PRIVATE_REPO_SETUP.pt_BR.md section 6.0.1"
echo "Docker: if journal shows live-restore + swarm incompatible, from repo on LAB-NODE-01:"
echo "      sudo bash scripts/lab-node-01-docker-remove-live-restore-and-restart.sh"

#!/usr/bin/env bash
# Install VeraCrypt Console on Debian 13 amd64 (e.g. LMDE 7 / LAB-NODE-01) from Launchpad .deb + PGP verify.
# Run on the LAB-NODE-01 after: sudo -v  (same tmux pane). No secrets in this script.
# Ref: docs/private/homelab/VERACRYPT_PRIVATE_REPO_SETUP.pt_BR.md section 6.1 (Debian 13 amd64).
set -eu

VC_VER="1.26.24"
DIR="${HOME}/veracrypt-${VC_VER}-d13-amd64"
DEB="veracrypt-console-${VC_VER}-Debian-13-amd64.deb"
SIG="${DEB}.sig"
BASE="https://launchpad.net/veracrypt/trunk/${VC_VER}/+download"

mkdir -p "${DIR}"
cd "${DIR}"

if [[ ! -f "${DEB}" ]]; then
  echo "==> Download ${DEB}"
  wget -O "${DEB}" "${BASE}/${DEB}"
  wget -O "${SIG}" "${BASE}/${SIG}"
fi

echo "==> Import VeraCrypt signing key (if needed)"
curl -fsSL "https://www.idrix.fr/VeraCrypt/VeraCrypt_PGP_public_key.asc" | gpg --import || true

echo "==> gpg --verify"
gpg --verify "${SIG}" "${DEB}"

echo "==> apt install (requires sudo; run sudo -v first in this tty)"
sudo apt-get update -qq
sudo apt-get install -y "./${DEB}"

echo "==> veracrypt --version"
veracrypt --version
echo "OK: VeraCrypt console installed."

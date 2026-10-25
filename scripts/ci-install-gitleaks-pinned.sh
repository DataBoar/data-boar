#!/usr/bin/env bash
# Install pinned gitleaks to a target directory (CI / operator); binary SHA256 fail-closed.
set -Eeuo pipefail

DEST="${1:-./gitleaks-install}"
mkdir -p "$DEST"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/db-tool-bootstrap.sh
source "$REPO_ROOT/scripts/db-tool-bootstrap.sh"

base="https://github.com/gitleaks/gitleaks/releases/download/v${DB_GITLEAKS_VERSION}"
tarball="gitleaks_${DB_GITLEAKS_VERSION}_linux_x64.tar.gz"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

curl -sSfL "${base}/${tarball}" -o "${work}/${tarball}"
tar -xzf "${work}/${tarball}" -C "$work" gitleaks
db_verify_gitleaks_binary_sha "${work}/gitleaks"
install -m 0755 "${work}/gitleaks" "${DEST}/gitleaks"
echo "Installed gitleaks ${DB_GITLEAKS_VERSION} -> ${DEST}/gitleaks"

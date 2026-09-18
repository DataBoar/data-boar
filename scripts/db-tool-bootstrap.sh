#!/usr/bin/env bash
# Bootstrap pinned CLIs for local check-all parity with CI (issue #1933).
set -Eeuo pipefail

DB_BOOTSTRAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/tool-pins.sh
source "${DB_BOOTSTRAP_DIR}/tool-pins.sh"

DB_CACHE_DIR="${DB_CACHE_DIR:-${DB_BOOTSTRAP_DIR}/.cache}"

db_prepend_path() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  case ":${PATH}:" in
    *":${dir}:"*) ;;
    *) export PATH="${dir}:${PATH}" ;;
  esac
}

db_prepend_path "${HOME}/bin"
db_prepend_path "${HOME}/.local/bin"

db_verify_gitleaks_binary_sha() {
  local bin_path="$1"
  echo "${DB_GITLEAKS_LINUX_X64_BINARY_SHA256}  ${bin_path}" | sha256sum -c -
}

db_ensure_gitleaks() {
  if command -v gitleaks >/dev/null 2>&1 && gitleaks version 2>/dev/null | grep -qF "${DB_GITLEAKS_VERSION}"; then
    return 0
  fi
  mkdir -p "${DB_CACHE_DIR}"
  local base tarball bin
  base="https://github.com/gitleaks/gitleaks/releases/download/v${DB_GITLEAKS_VERSION}"
  tarball="gitleaks_${DB_GITLEAKS_VERSION}_linux_x64.tar.gz"
  bin="${DB_CACHE_DIR}/gitleaks"
  if [[ ! -x "$bin" ]]; then
    echo "check-all: downloading gitleaks v${DB_GITLEAKS_VERSION} to ${DB_CACHE_DIR}..." >&2
    curl -sSfL "${base}/${tarball}" -o "${DB_CACHE_DIR}/${tarball}"
    tar -xzf "${DB_CACHE_DIR}/${tarball}" -C "${DB_CACHE_DIR}" gitleaks
    db_verify_gitleaks_binary_sha "$bin"
    chmod +x "$bin"
  else
    db_verify_gitleaks_binary_sha "$bin"
  fi
  db_prepend_path "${DB_CACHE_DIR}"
  command -v gitleaks >/dev/null 2>&1
}

db_ensure_osv_scanner() {
  if command -v osv-scanner >/dev/null 2>&1; then
    if osv-scanner --version 2>/dev/null | grep -qF "${DB_OSV_SCANNER_VERSION}"; then
      return 0
    fi
  fi
  mkdir -p "${DB_CACHE_DIR}"
  local base download_path bin
  base="https://github.com/google/osv-scanner/releases/download/v${DB_OSV_SCANNER_VERSION}"
  download_path="${DB_CACHE_DIR}/osv-scanner.download"
  bin="${DB_CACHE_DIR}/osv-scanner"
  if [[ ! -x "$bin" ]]; then
    echo "check-all: downloading osv-scanner v${DB_OSV_SCANNER_VERSION} to ${DB_CACHE_DIR}..." >&2
    curl -sSfL "${base}/osv-scanner_linux_amd64" -o "$download_path"
    echo "${DB_OSV_SCANNER_LINUX_AMD64_SHA256}  ${download_path}" | sha256sum -c -
    mv "$download_path" "$bin"
    chmod +x "$bin"
  else
    echo "${DB_OSV_SCANNER_LINUX_AMD64_SHA256}  ${bin}" | sha256sum -c -
  fi
  db_prepend_path "${DB_CACHE_DIR}"
  command -v osv-scanner >/dev/null 2>&1
}

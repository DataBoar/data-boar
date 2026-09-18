#!/usr/bin/env bash
# Pinned third-party CLI versions + fail-closed SHA256 (issue #1933).
# Sourced by db-tool-bootstrap.sh, CI workflow run blocks, and regression tests.
set -Eeuo pipefail

export DB_GITLEAKS_VERSION="${DB_GITLEAKS_VERSION:-8.30.1}"
# linux_x64 binary inside official release tarball (not checksums.txt self-verify).
export DB_GITLEAKS_LINUX_X64_BINARY_SHA256="${DB_GITLEAKS_LINUX_X64_BINARY_SHA256:-88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509}"

export DB_OSV_SCANNER_VERSION="${DB_OSV_SCANNER_VERSION:-2.6.0}"
export DB_OSV_SCANNER_LINUX_AMD64_SHA256="${DB_OSV_SCANNER_LINUX_AMD64_SHA256:-ca69b3d3cd08f889a49dc0a383122f71cc528b83803671df5fd874d97485b108}"

# Maintainer-owned allowlist (not deletable root .gitleaks.toml bypass).
export DB_GITLEAKS_POLICY_CONFIG="${DB_GITLEAKS_POLICY_CONFIG:-security/gitleaks.toml}"

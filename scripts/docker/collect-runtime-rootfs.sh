#!/bin/bash
# Bundle a minimal rootfs layer for distroless runtime (issue #1028).
# Run inside the runtime-assembler stage (Debian 13 + runtime .deb libs + /usr/local).
# Usage: collect-runtime-rootfs.sh <export-dir>
set -euo pipefail

EXPORT="${1:?export directory required}"
mkdir -p "${EXPORT}"

copy_path() {
    local src="$1"
    if [[ ! -e "${src}" ]]; then
        return 0
    fi
    local dest="${EXPORT}${src}"
    mkdir -p "$(dirname "${dest}")"
    cp -a "${src}" "${dest}"
}

# Python install + console scripts (pip/wheel already removed in Dockerfile RUN).
copy_path /usr/local

# TLS for httpx / connectors (PLAN_IMAGE_HARDENING.md gap: verify TLS smoke in PR-A).
copy_path /etc/ssl/certs/ca-certificates.crt
# tzdata: not bundled yet — container defaults to UTC unless operator sets TZ= (see PLAN gap table).

# unixODBC driver registration (pyodbc).
for f in /etc/odbcinst.ini /etc/odbc.ini; do
    copy_path "${f}"
done

collect_ldd_paths() {
    local bin="$1"
    ldd "${bin}" 2>/dev/null | awk '
        /=> \// { if ($3 != "") print $3 }
        /^\// { print $1 }
    ' || true
}

DEPS_FILE="$(mktemp)"
trap 'rm -f "${DEPS_FILE}"' EXIT

add_deps_from() {
    local target="$1"
    [[ -f "${target}" ]] || return 0
    collect_ldd_paths "${target}" >> "${DEPS_FILE}"
}

# Extension modules and interpreter.
while IFS= read -r -d '' so; do
    add_deps_from "${so}"
done < <(find /usr/local/lib/python3.13/site-packages -name '*.so' -print0 2>/dev/null || true)

for py in /usr/local/bin/python3.13 /usr/local/bin/python3; do
    add_deps_from "${py}"
done

# DB client libraries installed via apt in assembler.
while IFS= read -r -d '' lib; do
    add_deps_from "${lib}"
done < <(
    find /usr/lib /lib -type f \( \
        -name 'libpq.so*' -o \
        -name 'libffi.so*' -o \
        -name 'libodbc*.so*' -o \
        -name 'libmariadb.so*' -o \
        -name 'libssl.so*' -o \
        -name 'libcrypto.so*' \
    \) -print0 2>/dev/null || true
)

sort -u "${DEPS_FILE}" | while read -r lib; do
    [[ -n "${lib}" && -f "${lib}" ]] || continue
    # Distroless cc-debian13 ships glibc; skip core libc to avoid clobbering the base.
    case "${lib}" in
        /lib/*/libc.so.*|/lib/*/libm.so.*|/lib/*/libpthread.so.*|/lib/*/libdl.so.*|/lib/*/librt.so.*|/lib/*/libresolv.so.*)
            continue
            ;;
    esac
    copy_path "${lib}"
done

# Writable data mount point (nonroot uid 65532 = distroless :nonroot).
mkdir -p "${EXPORT}/data"
chown 65532:65532 "${EXPORT}/data"

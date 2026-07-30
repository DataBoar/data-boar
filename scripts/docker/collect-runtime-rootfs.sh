#!/bin/bash
# Bundle a minimal rootfs layer for distroless runtime (issue #1028).
# Run inside the runtime-assembler stage (Debian 13 + runtime .deb libs + /usr/local).
# Usage: collect-runtime-rootfs.sh <export-dir>
#
# Debian 13 / distroless cc-debian13 use usr-merge: /lib and /lib64 are symlinks into /usr.
# Never write ${EXPORT}/lib or ${EXPORT}/lib64 (real dirs) — BuildKit COPY fails on symlink targets.
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

# Map runtime library paths to usr-merged destinations under EXPORT.
usrmerge_dest() {
    local src="$1"
    case "${src}" in
        /lib/*) echo "/usr${src}" ;;
        /lib64/*) echo "/usr${src}" ;;
        *) echo "${src}" ;;
    esac
}

copy_lib_path() {
    local src="$1"
    [[ -f "${src}" || -L "${src}" ]] || return 0
    local dest_path
    dest_path="$(usrmerge_dest "${src}")"
    local dest="${EXPORT}${dest_path}"
    mkdir -p "$(dirname "${dest}")"
    cp -a "${src}" "${dest}"
    # ldd often reports the SONAME symlink; ship the real object too or the link is dangling in distroless.
    if [[ -L "${src}" ]]; then
        local real
        real="$(readlink -f "${src}" || true)"
        if [[ -n "${real}" && -f "${real}" && "${real}" != "${src}" ]]; then
            local real_dest_path real_dest
            real_dest_path="$(usrmerge_dest "${real}")"
            real_dest="${EXPORT}${real_dest_path}"
            mkdir -p "$(dirname "${real_dest}")"
            cp -a "${real}" "${real_dest}"
        fi
    fi
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

# Extension modules and interpreter (site-packages + stdlib lib-dynload — e.g. _sqlite3 → libsqlite3).
while IFS= read -r -d '' so; do
    add_deps_from "${so}"
done < <(
    find /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/lib-dynload \
        -name '*.so' -print0 2>/dev/null || true
)

for py in /usr/local/bin/python3.13 /usr/local/bin/python3; do
    add_deps_from "${py}"
done

# DB client libraries installed via apt in assembler (usr-merged paths only).
while IFS= read -r -d '' lib; do
    add_deps_from "${lib}"
done < <(
    find /usr/lib /usr/lib64 -type f \( \
        -name 'libpq.so*' -o \
        -name 'libffi.so*' -o \
        -name 'libodbc*.so*' -o \
        -name 'libmariadb.so*' -o \
        -name 'libssl.so*' -o \
        -name 'libcrypto.so*' \
    \) -print0 2>/dev/null || true
)

# Avoid pipe-subshell: copy every ldd dependency (and SONAME symlink targets) into EXPORT.
while read -r lib; do
    [[ -n "${lib}" && -e "${lib}" ]] || continue
    # Distroless cc-debian13 ships glibc; skip core libc to avoid clobbering the base.
    case "${lib}" in
        /lib/*/libc.so.*|/lib/*/libm.so.*|/lib/*/libpthread.so.*|/lib/*/libdl.so.*|/lib/*/librt.so.*|/lib/*/libresolv.so.*|/usr/lib/*/libc.so.*|/usr/lib/*/libm.so.*|/usr/lib/*/libpthread.so.*|/usr/lib/*/libdl.so.*|/usr/lib/*/librt.so.*|/usr/lib/*/libresolv.so.*)
            continue
            ;;
    esac
    copy_lib_path "${lib}"
done < <(sort -u "${DEPS_FILE}")

# Writable data mount point (nonroot uid 65532 = distroless :nonroot).
mkdir -p "${EXPORT}/data"
chown 65532:65532 "${EXPORT}/data"

# Guard: usr-merge safety — must not ship real /lib or /lib64 trees.
if [[ -d "${EXPORT}/lib" || -d "${EXPORT}/lib64" ]]; then
    echo "collect-runtime-rootfs: refusing usr-merge conflict (${EXPORT}/lib or lib64 is a directory)" >&2
    exit 1
fi

# Fail closed: CPython sqlite3 (integrity_anchor / data-boar --version) needs a resolvable libsqlite3.
# SONAME symlink alone is not enough — the real object must be present (distroless has no apt).
sqlite_link=""
for candidate in \
    "${EXPORT}/usr/lib/x86_64-linux-gnu/libsqlite3.so.0" \
    "${EXPORT}/lib/x86_64-linux-gnu/libsqlite3.so.0"; do
    if [[ -e "${candidate}" || -L "${candidate}" ]]; then
        sqlite_link="${candidate}"
        break
    fi
done
if [[ -z "${sqlite_link}" ]]; then
    echo "collect-runtime-rootfs: FATAL missing libsqlite3.so.0 (ldd lib-dynload/_sqlite3*.so)" >&2
    exit 1
fi
if [[ -L "${sqlite_link}" ]]; then
    sqlite_real="$(readlink -f "${sqlite_link}" || true)"
    if [[ -z "${sqlite_real}" || ! -f "${sqlite_real}" ]]; then
        echo "collect-runtime-rootfs: FATAL dangling libsqlite3.so.0 -> ${sqlite_real:-unresolved}" >&2
        exit 1
    fi
fi
echo "collect-runtime-rootfs: OK libsqlite3 via ${sqlite_link}"

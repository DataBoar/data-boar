#!/usr/bin/env bash
# Validate the #1404 void-packages overlay inside a Podman Void container.
# Default: xbps-src show (template parse). --build needs a populated staging tree.
# No lab metal. No real hostnames. musl --build needs a musl staging tree — glibc
# bytes must not be installed onto musl.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="show"
LIBC="glibc"
STAGING="${ROOT}/packaging/nfpm/staging"
CORPUS=""
IMAGE_GLIBC="${VOID_XBPS_IMAGE_GLIBC:-ghcr.io/void-linux/void-glibc:latest}"
IMAGE_MUSL="${VOID_XBPS_IMAGE_MUSL:-ghcr.io/void-linux/void-musl:latest}"

usage() {
  cat <<'EOF'
Usage: scripts/void-xbps-podman-validate.sh [--show|--build] [--libc glibc|musl] [--staging DIR] [--corpus DIR]

  --show     Overlay template into a void-packages clone and run ./xbps-src show data-boar (default)
  --build    Also ./xbps-src pkg data-boar (requires FILESDIR/staging with embedded cp314t)
  --libc     glibc (default) or musl — musl --build needs a musl-populated staging tree
  --staging  Staging root (default: packaging/nfpm/staging)
  --corpus   After a successful --build + install, scan this directory and print finding count

Environment: VOID_XBPS_IMAGE_GLIBC, VOID_XBPS_IMAGE_MUSL
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --show) MODE="show"; shift ;;
    --build) MODE="build"; shift ;;
    --libc)
      LIBC="${2:-}"
      shift 2
      ;;
    --staging)
      STAGING="${2:-}"
      shift 2
      ;;
    --corpus)
      CORPUS="${2:-}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${LIBC}" != "glibc" && "${LIBC}" != "musl" ]]; then
  echo "ERROR: --libc must be glibc or musl" >&2
  exit 2
fi

ENGINE=""
if command -v podman >/dev/null 2>&1; then
  ENGINE=podman
elif command -v docker >/dev/null 2>&1; then
  ENGINE=docker
  echo "NOTE: podman not found; using docker for the same official Void image." >&2
else
  echo "ERROR: podman (preferred) or docker is required for Void xbps validation (not lab metal)." >&2
  exit 1
fi

IMAGE="${IMAGE_GLIBC}"
if [[ "${LIBC}" == "musl" ]]; then
  IMAGE="${IMAGE_MUSL}"
fi

if [[ "${MODE}" == "build" ]]; then
  if [[ ! -x "${STAGING}/usr/lib/data-boar/python3.14t/bin/python3.14t" ]]; then
    echo "ERROR: --build refused — missing embedded interpreter under ${STAGING}" >&2
    echo "Run: bash scripts/native-nfpm-populate-staging.sh  (glibc x86-64)" >&2
    echo "musl --build needs a musl staging tree; do not reuse glibc bytes." >&2
    exit 1
  fi
  if [[ "${LIBC}" == "musl" ]]; then
    echo "NOTE: musl --build requires staging built for musl, not the glibc nfpm tree." >&2
  fi
fi

echo "void-xbps-podman-validate: engine=${ENGINE} mode=${MODE} libc=${LIBC} image=${IMAGE}"

ENGINE_ARGS=(
  run --rm
  -v "${ROOT}:/src:ro"
  -e MODE="${MODE}"
  -e CORPUS="${CORPUS}"
)
if [[ "${ENGINE}" == "podman" ]]; then
  ENGINE_ARGS+=(--security-opt label=disable)
fi
if [[ -d "${STAGING}" ]]; then
  ENGINE_ARGS+=(-v "${STAGING}:/staging:ro")
fi

"${ENGINE}" "${ENGINE_ARGS[@]}" \
  "${IMAGE}" \
  /bin/sh -c '
# Void images: /bin/sh is dash. pipefail is a bashism.
# bash: xbps-src shebang #!/bin/bash. util-linux: getopt + runuser.
# shadow: useradd. xbps-src refuses to run as root.
set -eu
command -v xbps-install >/dev/null
xbps-install -Syu git curl ca-certificates bash util-linux shadow >/dev/null
command -v bash >/dev/null
command -v getopt >/dev/null
command -v useradd >/dev/null
command -v runuser >/dev/null
useradd -m -U builder
WORKDIR="$(mktemp -d)"
cd "${WORKDIR}"
git clone --depth 1 https://github.com/void-linux/void-packages.git
cd void-packages
mkdir -p srcpkgs
cp -a /src/packaging/void/generated/srcpkgs/data-boar srcpkgs/data-boar
if [ -d /staging/usr ]; then
  mkdir -p srcpkgs/data-boar/files/staging
  cp -a /staging/. srcpkgs/data-boar/files/staging/
fi
while IFS= read -r name; do
  [ -n "${name}" ] || continue
  ln -sfn data-boar "srcpkgs/${name}"
done < /src/packaging/void/generated/srcpkgs/SUBPACKAGE_LINKS.txt
chown -R builder:builder "${WORKDIR}"
runuser -u builder -- ./xbps-src show data-boar
if [ "${MODE}" = "build" ]; then
  runuser -u builder -- ./xbps-src binary-bootstrap
  runuser -u builder -- ./xbps-src pkg data-boar
  echo "xbps-src pkg data-boar: OK"
  if [ -n "${CORPUS}" ] && [ -d "/src/${CORPUS#/}" ]; then
    echo "corpus scan is operator-side after xbps-install from hostdir/binpkgs"
  fi
fi
'

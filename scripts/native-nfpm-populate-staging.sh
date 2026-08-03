#!/usr/bin/env bash
# Populate packaging/nfpm/staging/ with a real cp314t embed + layer-1 wheelhouse (#1437).
#
# Fail-closed: network failures or missing assets abort (no fake payload).
# Does not commit the embed tree — CI only (see .gitignore).
#
# Env (optional):
#   UV_VERSION / UV_SHA256     — uv CLI pin (default matches Dockerfile.nogil)
#   UV_PYTHON                 — freethreaded request (default 3.14.6+freethreaded)
#   WHEELHOUSE_TAG            — hosted wheelhouse release tag
#   NFPM_STAGING_ROOT         — override staging root (tests)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

UV_VERSION="${UV_VERSION:-0.12.0}"
UV_SHA256="${UV_SHA256:-eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9}"
UV_PYTHON="${UV_PYTHON:-3.14.6+freethreaded}"
WHEELHOUSE_TAG="${WHEELHOUSE_TAG:-wheelhouse-x86-64-v1-2026-07-29}"
STAGING_ROOT="${NFPM_STAGING_ROOT:-${ROOT}/packaging/nfpm/staging}"
PREFIX_STAGING="${STAGING_ROOT}/usr/lib/data-boar"
PY_PREFIX="${PREFIX_STAGING}/python3.14t"
UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-/tmp/uv-pythons-native-nfpm}"

echo "=== native-nfpm-populate-staging (#1437) ==="
echo "staging=${STAGING_ROOT}"
echo "uv_python=${UV_PYTHON} wheelhouse=${WHEELHOUSE_TAG}"

# --- uv CLI (pinned; same contract as Dockerfile.nogil) ---
UV_BIN_DIR="${UV_BIN_DIR:-${HOME}/.local/bin}"
mkdir -p "${UV_BIN_DIR}"
export PATH="${UV_BIN_DIR}:${PATH}"
if ! command -v uv >/dev/null 2>&1 || [[ "$(uv --version 2>/dev/null | awk '{print $2}')" != "${UV_VERSION}" ]]; then
  echo "=== installing uv ${UV_VERSION} → ${UV_BIN_DIR} ==="
  tmp="$(mktemp -d)"
  curl -fsSL \
    "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
    -o "${tmp}/uv.tgz"
  echo "${UV_SHA256}  ${tmp}/uv.tgz" | sha256sum -c -
  tar -xzf "${tmp}/uv.tgz" -C "${tmp}"
  install -m 0755 "${tmp}/uv-x86_64-unknown-linux-gnu/uv" "${UV_BIN_DIR}/uv"
  rm -rf "${tmp}"
fi
uv --version

# --- freethreaded CPython into product prefix ---
echo "=== uv python install ${UV_PYTHON} ==="
export UV_PYTHON_INSTALL_DIR
mkdir -p "${UV_PYTHON_INSTALL_DIR}"
uv python install "${UV_PYTHON}"
PYROOT="$(find "${UV_PYTHON_INSTALL_DIR}" -maxdepth 1 -type d -name 'cpython-*freethreaded*' | sort | tail -1)"
if [[ -z "${PYROOT}" || ! -x "${PYROOT}/bin/python3.14t" ]]; then
  echo "ERROR: freethreaded CPython not found under ${UV_PYTHON_INSTALL_DIR}" >&2
  exit 1
fi

rm -rf "${PY_PREFIX}"
mkdir -p "${PREFIX_STAGING}"
cp -a "${PYROOT}/." "${PY_PREFIX}/"
test -x "${PY_PREFIX}/bin/python3.14t"
PYBIN="${PY_PREFIX}/bin/python3.14t"
# apply_wheelhouse_v1.sh invokes bare `python` — ensure it hits freethreaded.
if [[ ! -e "${PY_PREFIX}/bin/python" ]]; then
  ln -s python3.14t "${PY_PREFIX}/bin/python"
fi

# Drop PEP 668 marker so pip can install into the embed.
rm -f "${PY_PREFIX}/lib/python3.14t/EXTERNALLY-MANAGED" \
  "${PY_PREFIX}/lib/python3.14/EXTERNALLY-MANAGED" || true
"${PYBIN}" -m ensurepip --upgrade
"${PYBIN}" -c 'import sys; assert hasattr(sys, "_is_gil_enabled") and sys._is_gil_enabled() is False, sys.version'

# --- product + deps into embed site-packages ---
# SQLAlchemy C-ext re-enables GIL; force pure-Python (same as Dockerfile.nogil).
export DISABLE_SQLALCHEMY_CEXT=1
export PATH="$(dirname "${PYBIN}"):${PATH}"

echo "=== pip install requirements + data-boar (editable-style into embed) ==="
"${PYBIN}" -m pip install --no-cache-dir --upgrade "pip>=25.3"
"${PYBIN}" -m pip install --no-cache-dir -r "${ROOT}/requirements.txt"
"${PYBIN}" -m pip install --no-cache-dir --force-reinstall --no-binary sqlalchemy "sqlalchemy==2.0.50"
"${PYBIN}" -m pip install --no-cache-dir --no-deps "${ROOT}"

echo "=== apply wheelhouse layer-1 + boar_fast_filter cp314t ==="
# Preflight: layer-1 wheels must be reachable (fail-closed, no fake payload).
WH_BASE="https://github.com/DataBoar/data-boar-site/releases/download/${WHEELHOUSE_TAG}"
for whl in \
  "numpy-2.5.1-cp314-cp314t-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl" \
  "boar_fast_filter-0.1.0-cp314-cp314t-manylinux_2_28_x86_64.whl"
do
  code="$(curl -fsSIL -o /dev/null -w '%{http_code}' "${WH_BASE}/${whl}" || true)"
  if [[ "${code}" != "200" ]]; then
    echo "ERROR: wheelhouse asset not downloadable (HTTP ${code}): ${WH_BASE}/${whl}" >&2
    exit 1
  fi
done

WHEELHOUSE_TAG="${WHEELHOUSE_TAG}" SKIP_POPCNT_GATE=1 \
  bash "${ROOT}/scripts/docker/apply_wheelhouse_v1.sh"

"${PYBIN}" -c 'import sys; assert sys._is_gil_enabled() is False, "GIL re-enabled after wheelhouse"'
"${PYBIN}" -c 'import numpy, scipy, sklearn, pandas, boar_fast_filter; print("layer1_ok", numpy.__version__)'

# --- launcher + config ---
mkdir -p "${STAGING_ROOT}/usr/bin" "${STAGING_ROOT}/etc/data-boar"
cat > "${STAGING_ROOT}/usr/bin/data-boar" <<'EOF'
#!/bin/sh
# Native Enterprise channel launcher (ADR-0084). Presence of cp314t does NOT
# unlock Enterprise — worker caps (#551) + pro_prefilter_accel remain the gates.
export DISABLE_SQLALCHEMY_CEXT=1
exec /usr/lib/data-boar/python3.14t/bin/python3.14t -m data_boar "$@"
EOF
chmod +x "${STAGING_ROOT}/usr/bin/data-boar"

if [[ -f "${ROOT}/deploy/config.example.yaml" ]]; then
  cp -f "${ROOT}/deploy/config.example.yaml" \
    "${STAGING_ROOT}/etc/data-boar/config.example.yaml"
fi

echo "=== smoke: -m data_boar --version (staging tree) ==="
"${PYBIN}" -m data_boar --version

# Guard: no placeholder text left as the interpreter binary.
if file "${PYBIN}" | grep -qi 'ASCII text\|empty'; then
  echo "ERROR: python3.14t still looks like a placeholder text file" >&2
  exit 1
fi

echo "=== staging populated (real cp314t + wheelhouse) ==="

#!/bin/bash
# Post-build smoke for hardened release image (#1028 PR-A).
# Usage: ./scripts/docker/docker-image-smoke.sh <image:tag> [expected_public_version]
#
# Checks: public version line, no maturity-octet leak, boar_fast_filter import, TLS (httpx -> HTTPS).
set -euo pipefail

IMAGE="${1:?image ref required (e.g. data_boar:lab)}"
VERSION="${2:-}"

PYTHON="/usr/local/bin/python3.13"
RUN=(podman run --rm "${IMAGE}" "${PYTHON}")

if ! command -v podman >/dev/null 2>&1; then
    echo "docker-image-smoke: podman not in PATH" >&2
    exit 127
fi

echo "=== docker-image-smoke: ${IMAGE} ==="

OUT="$("${RUN[@]}" -c 'from core.about import _package_version; print(_package_version())')"
echo "public version -> ${OUT}"

if [[ -n "${VERSION}" ]]; then
    grep -qw "${VERSION}" <<<"${OUT}" || {
        echo "FAIL: expected public version token ${VERSION}" >&2
        exit 1
    }
    if grep -Eq "${VERSION}\\.[0-9]" <<<"${OUT}"; then
        echo "FAIL: maturity octet leaked in public version string" >&2
        exit 1
    fi
fi

"${RUN[@]}" -c "import boar_fast_filter; print('boar_fast_filter:', boar_fast_filter.__name__)"

"${RUN[@]}" -c "
import httpx
resp = httpx.get('https://example.com', timeout=20.0, follow_redirects=True)
resp.raise_for_status()
assert resp.status_code == 200, resp.status_code
print('tls_probe: ok status=', resp.status_code)
"

echo "=== docker-image-smoke: PASS ==="

# LGPD/GDPR/CCPA audit app. Default: web API + frontend (dashboard, reports, config UI).
# Override CMD to run CLI one-shot scan (see docs/deploy/DEPLOY.md).
# Multi-stage: builder (toolchain) -> runtime-assembler (bundle libs) -> distroless nonroot (#1028).

# -----------------------------------------------------------------------------
# Stage 1: build Python extensions and install dependencies
# -----------------------------------------------------------------------------
# Rolling 3.14 slim (Debian 13 / trixie): aligns with CI matrix + field-tested
# wheelhouse cells; licensing enforcement gate green (#551 / cluster closed).
# Digest pin (ADR-0074 / #988): Dependabot docker ecosystem proposes digest bumps.
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ pkg-config curl ca-certificates binutils \
    libpq-dev libffi-dev libssl-dev unixodbc-dev default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY . /app

# Hosted x86-64-v1 wheelhouse (DataBoar/data-boar-site). Override for offline builds.
ARG WHEELHOUSE_TAG=wheelhouse-x86-64-v1-2026-07-29

RUN pip uninstall -y wheel || true && \
    pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --force-reinstall "wheel>=0.46.2" && \
    python -c "import wheel; import sys; sys.exit(0 if tuple(map(int, wheel.__version__.split('.'))) >= (0,46,2) else 1)" && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir --no-deps -e /app && \
    # Lean base only: sql-community + mssql (pymssql) + oracle from pyproject extras.
    # Remaining extras: mount ABI-compatible wheels at /extras (#1400/#1399) — not fat image.
    # ODBC MSSQL: mount ``mssql-pyodbc`` wheels at runtime (#1588).
    pip install --no-cache-dir "/app[sql-community,mssql,oracle]" && \
    python /app/scripts/generate_extras_manifest.py --probe --write /app/EXTRAS_MANIFEST.json && \
    WHEELHOUSE_TAG="${WHEELHOUSE_TAG}" bash /app/scripts/docker/apply_wheelhouse_v1.sh && \
    PY_XY="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" && \
    rm -rf "/tmp/wheelhouse-v1-glibc-cp$(python -c 'import sys; print(f"{sys.version_info.major}{sys.version_info.minor}")')" && \
    (find "/usr/local/lib/python${PY_XY}/site-packages" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true) && \
    (find "/usr/local/lib/python${PY_XY}/site-packages" -name "*.pyc" -delete 2>/dev/null || true)

# -----------------------------------------------------------------------------
# Stage 2: assemble runtime rootfs (shell stage — not shipped)
# -----------------------------------------------------------------------------
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS runtime-assembler

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libffi8 unixodbc libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

RUN PY_XY="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" && \
    ln -sf "python${PY_XY}" /usr/local/bin/python3 && \
    ln -sf "python${PY_XY}" /usr/local/bin/python

# Runtime extras mount point (#1400): owned by distroless nonroot (65532); no --user 0.
RUN mkdir -p /extras && chown 65532:65532 /extras

# No pip/wheel/setuptools in the release image (app does not install packages at runtime, #1028).
RUN PY_XY="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" && \
    "/usr/local/bin/python${PY_XY}" -m pip uninstall -y pip wheel setuptools 2>/dev/null || true && \
    rm -f /usr/local/bin/pip /usr/local/bin/pip3 "/usr/local/bin/pip${PY_XY}" /usr/local/bin/wheel 2>/dev/null || true

COPY scripts/docker/collect-runtime-rootfs.sh /tmp/collect-runtime-rootfs.sh
RUN chmod +x /tmp/collect-runtime-rootfs.sh && /tmp/collect-runtime-rootfs.sh /rootfs

# -----------------------------------------------------------------------------
# Stage 3: minimal distroless runtime (nonroot uid 65532, no shell/apt)
# -----------------------------------------------------------------------------
# gcr.io/distroless/cc-debian13:nonroot — Debian 13 matches python:3.14-slim (trixie) glibc.
# Human tag comment: cc-debian13:nonroot (#1028 / PLAN_IMAGE_HARDENING.md).
FROM gcr.io/distroless/cc-debian13:nonroot@sha256:a77defd6fedbb3392b175ba8ea3d1c22be963c1597c248c3ba987ddd80bfb512

LABEL org.opencontainers.image.description="LGPD/GDPR/CCPA audit. Default: web API and frontend on port 8088. Override command for CLI one-shot."

WORKDIR /app

COPY --from=runtime-assembler /rootfs /
COPY --chown=65532:65532 . .
COPY --from=builder --chown=65532:65532 /app/EXTRAS_MANIFEST.json /app/EXTRAS_MANIFEST.json

ENV CONFIG_PATH=/data/config.yaml
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Runtime extras extension (#1400): mount prebuilt ABI-compatible wheels here.
ENV PYTHONPATH=/extras:/app
# Stable fingerprint in container pools (Enterprise); empty = hostname-derived (Pro/Pro+).
ENV DATA_BOAR_MACHINE_SEED=
VOLUME ["/extras"]

USER 65532:65532

EXPOSE 8088

# Distroless has no shell: JSON exec form only. A shell-form probe would fail.
# Probe GET /health on loopback (always public). Matches default CMD port 8088.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["/usr/local/bin/python3.14", "-c", "import urllib.request, sys; r = urllib.request.urlopen('http://127.0.0.1:8088/health', timeout=8); sys.exit(0 if r.status == 200 else 1)"]

CMD ["/usr/local/bin/python3.14", "main.py", "--config", "/data/config.yaml", "--web", "--port", "8088", "--allow-insecure-http"]

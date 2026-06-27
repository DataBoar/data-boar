# LGPD/GDPR/CCPA audit app. Default: web API + frontend (dashboard, reports, config UI).
# Override CMD to run CLI one-shot scan (see docs/deploy/DEPLOY.md).
# Multi-stage: builder (toolchain) -> runtime-assembler (bundle libs) -> distroless nonroot (#1028).

# -----------------------------------------------------------------------------
# Stage 1: build Python extensions and install dependencies
# -----------------------------------------------------------------------------
# Rolling 3.13 slim (Debian 13 / trixie): aligns with CI, requires-python >=3.12.
# Digest pin (ADR-0074 / #988): Dependabot docker ecosystem proposes digest bumps.
FROM python:3.14-slim@sha256:63a4c7f612a00f92042cbdcc7cdc6a306f38485af0a200b9c89de7d9b1607d15 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ pkg-config curl ca-certificates \
    libpq-dev libffi-dev libssl-dev unixodbc-dev default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY . /app

RUN pip uninstall -y wheel || true && \
    pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --force-reinstall "wheel>=0.46.2" && \
    python -c "import wheel; import sys; sys.exit(0 if tuple(map(int, wheel.__version__.split('.'))) >= (0,46,2) else 1)" && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir --no-deps -e /app && \
    pip install --no-cache-dir \
        "psycopg2-binary>=2.9.11" "pymysql>=1.2.0" "mariadb>=1.1.14" \
        "pyodbc>=5.3.0" "oracledb>=4.0.1" && \
    (find /usr/local/lib/python3.13/site-packages -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true) && \
    (find /usr/local/lib/python3.13/site-packages -name "*.pyc" -delete 2>/dev/null || true)

# boar_fast_filter (PyO3): build against glibc in builder; wheel lands in site-packages (#1028 PR-A).
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable \
    && . /root/.cargo/env \
    && pip install --no-cache-dir "maturin>=1.14.0" \
    && cd /app/rust/boar_fast_filter \
    && maturin build --release -o /tmp/boar-wheels \
    && pip install --no-cache-dir /tmp/boar-wheels/boar_fast_filter*.whl \
    && python -c "import boar_fast_filter" \
    && rm -rf /root/.cargo/registry /root/.cargo/git /tmp/boar-wheels

# -----------------------------------------------------------------------------
# Stage 2: assemble runtime rootfs (shell stage — not shipped)
# -----------------------------------------------------------------------------
FROM python:3.14-slim@sha256:63a4c7f612a00f92042cbdcc7cdc6a306f38485af0a200b9c89de7d9b1607d15 AS runtime-assembler

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libffi8 unixodbc libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

RUN ln -sf python3.13 /usr/local/bin/python3 && ln -sf python3.13 /usr/local/bin/python

# No pip/wheel/setuptools in the release image (app does not install packages at runtime, #1028).
RUN /usr/local/bin/python3.13 -m pip uninstall -y pip wheel setuptools 2>/dev/null || true && \
    rm -f /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13 /usr/local/bin/wheel 2>/dev/null || true

COPY scripts/docker/collect-runtime-rootfs.sh /tmp/collect-runtime-rootfs.sh
RUN chmod +x /tmp/collect-runtime-rootfs.sh && /tmp/collect-runtime-rootfs.sh /rootfs

# -----------------------------------------------------------------------------
# Stage 3: minimal distroless runtime (nonroot uid 65532, no shell/apt)
# -----------------------------------------------------------------------------
# gcr.io/distroless/cc-debian13:nonroot — Debian 13 matches python:3.13-slim glibc (not cc-debian12).
# Human tag comment: cc-debian13:nonroot (#1028 / PLAN_IMAGE_HARDENING.md).
FROM gcr.io/distroless/cc-debian13:nonroot@sha256:7f2a0e5b50575d355720a9d7ca9c871124780eb6a1dc0dbd70a67d5fd11629d2

LABEL org.opencontainers.image.description="LGPD/GDPR/CCPA audit. Default: web API and frontend on port 8088. Override command for CLI one-shot."

WORKDIR /app

COPY --from=runtime-assembler /rootfs /
COPY --chown=65532:65532 . .

ENV CONFIG_PATH=/data/config.yaml
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

USER 65532:65532

EXPOSE 8088

CMD ["/usr/local/bin/python3.13", "main.py", "--config", "/data/config.yaml", "--web", "--port", "8088", "--allow-insecure-http"]

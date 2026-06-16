# LGPD/GDPR/CCPA audit app. Default: web API + frontend (dashboard, reports, config UI).
# Override CMD to run CLI one-shot scan (see docs/deploy/DEPLOY.md).
# Multi-stage build: compile in builder, run in minimal runtime (no gcc/-dev in final image).

# -----------------------------------------------------------------------------
# Stage 1: build Python extensions and install dependencies
# -----------------------------------------------------------------------------
# Rolling 3.13 slim: aligns with CI (3.12 + 3.13), requires-python >=3.12, and Docker Scout
# base-image recommendations (fewer base CVEs vs. 3.12-slim at last scan).
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ pkg-config \
    libpq-dev libffi-dev libssl-dev unixodbc-dev default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
# `requirements.txt` (uv export --no-emit-project) is dependency-only and pip-installable:
# pinned + hashed wheels, no editable `-e .`. The project itself is installed separately below.
COPY . /app

# Upgrade pip/wheel in builder before deps (Scout: pip<25.3, wheel<=0.46.1 had CVEs; image inherits site-packages).
# Install the hashed dependency set first, then the project (--no-deps -e) so its console scripts resolve.
# Do not end this RUN with `; true` — it would mask a failed `pip install`.
RUN pip uninstall -y wheel || true && \
    pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --force-reinstall "wheel>=0.46.2" && \
    python -c "import wheel; import sys; sys.exit(0 if tuple(map(int, wheel.__version__.split('.'))) >= (0,46,2) else 1)" && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir --no-deps -e /app && \
    (find /usr/local/lib/python3.13/site-packages -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true) && \
    (find /usr/local/lib/python3.13/site-packages -name "*.pyc" -delete 2>/dev/null || true)

# -----------------------------------------------------------------------------
# Stage 2: minimal runtime (no build tools, only runtime libs + app)
# -----------------------------------------------------------------------------
FROM python:3.13-slim

LABEL org.opencontainers.image.description="LGPD/GDPR/CCPA audit. Default: web API and frontend on port 8088. Override command for CLI one-shot."

# Runtime libs only (no -dev, no build-essential). Required by compiled wheels:
# libpq5=PostgreSQL, libffi8=cffi/cryptography, unixodbc=pyodbc, libmariadb3=mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libffi8 unixodbc libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Optional rich media (not installed by default — keeps image small): if you set
# file_scan.scan_image_ocr or need ffprobe for video tags, extend this stage with e.g.
# tesseract-ocr, tesseract-ocr-eng, ffmpeg (provides ffprobe), and pip install ".[richmedia]".

WORKDIR /app

# Copy installed packages from builder (no gcc/dev in this image)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Re-assert pip/wheel in the runtime layer so Docker Scout does not flag stale tooling copied from
# older builder caches (CVEs on wheel<=0.46.1, pip<25.3). App deps already live under site-packages.
RUN pip uninstall -y wheel || true && \
    pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --force-reinstall "wheel>=0.46.2" && \
    python -c "import wheel; import sys; sys.exit(0 if tuple(map(int, wheel.__version__.split('.'))) >= (0,46,2) else 1)"

# Copy application code
COPY . .

ENV CONFIG_PATH=/data/config.yaml
ENV PYTHONUNBUFFERED=1
# Docker image default: expose web API on all interfaces inside the container
# so published ports work from outside Docker Desktop/WSL host.
ENV API_HOST=0.0.0.0

RUN useradd -r -u 1000 -d /data appuser && \
    mkdir -p /data && chown -R appuser:appuser /data

USER appuser

EXPOSE 8088

# Default: web API and frontend. CLI one-shot: override with --entrypoint python and args.
# Plaintext HTTP with explicit opt-in (mount TLS cert/key and drop this flag for HTTPS).
CMD ["python", "main.py", "--config", "/data/config.yaml", "--web", "--port", "8088", "--allow-insecure-http"]

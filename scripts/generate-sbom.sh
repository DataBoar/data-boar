#!/usr/bin/env bash
# Generate CycloneDX SBOMs per ADR 0003 (Linux/macOS twin of generate-sbom.ps1).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> uv sync --group dev"
uv sync --group dev

echo "==> uv export -> requirements-sbom.txt"
uv export --no-emit-package pyproject.toml -o requirements-sbom.txt

echo "==> CycloneDX (Python)"
uv run cyclonedx-py requirements requirements-sbom.txt \
  --pyproject pyproject.toml \
  --sv 1.6 \
  --of JSON \
  --output-reproducible \
  -o sbom-python.cdx.json

echo "==> Merge Cargo.lock into application CycloneDX (#1950)"
uv run python scripts/application_sbom.py merge \
  --python-bom sbom-python.cdx.json \
  --out sbom-python.cdx.json \
  --canonical
uv run python scripts/application_sbom.py check --application sbom-python.cdx.json

echo "==> docker build -> data_boar:sbom"
docker build -t data_boar:sbom -f Dockerfile .

echo "==> Syft (image SBOM)"
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "${ROOT}:/out" \
  anchore/syft:v1.28.0 \
  scan docker:data_boar:sbom \
  -o cyclonedx-json=/out/sbom-docker-image.cdx.json

mkdir -p sbom
cp -f sbom-docker-image.cdx.json sbom/sbom-runtime.cdx.json
uv run python scripts/application_sbom.py check \
  --application sbom-python.cdx.json \
  --runtime sbom-docker-image.cdx.json

echo "==> emit-provenance (unsigned local record; not SLSA)"
uv run python scripts/emit_provenance.py emit --require-sboms
uv run python scripts/emit_provenance.py verify --require-sboms

echo "Done: sbom-python.cdx.json, sbom-docker-image.cdx.json, sbom/sbom-application.cdx.json, sbom/sbom-runtime.cdx.json, sbom/provenance-local.json"

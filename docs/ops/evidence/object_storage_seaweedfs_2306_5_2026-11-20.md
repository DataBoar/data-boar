# Object storage local proof — SeaweedFS (slice 2306.5, issue #2312)

**Date:** 2026-11-20 (operator workstation, America/Sao_Paulo).

**Branch:** `epic/s3-object-storage-reader` (read-only checkout; this evidence file only).

**Design:** `docs/desenho/2306.md` — local proof for R-3, R-5, R-8 against a real S3-compatible server.

This document is **evidence of what was run**, not a legal conclusion and does not claim regulatory completeness or protection against fines.

## Product under test

| Field | Value |
| ----- | ----- |
| Server product | SeaweedFS |
| Reported version | `30GB 4.54` (`weed version` inside the container) |
| Container image | `docker.io/chrislusf/seaweedfs:latest` |
| Image digest | `sha256:4b42c212543a0acd4c0e675215ecdcaf62a186ef98def76c7e12701871222d15` |
| Host OS | Debian 13 (kernel `7.2.12+deb13-amd64`, x86_64) |
| Podman | 5.4.2 |
| Data Boar | `uv run python main.py` on the epic branch; `licensing.mode: open` in ephemeral config |
| Acceptance regression | `uv run pytest tests/test_object_storage_acceptance.py -q` → **48 passed** (no product code changed) |

## Network and TLS

- Ephemeral assets under `~/.cache/claude-pm/2306.5/` only (certs, config, corpus, logs, SQLite, report `.xlsx`).
- Self-signed TLS for `127.0.0.1` + `SSL_CERT_FILE` pointing at the local CA (no `verify_ssl: false` in config).
- S3 HTTPS endpoint: `https://127.0.0.1:19443` with `allow_private_networks: true`, `driver: s3_compatible`, `addressing_style: path`, `region: us-east-1`.

## Commands (secrets `<redacted>`)

```bash
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ~/.cache/claude-pm/2306.5/server.key \
  -out ~/.cache/claude-pm/2306.5/server.crt -days 1 \
  -subj "/CN=127.0.0.1" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
cp ~/.cache/claude-pm/2306.5/server.crt ~/.cache/claude-pm/2306.5/ca.crt

podman run -d --name seaweed-2306-5 \
  -p 127.0.0.1:19443:19443 \
  -v ~/.cache/claude-pm/2306.5:/certs:Z \
  -v ~/.cache/claude-pm/2306.5/data:/data:Z \
  docker.io/chrislusf/seaweedfs:latest server \
  -dir=/data -filer -s3 \
  -s3.port.https=19443 -s3.ip.bind=0.0.0.0 \
  -s3.cert.file=/certs/server.crt -s3.key.file=/certs/server.key \
  -s3.config=/certs/s3.json \
  -s3.allowUntrustedRemoteEndpoints=true

export AWS_ACCESS_KEY_ID=<redacted>
export AWS_SECRET_ACCESS_KEY=<redacted>
export AWS_DEFAULT_REGION=us-east-1
aws --endpoint-url https://127.0.0.1:19443 \
  --ca-bundle ~/.cache/claude-pm/2306.5/ca.crt \
  s3 mb s3://databoar-sintetico

export DATA_BOAR_S3_ACCESS_KEY_ID=<redacted>
export DATA_BOAR_S3_SECRET_ACCESS_KEY=<redacted>
export SSL_CERT_FILE=~/.cache/claude-pm/2306.5/ca.crt
uv run python main.py --config ~/.cache/claude-pm/2306.5/config.yaml

podman rm -f seaweed-2306-5
```

## Real outputs (trimmed)

**ListObjectsV2 with `encoding-type=url`:** keys URL-encoded (`corpus/plus%2Bok.txt`, `corpus/%C3%A7%C3%A3o.txt`). Upload `corpus/a b.txt` → listed `corpus/a+b.txt`. Upload `corpus//dup.txt` → listed `corpus/dup.txt` (SeaweedFS; design P14).

**Scan log:** `listed=6 scanned=6 bytes=374` … `unsafe_key=0`.

**Build note:** the run used the epic branch, not a released build. The runtime printed `INTEGRITY TAMPER DETECTED … runtime self-marked -alpha (development / not CI-validated)` because the behaviour-critical modules diverge from the validated anchor, which is expected on an unreleased branch. This proof therefore covers the connector code on the branch, not a signed release.

**Target coverage:** `COMPLETE` — listed 6, scanned 6, not_scanned 0.

**Inventory technical:** `"server_header": "SeaweedFS 30GB 4.54"`.

**curl `Server`:** `SeaweedFS 30GB 4.54`.

## Requirements vs proof

| Id | Result | Notes |
| --- | --- | --- |
| R-3 | **PROVEN** | URL encoding + 6/6 coverage; `//` normalized by server |
| R-5 | **PROVEN** | Path style + `us-east-1` |
| R-8 | **PROVEN** | Server header captured |

## Not proven

Amazon S3, R2, MinIO (this run), SSE-KMS/IAM (R-4, R-7), performance, deliberate `SignatureDoesNotMatch` (not run).

## Operator artifacts

Ephemeral tree `~/.cache/claude-pm/2306.5/` (config, DB, report xlsx) — not in Git.

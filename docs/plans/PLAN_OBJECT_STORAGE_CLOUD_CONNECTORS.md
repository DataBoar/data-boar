# Plan: Object storage connectors (S3-class, Azure Blob, GCS)

**Status:** Deferred
**Date:** 2026-03-26
**Authors:** Fabio Leitao
**Priority:** H2

## Purpose

Enterprises increasingly store “data soup” in **cloud object storage**: **Amazon S3**, **S3-compatible APIs** (MinIO, Cloudflare R2, etc.), **Azure Blob Storage**, **Google Cloud Storage**. Today Data Boar scans **filesystem**, **SMB/WebDAV/SharePoint/NFS**, **databases**, **REST/API**, and optional **Snowflake**—but **not** blob buckets as first-class targets.

**Goal:** Operators can declare a target (e.g. `type: object_storage`, `driver: s3`) in `config.yaml`, run a scan, and receive the same **metadata-only findings** and Excel/report flow as for other connectors, with **least-privilege IAM**, **timeouts**, and **clear operator docs** (EN + pt-BR).

---

## Relationship to other plans

- **Compressed files / rich media:** Once objects are downloaded or streamed, reuse **existing** file pipeline (`file_scan`, `scan_compressed`, `use_content_type`, optional rich-media flags) where applicable. No duplicate format logic in the connector beyond **object listing + fetch**.
- **Data source inventory / CVE (optional):** Future `data_source_inventory` rows may record bucket region, encryption-at-rest hints, or public-access posture—coordinate with [PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md](PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md) when that work advances.
- **SAP / other connectors:** Same registry pattern (`core/connector_registry.py`); optional extras in `pyproject.toml` (e.g. `.[cloud]` with `boto3`, later `azure-storage-blob`, `google-cloud-storage`).

---

## Phased scope

### Phase 1 — **Amazon S3** (primary)

| #   | To-do                                                                                                                                                                                                                                                                                        | Status    |
| -   | -----                                                                                                                                                                                                                                                                                        | ------    |
| 1.1 | **Config schema:** `type: object_storage`, `driver: s3`, `bucket`, optional `prefix`, `region`, `endpoint_url` (for MinIO/R2), auth via **env** / **profile** / explicit keys only when documented as discouraged; align with `pass_from_env` patterns.                                      | ⬜ Pending |
| 1.2 | **Connector module:** `connectors/s3_object_storage_connector.py` (or `object_storage_connector.py` with driver dispatch): list objects (paginated), filter by extension / size cap, download to temp or stream, delegate to shared “scan file bytes/path” helpers used by share connectors. | ⬜ Pending |
| 1.3 | **Register** in `core/connector_registry.py`; engine wiring; optional-import guard + `[cloud]` extra.                                                                                                                                                                                        | ⬜ Pending |
| 1.4 | **Limits:** `max_objects`, `max_download_bytes`, per-object timeout, respect global connector timeouts; **no** full-bucket unbounded scan by default.                                                                                                                                        | ⬜ Pending |
| 1.5 | **Tests:** `moto` or MinIO container in CI (or heavy tests marked optional); unit tests for listing + one synthetic object path.                                                                                                                                                             | ⬜ Pending |
| 1.6 | **Docs:** `USAGE` / `TECH_GUIDE` / operator samples (EN + pt-BR); IAM policy example (least privilege); security note on **never** using overly broad `s3:*` for audit use.                                                                                                                  | ⬜ Pending |

### Phase 2 — **S3-compatible and Azure Blob**

| #   | To-do                                                                                                                   | Status    |
| -   | -----                                                                                                                   | ------    |
| 2.1 | Validate **MinIO** / custom `endpoint_url` + path-style vs virtual-hosted; document quirks.                             | ⬜ Pending |
| 2.2 | **Azure Blob:** `driver: azure_blob`, connection string or managed identity story (research); same finding shape as S3. | ⬜ Pending |

### Phase 3 — **Google Cloud Storage**

| #   | To-do                                                                                  | Status    |
| -   | -----                                                                                  | ------    |
| 3.1 | `driver: gcs`, bucket + prefix, ADC or JSON key path via env; list + download pattern. | ⬜ Pending |

---

## Security and compliance notes

- **Credentials:** Prefer **instance/profile/ workload identity** over long-lived keys; document rotation and `api_key_from_env`-style patterns for any secret-bearing config.
- **Data processing:** Same product rule as today—**metadata only** in findings; avoid logging object body content.
- **LGPD/GDPR:** Scanning a bucket may process **personal data** in the customer’s estate; operator docs should state **lawful basis / contract** and **DPA** expectations are the customer’s responsibility.
- **Public buckets:** Optional future flag to **warn** if bucket policy suggests public read (SDK-dependent); not a replacement for CSPM tools.

---

## Pitch / README

When **Phase 1** ships, add **S3-class object storage** to the “data soup” list in **README.md** / **README.pt_BR.md** and trim this plan’s “not started” wording in [PLANS_TODO.md](PLANS_TODO.md).

---

## Last updated

2026-03-25 — Plan created; implementation deferred to a dedicated feature slice.

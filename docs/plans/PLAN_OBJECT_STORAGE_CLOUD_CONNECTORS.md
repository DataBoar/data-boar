# Plan: Object storage connectors (S3-class, Azure Blob, GCS)

<!-- plans-hub-summary: Read-only object storage connector: provider-neutral common layer with S3 and S3-compatible drivers first, env-only credentials, pinned host per target, per-target limits with partial-coverage reporting; Azure Blob and GCS later as drivers; Enterprise tier. -->

**Status:** In progress (Phase 1, S3 and S3-compatible read connector, merged on `main` by PR [#2350](https://github.com/DataBoar/data-boar/pull/2350) on 2026-11-22; Phase 2, Azure Blob, in design: [#2307](https://github.com/DataBoar/data-boar/issues/2307); GCS not started)
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
| 1.1 | **Config schema:** `type: object_storage`, drivers `s3` / `s3_compatible`, `bucket`, optional `prefix`, `region`, `endpoint_url` (required on `s3_compatible`), auth **only** via `auth.*_from_env` ([#1977](https://github.com/DataBoar/data-boar/issues/1977)); no AWS credential chain or inline keys. | ✅ Epic #2306 |
| 1.2 | **Connector module:** `connectors/s3_object_storage_connector.py` (or `object_storage_connector.py` with driver dispatch): list objects (paginated), filter by extension / size cap, download to temp or stream, delegate to shared “scan file bytes/path” helpers used by share connectors. | ✅ `object_storage_connector.py` |
| 1.3 | **Register** in `core/connector_registry.py`; engine wiring; optional-import guard + `[cloud]` extra.                                                                                                                                                                                        | ✅ No `[cloud]` extra (SigV4 in-tree) |
| 1.4 | **Limits:** `max_objects`, `max_download_bytes`, per-object timeout, respect global connector timeouts; **no** full-bucket unbounded scan by default.                                                                                                                                        | ✅ Epic #2306 |
| 1.5 | **Tests:** `moto` or MinIO container in CI (or heavy tests marked optional); unit tests for listing + one synthetic object path.                                                                                                                                                             | ✅ Simulated S3 + SeaweedFS evidence (#2312) |
| 1.6 | **Docs:** `USAGE` / `TECH_GUIDE` / operator samples (EN + pt-BR); IAM policy example (least privilege); security note on **never** using overly broad `s3:*` for audit use.                                                                                                                  | ✅ Epic #2311 + README pitch (#2306) on branch; epic PR pending |

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

- **Credentials:** **Env-only** credential names on the target (`auth.*_from_env`); no instance profile, no IMDS chain, no shared credentials file. Document rotation in operator runbooks; customer injects keys at runtime.
- **Data processing:** Same product rule as today—**metadata only** in findings; avoid logging object body content.
- **LGPD/GDPR:** Scanning a bucket may process **personal data** in the customer’s estate; operator docs should state **lawful basis / contract** and **DPA** expectations are the customer’s responsibility.
- **Public buckets:** Optional future flag to **warn** if bucket policy suggests public read (SDK-dependent); not a replacement for CSPM tools.

---

## Pitch / README

**S3-class object storage** is in the README “data soup” paragraph on epic branch (**#2306**); after local **SeaweedFS 4.54** evidence ([#2312](https://github.com/DataBoar/data-boar/issues/2312)), README polish may cite that proof while **Amazon S3 / R2 / MinIO appliance** stay “not tested against the real service”. Trim “not implemented” rows in [PLANS_TODO.md](PLANS_TODO.md) when the epic PR merges.

---

## Last updated

2026-11-21 — Phase 1 implementation and 2306.4 documentation in progress on `epic/s3-object-storage-reader`.

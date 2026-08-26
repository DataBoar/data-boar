# Feature map by subscription tier

**Português (Brasil):** [PRICING.pt_BR.md](PRICING.pt_BR.md)

This page answers **what is gated at which tier**. It is **not** a price list. Amounts, discounts, and partner rates stay off the public tree.

**Source of truth:** `FEATURE_TIER_MAP` in `core/licensing/tier_features.py` (minimum tier per feature key). Tiers are **additive** in enforced mode: Pro includes Community keys; Enterprise includes Pro keys.

Go-to-market bands, worker **quantity** claims, and narrative packs: [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md). Policy draft: [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md). Token shape: [LICENSING_SPEC.md](LICENSING_SPEC.md). Operator how-to: [USAGE.md](USAGE.md).

Default development/CI is `licensing.mode: open` (all keys available). Gates apply when enforcement is on.

## Community / Pro / Enterprise (issue #610 columns)

Grouped from the registry. A cell is **included** when that column’s tier is **at least** the feature’s minimum.

| Capability group | Community | Pro | Enterprise |
| ---------------- | :-------: | :-: | :--------: |
| Filesystem scan; self-hosted SQL/NoSQL (`sqlite` / Postgres / MySQL / MariaDB / Mongo / Redis); generic REST/API connectors | Yes | Yes | Yes |
| Core detectors (CPF, RG, email, phone, name heuristic, CNPJ, address); compressed files; content-type check; synthetic-data testing | Yes | Yes | Yes |
| Reports XLSX and HTML; REST API; dashBOARd; Docker and Ansible deploy keys | Yes | Yes | Yes |
| OCR; PDF report; DPO-style compliance grade report; scheduled scans; dashboard RBAC (fixed); API-key UI; maturity self-assessment POC; email/Slack notifications; SBOM export; build-integrity verify; SQL findings sink; governance lens (Pro key) | — | Yes | Yes |
| Managed / corporate connectors (Power BI, HubSpot, SharePoint, Dataverse, WebDAV, SMB/CIFS, NFS, MSSQL, Oracle, Snowflake, SAP, S3, Azure Blob, GCS) | — | Yes | Yes |
| Custom PDF branding; Enterprise scheduler UI; Enterprise governance lens; multi-tenant; **SSO SAML**; PDF digital signature; scheduled PDF email; historical comparison; audit-log export; custom detectors; VCS connector; plugin/partner interface; partner provider driver; remediation plugin and manifest export | — | — | Yes |

**Corrections vs a three-bullet sales sketch:** PDF **digital signature** is an **Enterprise** key (`pdf_digital_signature`), not Pro. There is **no** `report_jsonl` key — Community reporting in the map is **XLSX/HTML**. **SSO** in the map is `sso_saml`; OIDC/LDAP appear in [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md) as product **intent**, not as `FEATURE_TIER_MAP` keys. Dedicated support SLAs are **commercial terms**, not feature keys.

## Other registry bands (do not hide)

The same file also defines **Std** (`std`), **Pro+** (`pro_plus`), **Partner**, and **Open** (`open` = enforcement off). They are not extra price columns here.

| Band | What the code says |
| ---- | ------------------ |
| **Std** | Commercial entry token band (Boar-Std). **No unique feature keys** in `FEATURE_TIER_MAP` — rights/support live in licence/claims, not this map. |
| **Pro+** | `pro_prefilter_accel` (CLI→ProScanner path) and `rust_regex_stage` (Rust regex stage). |
| **Partner** | Enumerated for channel agreements; capability is **at least Pro+** in the module comment — no extra keys beyond Enterprise/Pro+ list above. |
| **Open** | Bypass: all features available for dev/lab. |

## Contact (no amounts)

For Pro, Pro+, Partner, or Enterprise evaluation: **contact@databoar.com.br** or open a GitHub issue on this repository. Do not treat this page as a quote.

## Drift

When you add a key to `FEATURE_TIER_MAP`, update this page in the same PR.

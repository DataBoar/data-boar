# Plan: Optional strong-crypto validation and inference of anonymisation/controls

**Status:** Deferred
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan adds an **optional** mode, enabled by a **CLI flag** and/or **web dashboard** option, to **validate use of strong cryptography** on the app’s connections to multiple data sources and, where possible, **infer anonymisation and other control steps** that may be in place. Results are reported in a dedicated sheet or section so IT and cybersecurity can see transport security and control posture alongside compliance findings. The feature is **off by default** and does not change existing scan behaviour when disabled.

---

## Goals

- **Opt-in:** Enable via **CLI** (e.g. `--validate-crypto` or `--audit-crypto`) and/or **web dashboard** (e.g. checkbox “Also validate strong crypto and infer controls” when starting a scan). When enabled, the scan runs as today and additionally runs crypto/controls checks per connection.
- **Strong crypto validation:** For each connection the app makes (SQL, NoSQL, REST, SMB, etc.), where technically feasible:
- **TLS/HTTPS:** Validate that the connection uses TLS (prefer 1.2 or 1.3), certificate validation is in use, and optionally flag weak ciphers or deprecated protocols.
- **Protocol-level crypto:** For SMB, flag whether signing and/or encryption is in use (SMB 3.x); for other protocols, record encryption-in-transit status when detectable.
- **Inference of anonymisation and controls:** Where the app can **infer** (best-effort, heuristic only) that anonymisation or other controls might be in place, record hints for the report. Examples:
- **Column/field names** suggesting hashing, masking or tokenisation (e.g. `*_hash`, `*_masked`, `*_token`, `anon_*`, `pseudonym_*`).
- **Metadata or schema hints** from the data source (e.g. “encrypted column”, “masking policy”) when exposed by the driver or API.
- **No guarantee:** This is inference only; the app does not verify that data is actually anonymised or that controls are effective. Report text must state that clearly.
- **Report:** Add a report sheet or section (e.g. “Crypto & controls”) with: target name, connection type, strong-crypto result (OK / warning / fail / not applicable), details (TLS version, SMB signing, etc.), and inferred controls (anonymisation hints, if any). Professional tone for IT and security teams.
- **No regressions:** Default behaviour unchanged; when the flag is off, no extra checks and no new sheet. When on, failures in crypto checks do not fail the overall scan; results are recorded and reported.

---

## Current state

- **CLI:** [main.py](../main.py) uses argparse: `--config`, `--web`, `--port`, `--reset-data`, `--tenant`, `--technician`. No scan-mode flags today.
- **API:** POST `/scan` and POST `/scan_database` accept optional body with `tenant` and `technician` ([ScanStartBody](https://github.com/FabioLeitao/data-boar/blob/main/api/routes.py)). No option for “validate crypto” or “audit controls”.
- **Dashboard:** Scan is triggered from the dashboard; no checkbox for extra audit modes.
- **Connectors:** Connections are made with existing drivers (SQLAlchemy, pymongo, redis, httpx, smbclient, etc.). TLS is often used (e.g. HTTPS, postgresql+psycopg2 over SSL) but the app does not currently **validate** minimum TLS version or cipher strength, nor report it per target.
- **Data source versions plan:** [PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md](PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md) will add transport_security to the inventory; this plan **complements** it by adding an explicit **validation** step (strong crypto) and **control inference** (anonymisation hints), both optional and gated by a flag.

---

## Scope: what can be validated or inferred per connection type

| Connection type                 | Strong crypto validation                                                            | Anonymisation/controls inference                                                      |
| -----------------               | ---------------------------------------------------------                           | ----------------------------------------------------------                            |
| **SQL**                         | TLS version and cert validation from connection if available; optional cipher check | Column names suggesting hash/mask/token/anon; DB metadata (e.g. “masking”) if exposed |
| **MongoDB**                     | TLS from client options; certificate validation                                     | Field names; no standard “masking” metadata                                           |
| **Redis**                       | TLS if connection uses it; cert validation                                          | Key names (e.g. token_, anon_)                                                        |
| **REST / Power BI / Dataverse** | HTTPS, TLS version from client session                                              | Response or header hints (e.g. “masked”) if present                                   |
| **SMB / CIFS**                  | Signing and encryption (SMB 3.x) if exposed by library                              | N/A (file share; no column-level metadata)                                            |
| **SharePoint / WebDAV**         | HTTPS only (scheme + TLS from client)                                               | N/A or document metadata if exposed                                                   |
| **Filesystem**                  | N/A (local path)                                                                    | N/A                                                                                   |

All validation and inference is **best-effort**: if the driver or API does not expose the information, record “not available” and do not fail the scan.

---

## Flags and configuration

- **CLI:** Add a single flag, e.g. `--validate-crypto`, that when set enables strong-crypto validation and control inference for that run. Pass this into the engine/config so connectors (or a post-connect step) know to run the extra checks.
- **Config (optional):** Optionally support a config key, e.g. `scan.validate_crypto: true`, so that config-driven runs (e.g. from API without body) can enable the mode. CLI flag overrides config when both are present.
- **API:** Extend the scan request body (e.g. POST `/scan`, POST `/scan_database`) with an optional field such as `validate_crypto: true`. When true, the started scan runs with validation and inference enabled.
- **Dashboard:** Add a checkbox or toggle (e.g. “Validate strong crypto and infer controls”) on the scan form. When checked, send `validate_crypto: true` in the request body. Document in dashboard help that this is best-effort and inference-only for controls.

---

## Data model and report

- **Storage:** Either extend the existing “data source inventory” (from [PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md](PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md)) with columns for crypto result and inferred controls, or add a small dedicated table, e.g. `crypto_controls_audit` (session_id, target_name, connection_type, strong_crypto_result, strong_crypto_details, inferred_controls_summary, created_at). Choice can be made at implementation time to avoid duplication with inventory.
- **Report:** A dedicated sheet **“Crypto & controls”** (or a section in “Data source inventory” / “Hardening recommendations” when those exist) with:
- Target name, connection type, strong-crypto result (OK / warning / not available / fail), details (e.g. “TLS 1.2”, “SMB signing enabled”), inferred controls (short text, e.g. “Column names suggest hashing/masking; not verified”).
- Disclaimer in the report or in docs: “Inferred controls are heuristic only; the application does not verify that data is actually anonymised or that controls are effective.”
- **When flag is off:** Do not create the table rows and do not add the sheet (or add an empty sheet with a single row “Crypto and controls validation was not requested for this run.”). Existing report layout unchanged.

---

## Implementation phases (to-dos)

### Phase 1: Flag and wiring

| #   | To-do                                                                                                                | Status |
| --- | ---------------------------------------------------------------------                                                | ------ |
| 1.1 | Add CLI flag `--validate-crypto` in main.py; pass through to config or engine                                        | ⬜      |
| 1.2 | Optional config key `scan.validate_crypto`; CLI overrides when set                                                   | ⬜      |
| 1.3 | Extend API scan body (POST /scan, POST /scan_database) with optional `validate_crypto: bool`; wire to engine         | ⬜      |
| 1.4 | Dashboard: add checkbox “Validate strong crypto and infer controls”; send flag in scan request                       | ⬜      |
| 1.5 | Engine: accept validate_crypto and pass to connectors or post-processing; when false, skip all crypto/controls logic | ⬜      |
| 1.6 | Tests: CLI flag and API body; engine receives flag; no new behaviour when flag false                                 | ⬜      |
| 1.7 | Docs: USAGE and TECH_GUIDE describe flag and config; dashboard help text                                             | ⬜      |

### Phase 2: Strong-crypto validation per connection

| #   | To-do                                                                                                                              | Status |
| --- | ---------------------------------------------------------------------                                                              | ------ |
| 2.1 | Define “strong crypto” criteria (e.g. TLS &gt;= 1.2, cert validation; SMB signing/encryption) in a small rule set or module        | ⬜      |
| 2.2 | SQL connector: when validate_crypto, after connect get TLS version and cert validation from connection if available; record result | ⬜      |
| 2.3 | MongoDB / Redis: TLS and cert from client/session; record result                                                                   | ⬜      |
| 2.4 | REST / Power BI / Dataverse: HTTPS + TLS from httpx client; record                                                                 | ⬜      |
| 2.5 | SMB: when library exposes it, detect signing/encryption; record                                                                    | ⬜      |
| 2.6 | Persist results (new table or extend inventory); add “Crypto & controls” report sheet with strong-crypto column                    | ⬜      |
| 2.7 | Tests: unit tests for criteria; integration test with mock or real TLS connection; report sheet present when flag on               | ⬜      |
| 2.8 | Docs: what is validated, limitations, link to SECURITY or hardening                                                                | ⬜      |

### Phase 3: Inference of anonymisation and controls

| #   | To-do                                                                                                                                                           | Status |
| --- | ---------------------------------------------------------------------                                                                                           | ------ |
| 3.1 | Define heuristics: column/field/key name patterns (e.g. *_hash, *_masked, anon_*, pseudonym_*); optional DB metadata (e.g. “masking”) when exposed              | ⬜      |
| 3.2 | SQL connector: when validate_crypto, run name heuristics on discovered column names; optionally query metadata for masking/encryption hints if dialect supports | ⬜      |
| 3.3 | MongoDB / Redis: field/key name heuristics; record short summary (e.g. “3 field names suggest hashing”)                                                         | ⬜      |
| 3.4 | Store inferred-controls summary per target; add column to “Crypto & controls” sheet; include disclaimer in sheet or report footer                               | ⬜      |
| 3.5 | Tests: heuristics on sample names; disclaimer present in report                                                                                                 | ⬜      |
| 3.6 | Docs: inference is best-effort and not a guarantee; for compliance, human review required                                                                       | ⬜      |

### Phase 4: Polish and regression

| #   | To-do                                                                                                               | Status |
| --- | ---------------------------------------------------------------------                                               | ------ |
| 4.1 | Ensure crypto check failures do not fail the scan; only record and report                                           | ⬜      |
| 4.2 | Full test suite passes; mark plan steps in PLANS_TODO.md                                                            | ⬜      |
| 4.3 | Optional: link “Crypto & controls” to “Data source inventory” / “Hardening” when both features exist (same session) | ⬜      |

---

## Dependencies and constraints

- **Optional only:** Feature is disabled by default. No change to config schema required for existing users (key can be optional).
- **No secrets in report:** Do not log or report certificates, keys or connection strings; only “TLS 1.2”, “certificate validated”, “SMB encryption on”, etc.
- **Inference disclaimer:** Report and docs must state that anonymisation/control inference is heuristic and not verified.
- **Compatibility with Data source versions plan:** Can share the same session and report; crypto result can be part of inventory or a separate sheet. This plan does not block and is not blocked by that plan.

---

## Conflict and placement in roadmap

- **No conflicts** with Security hardening, Secrets vault, Version check, Compliance samples, Compressed files, Dashboard i18n, or Data source versions & hardening.
- **Recommended placement:** After **Data source versions & hardening** (so transport_security and report structure exist and can be reused or extended), or in parallel if we keep a separate “Crypto & controls” sheet. See [PLANS_TODO.md](PLANS_TODO.md) for the full sequence.

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.

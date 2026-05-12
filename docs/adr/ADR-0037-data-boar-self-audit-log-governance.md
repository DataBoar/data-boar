# ADR 0037 — Data Boar self-audit log and governance of the auditor

## Context

Enterprise buyers, **CISOs**, and **DPOs** increasingly ask not only “what did the scanner find?” but **“who operated the scanner, who changed its behaviour, and can we prove it?”** That is the **governance of the auditor**: the inventory product itself must be **defensible** under customer audit and internal SOC2-style control narratives.

Today the application mixes several evidence surfaces (SQLite, optional WebAuthn, file logs, JSON export) but does **not** yet offer a single, marketing-ready story such as “every report download and every config save is immutably logged with actor identity.” Saying otherwise would mis-sell maturity.

## Decision (current truth)

We **document and commit** to the following as the **2026 baseline**:

1. **Scan run attribution (who kicked off discovery)**
   - `scan_sessions` stores `session_id`, timestamps, `status`, optional **`tenant_name`** and **`technician_name`** (CLI/API/dashboard flow), optional **`config_scope_hash`**, optional **`jurisdiction_hint`** opt-in flag.
   - Findings and `scan_failures` attach to `session_id`. This supports **“which organisational context ran this scan?”** but not fine-grained per-HTTP-request forensics.

2. **Tamper-evidence and retention-related append-only signals**
   - **`data_wipe_log`**: append-only rows for wipe operations (not removed by reset helpers).
   - **`--export-audit-trail`** / `core.audit_export.build_audit_trail_payload`: machine-readable JSON bundling session summaries, wipe log, runtime trust snapshot, dashboard transport snapshot, and **maturity self-assessment integrity** (HMAC-style counts when configured). Reserved fields `integrity_anchor` / `integrity_events` document future **release/build integrity** work (see internal plan **PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY** Phase E).
   - **Notification send log** (`notification_send_log`): outbound operator pings (success/failure, redacted error summary).

3. **Access control to the operator surface (not the same as an access log)**
   - Optional **WebAuthn** + session cookie **gate** for locale HTML routes when enabled and credentials exist: reduces anonymous dashboard use; **does not** by itself replace a dedicated **admin audit log** table listing each page view or file download.

4. **Operational logs (host-bound)**
   - `utils/logger` writes **`audit_YYYYMMDD.log`** (and console) with **redaction** policy (`sanitize_log_text` / `clean_error` per ADR 0036): suitable for **SRE** and incident response on the host, **not** a contractual substitute for centralised SIEM unless the customer forwards and correlates them.

5. **Explicit gaps (do not claim today)**
   - **No** first-class immutable table of “who downloaded report X at time T” or “who POSTed config change Y” with cryptographic Colleague-Nning for every operator action.
   - **Config** changes persist to the **config file** on disk; the app does not append a separate **config_change_audit** row per save.
   - **Report regeneration** via API is attributable only indirectly (new session or same session patterns depending on flow), not via a dedicated “report_access_log.”

## Direction (product and docs)

- **Near term:** Keep **COMPLIANCE_AND_LEGAL**, **SECURITY**, **OBSERVABILITY_SRE**, and **[MAP.md](../MAP.md)** aligned with this ADR so sales and integrators repeat **accurate** claims.
- **Mid term (when prioritised):** Add optional **operator action audit** persistence (e.g. append-only table: actor, action, resource, timestamp, client IP hash) behind config; wire **report download** and **config save** paths first; consider SIEM-friendly export alongside `--export-audit-trail`.
- **Release integrity:** Follow **PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY** for binary/config anchor fields referenced in `audit_export` placeholders.

## Consequences

- **Positive:** Customers and reviewers can map **existing** artefacts to control families (identification, logging, integrity checks for subsets of data) without the vendor over-claiming.
- **Negative:** RFPs that demand **full** “DLP-style” admin audit for every UI click still need **roadmap** or **partner SIEM** scope until implemented.
- **Career / positioning:** Framing “**governance of the auditor**” honestly (current + gaps + plan) is stronger than implying complete self-audit today.

## References

- `core/database.py` — `ScanSession`, `ScanFailure`, `NotificationSendLog`, wipe log helpers.
- `core/audit_export.py` — `build_audit_trail_payload`, `AUDIT_TRAIL_SCHEMA_VERSION`.
- `utils/logger.py` — file audit log naming and redaction-aware messages.
- `api/webauthn_html_gate.py`, `api/webauthn_routes.py` — dashboard authentication option.
- ADR 0036 — exception and log PII redaction (auditor must not leak subject data).
- **[MAP.md](../MAP.md)** — concern-first navigation including compliance bridges.

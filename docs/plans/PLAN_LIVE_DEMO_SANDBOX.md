# Plan: Live Demo Sandbox (`dashboard.net.br`)

<!-- plans-hub-summary: Public synthetic demo on one VPS behind a protected edge: read-only curated scans, admin-gated writes, a 30-minute reset instance and a no-reset presentation instance. Not a production tenant. -->

Status: in progress — v0 running on a single host (synthetic corpus and database seeds loaded); periodic reset fix, publishing the archive scenario and acceptance still open (#1447, epic #1446)
Scope: public, synthetic-data demonstration environment
Synced with: [PLANS_TODO.md](PLANS_TODO.md)

## Objective

Publish a safe, resettable Data Boar demonstration at `dashboard.net.br` without
turning the demo into a production data-processing endpoint. The application must
remain portable to a customer-owned cloud or an air-gapped runner.

Infrastructure specifics (hosting provider, addresses, firewall and egress rules,
allowlists, keys, costs) live in a **private** runbook and are intentionally not
recorded in this public repository.

## v0 architecture (current)

- **One VPS.** The whole demo runs on a single host; no multi-region or HA claims.
- **Podman rootless.** Containers run without root on the host; the dashboard,
  synthetic file corpus and curated database targets share a private container
  network.
- **Protected edge.** The public path goes through a proxy/CDN; the origin accepts
  traffic only from that edge. Application and data services are not directly
  reachable from the Internet, and administrative access does not use a public
  SSH path.
- **Two instances:**
  - **main** — the public demo, restored to the synthetic baseline every 30 minutes;
  - **presentation** — same build and data, without the periodic reset, for guided
    sessions.
- **Access model.** Reading (dashboard, findings, reports) is open. Writes and
  `/config` require the administrator password; visitors cannot add targets or
  credentials.
- **Curated targets.** File corpus from `core/demo/synthetic_corpus.py` (scenarios
  `1_happy`, `2_unhappy`, `4_false_positive`) plus the database seeds in
  `deploy/lab-smoke-stack/init/`. Synthetic data only; no customer credentials,
  production data or paid third-party secrets.

## Synthetic identifiers

Marks: **[V]** verified in code or tests on this branch; **[H]** hypothesis or
proposal not yet verified.

- **[V]** The detector tags `LGPD_CPF` / `LGPD_CNPJ` only when the Mod-11 check
  digits are valid (`_CHECKSUM_GATED_PATTERNS` in `core/detector.py`). With invalid
  check digits the demo corpus produced no `LGPD_CPF` / `LGPD_CNPJ` finding.
- **[V]** Where the demo must find CPF/CNPJ (`1_happy`, `2_unhappy`, the protected
  archive), the corpus uses small, fixed pools with **valid** check digits,
  labelled synthetic in the code, in `EXPECTED.txt` and in the corpus manifest.
  A valid check digit does not prove a number is unassigned, so this plan makes no
  claim that the values cannot match a real record.
- **[V]** Only `4_false_positive` uses invalid check digits, built so by
  construction with a fixed seed (#2176); tests pin that every checksum-valid
  CPF/CNPJ in the demo corpus comes from the declared pools.
- **[V]** E-mails use RFC 2606 / RFC 6761 reserved names only (`example.com`,
  `.invalid`, `.test`); one CNPJ publicly associated with a real company was
  replaced by a generated value.
- **[V]** Expected result of `4_false_positive`: no `LGPD_CPF` / `LGPD_CNPJ`.
  Known detector false positive: `PHONE_BR` on 11-digit codes (#2235, not fixed in
  the demo work); other files still get ML-based MEDIUM signals.

## Protected archive scenario

- **[V]** Scenario `protected_archive` (folder `9_protected_archive`) writes a
  `.7z` encrypted with a fictitious demo password, documented in its
  `EXPECTED.txt` (never a real credential), with synthetic PII inside. It needs
  the optional `compressed` extra (`py7zr`); without it the generator writes only
  `EXPECTED.txt` and explains how to enable it.
- **[V]** Without a password in `file_scan.file_passwords`, the archive is
  **flagged** in `scan_failures` (`encrypted_no_password`) and never reported as
  clean; with the demo password configured, the content is read and its findings
  appear (`tests/test_demo_protected_archive.py`).
- **[V]** No license-tier split exists for this today: compressed-file scanning is
  a Community feature and `file_passwords` is not tier-gated. The demo presents it
  as "flagged without the password, read with the configured password", not as an
  open-core/Pro difference.
- **[H]** Proposed wiring on the demo host (not applied yet): generate
  `protected_archive` with the other curated scenarios, enable `scan_compressed`
  with `.7z` in `compressed_extensions`, keep the main instance without the
  password (shows the flagged state) and configure the password on the
  presentation instance through the admin-gated `/config` (shows the read state).

## Safety controls

- Read-only/curated connector targets in v0; no visitor editor.
- No user-controlled arbitrary network destination in the public demo.
- Resource, request, and scan-size caps.
- Periodic reset to a known-good synthetic state (main instance).
- Visitor-facing errors rewritten as friendly messages.
- Logs and telemetry must not contain credentials or raw sensitive payloads.

## Delivery sequence

1. Single host with rootless containers and the protected edge — **done**.
2. Synthetic file corpus (scenarios 1, 2, 4) and database seeds loaded — **done**.
3. Fix the periodic reset of the main instance and verify it restores the
   baseline — **open**.
4. Synthetic identifiers aligned (valid check digits where the demo must find,
   invalid only in scenario 4, reserved e-mail domains) — **done in the repo**
   (#1447), pending publication to the demo host.
5. Protected `.7z` scenario in the corpus generator — **done in the repo**; adding
   it to the curated scan list on the demo host — **open**.
6. SMB target — **conditional** on measured RAM headroom on the host.
7. Add the demo link to `databoar.com.br` only after the endpoint is stable.
8. Record operational limits and the migration path to BYO-cloud and air-gapped
   deployments.

## Acceptance criteria (v0)

- `dashboard.net.br` serves the curated demo over HTTPS through the protected edge;
  reading is open, writes and `/config` require the administrator password.
- No application or data service is directly reachable from the public Internet.
- The main instance resets to the documented synthetic baseline every 30 minutes;
  the presentation instance stays up without reset.
- Curated scans cover the file corpus and the seeded database targets.
- The protected `.7z` is flagged without a password and read with the configured
  demo password.
- SMB is included only if the RAM measurement allows it.
- The operational runbook (edge, egress, reset, provisioning) exists and stays
  private, outside the public repository.

## Explicit non-goals for v0

- NFS targets: they need a kernel NFS service and root on the host, which the
  rootless single-host design excludes.
- Visitor editor or visitor-supplied targets (v1).
- Production customer tenancy or durable customer data.
- Arbitrary third-party credentials.
- Multi-region high availability.
- Claiming SaaS isolation guarantees beyond the documented single-demo scope.

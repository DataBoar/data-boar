# Plan: Live Demo Sandbox (`dashboard.net.br`)

<!-- plans-hub-summary: Public synthetic demo on one VPS behind a protected edge: read-only curated scans, admin-gated writes, a 30-minute reset instance and a no-reset presentation instance. Not a production tenant. -->

Status: in progress — v0 running on a single host (synthetic corpus and database seeds loaded); periodic reset fix, archive scenario and acceptance still open (#1447, epic #1446)
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

## Synthetic identifiers (decision pending)

> **To be decided by the operator.** Which synthetic identifier the demo uses to
> show LGPD detection is open. The detector tags `LGPD_CPF` / `LGPD_CNPJ` only
> when the Mod-11 check digits are valid, and a valid check digit cannot prove the
> number is not assigned to a real person. Options under evaluation:
>
> - **(a)** CPF/CNPJ with valid check digits from a small, declared synthetic pool
>   (detected as `LGPD_CPF` / `LGPD_CNPJ`; non-collision is not provable);
> - **(b)** CPF/CNPJ with invalid check digits (never a real number; not tagged
>   `LGPD_CPF` / `LGPD_CNPJ`, only e-mail/phone/ML signals remain);
> - **(c)** identifiers that are fictitious by definition — network test card
>   numbers (Luhn-valid) and e-mail under reserved domains (`.invalid`, `.test`,
>   `example.com`) — alongside (a) or (b).
>
> Scenario `4_false_positive` is now deterministic and contains no checksum-valid
> CPF/CNPJ (#2176); its remaining non-CPF signals are tracked separately.

## Protected archive scenario (wording pending)

A password-protected `.7z` with synthetic content will be added to the demo corpus,
with a fictitious demo password documented next to it (never a real credential).
Expected behaviour:

- **without** the password configured, the archive is **flagged** in
  `scan_failures` (`encrypted_no_password`) — never reported as clean;
- **with** the password in `file_scan.file_passwords`, the content is read and its
  findings appear.

> **To be decided by the operator:** whether reading protected archives is split by
> license tier. Today archive scanning and `file_passwords` are not tier-gated, so
> the demo must not present this scenario as an open-core/Pro difference until that
> decision is made.

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
4. Decide the synthetic identifier option and the archive-scenario wording — **open
   (operator)**.
5. Add the protected `.7z` scenario to the corpus and the curated scan list —
   **open**.
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

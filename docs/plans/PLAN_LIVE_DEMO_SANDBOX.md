# Plan: Live Demo Sandbox (`dashboard.net.br`)

<!-- plans-hub-summary: Public synthetic demo on one VPS behind a protected edge: read-only curated scans, admin-gated writes, a 30-minute reset instance and a no-reset presentation instance; next phase adds short-lived per-prospect pods (#2280). Not a production tenant. -->

Status: in progress — v0 running on a single host (synthetic corpus and database seeds loaded); periodic reset fix, publishing the archive scenario and acceptance still open (#1447, epic #1446). Per-prospect ephemeral pods designed (#2280, design `docs/desenho/2280.1.md`), implementation not started
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
9. Per-prospect ephemeral pods (#2280): design — **done**
   (`docs/desenho/2280.1.md`); phase A (commands, unit, reaper, Ansible, acceptance)
   and phase B (upload) — **open**.
10. **[H]** **Presentation** instance: operator `sharepoint_online` pilot on personal
    OneDrive — **evidence recorded** 2026-11-18
    ([m365_graph_onedrive_delegated_2260_2026-11-18.md](../ops/evidence/m365_graph_onedrive_delegated_2260_2026-11-18.md));
    read-only **`object_storage`** (e.g. SeaweedFS or S3-compatible on the demo host)
    after epic **#2306** merges — **not wired on `apresentacao` yet**; local operator
    proof already exists ([object_storage_seaweedfs_2306_5_2026-11-20.md](../ops/evidence/object_storage_seaweedfs_2306_5_2026-11-20.md)).

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

## Next phase: per-prospect ephemeral pods (#2280)

Goal: during a guided presentation, give one prospect a private, short-lived
Data Boar instance at `<slug>.dashboard.net.br`, with the same build and detection
profile as the presentation instance, that evaporates at the end. Design:
[`docs/desenho/2280.1.md`](../desenho/2280.1.md) (task #2282). Infrastructure
specifics stay in the private runbook, as for v0.

Marks: **[T]** tested on a project container (rootless Podman 5.4, systemd user
units); **[H]** to confirm on the target host.

- **Deterministic commands, no LLM:** `prospect-up <slug> [--ttl 30m]`,
  `prospect-down <slug>`, `prospect-list` and a reaper timer. The slug is a single
  validated DNS label. Every command is idempotent. `down` and the reaper leave
  no container, network, volume, unit, proxy route or state behind.
- **Templated Quadlet unit** `deploy/demo/quadlet/demo-prospect@.container`: the
  TTL is `RuntimeMaxSec` in a per-instance runtime drop-in. The container is
  started only by its own unit, so its `conmon` stays in that unit's cgroup, which
  is the fix for the old reset failure **[T]**. Not started at boot.
- **Isolation:** one internal network per prospect, with no egress and no reach
  to the host or to another prospect **[T]**. Loopback-only published port.
  Memory, swap, CPU and PID limits. Read-only root, in-memory `/data` and `/tmp`,
  no capabilities, `no-new-privileges`, container logs off the persistent journal.
- **Gate (phase A):** proxy basic auth with a random per-prospect password. The
  proxy injects a per-pod API key, which the product requires for a non-loopback
  bind **[T]**. Per-pod self-signed TLS between the proxy and the pod; the shared
  origin certificate never enters a pod. Passkey only after #2100.
- **Config:** the presentation's full detection profile, with only the synthetic
  file corpus as target: no remote or shared-host database targets and no
  third-party cloud targets. Learned patterns are off.
- **Proxy routes:** one route fragment per prospect, loaded atomically through the
  proxy admin socket. A rejected config is rolled back and the public demo keeps
  serving **[T]**.
- **Install:** Ansible role `demo_prospect` and `deploy/ansible/site-demo-prospect.yml`.
  OpenTofu only for the long-lived wildcard DNS record.
- **Slot model (operator decision):** the demo host runs at most two Data Boar
  instances, the public main instance and the presentation instance. A prospect
  pod is not a third one: it **takes the main instance's slot** for the session,
  and only one prospect runs at a time. `prospect-up` stops the main instance
  only after explicit confirmation (`--stop-dashboard`), and never removes it.
  `prospect-down` and the TTL reaper bring it back and check its status; a failed
  restart alerts the operator instead of leaving the public demo down silently.
  The main instance is restarted in its own systemd scope, so its `conmon`
  survives **[T]**. The presentation instance is never touched.
- **Phase B (upload), designed per task before release, supervised and only in
  the prospect slot:** a separate upload service outside the product, with no
  host environment or host data mounts, writes to an in-memory volume shared
  read-only with the pod; the whole slot stays within the main instance's
  memory limit. One automatic scan runs per closed batch (409 is queued). Uploaded files are
  deleted when that scan ends; the metadata-only findings stay until the TTL.
  There is a per-IP limit, real-type checks and a consent notice. Uploaded
  archives, PDF and OOXML stay off until the decompression limits (member count,
  total size, ratio, inner size, nesting, lying headers, container formats) are
  tested against malicious files (task 2280.7).

## Explicit non-goals for v0

- NFS targets: they need a kernel NFS service and root on the host, which the
  rootless single-host design excludes.
- Visitor editor or visitor-supplied targets (v1).
- Production customer tenancy or durable customer data.
- Arbitrary third-party credentials.
- Multi-region high availability.
- Claiming SaaS isolation guarantees beyond the documented single-demo scope.

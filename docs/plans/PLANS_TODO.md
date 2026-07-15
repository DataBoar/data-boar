# Consolidated plans – sequential to-dos

Plan files are kept in **English only** for history and progress tracking. Operator-facing documentation (how to use, config, deploy, etc.) exists in both EN and pt-BR; see [README.md](README.md) ([pt-BR](README.pt_BR.md)).

This document is the **single source of truth** for the project's plan status and remains in **`docs/plans/`** at all times. It lists **incomplete goals** from active plans and the **recommended sequential to-dos** to achieve them. Completed plan documents are archived in **`docs/plans/completed/`** for reference; links below point to those files.

**Plans hub (collaborator map):** **[PLANS_HUB.md](PLANS_HUB.md)** ([pt-BR](PLANS_HUB.pt_BR.md)) — auto-maintained table of **every** `PLAN_*.md` (open + completed) with short summaries and optional cross-links. Refresh with `python scripts/plans_hub_sync.py --write` when you add or archive a plan; CI enforces freshness via `plans_hub_sync.py --check`.

**How the pieces fit:** **`PLAN_*.md`** = durable spec · **`PLANS_HUB.md`** = index of all plan files · **`PLANS_TODO.md`** = execution mirror and dependency dashboard — see **[PLANS_DOCUMENTATION_HIERARCHY.md](../ops/PLANS_DOCUMENTATION_HIERARCHY.md)** ([pt-BR](../ops/PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md)).

**Integrity / tamper-evidence (index):** links-only map in **[Integrity and tamper-evidence index (planning map)](#integrity-and-tamper-evidence-index-planning-map)** below — no separate `PLAN_INTEGRITY_*.md` file.

**Token-aware work:** When context or token limits apply (e.g. after an initial Pro+ burst), prefer **one plan or one to-do per session**; open only the files needed for that step. See **[TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md)** for short vs long-term goals, artifact references (Docker Hub, `docs/private/`), and one-session workflow.

**Safety / IP / profitability burst:** When protecting revenue or reducing public exposure matters more than token savings for a short period, use **Priority band A** below first, then return to the token-aware table. See **[CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md)** for phased steps and copy-paste prompts for the agent.

**Policy:** When implementing a plan step, **update documentation** (USAGE, TECH_GUIDE, SECURITY, or dedicated docs) and **add or run tests** as the feature is implemented. After completing or adding to-dos, **update this file and the plan file** so progress is tracked in one place. All steps are intended to be **non-destructive**, **non-regression**, and **tested** before marking done.

## Status taxonomy (horizon + urgency)

Use these tags in headings to keep priorities explicit and machine-countable:

- Horizons: `[H0]` must-do-now, `[H1]` short-term, `[H2]` medium-term, `[H3]` long-term/production-ready milestone, `[H4]` far horizon (post-lato/master's scenario), `[H5]` dream horizon (PhD thesis scenario).
- Urgency: `[U0]` security/safety now, `[U1]` low-AI/high-gain soon, `[U2]` not critical next, `[U3]` backlog/catalogue.
- **Gravity (findings):** `[G0]` negligible, `[G1]` low, `[G2]` significant, `[G3]` critical (compliance breach, PII leak, Safe-Hold candidate). **Orthogonal** to GitHub **`[P0]-[P3]`** execution labels and to **CodeQL P0/P1/P2** — see **[PLAN_G_TIER.md](PLAN_G_TIER.md)** ([pt-BR](PLAN_G_TIER.pt_BR.md)).
- Status labels used in to-do rows/tables: `✅ Done`, `⬜ Pending`, `🔄 Tracked`, `Tracked (partially done)`, `Under consideration`, `Backlog`.

<!-- PLANS_STATUS_DASHBOARD:START -->
## Status dashboard (auto-generated)

Do not edit this block manually; refresh with `python scripts/plans-stats.py --write`.

- **Status rows counted:** 209  (Done: 130 | Incomplete: 79)
- **Incomplete breakdown:** Pending `⬜`=72, Tracked `🔄` / `Tracked (partially done)`=7, Under consideration=0, Backlog-marked rows=0

| Horizon | Total rows | Done | Incomplete |
| ------- | ----------: | ----: | ----------: |
| `H0` | 45 | 31 | 14 |
| `H1` | 39 | 30 | 9 |
| `H2` | 0 | 0 | 0 |
| `H3` | 118 | 62 | 56 |
| `H4` | 0 | 0 | 0 |
| `H5` | 0 | 0 | 0 |
| `UNSPECIFIED` | 7 | 7 | 0 |
<!-- PLANS_STATUS_DASHBOARD:END -->

**Plan status:** Corporate compliance ✅ · Minor data detection ✅ · Aggregated identification ✅ · Sensitive categories ML/DL ✅ · Rate limiting ✅ · Web hardening ✅ · Logo and naming ✅ · **Security hardening** ✅ Done (Tier 1) · **Secrets/vault** ✅ Phase A done (Tier 1); **Active** plan — Phases B–C backlog · **Configurable timeouts** ✅ Done · **Commercial licensing (runtime + docs + issuer bootstrap)** ✅ Phase 1 in repo (see `docs/LICENSING_SPEC.md`, `core/licensing/`); operational hardening ⬜ Priority band A · **Release 1.6.4** ✅ shipped **2026-03-20** (GitHub Release **v1.6.4**, Docker Hub **`fabioleitao/data_boar:1.6.4`**, `docs/releases/1.6.4.md`; maintenance **#99–#104**) · **Release 1.6.5** ✅ `docs/releases/1.6.5.md` (prior slice; tags/Hub may lag) · **Release 1.6.6** ✅ shipped **2026-03-25** (Git **v1.6.6**, GitHub Release, Docker Hub **`fabioleitao/data_boar:1.6.6`** + **`latest`**, `docs/releases/1.6.6.md`) · **Release 1.6.7** ✅ shipped **2026-03-26** (GitHub Release **v1.6.7** Latest, Docker Hub **`fabioleitao/data_boar:1.6.7`** + **`latest`**, [`docs/releases/1.6.7.md`](../releases/1.6.7.md), [`CHANGELOG.md`](../../CHANGELOG.md); legacy **`run.py`** removed — **migrate to `main.py`** with correct **bind** and **transport** flags) · **Release 1.6.8** ✅ shipped **2026-04-02** (GitHub **v1.6.8**, Docker Hub **`fabioleitao/data_boar:1.6.8`** + **`latest`**, [`docs/releases/1.6.8.md`](../releases/1.6.8.md); paste **Hub description** from [`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md)) · **Release 1.7.0** ✅ shipped **2026-04-17** (GitHub **v1.7.0**, Docker Hub **`fabioleitao/data_boar:1.7.0`** + **`latest`**, [`docs/releases/1.7.0.md`](../releases/1.7.0.md); **minor** — detector hints, HEIC, compliance/glossary expansion) · **Release 1.7.1** ✅ shipped **2026-04-21** (GitHub **v1.7.1**, Docker Hub **`fabioleitao/data_boar:1.7.1`** + **`latest`**, [`docs/releases/1.7.1.md`](../releases/1.7.1.md); **patch** — scope import CSV, maturity POC ops smoke, assessment JWT/`dbtier` tests) · **Version check & self-upgrade** ⬜ Not started · **Build identity & release integrity** ✅ **POC baseline** (Phase **E.11** CLI audit export on `main`); **⬜** SQLite anchor / startup re-verify / tamper string — [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) · **Additional compliance samples** ✅ Done · **Compliance standards alignment (ISO/IEC 27701, FELCA)** ✅ Done (doc only) · **US child privacy technical alignment (COPPA / AB 2273 / CO CPA minors)** ✅ Phase 1 ([PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.md](completed/PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.md)) · **Additional detection techniques & FN reduction** **🔄 Active** (POC **1–11** on `main`); **v1.8.0 #1056** entity taxonomy + checksum gates + span-alignment (doc-first); **⬜** optional aggregated/incomplete-data modes, dictionaries, FK context, NER/API paths (priorities **6+**). · **Compressed files** ✅ Done (steps 1–12; follow-ups 13–14 optional) · **Content type & cloaking detection** ✅ Core plan done (optional: man pages / OpenAPI examples) · **Data source versions & hardening** ⬜ Not started · **Strong crypto & controls validation** ⬜ Not started · **CNPJ alphanumeric format validation** ✅ Phase 4 done (Phase 5 checksum future) · **Selenium QA test suite** ⬜ Not started · **Synthetic data & confidence validation** ⬜ Not started · **Notifications (off-band + scan-complete)** ✅ Phase 1–4.2 + manual script audit ([PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md)); Phase 4.3+ backlog · **Dashboard i18n (M-LOCALE-V1)** ✅ shipped **2026-04** on **`main`** · **M-LOCALE-PLUS** (optional extra locales) ⬜ backlog · **Dashboard mobile responsive** ⬜ Planned ([PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](PLAN_DASHBOARD_MOBILE_RESPONSIVE.md) — **M-MOBILE-V1**) · **Dashboard reports RBAC** ✅ **Phase 2** on **`main`** (`api.rbac`, `roles_json`, **Pro+** `dashboard_rbac`); **⬜ Phase 3** SSO/OIDC (GitHub [#86](https://github.com/FabioLeitao/data-boar/issues/86); [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md)) · **Operator API key–first auth UX** ⬜ Exploratory sidequest ([PLAN_OPERATOR_API_KEY_FIRST_AUTH_UX.md](PLAN_OPERATOR_API_KEY_FIRST_AUTH_UX.md); JWT/Bearer toil → env/API key habit) · **SAP connector** ⬜ Not started · **Scope import / inventory bootstrap (exports → YAML)** ✅ **Phases B–D on `main`** (generic CSV → YAML fragment + operator docs); **⬜ Phase E** vendor adapters when promoted ([PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](PLAN_SCOPE_IMPORT_FROM_EXPORTS.md)) · **Object storage (S3-class, Azure Blob, GCS)** ⬜ Not started ([PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md)) · **Semgrep CI** ✅ **Complete** — [`.github/workflows/semgrep.yml`](../../.github/workflows/semgrep.yml) + [PLAN_SEMGREP_CI.md](completed/PLAN_SEMGREP_CI.md); Slack notify includes **Semgrep** failures when **`SLACK_WEBHOOK_URL`** set · **Bandit** ✅ **POC baseline + Phase 3 triage** — dev dep + `[tool.bandit]` + CI job **strict** (`-ll -ii`) on **`main`** ([PLAN_BANDIT_SECURITY_LINTER.md](completed/PLAN_BANDIT_SECURITY_LINTER.md)) · **Additional data soup formats** ✅ **POC tiers on `main`** — **Tier 3** rich media (optional **`.[richmedia]`**); **Tier 1** columnar/legacy + **opt-in stego hints** (`scan_for_stego`, optional **`[dataformats]`**); **⬜ Tier 3b** tracker heuristics + **Tier 4** doc-layer backlog ([PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](completed/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md)) · **Home lab (–1L)** 🔄 Partial: LAN dashBOARd + `uv`/git on a second host; playbook [§9 multi-host Linux](../ops/HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros) (DNS/SSH; Void/Pi notes; no agent-side OS installs). **Done** when [§12](../ops/HOMELAB_VALIDATION.md#12-when-you-are-done-with-a-lab-pass) criteria + dated note (e.g. `docs/private/`). · **Incremental filesystem scan idempotency** ✅ **Phase 1 done** (2026-05-14: `source_mtime_ns`/`source_size`/`content_fingerprint` on `FilesystemFinding`; [ADR-0051](../adr/ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md)) · **⬜ Phase 2–3** object-state index + skip-unchanged flag ([PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md](PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md))
### Commercial licensing — future reminder (partner / tiered SKUs)

When revising **license terms** for IP, commerciality, and profitability, explicitly design **multiple SKUs** (e.g. **direct end-user commercial** vs **partner / pro / enterprise**—names TBD) so **consulting partners** can deliver to **their customers** under a **partner-appropriate** subscription and price point, with different objectives and cost-to-serve (analogous to tiered DB licensing: Express / Standard / Enterprise / options). **Legal + pricing first;** then JWT claims and runtime enforcement. Include a prioritized matrix for **tier-driven feature packs**, **`uv` extras profiles** (`.[nosql]`, `.[datalake]`, etc.), and an explicit **kill switch** path for emergency disable/restriction. Documented in [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) and [LICENSING_SPEC.md](../LICENSING_SPEC.md) (future extensions).

**Brand and experience IP (same pass):** Include **mascot**, **Data Boar / dashBOARd** naming, **data soup** metaphor and connector narrative, **UI/report appearance**, documented **operation** (CLI/API/Docker story), and **companion artifacts** (Docker image branding, website, related repos) in trademark and commercial-license review — see [LICENSING_OPEN_CORE_AND_COMMERCIAL.md § Brand, narrative, and experience IP](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md#brand-narrative-and-experience-ip-inventory-for-counsel-and-commercial-policy) and [COPYRIGHT_AND_TRADEMARK.md](../COPYRIGHT_AND_TRADEMARK.md#6-brand-narrative-and-product-experience-inventory).

### Partner / sector demand (use-case storyboards)

When **partners** or **buyers** anchor on a vertical (MSP, insurance, RPO, real estate, NGO, EdTech, port, law, accounting, pharma), route demand **without scope creep**: (1) use the narrative index **[../use-cases/README.md](../use-cases/README.md)** ([pt-BR](../use-cases/README.pt_BR.md)); (2) map gaps to **shipped** operator surfaces (`USAGE`, connectors, reports) before inventing new flags; (3) promote **one** backlog row here or in the relevant `PLAN_*.md` when **repeatable revenue evidence** exists; keep token batching per **[TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md)**.

### Integration / active threads — last refreshed **2026-07-12**

- **Completão A/B benchmark (`v1.7.3` lab ref vs `origin/main`):** `scripts/benchmark-ab.ps1` + `docs/plans/BENCHMARK_EVOLUTION.md` — **2026-04-27** hardened **`lab-op-git-ensure-ref`** (SSH stderr / `Start-Process`), **`completaoImageRefs`** parsing, and image-preflight coercion in **`lab-completao-orchestrate.ps1`**; benchmark default is **lab-ref-only** Round A (avoid local checkout of legacy tag unless `-LocalLegacyCheckout`). **Wall-clock A/B not finished** in the agent tool window (Round A can exceed **~60 min** on the full manifest) — operator: run the script locally to produce **`benchmark_runs/times.txt`** + **`telemetry.json`**; private checklist **`docs/private/homelab/BENCHMARK_AB_OPERATOR_NOTES_2026-04-27.pt_BR.md`**.
- **Engineering doctrine consolidation (manifestos doc-only, Slice 1 in PR):** Five normative manifestos under [`docs/ops/inspirations/`](../ops/inspirations/) — [THE_ART_OF_THE_FALLBACK.md](../ops/inspirations/THE_ART_OF_THE_FALLBACK.md), [DEFENSIVE_SCANNING_MANIFESTO.md](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md), [ENGINEERING_BENCH_DISCIPLINE.md](../ops/inspirations/ENGINEERING_BENCH_DISCIPLINE.md), [INTERNAL_DIAGNOSTIC_AESTHETICS.md](../ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md), [ACTIONABLE_GOVERNANCE_AND_TRUST.md](../ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md). Drives Slices 2–4 (RCA blocks in `completão`, doctrinal code comments referencing manifestos, refresh of [BENCHMARK_EVOLUTION.md](BENCHMARK_EVOLUTION.md)) — see [PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md](PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md). **Zero impact on customer DB locks** (Slice 1 is doc-only).
- **Lab lessons + completão evidence (public vs private):** Dated snapshots under **`docs/ops/lab_lessons_learned/`** + rolling hub **`docs/ops/LAB_LESSONS_LEARNED.md`** per [ADR 0042](../adr/ADR-0042-lab-lessons-learned-archive-contract.md); session **`lab-lessons`** loads **`.cursor/rules/lab-lessons-learned-archive.mdc`** when globs miss — see [OPERATOR_AGENT_COLD_START_LADDER.md](../ops/OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`lab-lessons`)*. Keep narrative + LAN context in **`docs/private/homelab/COMPLETAO_SESSION_*.md`**; reference **numbers and symptoms only** in **tracked** docs; file follow-ups as rows here, then **`python scripts/plans-stats.py --write`**. [LAB_COMPLETAO_RUNBOOK.md](../ops/LAB_COMPLETAO_RUNBOOK.md) § *Public vs private lab evidence*.
- **post4 trust-floor closure (2026-07-12):** merged hardening issues **[#1194](https://github.com/FabioLeitao/data-boar/issues/1194)**, **[#1195](https://github.com/FabioLeitao/data-boar/issues/1195)**, **[#1201](https://github.com/FabioLeitao/data-boar/issues/1201)**, **[#1202](https://github.com/FabioLeitao/data-boar/issues/1202)**, **[#1137](https://github.com/FabioLeitao/data-boar/issues/1137)**, **[#1198](https://github.com/FabioLeitao/data-boar/issues/1198)**, **[#1130](https://github.com/FabioLeitao/data-boar/issues/1130)** via PRs **[#1203](https://github.com/FabioLeitao/data-boar/pull/1203)**–**[#1209](https://github.com/FabioLeitao/data-boar/pull/1209)** and **[#1214](https://github.com/FabioLeitao/data-boar/pull/1214)**; trust-floor scope for post4 marked closed. New queued follow-ups: **[#1210](https://github.com/FabioLeitao/data-boar/issues/1210)** (merge-secrets), **[#1211](https://github.com/FabioLeitao/data-boar/issues/1211)** (integrity fail-open), **[#1212](https://github.com/FabioLeitao/data-boar/issues/1212)** (GRACE).
- **Wheelhouse seed via GitHub Releases (`#1182`, 2026-07-12):** `cp314` musllinux seed uploaded to **`DataBoar/data-boar-site`** release **`wheelhouse-2026-07-12`** (asset: repaired `scikit_learn` wheel) and validated with `pipx install ... --find-links` + Alpine `data-boar --demo` findings. Tracking plan: [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md). **Gate anti-link-morto:** do **not** update `TROUBLESHOOTING` / `OS_COMPATIBILITY_TESTING_MATRIX` URLs until the hosted command contract is finalized and verified.
- **S0 – Trust burst:** **–1** merged in **[#195](https://github.com/FabioLeitao/data-boar/pull/195)** (Dependabot-equivalent bumps: FastAPI/pydantic/rich/mypy/Ruff + dev transitives; **github-actions**: `astral-sh/setup-uv` **v8.1.0**, `github/codeql-action` **4.35.2** SHAs); **`uv lock`** + **`requirements.txt`** on **`main`**. Pre-merge: **`uvx pip-audit`** clean; **–1b** snapshot on Hub **`fabioleitao/data_boar:latest`**: **`docker scout quickview`** **0C / 0H / 1M / 31L**; **`docker-scout-critical-gate.ps1`** pass. **Next release / prod image:** rebuild + push so Hub digest matches this lockfile; then Scout again. **A3** Hub tag hygiene remains **operator** (UI). Dependabot **#191–#194** closed as superseded by **#195**.
- **S0b / M-OBS (partial):** **Backup and restore** for persistent data documented in [DEPLOY.md](../deploy/DEPLOY.md) **§9** and [DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md) **§9** (config + SQLite + reports under `/data`). Kanban **Selected** now **S1 – Lab proof (–1L)** — see [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §3.
- **S2a – Transport + trust (open-core POC, demo-ready):** **Active sprint pairing** — ship the **first implementation slice** of [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md) **Phase 7** (transport integrity / tamper-aware **trust** or **tinted** runtime) **together with** **one** access/governance step from [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) / **[#86](https://github.com/FabioLeitao/data-boar/issues/86)**: **doc-first** refresh of route matrix + `/status` / middleware narrative for enterprise deploys, **or** a **thin code** change that surfaces a canonical **trust-state** next to existing `dashboard_transport` / `enterprise_surface` (same PR or tightly coupled follow-up). Vocabulary and output policy: [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md) §A1–A2 minimum. **Demo bar:** operator can show TLS (native or documented reverse-proxy) plus **`GET /status`** / **`--export-audit-trail`** carrying **both** transport and trust signals; cross-check [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](../ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md). Kanban + sprint row: [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §3 / §4 (**S2a**).
- **Sprint focus:** **S2a – Transport + trust (POC)** is **Selected** for the **next agent-heavy window** (interleave **S1 – Lab proof** / –1L when hardware calendar demands it). After **S2a** reaches demo-ready checkpoint, return to Tier-2 table orders **4–7** and maturity **M-MATURITY-POC** / **#86** Phase 1 sequencing per §4.2 below. **S0** checklist closure: [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) **§4.0**.
- **Branches:** Work ships via **PRs to `main`**; avoid tracking a long-lived “integration” branch name here (it goes stale).
- **v1.8.0 competitive survey (docs-first, milestone v1.8.0):** Six issues **[#1056](https://github.com/FabioLeitao/data-boar/issues/1056)–[#1061](https://github.com/FabioLeitao/data-boar/issues/1061)** enrich existing `PLAN_*.md` files (no greenfield features). **Order:** #1056 detection taxonomy → #1057 remediation policies → #1058 findings catalog export → #1059 packaging extras → #1061 DSAR tombstone → #1060 composite eval. **One PR per issue** (`Closes #N`); each PR runs `plans_hub_sync.py --write` + updates this file. Methodology: `compliance-sample-*.yaml`, `norm_tag`, `report.recommendation_overrides`, disclaimers per [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md). **Revisit (completed):** content-type/cloaking (#884), sensitive-categories ML/DL — addendum only unless operator reopens.
- **Wave 1 — sequenciamento explícito (v1.7.4 + v1.8.0-beta fase U0/U1):** Executar na ordem do issue #656. Parar após todos os itens da Fase 5 fechados. Não avançar para U2 sem instrução do operador. **Mapa visual:** [#654](https://github.com/FabioLeitao/data-boar/issues/654) — [ISSUE_QUEUE_SEQUENCING_MAP.md](../ops/ISSUE_QUEUE_SEQUENCING_MAP.md) (Mermaid; refresh when **NÃO INICIAR** chains change).
- **Cloud object storage (data soup):** **Not implemented yet** — phased plan [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) (S3 first, then Azure Blob, GCS); reuses file/compressed pipeline after list + fetch.
- **SQL sampling (SRE + audit evidence):** **Slice 1** on `main` — per-column reads use **`WHERE <col> IS NOT NULL`** before the row cap; **`connectors/sql_sampling.py`** (`SamplingManager` + legacy `SqlColumnSampleQueryBuilder`, per-table **strategy** INFO log, optional `TableSamplingMetadata` labels, **`DATA_BOAR_SQL_SAMPLE_LIMIT`** env override). **Slice 1b** — optional YAML **`sql_sampling.overrides`** cascade (**`core/sampling_policy.py`**, `SQLConnector` + Snowflake). **Slice 2–3** (metadata-first caps, optional `TABLESAMPLE` / coverage metadata, egress-aware defaults; per-statement timeout matrix follow-up) — [PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md](completed/PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md), [ADR 0043](../adr/ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md).
- **Action Plan Generator (APG — post-scan):** Turn findings into **tiered suggested actions** + optional **remediation snippet export** + **scan evidence manifest** for diligence narratives—not legal conclusions. PoC phases: schema/report hooks, exposure diagnosis narrative, JSON/SQL templates, audit log alignment with export trail — [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) (cross-links: [PLAN_PDF_GRC_REPORT.md](PLAN_PDF_GRC_REPORT.md), [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md), ADR **0025**).
- **Semgrep:** ✅ **Plan complete** — OSS scan on push/PR; [PLAN_SEMGREP_CI.md](completed/PLAN_SEMGREP_CI.md). **Slack on CI/Semgrep failure:** **`Slack CI failure notify`** ships on **`origin`** (**`.github/workflows/slack-ci-failure-notify.yml`**); **private snapshot** **`docs/private/raw_pastes/cursor-incident/slack-ci-failure-notify.yml.old`** documents pause drills — [OPERATOR_NOTIFICATION_CHANNELS.md](../ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1.1. Optional smoke: temporary failing branch — see plan § *Optional operator smoke*.
- **Bandit:** **`bandit`** in **`uv` dev** group; **`[tool.bandit]`** in **`pyproject.toml`**; job **Bandit (strict)** inside [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — **POC baseline on `main`**. Low triage log: [PLAN_BANDIT_SECURITY_LINTER.md](completed/PLAN_BANDIT_SECURITY_LINTER.md) Phase 3.
- **Rich media / data soup:** **Tier 3** rich-media slice is **on `main`**; **Tier 1** + **opt-in stego hints** are **on `main`** ([PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](completed/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md)). **Tier 3b** (embedded trackers) + **Tier 4** doc-layer taxonomy remain **planned**.
- **Data soup narrative (positioning, docs):** “Hidden / cloaked / legacy / forgotten” ingredients + **stacked opt-in** discovery (file heuristics, [export breadcrumbs](completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md), [allowlisted port hints](PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.md)) — **product positioning**; **not** a legal, regulatory, or completeness guarantee.
- **Jurisdiction hints (shipped):** Optional DPO-oriented **Report info** rows from **finding metadata** heuristics (`report.jurisdiction_hints`, CLI/API/dashboard opt-in); **not** legal conclusions — [ADR 0026](../adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md), [USAGE.md](../USAGE.md). Further regions/samples remain **incremental** (config + code), not a completeness promise.
- **Dependabot / pip-audit / PyPI supply chain:** Committed **`uv.lock`**, CI **`pip-audit`**, and **Dependabot** (pip + github-actions) address **known CVEs** and **dependency drift** on the **PyPI** install path—they do **not** replace human review of PRs or detect every **malicious** / typosquat scenario. **SBOM** artifacts: [ADR 0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). CI workflows (**`ci.yml`**, **CodeQL**, **Semgrep**, **slack-ops-digest**) pin third-party Actions to **commit SHAs**; **`setup-uv`** pins **uv** CLI semver — bump via **Dependabot** (github-actions) or deliberately; details: [WORKFLOW_DEFERRED_FOLLOWUPS.md](../ops/WORKFLOW_DEFERRED_FOLLOWUPS.md). Framing (trust, marketplaces): [SUPPLY_CHAIN_AND_TRUST_SIGNALS.md](../ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md). **Bump workflow:** edit **`pyproject.toml`**, then **`uv lock`**, **`uv export --no-emit-package pyproject.toml -o requirements.txt`**, **`.\scripts\check-all.ps1`**. **Upstream-blocked alerts:** [DEPENDABOT_PYOPENSSL_SNOWFLAKE.md](../ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md); [DEPENDABOT_PYGMENTS_CVE.md](../ops/DEPENDABOT_PYGMENTS_CVE.md).
- **Docker Hub / Scout (–1b):** After **deps or Dockerfile** changes, rebuild, **push**, **`docker scout quickview`**. Debian **base** packages may still show **CVEs with no fix** in the current slim image (e.g. **ncurses**) — acceptable until **`python:*-slim`** refreshes; document operator exceptions if needed.
- **Published stable / next public:** current **published** stable line is **`v1.7.4`** / Python **`1.7.4`** on GitHub + Hub (**2026-06-26**); prior golden **`v1.7.2-safe`** / **`1.7.2+safe`** remains documented; **1.7.1** and **1.7.3** remain in history; follow **`docs/releases/`** + VERSIONING checklist. **Next public horizon:** **`1.8.0-beta`** per [VERSIONING.md](../VERSIONING.md). **Pick one primary slice per bundle** (avoid mixing maturity POC closure, vendor adapters, and unrelated H3 fronts): default candidates are **(a)** maturity assessment **POC ready** (`scripts/smoke-maturity-assessment-poc.ps1` + [SMOKE_MATURITY_ASSESSMENT_POC.md](../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) checklist) **or** **(b)** first **scope-import** vendor adapter when a thread promotes it.
- **Dashboard transport (HTTPS / explicit HTTP):** Shipped on `main` — `main.py --web` requires **`--https-cert-file`+`--https-key-file`** or **`--allow-insecure-http`** (or `api.*` equivalents); Docker **`CMD`** includes `--allow-insecure-http`; **`GET /status`** and **`GET /health`** expose **`dashboard_transport`** and **`enterprise_surface`**. See [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md) (Phase 4 audit-export ✅; Phase 7 tamper-trust ⬜).
- **Opt-in port / service hints (roadmap):** Proposal only — allowlisted hosts/ports, zero-trust friendly, optional enterprise feature; [PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.md](PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.md).
- **Scope import / inventory bootstrap (roadmap):** **v1 shipped on `main`:** `scripts/scope_import_csv.py` + `config/scope_import_csv.py` + **GLPI adapter** (`scope_import_glpi`) + tests + USAGE/TECH_GUIDE + **EN/pt-BR** [SCOPE_IMPORT_QUICKSTART.md](../ops/SCOPE_IMPORT_QUICKSTART.md) — canonical **CSV → YAML `targets` fragment** for operator merge; see [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md). **Further vendor adapters** (Live Optics, Nagios/Cacti-class, observability exports) **stay backlog until promoted**; complements opt-in port hints (**passive seed** vs **active** probes). **Medium-term [H2]:** [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) — **lakehouse as soup ingredient** (SQL scan) + **UC / curated tables as recipe** (inventory → targets); **Pro/Enterprise–shaped**, **customer-pull** before deep design. **[H2] findings sink:** [PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md](PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md) — optional **export/sync of scan findings** from local SQLite to **customer-chosen** corporate stores (SQL, MongoDB, lake/object staging); same **customer-pull** rule; **reorder PLANS_TODO** if a contract requires it sooner.
- **Maturity self-assessment / LGPD questionnaire (operator artefacts → product backlog):** [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) — **POC A on `main`:** gated `GET`/`POST /{locale}/assessment` (flag + tier), optional YAML pack, **SQLite** answers, optional **HMAC** row sealing + **`GET /status`** / **`--export-audit-trail`** integrity summary — **no** bundled proprietary questionnaire text in public Git. **Scoring + export ✅** — YAML **`scores`** (rubric), **%** on post-submit summary, **`GET /{locale}/assessment/export`** (CSV/Markdown **attachment**; USAGE describes download vs disk). **Per-batch history table on `GET /{locale}/assessment` ✅** (see [ADR 0032](../adr/ADR-0032-maturity-assessment-batch-history-sqlite.md)). **POC ready** closure: **`scripts/smoke-maturity-assessment-poc.ps1`** (levels **A+B**) + [SMOKE_MATURITY_ASSESSMENT_POC.md](../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) manual **§D** (level **C**; §E optional); checklist + **A/B/C evidence** in plan § *POC ready — evidence levels*; **autonomous vs operator** boundary + pytest↔§D mapping in plan + runbook; milestone **M-MATURITY-POC** in [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.2 / §5. **Tier/JWT slice** sketch (orthogonal to **#86**): same plan § *Next slice*; [LICENSING_SPEC.md](../LICENSING_SPEC.md) `dbtier` row. **Next:** after closure, **[GitHub #86](https://github.com/FabioLeitao/data-boar/issues/86) Phase 1** (session + passwordless on `/{locale}/…`) on a **dedicated branch/PR** — then revisit maturity (DOCX→YAML per **tenant**, annex/bundle, consultant UX). Align **tier JWT enforcement** with [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) (Phases **1+**). **Related:** technical **PDF GRC** report for scan findings — [PLAN_PDF_GRC_REPORT.md](PLAN_PDF_GRC_REPORT.md) (planned, not the org form). Private: `docs/private/raw_pastes/general/LGPD_DOCS/`. **Commercial / subscription** feature—not open core.
- **Stricto sensu research (M.Sc. / Ph.D.) using Data Boar as platform:** Backlog — [PLAN_STRICTO_SENSU_RESEARCH_PATH.md](PLAN_STRICTO_SENSU_RESEARCH_PATH.md) (questions, experiments, methodology, advisor outreach). Stays aligned with product evolution: comparative detection/modeling, evidence metrics, repeatability—see **§7** in that plan and **N3** in [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md). Revisit for literature synthesis, thesis narrowing, or benchmark design in **dedicated higher-context sessions** (e.g. after Priority band A or when enrollment timeline is real); token batching in [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md).
- **Clojure/Lisp augmentation feasibility (sidecar R&D):** Proposed far-horizon track — [PLAN_CLOJURE_AUGMENTATION.md](PLAN_CLOJURE_AUGMENTATION.md) (EN) and [PLAN_CLOJURE_AUGMENTATION.pt_BR.md](PLAN_CLOJURE_AUGMENTATION.pt_BR.md) (pt-BR mirror). Scope is feasibility evidence and go/no-go gates; it does **not** replace Rust/Python baseline and should only be promoted if measurable value appears for policy reasoning or thesis experiments.
- **D-WEB (Phase 0, #86):** Route matrix + **actual** middleware order (Starlette outer→inner) + **target** Mermaid (session → locale → RBAC) + proxy pointers — [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) § *Phase 0 deliverable*; cross-link from [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md) § *Meshing with dashboard reports RBAC*.
- **WebAuthn JSON (Phase 1a, #86 track):** Vendor-neutral **`/auth/webauthn/*`** + SQLite + signed cookie on **`main`** (default **off**) — [ADR 0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md), [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) § *Phase 1a deliverable*, [SMOKE_WEBAUTHN_JSON.md](../ops/SMOKE_WEBAUTHN_JSON.md). **Phase 1b** (HTML session gates + CSRF) ✅ on **`main`**. **Phase 2** (**RBAC**) ✅ on **`main`** when tier allows. **Phase 3** (SSO/OIDC) remains **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** follow-up.
- **Sprint mirror:** [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §3 + **M-RICH** when milestones change.
- **Gemini / LLM doc triage (optional):** After a public-bundle review, use [PLAN_GEMINI_FEEDBACK_TRIAGE.md](PLAN_GEMINI_FEEDBACK_TRIAGE.md) for non-authoritative optional to-dos and promotion gates—does not override CI, pytest, or agreed sequencing until promoted here or in an issue.
- **Taxonomy axes (G0-G3 + hub):** [PLAN_G_TIER.md](PLAN_G_TIER.md) ([pt-BR](PLAN_G_TIER.pt_BR.md)) formalizes **gravity** for findings; [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md) maps orthogonal axes; [ADR-0055](../adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md) records the anti-collision contract. **`scripts/inv-adr.ps1`** regenerates **`docs/adr/INVENTORY.txt`**.
- **ADR governance enforcement (#1162):** Phase 1 deterministic anti-regression tests (T1 lifecycle, T2 locale/structure, T5 anti-deletion rename-aware, T6 date immutability) — [PLAN_ADR_GOVERNANCE_ENFORCEMENT.md](PLAN_ADR_GOVERNANCE_ENFORCEMENT.md); pre-commit + CI. Phase 2 (T3 prose density, T4 anti-dangling refs, ADR-0074 smoke) ⬜ deferred.
- **No-coauthorship kombi (A.I.I.D.C.O.B.P.P. v1.4):** Fail-closed gate — `.gitleaks.toml` rule `no-coauthorship-at-all` + `tests/test_commit_no_tool_coauthorship.py` (commit messages) + `tests/test_gitleaks_config.py` (`gitleaks detect --config .gitleaks.toml`); pre-commit + CI pytest; `gitleaks.yml` uses repo config — [PLAN_NO_COAUTHORSHIP_GATE.md](PLAN_NO_COAUTHORSHIP_GATE.md). **Operator:** disable Cursor co-author injection; amend polluted commits forward (no `--no-verify` / `commit-tree`).
- **Hybrid taxonomy (#1071, Fideslang eval — closed 2026-06-30):** RO recommendation **B-interno + A-export-adapter** — three implementation slices (all **optional**, backward compatible): **(1)** [PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md](PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md) **[#1074](https://github.com/FabioLeitao/data-boar/issues/1074)** — hierarchical `norm_tag` + Data-Subject → closes **#1069** (supersedes [#1072](https://github.com/FabioLeitao/data-boar/issues/1072)); **(2)** [PLAN_DATA_USE_AXIS.md](PLAN_DATA_USE_AXIS.md) **[#1075](https://github.com/FabioLeitao/data-boar/issues/1075)**; **(3)** [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md) **[#1076](https://github.com/FabioLeitao/data-boar/issues/1076)** → SWOT **W-novo-1** when customer-pull. Legacy Bearer-only plan: [PLAN_SUBJECT_CATEGORY_AXIS.md](PLAN_SUBJECT_CATEGORY_AXIS.md).
- **Plan checkbox discipline:** When code ships for a named plan slice, update **`PLAN_*.md`** checkboxes in the **same PR** — see **`AGENTS.md`** (*Plan checkbox discipline*); **`plans-status-pl-sync.mdc`** stays situational (plan globs only).
- **Licensing enforcement (open issues — PMO index):** Cluster **#704** [P0] (Maestro + JWT on four lab hosts) → **#719** [P1] **`[U1]`** (silent bypass via `DATA_BOAR_ENV=development` / `DEBUG=1` — CRITICAL log + Docker doc) → **#708–#722** (issuer, trial/grace/revocation ADRs). Table below under **`[H0][U1]` Licensing enforcement**; **A6** `license-smoke` should gain a **#719** regression when the fix lands. **After** Wave 1 **#656** U0/U1 slices and **#406** release gate — not a substitute for **#606** [P0] plugin hooks unless operator reprioritizes.
- **LAB-OP Ansible + host hygiene ([#756](https://github.com/FabioLeitao/data-boar/issues/756)):** **`[H0][U1]`** one lab node's disk at **~90%** (may block completão / bare mirror on that node) · **`[H0][U2]`** install **`bw`** CLI via the lab Ansible playbook (idempotent). Issue states **no release-gate blocker** — operator-paced; see **LAB-OP** paragraph below and **M-PILOT-READY** completão row.
- **Forensics primer — first responder ([#747](https://github.com/FabioLeitao/data-boar/issues/747)):** Complements parent **[#685](https://github.com/FabioLeitao/data-boar/issues/685)**; thin **`docs(primers)`** checklist · **`[H2][U3][P2]`** — Gemini Cold row **G-26-19** below; hub chain **#685 → #747 → #744** when primers hub expands.

**Gemini Cold — promoted sequence (safest first, `[H3][U3]` doc/hygiene unless noted):** Use a **`docs`** or **`houseclean`** session; run **`check-all`** before merge. Source IDs: §6 of [PLAN_GEMINI_FEEDBACK_TRIAGE.md](PLAN_GEMINI_FEEDBACK_TRIAGE.md).

| Seq | ID | Slice | Notes |
| --- | -- | ----- | ----- |
| 1 | **G-26-04** | README / TECH_GUIDE — install identity (**Data Boar** / PyPI **`data-boar`**) | ✅ Done — `pyproject` + docs aligned (PyPI publish when scheduled) |
| 2 | **G-26-13** | **Corporate-Entity-C** — one-line definition; align EN ↔ pt-BR in **GLOSSARY** (or linked ops stub) | ✅ Done — entry exists in both `GLOSSARY.md` and `GLOSSARY.pt_BR.md` (row 218/220) |
| 3 | **G-26-09** | Man pages — editorial pass (`docs/data_boar.1` + install docs): why two pages, de-duplicate install narrative | Docs only |
| 3a | **G-26-19** / **[#747](https://github.com/FabioLeitao/data-boar/issues/747)** | Forensics primer — first-responder checklist (complements **[#685](https://github.com/FabioLeitao/data-boar/issues/685)**) | **`[H2][U3][P2]`** thin PR; link from [PRIMERS_HUB.md](PRIMERS_HUB.md) when merged |
| 4 | **G-26-08** | README — optional quality badges (Sonar / CI / Ruff); keep shields minimal | Verify URLs; avoid noisy or broken badges |
| 5 | **G-26-16** | Compliance samples — document “composition” pattern for shared English terms / `base-global` idea | Doc-only DX |
| 6 | **G-26-07** | New **COMPLIANCE_TAGS.md** (or slice) — glossary of `norm_tag` / labels; link from **COMPLIANCE_FRAMEWORKS** or **GLOSSARY** | Larger doc pass |
| 7 | **G-26-10** | USAGE/TECH_GUIDE — FAQ or **limitations** rows only where still blank (passworded ZIP/PDF, OCR scale, …) | Scattered; batch in one PR if possible |
| 8 | **G-26-18** | Config/parser — document real behaviour (unknown keys, multi-`norm_tag`, ML + encoding limits); code truth first | Read code + tests before writing |
| 9 | **G-26-14** | **`include_profiles` / auto-merge** for `recommendation_overrides` | **Product decision** — last; feature vs docs-only |

### GitHub open issues (triage queue)

Refresh periodically: `gh issue list --state open --limit 50` (requires [`gh`](https://cli.github.com/) auth). This table is **not** the full product backlog—only **open** issues linked into plans so they are not lost.

| #                                                        | Short title                                      | Type                  | Plan                                                                                 | Sequence (token-aware)                                                                   |
| -                                                        | -----------                                      | ----                  | ----                                                                                 | ------------------------                                                                 |
| [86](https://github.com/FabioLeitao/data-boar/issues/86) | Reports / dashboard access by role or permission | Feature + security UX | [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) | **`[H1]`** firm (does not block **1.7.4**); after **Priority band A**; **Phase 0 (D-WEB)** ✅; **Phase 1** = session + **passwordless (WebAuthn)** ✅; **Phase 2** = **RBAC** ✅ (`api.rbac`, Pro+); **Phase 3** = enterprise SSO/OIDC optional ⬜ |
| [512](https://github.com/FabioLeitao/data-boar/issues/512) | Maintainer batch — P0/P1 triage + PR discipline | Process / PMO | [PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md](PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md) | **P0** — thin PRs, promote durable work into **`PLAN_*.md`** + **`plans_hub_sync --write`** |
| [483](https://github.com/FabioLeitao/data-boar/issues/483) | Public contact surfaces / domain alias policy | Docs / governance | [PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md](completed/PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md) | **Closed** — SECURITY / CoC / CONTRIBUTING alignment ([#628](https://github.com/FabioLeitao/data-boar/pull/628)) |
| [520](https://github.com/FabioLeitao/data-boar/issues/520)–[522](https://github.com/FabioLeitao/data-boar/issues/522) | CLI: validate-config, session diff, DSAR export | Feature (CLI) | [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](completed/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md) | **Closed** — slices A–C on `main`; archived plan |
| [704](https://github.com/FabioLeitao/data-boar/issues/704) | Maestro + JWT enterprise on four lab hosts | Security / licensing | [LICENSING_SPEC.md](../LICENSING_SPEC.md) · **M-PILOT-READY** | **`[H0][U0/U1]`** [P0] — before **#719**; after Wave 1 **#656** U0/U1 when operator names lab licensing slice |
| [719](https://github.com/FabioLeitao/data-boar/issues/719) | Dev env vars bypass JWT enforcement (no audit log) | Bug / security | [LICENSING_SPEC.md](../LICENSING_SPEC.md) · [DEPLOY.md](../deploy/DEPLOY.md) | **`[H0][U1]`** [P1] — after **#704** or in parallel if prod exposure confirmed; **A6** regression when fixed |
| [1210](https://github.com/FabioLeitao/data-boar/issues/1210) | Merge-secrets hardening follow-up | Security / config | [PLAN_SECRETS_VAULT.md](PLAN_SECRETS_VAULT.md) | **`[H0][U1]`** [P1] — queued after post4 trust-floor closure (2026-07-12) |
| [1211](https://github.com/FabioLeitao/data-boar/issues/1211) | Integrity fail-open hardening follow-up | Security / integrity | [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) | **`[H0][U1]`** [P1] — fail-closed integrity continuation after #1202/#1195 |
| [1212](https://github.com/FabioLeitao/data-boar/issues/1212) | GRACE follow-up (post4 trust-floor) | Security / licensing | [LICENSING_SPEC.md](../LICENSING_SPEC.md) · **M-PILOT-READY** | **`[H0][U2]`** [P1] — queued on 2026-07-12 with #1210/#1211 |
| [1182](https://github.com/FabioLeitao/data-boar/issues/1182) | Wheelhouse distribution (musl/no-AVX, cp313/cp314) | Packaging / distro | [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) | **`[H1][U1]`** [P1] — cp314 GitHub Releases seed done; expand cp313 + hosted index (`simple/`) before broad doc rollout |
| [756](https://github.com/FabioLeitao/data-boar/issues/756) | Lab Ansible: `bw` CLI + lab-node disk hygiene | Lab-op / workflow | [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md) · [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md) | **`[H0][U1]`** disk on one lab node ([#756](https://github.com/FabioLeitao/data-boar/issues/756)) · **`[U2]`** `bw` playbook — **not** release gate; see **LAB-OP** § below |
| [747](https://github.com/FabioLeitao/data-boar/issues/747) | Forensics primer first-responder checklist | Docs | [PRIMERS_HUB.md](PRIMERS_HUB.md) · parent **[#685](https://github.com/FabioLeitao/data-boar/issues/685)** | **`[H2][U3]`** [P2] — Gemini Cold **G-26-19**; after higher-band docs/man slices |
| [1056](https://github.com/FabioLeitao/data-boar/issues/1056)–[1061](https://github.com/FabioLeitao/data-boar/issues/1061) | v1.8.0 competitive survey — enrich existing plans (docs-first) | Docs / product spec | See integration bullet *v1.8.0 competitive survey*; **#1056** → [PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md](PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md) + [PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md](PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md) | **`[H2][U1]`** milestone **v1.8.0**; **one PR per issue**; order **#1056 → #1057 → #1058 → #1059 → #1061 → #1060** |

**Claude audit / doc-hygiene issue sweep (#87+, 2026-05):** Ship **thin PRs** (one subject per commit cluster; `check-all` before integration). **Sequence when titles disagree:** band in headline **`[P0]` → `[P1]` → `[P2]` → `[P3]`**, then **ascending issue #**; issues **without** a band trail the banded set, still by **#**. **Source of truth:** `gh issue list --state open --limit 200` (~**135** open as of **2026-05-20**; **no** new issues filed that day — backlog is stable, not growing overnight). **Duplicate / echo issues:** after merge + green CI, close the canonical issue then mark duplicates with evidence — [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](../ops/GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md) ([pt-BR](../ops/GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md)). **Priority discipline ([THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md)):** stay in **P1** until blocked — do **not** cherry-pick **P3** housekeeping while **P1** man/docs slices remain. **Head of queue (2026-05-20; PMO rows for #704/#719/#756/#747 added 2026-06-03):** **P0** only [#606](https://github.com/FabioLeitao/data-boar/issues/606) (Enterprise plugin hooks — product scope; defer unless operator names it). **P0/P1 licensing (lab + enforcement):** [#704](https://github.com/FabioLeitao/data-boar/issues/704) then [#719](https://github.com/FabioLeitao/data-boar/issues/719) — see **`[H0][U1]` Licensing enforcement** table. **P1 docs/man (thin):** [#431](https://github.com/FabioLeitao/data-boar/issues/431), [#444](https://github.com/FabioLeitao/data-boar/issues/444) (`data_boar.5`), then [#483](https://github.com/FabioLeitao/data-boar/issues/483) (domain/contact policy). **P2 security (thin):** [#622](https://github.com/FabioLeitao/data-boar/issues/622) (`redact_config` substring keys). **P2 docs (primers):** [#747](https://github.com/FabioLeitao/data-boar/issues/747). **Lab-op (non-gate):** [#756](https://github.com/FabioLeitao/data-boar/issues/756). **Governance closed:** [#419](https://github.com/FabioLeitao/data-boar/issues/419), [#423](https://github.com/FabioLeitao/data-boar/issues/423), [#424](https://github.com/FabioLeitao/data-boar/issues/424) via PR **#621**. **Man timeouts:** [#454](https://github.com/FabioLeitao/data-boar/issues/454) ✅ (supersedes #448 key-name drift).

**GitHub triage snapshot (refresh when batching):** Recently closed: governance **#419–#424** (PR **#621**); public contacts **#418**, **#480**, **#483** (PR **#628**); man5 **#431**, **#444**, **#622** (PR **#624**); hubs **#571**, ADR inventory **#578**, rules hub **#582–#583** (PR **#619–#620**); connectors **#502**, **#503**, **#508**, **#517**, **#495**. **Post4 trust-floor closure (2026-07-12):** merged **#1194 #1195 #1201 #1202 #1137 #1198 #1130** via PRs **#1203–#1209** and **#1214**; new queued follow-ups **#1210 #1211 #1212**. **Coordination:** [#512](https://github.com/FabioLeitao/data-boar/issues/512) (**P0** PMO batch). **CLI / evidence:** [#520](https://github.com/FabioLeitao/data-boar/issues/520)–[#522](https://github.com/FabioLeitao/data-boar/issues/522).

**Dashboard web surface cluster:** [#86](https://github.com/FabioLeitao/data-boar/issues/86) (RBAC) and [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md) (locale) share `api/routes.py` / templates. **Order:** **M-LOCALE-V1** ✅ (locale prefix on **`main`**, **2026-04**); **D-WEB** ✅; **M-MATURITY-POC** (smoke + runbook §D for full readiness) **then** **#86 Phase 1** on its own branch/PR — see [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.2 / §5 and the **Integration** bullet *Maturity self-assessment* above.

### Doc housekeeping — workflow guardrails (✅ 2026-03-22)

Post–PR **#118**: clarified **`private-layout`** vs **`docs/private/homelab`**, and **sprint theme vs token-cherry-picking**, in **`AGENTS.md`**, **`CONTRIBUTING.md`**, **`PRIVATE_OPERATOR_NOTES.md`**, **`.cursor/rules/execution-priority-and-pr-batching.mdc`**, **`TOKEN_AWARE_USAGE.md`**, **`.cursor/skills/token-aware-automation/SKILL.md`**. Ongoing source: **`AGENTS.md`** scope table + execution rule §3.

---

## Conflict and dependency analysis

| Plan                                           | Depends on                                                                                                                            | Conflicts with | Notes                                                                                                                                                                                                                                                                     |
| ----                                           | ----------                                                                                                                            | -------------- | -----                                                                                                                                                                                                                                                                     |
| Security hardening                             | —                                                                                                                                     | None           | Additive (validation, docs, audit). Do first to strengthen base.                                                                                                                                                                                                          |
| Secrets vault                                  | —                                                                                                                                     | None           | Phase A (redact, env) improves config safety before vault.                                                                                                                                                                                                                |
| Version check / self-upgrade                   | —                                                                                                                                     | None           | Backup excludes secrets (manifest); compatible with Secrets A. Optional Phase 9: .deb, apt repo, signing, bytecode-only (see plan §9).                                                                                                                                    |
| Build identity & release integrity             | Optional: C.1 manifest; SQLite migration (anchor table)                                                                               | None           | **Phase E:** persist hashes in SQLite; **`--reset-data` preserves** anchor; startup re-verify; tamper → **`-alpha`** in reports/status. Coordinate with `data_wipe` — [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md).               |
| Additional compliance samples                  | —                                                                                                                                     | None           | Config-only; samples and docs additive.                                                                                                                                                                                                                                   |
| Compressed files                               | Config loader (new keys)                                                                                                              | None           | Additive feature; optional dependency py7zr.                                                                                                                                                                                                                              |
| Content type & cloaking detection              | —                                                                                                                                     | None           | Opt-in magic-byte/MIME detection for renamed/cloaked files; more I/O/CPU; steganography out of scope for v1.                                                                                                                                                              |
| Dashboard i18n                                 | **D-WEB** ✅; **M-LOCALE-V1** ✅ on **`main`** (**2026-04**)                                                                                    | None           | **#86** Phase 1 next (session/passwordless on **`/{locale}/…`**). Optional **M-LOCALE-PLUS** (`es`/`fr`/…) + gettext backlog — [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md). |
| Dashboard mobile responsive                    | None — can ship before **D-WEB** / i18n                                                                                                | None           | CSS-first responsive layout + touch-friendly nav/tables; **M-MOBILE-V1** — [PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](PLAN_DASHBOARD_MOBILE_RESPONSIVE.md). Retest after locale prefixes or **#86**. |
| Data source versions & hardening               | —                                                                                                                                     | None           | Additive: new table data_source_inventory, new report sheets; optional CVE lookup.                                                                                                                                                                                        |
| Strong crypto & controls validation            | —                                                                                                                                     | None           | Optional flag (CLI + dashboard); new table or extend inventory; report sheet "Crypto & controls"; inference best-effort.                                                                                                                                                  |
| CNPJ alphanumeric format validation            | —                                                                                                                                     | None           | Format spec + regex/override; optional built-in or config flag; compatibility report; no change to legacy LGPD_CNPJ.                                                                                                                                                      |
| Selenium QA test suite                         | —                                                                                                                                     | None           | On-demand; optional [qa] deps; tests_qa/; report + recommendations; exclude from default pytest.                                                                                                                                                                          |
| Synthetic data & confidence validation         | —                                                                                                                                     | None           | Fixtures (files, SQL, NoSQL, shares); FP/FN + ground truth; confidence bands + operator guidance; timeouts/connectivity docs.                                                                                                                                             |
| Configurable timeouts                          | —                                                                                                                                     | None           | Global + per-target connect/read timeouts; sane defaults; connector wiring; recommendations (avoid DoS, too-fast).                                                                                                                                                        |
| Notifications (off-band + scan-complete)       | Optional: Secrets Phase A                                                                                                             | None           | Webhook notifier; scan-complete brief to operator/tenant (Slack, Teams, Telegram, etc.); recommendations.                                                                                                                                                                 |
| SAP connector                                  | Optional: Configurable timeouts                                                                                                       | None           | Add SAP (HANA/OData/RFC) to data soup; same discovery/sample/finding flow; optional [sap] extra. See PLAN_SAP_CONNECTOR.                                                                                                                                                  |
| Enterprise HR / SST / ERP / CRM / ITSM         | Optional: SAP, REST/SQL patterns, timeouts                                                                                            | None           | Umbrella: SOC (SST software), TOTVS-class ERP, CRM, folha/ponto, GLPI-class helpdesk, URM tools. Research per vendor; minimise health-data sampling. See PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.                                                                           |
| Databricks / Unity Catalog (lakehouse scan + catalog scope) | Optional: SQL connector patterns; Secrets Phase A; scope CSV / SQL emit pipeline                                                     | None           | **[H2]** **Pro/Enterprise–shaped** backlog: **(A)** Databricks SQL warehouse as **scan target** (Delta/Parquet-class tables); **(B)** UC or lakehouse **inventory tables** feeding the same **targets + `scope_import`** model as CSV exports (GLPI-class tools remain **sources** that may **land** in UC). **Customer-pull** before implementation. See PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN. |
| Findings corporate repository (export / sync beyond SQLite) | Optional: post-scan hooks; Secrets Phase A; object storage or DB drivers per customer                                                                | None           | **[H2]** **Pro/Enterprise–shaped:** prospects may require findings in **their** SQL, **MongoDB**, or **lake/object** landing zones—not **only** local SQLite. Phased: canonical **export bundle**, CLI hook, then native sinks. **Customer-pull**; may **preempt** other [H2] rows if contract requires. See PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT. |
| Scope import from exports (inventory bootstrap) | Optional: canonical schema; merge-safe config fragments                                                                              | ✅ Done (v1 CSV + GLPI on `main`; further vendor adapters backlog) | Offline exports (e.g. Live Optics, GLPI, Nagios/Cacti-class, Prometheus/Datadog/Dynatrace **exports** where available) → Data Boar target hints; early scan rounds for consultants/customer teams. Complements PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS. See [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md). |
| Additional data soup formats                   | Optional: Compressed, content-type                                                                                                    | None           | **POC tiers on `main`:** **Tier 3** rich media + **Tier 1** + **opt-in stego hints** (`[dataformats]` optional). **Tier 3b** + **Tier 4** backlog. See PLAN_ADDITIONAL_DATA_SOUP_FORMATS + **Integration / active threads**.                                                         |
| Additional detection techniques & FN reduction | Optional: Synthetic data (for validation)                                                                                             | None           | Additive: optional engines (fuzzy, stemming, format hint, embedding prototype); config thresholds; “suggested review”; reduce false negatives. See PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.                                                                 |
| Subject category axis (titular / data-subject) | Optional: PLAN_TAXONOMY_AXES; eval [#1071](https://github.com/FabioLeitao/data-boar/issues/1071) for naming/interop                                                                                  | None           | **[H2]** **superseded** by hybrid slice 1 — see [PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md](PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md). Legacy: [PLAN_SUBJECT_CATEGORY_AXIS.md](PLAN_SUBJECT_CATEGORY_AXIS.md) / [#1072](https://github.com/FabioLeitao/data-boar/issues/1072). |
| Hierarchical norm_tag + Data-Subject (hybrid #1071 slice 1) | Optional: PLAN_TAXONOMY_AXES; [#1069](https://github.com/FabioLeitao/data-boar/issues/1069) gap                                                                                                      | None           | **[H2]** **candidate v1.9.0:** BR-preserving `norm_tag` hierarchy + optional `data_subject` axis; default off. **[#1074](https://github.com/FabioLeitao/data-boar/issues/1074)**. Closes **#1069** titular dimension. |
| Data-Use axis (purpose / finalidade, hybrid slice 2) | Slice 1 loader stable (soft)                                                                                                         | None           | **[H2]** optional `data_use` axis (LGPD Art. 6/7 class labels); heuristic config; default off. **[#1075](https://github.com/FabioLeitao/data-boar/issues/1075)**. |
| Fideslang export adapter (hybrid slice 3) | Slice 1 internal taxonomy; customer-pull                                                                                            | None           | **[H3]** optional lossy `data_category` on export only; **no** `fideslang`/`ethyca-fides` dep. Closes SWOT **W-novo-1** when shipped. **[#1076](https://github.com/FabioLeitao/data-boar/issues/1076)**. |
| Home lab validation (production-readiness)     | Optional: –1/–1b maintenance in acceptable state                                                                                      | None           | Manual second-machine smoke per [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md); proves deploy + ≥1 connector path before demo/customer confidence; low token.                                                                                                      |
| Lab firewall + L3 + observability sequencing   | UniFi/DHCP baseline optional before heavy stacks; [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md) phases A–E | None           | **Spine:** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) orders phases **0–5** (firewall → assistant access → posture → optional metrics → syslog/Loki → optional Wazuh). Complements –1L; does not replace pytest/CI.   |
| Lab-OP CAPEX/OPEX & procurement spine          | Optional: latest lab-op inventory and private shopping master are updated                                                              | None           | Single tracked decision spine for priorities and justification across hardware/storage/network/power/HVAC/software/training; no prices in tracked docs. See [PLAN_LAB_OP_CAPEX_OPEX_AND_PROCUREMENT.md](PLAN_LAB_OP_CAPEX_OPEX_AND_PROCUREMENT.md).                         |
| Next wave platform + GTM alignment             | Optional: trust foundations and procurement baseline are in place                                                                        | None           | Post-trio plan for multi-format evidence outputs, modular connector/runtime roadmap, and academic-to-market evidence stream. See [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md).                                                                |
| Clojure/Lisp augmentation feasibility          | Optional: trust/commercial slices stable; one bounded PoC scenario and benchmark discipline available                                     | None           | Far-horizon R&D to test whether a Clojure sidecar improves policy reasoning or temporal evidence with acceptable overhead; keep default runtime path unchanged unless go/no-go gates are met. See [PLAN_CLOJURE_AUGMENTATION.md](PLAN_CLOJURE_AUGMENTATION.md).         |
| Compliance standards alignment                 | —                                                                                                                                     | None           | Doc only: ISO/IEC 27701 (PIMS), FELCA (minor data); COMPLIANCE_FRAMEWORKS + roadmap sentence; no code. See PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.                                                                                                                           |
| US child privacy technical alignment           | —                                                                                                                                     | None           | Config samples + EN/pt-BR docs (COPPA, CA AB 2273, CO CPA minors); no code; disclaimers for technical mapping only. See PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.                                                                                                        |
| Dashboard reports access control               | Optional: licensing / JWT claims; existing API-key middleware                                                                         | None           | Role- or group-based gates for `/reports` and downloads; GitHub **#86**. Default behaviour unchanged until opt-in config. See PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.                                                                                                      |
| Operator API key–first auth UX                 | Optional alignment with **#86** / D-WEB; **Secrets** Phase A env patterns                                                             | None           | Exploratory spike: JWT/Bearer toil → env/API key habits; **zero-trust** split; **off-band** handoff focal→technician; optional **one-shot CLI / QR transport** (OTP-like UX, standard crypto). See PLAN_OPERATOR_API_KEY_FIRST_AUTH_UX.                                   |
| Opt-in network port / service hints            | Config loader; audit/report surfaces; optional licensing                                                                              | None           | Bounded TCP connect + banner read on **allowlisted** hosts/ports only; not a full scanner. Written customer scope required. See PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.                                                                                                   |
| Object storage (S3 / Azure Blob / GCS)         | Optional: Compressed files, content-type, configurable timeouts, Secrets Phase A (env for keys)                                       | None           | **Additive** connector; list + download/stream objects then same filesystem scan path. See PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.                                                                                                                                          |
| Semgrep CI                                     | —                                                                                                                                     | None           | **Workflow only**; complements CodeQL. See PLAN_SEMGREP_CI.md.                                                                                                                                                                                                            |
| Bandit security linter                         | —                                                                                                                                     | None           | **Dev dep + CI job** (strict); config in pyproject. See [completed/PLAN_BANDIT_SECURITY_LINTER.md](completed/PLAN_BANDIT_SECURITY_LINTER.md).                                                                                                                                                                                  |
| CLI validate, session diff, DSAR export        | Config loader; optional fields from [PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md](PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md) | ✅ Done        | Operator CLI: `--validate-config`, session `--diff`, `--export-dsar` (metadata-first defaults). [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](completed/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md); [#520](https://github.com/FabioLeitao/data-boar/issues/520)–[#522](https://github.com/FabioLeitao/data-boar/issues/522) closed. |
| Maintainer issue batch and PMO sync            | `gh` CLI; CONTRIBUTING / commit ritual                                                                                                | None           | Batch P0/P1; promote issues → `PLAN_*.md` + `plans_hub_sync` / `plans-stats`. [PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md](PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md); [#512](https://github.com/FabioLeitao/data-boar/issues/512). |
| Operating domain contacts and alias policy     | —                                                                                                                                     | ✅ Done        | Doc-only: SECURITY / CoC / CONTRIBUTING contact alignment. [PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md](completed/PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md); [#483](https://github.com/FabioLeitao/data-boar/issues/483) closed. |

---

## Integrity and tamper-evidence index (planning map)

**Purpose:** Single **navigation anchor** in this file for **integrity, tamper-evidence, and trust-downgrade** work — **links + scope + non-goals** only. There is **no** separate `PLAN_INTEGRITY_*.md`; implementation detail stays in the plans below.

**Scope (what this index covers):**

- **Build / runtime / on-disk code:** optional hash manifest, SQLite anchor across wipes, startup re-verify, user-visible trust strings — [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) (Phases A–E; **E.11** audit-export baseline on `main`).
- **Transport / TLS / channel posture:** HTTPS-by-default, explicit HTTP risk, `dashboard_transport` / `enterprise_surface`; **Phase 7** certificate/trust monitoring and tamper-aware reactions — [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md).
- **Dashboard identity, sessions, FIDO2 / WebAuthn, RBAC:** route matrix, middleware order, phased passwordless then roles — [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md); GitHub [#86](https://github.com/FabioLeitao/data-boar/issues/86). Vendor-neutral WebAuthn JSON (Phase 1) — [ADR 0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md).
- **SQLite questionnaire / operator artefacts (POC):** per-row HMAC sealing, integrity summary on `/status` and `--export-audit-trail` — [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md); batch history — [ADR 0032](../adr/ADR-0032-maturity-assessment-batch-history-sqlite.md).
- **Commercial runtime trust:** embedded digest, optional release manifest, **`TAMPERED`** when licensing enforcement is on — [RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md), [LICENSING_SPEC.md](../LICENSING_SPEC.md).
- **Secure-by-default rollout constraints** (breaking-change framing): [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](../ops/SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md).
- **Supply chain inventory (dependencies / image):** [ADR 0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md), [SECURITY.md](../SECURITY.md) (SBOM filenames).
- **PII gate integrity (self-protecting seed gate) `[H0][U0]`:** word-boundary matcher, distinctive real seeds (no synthesis), CODEOWNERS + branch protection, CI modification tripwire, operator-approved per-location FP allowlist, hard rule against weakening gates — [PLAN_PII_GATE_INTEGRITY.md](PLAN_PII_GATE_INTEGRITY.md), [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md); GitHub #944.

**Non-goals (explicit):**

- This index does **not** add new commitments; it **routes** to existing plans only.
- A **local** hash manifest **without** signatures does **not** prove absence of tamper if an attacker can alter **both** code and manifest — see reality check in [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md).
- **WebAuthn JSON endpoints** and cookie helpers: **RBAC** is opt-in via **`api.rbac`** (Phase **2**); **SSO/OIDC** (Phase **3**) remains future work. Challenge store remains **in-process** unless a plan adds shared state (see ADR 0033).
- No claim of **nation-state** or **physical** tamper resistance; goals remain **supportability**, **audit narrative**, and **operator-visible** trust signals.

**Regression and tests:** No plan modifies wipe behaviour, SQLite schema (except Self-upgrade adds optional upgrade_log, Data source versions adds data_source_inventory, Strong crypto adds optional crypto_controls_audit or extends inventory), or existing config keys in a breaking way. New tests per plan must pass together with the full suite (`uv run pytest -v -W error`). Document each new feature in the relevant docs (EN + pt-BR where applicable).

---

## Review and sequence rationale

The recommended order below is chosen to:

- **Strengthen the base first:** Security hardening and Configurable timeouts reduce risk and improve robustness for all later work. **Both are already completed.**
- **Respect dependencies:** Secrets Phase A (redact, env) before Phase B (vault); Notifications can optionally use Secrets A for webhook URLs. **Phase A is completed; Phase B is deferred to a later billing cycle unless extra capacity is available.**
- **Batch additive features:** Compliance samples, Compressed files, Data source versions, and Strong crypto add config/report/sheets without breaking existing flows. **Near-term focus is on small, high-leverage slices of these plans.**
- **Defer optional or heavy work:** Version check, Selenium QA, Synthetic data, Notifications (later phases), SAP connector, **M-LOCALE-PLUS** (extra dashboard locales), and remaining **Additional data soup** items (**Tier 3b** trackers, **Tier 4** doc-layer) come after core security and scan/report features or when more usage budget is available.

## Tier summary (for planning):

- **Priority band A – Safety, IP exposure, profitability guardrails (do before resuming heavy token-aware feature slices when critical):** See table **“Priority band A”** below — Dependabot/Scout, Docker Hub tag hygiene, private issuer repo, partner access, optional `license-smoke` CI, legal/license boundary review. Does not replace cryptographic licensing; complements it.
- **Tier 1 – Foundation (completed):** Security hardening, Configurable timeouts, Secrets Phase A.
- **Tier 2 – Scan and report (POC baseline on `main`; token-efficient slices for what remains):** Compressed files ✅, Content type & cloaking ✅, Compliance samples ✅; **remaining:** Data source versions & hardening, Strong crypto & controls (orders **5–6**), SAP connector (later).
- **Tier 3 – Secrets and upgrade (deferred unless extra capacity):** Secrets Phase B, Version check & self-upgrade.
- **Tier 4 – Validation and ops (partial, high-value slices first):** CNPJ alphanumeric, Additional detection techniques & FN reduction, **Home lab smoke** (order **–1L**, after maintenance), Notifications (early phases), Selenium QA, Synthetic data & confidence, **Dashboard web surface** — optional **M-MOBILE-V1** (responsive CSS; [PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](PLAN_DASHBOARD_MOBILE_RESPONSIVE.md)); **D-WEB** ✅; **M-LOCALE-V1** ✅ (**2026-04**); **S2a** **Selected** — HTTPS **Phase 7** + **trust-state** (**4** / **4a**) paired with **#86** governance for **demo-ready** open-core signal — then **#86** Phase 1 (session/passwordless on **prefixed** paths) — see [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.2 and *Integration* **S2a**.

Plans without dependencies can be run in parallel within a tier (e.g. 4 and 5). Within a plan, execute phases in order.

---

## Recommended sequence (aggregated, token-aware)

**Optional PM view:** The same order is grouped into **token-aware sprints**, **milestones** (M-TRUST, M-OBS, M-LAB, …), **SRE/governance** notes, and **Mermaid Gantt / Kanban** patterns in **[SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)** ([pt-BR](SPRINTS_AND_MILESTONES.pt_BR.md))—useful for retros, sidequests (housekeeping, lab rush), and **operator-only** tasks (Hub, hardware, study). To see **how milestones compose** into a coherent posture (storytelling, trust baseline, paid surface, automation stretch), read **SPRINTS_AND_MILESTONES.md** section **5** subsection **Composing milestones (release lifecycle map)**—**not** alternate naming for releases; version strings follow [VERSIONING](../releases/).

The list below is ordered for the current billing cycle, with a focus on:

- **Near-term, high-value work** that fits in the remaining Pro usage.
- **AI-heavy** tasks where the agent’s help is most valuable.
- **Manual-friendly** tasks that you can do largely by hand or with existing tooling.

### H0/U0 Priority band A — Safety, security, IP exposure, profitability (sequence when critical)

Complete **in order** when you need to reduce public artifact exposure or tighten commercial posture **before** burning tokens on large feature work. Most steps are **manual on GitHub/Docker Hub** + short doc updates; use the agent for checklists, scripts, and repo docs.

| Step   | Task                                | Owner                    | Done when                                                                                                                                                         |
| ----   | ----                                | -----                    | ----------                                                                                                                                                        |
| **A1** | **Dependabot / dependency alerts**  | You + agent (PRs)        | Alerts triaged; safe merges; `pyproject.toml` + lockfiles + `requirements.txt` aligned; `.\scripts\check-all.ps1` green. Same as order **–1** in the table below. |
| **A2** | **Docker Scout / image CVEs**       | You + agent (Dockerfile) | `docker scout quickview` acceptable or documented exceptions; image rebuilt; smoke test. Same as **–1b**.                                                         |
| **A3** | **Docker Hub tag hygiene**          | **You (manual Hub UI)**  | Obsolete tags deleted or documented; only supported tags documented in [DEPLOY.md](../deploy/DEPLOY.md) §8; CI/partners confirmed not pinning removed tags.       |
| **A4** | **Private repo for issuer tooling** | **Done (2026-06-25)** | `FabioLeitao/license-studio` — see [LICENSE_STUDIO_SPINOUT.md](ops/LICENSE_STUDIO_SPINOUT.md); no signing keys in any public remote. |
| **A5** | **Partner access (e.g. collaborator)**      | **You**                  | Collaborator role on private repos as needed; no shared personal secrets via chat.                                                                                |
| **A6** | **Licensing smoke automation**      | Agent                    | `scripts/license-smoke.ps1` runs `tests/test_licensing.py` + `tests/test_licensing_fingerprint.py`; optional CI job — token-aware single session. When **[#719](https://github.com/FabioLeitao/data-boar/issues/719)** fix lands, extend smoke/regression for dev-env bypass (`DATA_BOAR_ENV` / `DEBUG`).                 |
| **A7** | **Legal / license boundary**        | **You + counsel**        | Open-core vs commercial terms documented; no repo change required for first call.                                                                                 |

**Every order –1 pass (cadence):** Briefly **re-check advisories that had no fix last time**: run **`uvx pip-audit -r requirements.txt`** (or equivalent); confirm whether **pygments** ([DEPENDABOT_PYGMENTS_CVE.md](../ops/DEPENDABOT_PYGMENTS_CVE.md)), **pyOpenSSL + Snowflake** ([DEPENDABOT_PYOPENSSL_SNOWFLAKE.md](../ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md)), or **Debian base** packages from **Docker Scout** now have a released fix — bump **`pyproject.toml` / rebuild image** when they do; otherwise keep triage docs and GitHub dismissals accurate.

**Quarterly blocked-dependency checkpoint (SECURITY.md / #427):** At least every **~90 days** (or sooner on any **–1** pass), update **Last triage** in the two Dependabot triage docs above, refresh the **SECURITY.md** checkpoint line, run **`gh api …/dependabot/alerts`** (or **Security → Dependabot**), and confirm **`uv.lock`** floors still match documented status. Last completed: **2026-05-22** (pygments **2.20.0**, pyOpenSSL **26.2.0** via Snowflake **4.5.0**).

After **A1–A3** (minimum), you can **resume token-aware pace** on Tier 2 features (e.g. content-type Step 4) unless A4–A7 are blocking revenue.

**`[H0]` Maestro + release gate (**M-PILOT-READY** drivers):**

| Item | Issue(s) | Status |
| ---- | -------- | ------ |
| Maestro SSH `ConnectTimeout` | [#403](https://github.com/FabioLeitao/data-boar/issues/403) | ✅ Done |
| benchmark-rc `targets:` key (not `scan_scope`) | [#407](https://github.com/FabioLeitao/data-boar/issues/407) | ✅ Done |
| Maestro `--bench-config` argument fix | [#404](https://github.com/FabioLeitao/data-boar/issues/404), [#408](https://github.com/FabioLeitao/data-boar/issues/408) | ✅ Done |
| Maestro Linux orchestrator (lab node: rsync/bash, `git_origin`, podman) | [#786](https://github.com/FabioLeitao/data-boar/issues/786) · [PLAN_MAESTRO_LINUX_ORCHESTRATOR.md](PLAN_MAESTRO_LINUX_ORCHESTRATOR.md) | ✅ Done (code); ⬜ lab-node pre-flight |
| Release gate **1.7.4** checklist (tag, Hub, `docs/releases/1.7.4.md`) | [#406](https://github.com/FabioLeitao/data-boar/issues/406) | ⬜ Pending — **blocked by lab provisioning** (2026-06-18, [LAB_LESSONS_LEARNED_2026_06_18.md](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md)): acceptance run never started a scan; rows below are the unblockers |
| Cross-platform completão runner (`cmd.exe` core → Linux transport) | issue TBD · [LAB_LESSONS_LEARNED_2026_06_18.md](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md) · [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) | ⬜ Pending — `lab-completao-orchestrate.ps1` dies at first remote call on the Linux primary; no orchestrated path today |
| Fleet `uv` non-interactive SSH `PATH` provisioning | issue TBD · [LAB_LESSONS_LEARNED_2026_06_18.md](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md) | ⬜ Pending — `uv` absent from non-interactive `PATH` on multiple nodes → scans never start |
| Native fast-filter build matrix (ARM wheel) | issue TBD · [LAB_LESSONS_LEARNED_2026_06_18.md](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md) | ⬜ Pending — `boar_fast_filter` x86_64-glibc + **musl wheel both build** (evidence-corrected); **ARM** is the real gap (no published ARM wheel, Build-Once); recurrence of 2026-05-13 single-node follow-up |
| `uv run` prunes locally-built wheel from `.venv` (musl) | issue TBD · [LAB_LESSONS_LEARNED_2026_06_18.md](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md) | ⬜ Pending — `musllinux` `boar_fast_filter` wheel builds but `uv run` re-resolve drops it → `ModuleNotFoundError`; ML sdists (no musl wheels) rebuild on sync. Pin/install local wheel so `uv run` keeps it |
| Auditor smoke: escalate repeated failure across nodes | issue TBD · [LAB_LESSONS_LEARNED_2026_06_18.md](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md) | ⬜ Pending — aggregate "same failure on N nodes" into one "lab-not-provisioned" verdict + abort, not per-node retry |
| `protect_canonical` guard (load-bearing in Maestro sync) | [#948](https://github.com/FabioLeitao/data-boar/issues/948) · [PLAN_MAESTRO_CANONICAL_GUARD](PLAN_MAESTRO_CANONICAL_GUARD.md) · [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) | 🔄 In progress |

**`[H0][U1]` Licensing enforcement — open GitHub issues (cluster):**

| Order | Issue | Band | U-axis | Status | Notes |
| ----: | ----- | ---- | ------ | ------ | ----- |
| 1 | [#704](https://github.com/FabioLeitao/data-boar/issues/704) | [P0] | U0/U1 | ⬜ Pending | Maestro + JWT enterprise on four lab hosts (**M-PILOT-READY** driver) |
| 2 | [#719](https://github.com/FabioLeitao/data-boar/issues/719) | [P1] | **U1** | ✅ Done | Env bypass **removed** (fail-closed + audit trail) — PR [#847](https://github.com/FabioLeitao/data-boar/pull/847) merged; QA path = 60-day machine-bound signed `.lic` (PR [#848](https://github.com/FabioLeitao/data-boar/pull/848) merged) |
| 3 | [#843](https://github.com/FabioLeitao/data-boar/issues/843) + [#705](https://github.com/FabioLeitao/data-boar/issues/705) | [P1] | U1 | ✅ Done | Connector tier gating in registry + `FEATURE_TIER_MAP` completion — PR [#849](https://github.com/FabioLeitao/data-boar/pull/849) merged; [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md) |
| 4 | [#551](https://github.com/FabioLeitao/data-boar/issues/551) | [P1] | U1 | ✅ Done | Worker cap `dbmax_workers` (enforced-only clamp + audit) + Python 3.14 CI matrix signal-only — PR [#850](https://github.com/FabioLeitao/data-boar/pull/850) merged |
| 5 | [#708](https://github.com/FabioLeitao/data-boar/issues/708)–[#722](https://github.com/FabioLeitao/data-boar/issues/722) | [P1] | U1–U2 | ⬜ Pending | Issuer ADRs, trial/grace/revocation — ascending **#** within band; promote individually when thin PR ready. **[#717](https://github.com/FabioLeitao/data-boar/issues/717) runtime kill-switch landed:** revocation list matches `sub` / `jti` / `dbkid` → fail-closed Community + `license_revoked` audit WARNING (management script + distribution process remain open in #717). Next: [#718](https://github.com/FabioLeitao/data-boar/issues/718) + [#846](https://github.com/FabioLeitao/data-boar/issues/846) fingerprint binding + deployment pack |

**Sequence:** After Wave 1 **[#656](https://github.com/FabioLeitao/data-boar/issues/656)** U0/U1 items and **#406** release gate unless operator confirms production JWT bypass (**#719** → treat as **U0**). Cross-ref Priority band **A6** and Integration bullet *Licensing enforcement*.

**GitHub triage (thin sweep 2026-05-16):** Duplicate filings closed with evidence on the canonical issue: **#437** → **#435**, **#438** → **#436** (duplicate titles for `data_boar.1` ENV / WEB INTERFACE gaps). **Update 2026-05-16:** **#434**, **#435**, **#436**, **#439**, and **#405** closed after merge **[#466](https://github.com/FabioLeitao/data-boar/pull/466)** (man §1 + `/help` + manifest; `Wait-BaremetalBenchSentinel.ps1` + `SleepBeforeCollect` fallback). Release/policy queue examples: **#418**–**#427**, **#406**.

**`[H1]` RBAC reports access — [#86](https://github.com/FabioLeitao/data-boar/issues/86)** (firm next gate; does not block **1.7.4**): ⬜ Pending — Phase 3+ / enterprise SSO/OIDC path per [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md).

**Reference:** [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md), [LICENSING_SPEC.md](../LICENSING_SPEC.md), [HOSTING_AND_WEBSITE_OPTIONS.md](../HOSTING_AND_WEBSITE_OPTIONS.md).

**`[H1]` Claims consistency / anti-overclaim gate — [#894](https://github.com/FabioLeitao/data-boar/issues/894):** ✅ Done (Phases A–D) — `tests/test_claims_consistency.py` (offline/deterministic) enforces **connector↔tier** at **build-time** (raises the #854 fail-closed) and validates `docs/CLAIMS.yml` headline-claim backing; feature↔gate stays **informative** until AST refinement (Phase E ⬜). LIGHT/automatic counterpart of the on-demand `claim-audit` (lab-op) HEAVY/manual auditor. [PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md](PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md).

**Home lab (production-readiness gate):** Sequenced as **order –1L** in the table below—run **after –1/–1b** when deps/image are in an acceptable state, **before** treating a build as demo/customer-ready without a second environment. Playbook: [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md) ([pt-BR](../ops/HOMELAB_VALIDATION.pt_BR.md)). Manual on your hardware; does not replace pytest/CI.

**Lab-op minimal stack (LAB-NODE-02 / ThinkPad LAB-NODE-01 / dedicated Linux host):** **ThinkPad LAB-NODE-01 + LMDE 7** concrete steps: [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) ([EN summary](../ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)). **Podman** + **k3s** default combo and install order: [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) ([pt-BR](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md)). **Policy:** do **not** add Nomad, Swarm, or a second orchestrator on the same host until **–1L** baseline (§1 + connector slice + optional `deploy/kubernetes/` smoke) is **green**; **Docker Desktop’s built-in Kubernetes** stays **dev-only** on the workstation and is **out of scope** for the lab-op baseline. **Spread** to other stacks **only after** this anchor is stable. **Optional observability** (Grafana, Prometheus or InfluxDB, Loki or Graylog+OpenSearch): sequenced in [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md) ([pt-BR](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)) §1 — **after** §1–§3 of the minimal stack doc. **Later (HP tower + Proxmox):** optional guests and **multi-VM** drills—see **§5** of the minimal stack doc.

### What to start next (by recommended execution under token constraints)

**Order = smallest-scope, high-value first.** Pick one when you're ready to implement; each can be done in one or a few sessions.

| Order | Plan                                                                | Why this order (scope / value)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ----- | ----                                                                | ------------------------------                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| –1    | **Dependabot & GH bots (security/maintenance)**                     | **Do early:** Review [Security → Dependabot alerts](https://github.com/FabioLeitao/data-boar/security/dependabot) and open Dependabot PRs. Apply only safe updates: edit `pyproject.toml` (or accept Dependabot PR), then `uv lock`, `uv export --no-emit-package pyproject.toml -o requirements.txt`, commit all three, run `.\scripts\check-all.ps1`. Merge only after CI green. See SECURITY.md (Dependabot SLAs, dependency policy).                                                                                                                                                                                                                                                                                                                                                                                 |
| –1b   | **Docker Hub Scout (image CVEs)**                                   | **Do early, after Dependabot:** Image on `main` uses **`python:3.13-slim`** (PR **#99**). After publish: **`docker scout quickview`** + **`docker scout recommendations`** on **`fabioleitao/data_boar:latest`** (or use **`.\scripts\docker-hub-publish.ps1`** after build — see [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md)). [Hub → Tags → Scout](https://hub.docker.com/r/fabioleitao/data_boar). Fix: Dockerfile base/digest, **and/or** **A1** dependency updates; rebuild, re-scan, `.\scripts\check-all.ps1`, smoke. Token-aware: one Scout pass + one fix round per session.                                                                                                                                                                                                          |
| –1L   | **Home lab — production-readiness smoke**                           | **When:** After –1/–1b are acceptable (or exceptions documented)—you are **ready to invest half a day on a second machine** (VM/container host), not before. **What:** Run [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md) §1 baseline (clone, tests, `docker build`, config, run, idle scan) **plus** at least one connector slice (e.g. §2 synthetic filesystem or §3 SQLite). **Proxmox / main server:** When a **hypervisor + Linux guest** becomes your lab anchor, run the same playbook **on the guest** (see [HOMELAB_VALIDATION §9.1](../ops/HOMELAB_VALIDATION.md#91-when-to-have-hardware-ready-operator-sync-with-planstodo-order-1l)). **Why:** Catches deploy/config gaps CI cannot see; high gain for production confidence; **manual, low AI tokens** (agent only for doc fixes if you find gaps). |
| 0q    | **Root QUICKSTART (5 min, DPO / non-technical)**                    | `QUICKSTART.md` at repo root (pt-BR) + [PLAN_QUICKSTART.md](PLAN_QUICKSTART.md); Docker or local lab path; links USAGE/TECH_GUIDE. GitHub **#609**. ✅ Done                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 0h    | **Hubs index + primers (GTM navigation)**                           | `docs/hubs/INDEX.md`, [PRIMERS_HUB.md](PRIMERS_HUB.md), [PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md](PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md), `scripts/check_hubs.py` in **check-all**. **#577**, **#589**, **#593**. ✅ Done                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 0     | **Compliance standards alignment (ISO/IEC 27701, FELCA)**           | Doc only: COMPLIANCE_FRAMEWORKS + roadmap; no code; smallest scope; supports pitch and audit narrative. ✅ Done                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 0a    | **US child privacy technical alignment (COPPA / AB 2273 / CO CPA) + EdTech FERPA sample** | Config samples under `docs/compliance-samples/` + COMPLIANCE_FRAMEWORKS + README + COMPLIANCE_AND_LEGAL; technical/DPO mapping disclaimers; ✅ Phase 1 ([PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.md](completed/PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.md)); **`compliance-sample-us_ferpa.yaml`** on `main` (inventory `norm_tag` **FERPA** — [PLAN_FERPA_AND_EDTECH_COMPLIANCE.md](PLAN_FERPA_AND_EDTECH_COMPLIANCE.md)).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 1     | **CNPJ alphanumeric format validation**                             | Research + regex + doc (Phase 1); focused, no schema change; high value for BR compliance. ✅ Phase 4 done                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2     | **Content type & cloaking detection**                               | Steps 1–6 done (CLI `--content-type-check`, `POST /scan` `content_type_check`, dashboard checkbox, tests, USAGE/TECH_GUIDE). Optional follow-ups: man pages, OpenAPI examples.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 3     | **Additional detection techniques & FN reduction**                  | ✅ **POC baseline on `main`** through priority **5** (`embedding_prototype_hint` + prior slices). **Next (token-aware, optional):** priorities **6+** (aggregated/incomplete-data modes, dictionaries, FK context, NER).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 4     | **Dashboard HTTPS-by-default (+ explicit HTTP risk mode)**          | Bring secure transport earlier for demo/beta confidence: native TLS>=1.2 path + explicit insecure override with warnings in logs/status/banner/audit; keep reverse-proxy compatibility. See [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 4a    | **Trust-state accelerators (GRC-inspired, runtime evidence)**       | Add trust-state contract and confidence-gated outputs (`trusted/degraded/untrusted` style) across logs/status/report/audit before broader expansion; see [PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md](PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 4m    | **Dashboard mobile responsive**                                       | **`[H3][U2]`** — iPhone/Android browsers: nav + tables + chart usable without broken layout; CSS-first; milestones **M-MOBILE-AUDIT** / **M-MOBILE-V1** in [PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](PLAN_DASHBOARD_MOBILE_RESPONSIVE.md). Independent of i18n (**D-WEB**); retest after **M-LOCALE-V1** ✅ or **#86**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 5     | **Strong crypto & controls validation**                             | Phase 1: CLI flag, config, API/dashboard checkbox, engine wiring (no criteria yet); then Phase 2 adds criteria.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 6     | **Data source versions & hardening**                                | Phase 1: `data_source_inventory` schema + save + one connector (e.g. SQL) + report sheet; one clear slice.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 7     | **Notifications (off-band + scan-complete)**                        | Phase 1: config shape + notifier module + one channel (e.g. webhook); docs and examples; medium scope.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 7a    | **Incremental filesystem scan idempotency** — Phase 1 ✅, Phase 2 ✅ — ScanObjectState table + upsert/get per ADR-0051; Phase 3 = skip-unchanged opt-in (planned). [PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md](PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md), [ADR-0051](../adr/ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md). |

**Deferred (larger or later):** Secrets Phase B, Version check & self-upgrade (incl. optional Phase 9: .deb/apt repo, signed packages, bytecode-only install, winget-like), Selenium QA, Synthetic data, SAP connector, **M-LOCALE-PLUS** (extra dashboard locales). **Backlog:** Additional data soup **Tier 3b** embedded-tracker heuristics + **Tier 4** ([PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](completed/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md)); **Tier 1** + **stego hints** + **Tier 3 rich media** are on **`main`** (see **Integration / active threads**). **Databricks / Unity Catalog** lakehouse scan + catalog-driven scope — [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) (**[H2]**, customer-pull, Pro/Ent-shaped). **Findings export / corporate repository** — [PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md](PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md) (**[H2]**, customer-pull; expedite if security review demands).

#### Resume next session (security/maintenance first, then feature work)

**Full-day suggestion (operator, offline-friendly):** [OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md](../ops/OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md) ([EN](../ops/OPERATOR_NEXT_DAY_CHECKLIST.md)) — Band A, lab-op unblocks, –1L, optional Corporate-Entity-C email, light evening wrap-up.

**If you have an open PR** with the latest plan edits (Dependabot/Scout to-dos, self-upgrade §9 .deb/apt/bytecode, **deb name availability and deps for easy deployment**): merge when ready, then continue below.

**If IP / Docker / profitability is urgent:** run **Priority band A** (table above) through at least **A3** before deep feature work; say *“Priority band A, step Ax”* to the agent (see playbook).

1. **Dependabot (order –1):** On GitHub go to **Security → Dependabot**. There are open alerts (e.g. pyOpenSSL, PyJWT, pypdf, SonarQube action). For each: either merge an existing Dependabot PR after local `check-all` and CI pass, or update `pyproject.toml` (and Actions in `.github/workflows` if needed), then `uv lock`, `uv export --no-emit-package pyproject.toml -o requirements.txt`, commit `pyproject.toml` + `uv.lock` + `requirements.txt`, run `.\scripts\check-all.ps1`, push and merge. One PR per ecosystem (pip vs github-actions) is enough; batch non-security updates if desired.
1. **Docker Hub Scout (order –1b):** Base image is **`python:3.13-slim`** on `main` (**#99**). After **build + push** (see [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md)): **`docker scout quickview`** + **`docker scout recommendations`** on **:latest**, or **`docker-hub-publish.ps1`** (runs both). Remaining CVEs: often **A1** (packages) + rebuild. `.\scripts\check-all.ps1` + smoke; document acceptable risk if needed. One review + fix round per session (token-aware).
1. **CodeQL:** Runs on push/PR to main; weekly schedule. No action unless **Security → Code scanning** shows new findings; then fix and re-run.
1. **CodeQL triage runbook skill (future, token-aware):** Create a compact Agent skill for one-command-like CodeQL triage sessions (fetch alerts, map with P0/P1/P2 matrix, propose minimal fix order, and output safe-next actions). Add when maintenance is green and we want faster recurring triage.
1. **PowerShell commit hardening (workflow):** Add a small Windows-safe helper path for multi-line commit messages (e.g. `scripts/commit-or-pr.ps1` enhancement or helper script) to avoid bash-heredoc failures in PowerShell. Target: fewer stalled release checkpoints on Win terminals; include one quick smoke test in docs.
1. **After bots and Scout are green:** Either run **order –1L** (home lab) if you want second-environment proof before the next feature burst, or continue the table in commercialization order: **HTTPS-by-default (4)** -> **Trust-state accelerators (4a)** -> **Strong crypto (5)** -> **Data source versions (6)** -> **Notifications (7)**.
1. **Study (your task):** **Through ~mid-April 2026**, primary focus = **Claude Certified Architect (CCA)** prep (Anthropic Academy / Skilljar; overview link in [PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md) §3.0). Keep **band A** on a thin cadence in parallel. **After that window** (or after a first CCA attempt), resume **paid cyber** (CWL §3.2, `docs/private/Learning_and_certs.md`): BTF → C3SA → MCBTA → PTF → …; one major lane at a time. Retake CCA later in the year if needed—knowledge still helps the product. Slot fixed study blocks (e.g. 1–2 sessions/week) after one feature slice; don’t mix deep study with same-day agent-heavy coding (token-aware). **Optional PUCRS extension certificates** (governance, criminal compliance, ethics—aligned with TCC narrative): planning table in PORTFOLIO §3.3; take **one course at a time** and prefer the **alternating “other”** study week (§3.0) so CWL stays the primary paid cyber lane unless you deliberately pause it. **Checklist:** [OPERATOR_MANUAL_ACTIONS.md](../ops/OPERATOR_MANUAL_ACTIONS.md). **After lato sensu:** post-lato options in PORTFOLIO §4.2.

### Compliance standards alignment (ISO/IEC 27701, FELCA) – [PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md](completed/PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md)

Doc-only; supports pitch and audit narrative. No code changes.

| # | To-do                                                                                               | Status |
| - | -----                                                                                               | ------ |
| 1 | Add subsection "Auditable and management standards" in COMPLIANCE_FRAMEWORKS.md (EN); link to plan. | ✅ Done |
| 2 | Add equivalent subsection in COMPLIANCE_FRAMEWORKS.pt_BR.md.                                        | ✅ Done |
| 3 | Update roadmap sentence in README.md (ISO/IEC 27701, FELCA, auditable/regional standards).          | ✅ Done |
| 4 | Update roadmap sentence in README.pt_BR.md equivalently.                                            | ✅ Done |
| 5 | PLANS_TODO: plan status, dependency row, "What to start next" order 0, this to-do block.            | ✅ Done |

### US child privacy technical alignment (COPPA / AB 2273 / CO CPA minors) – [PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.md](completed/PLAN_US_CHILD_PRIVACY_TECHNICAL_ALIGNMENT.md)

Config samples + product docs; **not** legal advice. **Phase 1** documents optional YAML profiles and external-facing disclaimers.

| # | To-do                                                                     | Status |
| - | -----                                                                     | ------ |
| 1 | Add three `compliance-sample-us_*.yaml` files.                            | ✅ Done |
| 2 | COMPLIANCE_FRAMEWORKS (EN + pt-BR): table rows + US subsection.           | ✅ Done |
| 3 | compliance-samples README (EN + pt-BR).                                   | ✅ Done |
| 4 | COMPLIANCE_AND_LEGAL (EN + pt-BR): paragraph without `docs/plans/` links. | ✅ Done |
| 5 | README pitch line (EN + pt-BR).                                           | ✅ Done |
| 6 | PLANS_TODO: status line, dependency row, order **0a**, this block.        | ✅ Done |

### Extended sensitive discovery positioning (clinical adjacency, IP, security artifacts) – [PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md](PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md)

Doc-first wave 1 shipped; **v1.8.0 wave 2 ([#1056](https://github.com/FabioLeitao/data-boar/issues/1056))** adds explicit entity taxonomy (SWIFT, IBAN, VIN, MAC, CVV/expiry, AWS keys, PIN).

| # | To-do                                                                                         | Status |
| - | -----                                                                                         | ------ |
| 1 | COMPLIANCE_AND_LEGAL.md: new section (EN) + pointer to docs/README for internal plans.        | ✅ Done |
| 2 | COMPLIANCE_AND_LEGAL.pt_BR.md: equivalent section (pt-BR).                                     | ✅ Done |
| 3 | COMPLIANCE_FRAMEWORKS.md + pt_BR: short cross-link to COMPLIANCE_AND_LEGAL (no `docs/plans/`). | ✅ Done |
| 4 | Add this plan file; run `plans_hub_sync.py --write` and `plans-stats.py --write`.             | ✅ Done |
| W2.1 | Wave 2 positioning section + cross-link PLAN_ADDITIONAL #1056 table ([#1056](https://github.com/FabioLeitao/data-boar/issues/1056)) | ✅ Done (docs PR) |
| W2.2 | Optional `compliance-sample-global_identifiers.yaml` stub (regex + disclaimers) | ⬜ Pending |
| W2.3 | COMPLIANCE_FRAMEWORKS pointer when sample lands (no overclaim) | ⬜ Pending |

## [H0] Maintainer PMO — GitHub triage ↔ `docs/plans/`

### Maintainer issue batch and PMO sync – [PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md](PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md)

**`[H0][U0]`** process — GitHub [#512](https://github.com/FabioLeitao/data-boar/issues/512).

| Phase | To-do | Status |
| ----- | ----- | ------ |
| 1.1–1.4 | Refresh open-issue snapshot; batch thin PRs; close with evidence | 🔄 Tracked |
| 2.1–2.2 | Promote multi-step threads into `PLAN_*.md` + dependency rows | 🔄 Tracked |
| 3.1 | `plans_hub_sync.py --write` and `plans-stats.py --write` after hub/dashboard inputs change | ⬜ Pending |

## [H1] CLI operator tools and public contact policy

### CLI validate, session diff, DSAR export – [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](completed/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md) *(archived)*

**`[H1][U1]`** — GitHub [#520](https://github.com/FabioLeitao/data-boar/issues/520), [#521](https://github.com/FabioLeitao/data-boar/issues/521), [#522](https://github.com/FabioLeitao/data-boar/issues/522).

| Phase | To-do | Status |
| ----- | ----- | ------ |
| A.1–A.4 | `--validate-config` (or agreed name): CLI + tests + USAGE / operator-help | ✅ Done |
| B.1–B.3 | Session `--diff`: inputs, stable output format, regression fixtures | ✅ Done |
| C.1–C.3 | `--export-dsar`: metadata-first default, explicit opt-in for samples, docs | ✅ Done |

### Operating-domain contacts and alias policy – [PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md](completed/PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md) *(archived)*

**`[H1][U1]`** docs — GitHub [#483](https://github.com/FabioLeitao/data-boar/issues/483).

| # | To-do | Status |
| - | ----- | ------ |
| 1 | SECURITY (EN + pt-BR): single coherent disclosure path | ✅ Done (GitHub advisories / Issues; no personal email per [#483](https://github.com/FabioLeitao/data-boar/issues/483)) |
| 2 | CODE_OF_CONDUCT pair: escalation matches SECURITY | ✅ Done (Contributor Covenant 2.1, PR **#621**; `conduct@databoar.com.br` enforcement contact) |
| 3 | CONTRIBUTING pair: vulnerability reporting points to SECURITY | ✅ Done ([CONTRIBUTING.md](../../CONTRIBUTING.md) → [SECURITY.md](../../SECURITY.md)) |
| 4 | Close #483 with file list + plan link | ✅ Done (PR **#628**; closes **#418**, **#480**, **#483**) |

### Release image hardening (distroless + grype VEX) – [PLAN_IMAGE_HARDENING.md](completed/PLAN_IMAGE_HARDENING.md)

**`[H1][U1]`** — GitHub [#1028](https://github.com/FabioLeitao/data-boar/issues/1028) `[P2][build][security]`. **Done** — PR-A merged (#1041); PR-B grype VEX + gate scripts + `.grype.yaml`. Distroless **nonroot** runtime; **`grype --fail-on high --only-fixed`** with documented VEX.

| Slice | To-do | Status |
| ----- | ----- | ------ |
| **PR-A** | Multi-stage distroless + smoke/TLS/PyO3 | ✅ Merged |
| **PR-B** | `.grype.yaml` VEX; `grype-image-gate` scripts; release docs | ✅ PR-B branch |

### Corporate-Entity-C 2026-03-18 — evolution review (9.1/10) and follow-ups

External review PDF (local): `docs/feedbacks, reviews, comments and criticism/analise_evolucao_data_boar_2026-03-18.pdf`. **In-repo tracking:** [Corporate-Entity-C_ANALISE_2026-03-18.md](Corporate-Entity-C_ANALISE_2026-03-18.md).

Second review cycle (premium WABIX, 2026-03-23): PDF `docs/feedbacks, reviews, comments and criticism/analise_evolucao_data_boar_2026-03-23_premium_wabix.pdf`. **In-repo tracking:** [Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md](Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md).

| Follow-up                                            | Status                         | Notes                                                                                                                                                                                                                                                                                                                |
| ---------                                            | ------                         | -----                                                                                                                                                                                                                                                                                                                |
| KPI panel (release / CI / security ops)              | ✅ Done (baseline) (**W-KPI**)  | Baseline defined in `PLAN_READINESS_AND_OPERATIONS.md` §4.7 with 2 manual KPIs (CI pass rate, security maintenance latency). Next slice: optional lightweight automation/export.                                                                                                                                     |
| Contract tests (reports + critical APIs)             | ✅ Done (**W-CONTRACT**)        | Report/heatmap artifacts regression: `tests/test_report_trends.py`; API/OpenAPI contract responses: `tests/test_routes_responses.py`.                                                                                                                                                                                |
| Decouple detector/report rules                       | 🔄 Incremental (**W-DECOUPLE**) | Small modules (e.g. fuzzy helper); Sonar complexity gates.                                                                                                                                                                                                                                                           |
| Doc snapshot per release                             | ✅ Baseline                     | `docs/releases/X.Y.Z.md` per version; **latest published stable: 1.7.4** (`docs/releases/1.7.4.md`, tag **`v1.7.4`**, GitHub + Hub **2026-06-26**); prior golden **1.7.2+safe** (`docs/releases/1.7.2-safe.md`, **`v1.7.2-safe`**); prior **1.7.3** and **1.7.1** notes remain in `docs/releases/1.7.3.md` and `docs/releases/1.7.1.md`. Optional “frozen bundle” → backlog.                                                                                                                   |
| Security vuln triage routine                         | 🔄 Tracked                      | **1.6.4 slice:** **A1** certifi **#101**, pyOpenSSL/Snowflake triage doc + **`maintenance-check`** Dependabot **alerts** section **#102–#103**; open GH alerts acceptable per backlog. Ongoing: Priority band **A1–A3**, `scripts/maintenance-check.ps1`, `SECURITY.md`.                                             |
| **Release 1.6.4** (VERSIONING + GitHub + Docker Hub) | ✅ Done (**W-REL-164**)         | **#104** on `main`; tag **`v1.6.4`**; [GitHub Release](https://github.com/FabioLeitao/data-boar/releases/tag/v1.6.4); **`fabioleitao/data_boar:1.6.4`** and **`:latest`** (digest `sha256:9081adbb03193a0a6c57b8218d57fc5fb47e7dc5867dccfdad81aac788f27623`); maintenance **#99–#103** + publish-order / Scout docs. |
| Aggregated “incomplete sample” wording               | ✅ Done                         | Cross-ref sheet note row + recommendation text.                                                                                                                                                                                                                                                                      |
| Staging fuzzy config                                 | ✅ Example                      | `deploy/config.staging.example.yaml`, `deploy/STAGING_CONFIG.md`.                                                                                                                                                                                                                                                    |
| Baseline path clarity for next Corporate-Entity-C exchange       | ✅ Doc + email draft (EN)       | Canonical list + copy-paste: [docs/ops/Corporate-Entity-C_IN_REPO_BASELINE.md](../ops/Corporate-Entity-C_IN_REPO_BASELINE.md) § email. Operator sends when ready; cite `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md` explicitly.                                                                                                                 |
| Notifications track (off-band + scan-complete)       | ✅ Phase 1–4.2 + script audit   | Multi-channel, tenant routing, dedupe, `notification_send_log`; `notify_webhook.py` writes audit via `sqlite_path`; Phase 4.3 digest/i18n → backlog ([PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md)).                                                            |

**LAB-OP (batch sync + inventory):** ✅ Docs + script aligned — [HOMELAB_HOST_PACKAGE_INVENTORY.md](../ops/HOMELAB_HOST_PACKAGE_INVENTORY.md) §4, **`scripts/lab-op-sync-and-collect.ps1`**, manifest + runbook under **`docs/private/homelab/`** (gitignored; template **`docs/private.example/homelab/LAB_OP_SYNC_RUNBOOK.md`**). **Open on hosts:** **`<lab-host-2>`** / secondary **SBC** — resolve local edits blocking **`git pull`** on **`scripts/homelab-host-report.sh`**, then re-run collect (or **`-SkipGitPull`** for report-only).

**LAB-OP — Ansible + host hygiene ([#756](https://github.com/FabioLeitao/data-boar/issues/756)):** ⬜ Pending — **`[H0][U1]`** free disk on one lab node (~**90%**; may block completão smoke and bare **`notes-sync`** mirror on that node) · **`[H0][U2]`** add **`bw`** (Bitwarden CLI) to the lab Ansible playbook for idempotent lab-op secret fetch. **Not** a **1.7.4** / **M-PILOT-READY** release-gate blocker per issue body — operator-paced on the lab-node/LMDE session; carryover from [OPERATOR_TODAY_MODE_2026-05-29.md](../ops/today-mode/OPERATOR_TODAY_MODE_2026-05-29.md). **Next:** `ssh` hygiene on that node (host details in the private manifest — [#756](https://github.com/FabioLeitao/data-boar/issues/756)), then playbook task + **`lab-op-sync-and-collect.ps1`** re-run.

**LAB-OP — URGENT (operator, electrical + purchasing):** 🔄 **Partial (private notes)** — **Done in operator copy of** **`docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.md`:** main **breaker** (**Schneider Easy9 C50**), **inverter** label (**Growatt MIC 3000TL-X**), **floor panels** §7.5–§7.7 (**Quarto** = lab **20 A** circuit), **split** on panel. **Still ⬜:** **Enel meter** photo (demand / limits as shown). **Clarified (operator):** no **second panel on the lab floor** — another panel exists on a **different floor** (living/kitchen area); optional photo for mapping only. Optional appliance label photos (fridge, chest freezer; occasional washer/microwave) noted in private **§0** — **not** a blocker. Meter gap **blocks** fully confident UPS sizing and Enel load-increase paperwork. Cover note (no prices): [LAB_OP_SHOPPING_LIST_COVER_NOTE.md](../private.example/homelab/LAB_OP_SHOPPING_LIST_COVER_NOTE.md). See [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](../ops/HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md). **Private synthesis / dream-tier shopping:** same file **§12**.

**LAB-OP — Wazuh (optional SIEM):** ⬜ **Deferred** — vuln mapping, hardening/CIS-style dashboards, centralized security reports on homelab hosts. **After** [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §1–§3 stable; prefer dedicated VM/LXC for manager (§6). Not required to validate Data Boar itself.

## Next slices (same trail — after lab-op stable + –1L policy):

1. **Corporate-Entity-C email:** Send paths from [Corporate-Entity-C_IN_REPO_BASELINE.md](../ops/Corporate-Entity-C_IN_REPO_BASELINE.md); cite `Corporate-Entity-C_ANALISE_2026-03-18.md` (and 2026-03-23 premium note if useful).
1. **Deploy hardening:** ✅ `docs/deploy/DEPLOY*.md` already call out `api.require_api_key`; **Kubernetes** aligned: [deploy/kubernetes/README.md](../deploy/kubernetes/README.md) § Security + comments in `configmap.yaml`. Compose/K8s operators still must set secrets in **their** env.
1. **Notifications Phase 4.3+** (digest, i18n) — backlog: [PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md).
1. **Maturity checklist:** [Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md](Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md) § **Maturity trail**.

### Secure default host binding (Wabix P0/P1 follow-up)

Tighten runtime defaults for the API host. Implemented: default `127.0.0.1`, opt-in `0.0.0.0` via `api.host`, docs and tests.

| # | To-do                                                                                                                                               | Status |
| - | -----                                                                                                                                               | ------ |
| 1 | Default host loopback for desktop: make the API bind to `127.0.0.1` by default when running as a normal process (CLI/desktop).                      | ✅ Done |
| 2 | Explicit opt-in for `0.0.0.0`: only bind to all interfaces when explicitly requested in config/CLI, or in container entrypoints where it is fenced. | ✅ Done |
| 3 | Docs: add a short note in `USAGE.md` / `USAGE.pt_BR.md` and `deploy/DEPLOY*.md` explaining the difference and safer recommended host settings.      | ✅ Done |
| 4 | Tests: add 1–2 small tests around API startup config (host value chosen from config vs CLI) to avoid regressions in future releases.                | ✅ Done |

### Documentation and sync reminders

- **Operator help sync (CLI, man, web, OpenAPI):** After new flags or API fields, keep **argparse `--help`**, **`docs/data_boar.1`**, **`docs/USAGE.md` / `USAGE.pt_BR.md`**, dashboard **`/help`**, and **OpenAPI** aligned. Checklist and bind-order notes: [OPERATOR_HELP_AUDIT.md](../OPERATOR_HELP_AUDIT.md). Regression: `tests/test_operator_help_sync.py` + `tests/operator_help_sync_manifest.py` (CLI, `/help`, man §1).
- **pt-BR translation review:** ✅ **Done (baseline)** — Locale sweep + **`tests/test_docs_pt_br_locale.py`** guard **`.pt_BR.md`**; **`.cursor/rules/docs-pt-br-locale.mdc`** + chat rule **`operator-chat-language-pt-br.mdc`** keep **pt-BR** (not pt-PT) for docs and dialogue. **Ongoing:** when syncing EN → pt-BR, still prefer **natural** wording over literal translation; extend the pytest allowlist/patterns if new false positives appear.
- **Legacy remote / branches cleanup (non-blocking):** Tidy local branches still tracking an optional **legacy** remote (often `*-legacy-and-history-only`, not `python2-…`); verify no active work, repoint upstream to **data-boar** or delete locally. Step-by-step: [ops/BRANCH_AND_DOCKER_CLEANUP.md](../ops/BRANCH_AND_DOCKER_CLEANUP.md) §7 · [REMOTES_AND_ORIGIN.md](../ops/REMOTES_AND_ORIGIN.md).
- **PyPI publish:** Product and **`pyproject.toml`** name are **`data-boar`**. First publish to the Python Package Index is **scheduled with the release process** (not blocking day-to-day dev). **Docker Hub** image: `fabioleitao/data_boar`.
- **Operator reachability (non-blocking):** Prefer **two channels** (e.g. GitHub notifications + **Slack** and/or **Signal** via Docker REST bridge). **Telegram is not** used for Data Boar ops (maintainer policy). Policy: [OPERATOR_NOTIFICATION_CHANNELS.md](../ops/OPERATOR_NOTIFICATION_CHANNELS.md) ([pt-BR](../ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)).
- **KPI snapshot automation (optional):** Weekly `scripts/kpi-export.py` via Actions `workflow_dispatch` or schedule → artifact or chat excerpt; see [PLAN_READINESS_AND_OPERATIONS.md](PLAN_READINESS_AND_OPERATIONS.md) §4.7.

### Operator API key–first auth UX (exploratory sidequest) – [PLAN_OPERATOR_API_KEY_FIRST_AUTH_UX.md](PLAN_OPERATOR_API_KEY_FIRST_AUTH_UX.md)

**Goal:** Cut **JWT / long Bearer paste** toil and misconfiguration; default operator habit to **API key + env** (Data Boar `api.require_api_key`) and **`token_from_env` / `oauth2_client`** for scan targets — **no custom token/crypto**. **`[H3][U2]`** · session keyword **`sidequest`** · subtype **`exploratory`**.

| # | To-do                                                                                                                   | Status    |
| - | -----                                                                                                                   | ------    |
| 1 | **S1:** Inventory where docs/scripts imply manual JWT/Bearer for routine automation                                     | ⬜ Pending |
| 2 | **S2:** One concrete operator pattern (env var names, curl, Compose/K8s secretRef) + doc gaps                           | ⬜ Pending |
| 3 | **S3:** If HTML dashboard is the pain: handoff note to **#86** / D-WEB (cookie vs header)                               | ⬜ Pending |
| 4 | **S4:** Record spike exit **A** (docs only) / **B** (small UX) / **C** (defer)                                          | ⬜ Pending |
| 5 | **S5:** Policy sketch — least-privilege split, **off-band** focal→technician, one-shot CLI / QR-as-transport (see plan) | ⬜ Pending |

### H1/U1 A. Near-term focus (current billing cycle)

1. **Home lab validation (order –1L)** *(manual, high gain for prod readiness)* — **Progress:** primary LAN host running dashBOARd + real scans. **Sub-slice closed (2026-04-08):** dev workstation — `docker-lab-build.ps1` → `data_boar:lab`, Docker smoke with `CONFIG_PATH` + mounted synthetic FS, `/health` OK, scan completed with findings; **`lab-op-sync-and-collect.ps1`** OK (LAB-NODE-04, LAB-NODE-03, lab-node-02, lab-node-01; logs under `docs/private/homelab/reports/`). **Still open for full –1L gate:** second-environment / distro matrix per [HOMELAB_VALIDATION §9](../ops/HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros) (not only this PC). **Sequence (staged):** **(A)** **Now —** second **x86_64** host (e.g. musl-based distro) + **ARM SBC**: minimum §1.1–1.2 + §2 synthetic FS per [HOMELAB_VALIDATION §9](../ops/HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros); optional Docker §1.3–1.5. **Early option:** **Linux** guests on the **primary laptop** via **GNOME Boxes** / **virt-manager** — [§1.5](../ops/HOMELAB_VALIDATION.md#15-vms-on-the-primary-laptop-gnome-boxes--virt-manager--smoke-before-proxmox) (not a Proxmox substitute); **FreeBSD** / **Haiku** there are **exploratory** only. **(B) When your x86 tower is online as main server** (e.g. **HP ML310e Gen8–class** + **Proxmox**): **before** a dedicated “main server” validation block, finish **your** manual install — Proxmox, **≥1 Linux VM or LXC** (Debian/Ubuntu guest recommended), bridge/VLAN + disk as in [§9.1 readiness table](../ops/HOMELAB_VALIDATION.md#91-when-to-have-hardware-ready-operator-sync-with-planstodo-order-1l); then run **§1 + §2 on the guest** and optionally host long-lived **§4** DB lab there. **(C) Deferred —** **Intel Mac mini (mid-2011)** until hardware is repaired; **lowest** priority row in §9 matrix (legacy macOS / Python ceiling — document in private notes when live). **(D) Secondary laptop (modern business class — e.g. ThinkPad LAB-NODE-01 Gen 3–4–class)** — **prioritise soon** if it has **more CPU/RAM** than older lab laptops: use as **parallel Docker / pytest** runner ([HOMELAB_VALIDATION §9.2](../ops/HOMELAB_VALIDATION.md#92-parallel-testing-rig-optional--secondary-laptop-or-tower-guest)); bare **Linux + Docker** or **Win11+WSL2**. **(E) Optional spare desktop —** older **Core i3**–class tower only **if** you need more **metal**: not a prerequisite—see [HOMELAB_VALIDATION §9](../ops/HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros) (*Spare commodity x86_64 desktop*) and [§9.1](../ops/HOMELAB_VALIDATION.md#91-when-to-have-hardware-ready-operator-sync-with-planstodo-order-1l). Record **dated** host-specific names/IPs/paths and **exact MTM** (machine type) only in `docs/private/` (gitignored). No feature code unless you document a gap.

1. **Maestro completão hardening follow-ups (2026-05-09 lessons, pre-`1.7.4-rc`)** *(technical queue promoted from latest public lab snapshot)*
   Source: [`docs/ops/LAB_LESSONS_LEARNED.md`](../ops/LAB_LESSONS_LEARNED.md) + [`docs/ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md`](../ops/lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md).

| # | To-do | Status |
| - | ----- | ------ |
| 1 | **Synthetic DB stack parity in Maestro path:** dedicated handlers are in place (`target_postgres`, `target_mariadb`, `target_mongodb`) and validated in a single run for reachable hosts (Mongo temporarily colocated on a secondary x86 lab host while WSL2 SSH remains down). | ✅ Done |
| 2 | **Collect/exit semantics split:** separate hard-fail exits from mixed online/offline warning outcomes so successful online rounds are machine-readable without false-red release signals. | ✅ Done |
| 3 | **Web readiness gate for long monitor loops:** add optional pre-loop check when `/health` is expected; fail-fast or downgrade to warning by explicit mode, then continue with deterministic behavior. | ✅ Done |
| 4 | **DB target port-collision fallback:** add deterministic fallback or prebind guard when configured DB target port is already occupied on host (latest hit: Postgres `55432` on a lab laptop class host). | ✅ Done |
| 5 | **WSL2 target SSH readiness:** move designated WSL2 lab host from `NETWORK ONLY` to `SSH UP` and execute one Mongo target round as part of completão evidence. | ✅ Done (scope decision) |
| 6 | **Sync strictness on failed transfer:** ensure `Sync-WorkingTree` hard-stops handler dispatch when `rsync` warns/fails (latest run had one lab laptop class host sync warning while orchestration proceeded). | ✅ Done |

1. **Post-`1.7.4` short-sprint closure queue** *(healthy next slices already scoped for execution)*
   Source plans: [`PLAN_BANDIT_SECURITY_LINTER.md`](completed/PLAN_BANDIT_SECURITY_LINTER.md), [`PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md`](completed/PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md), [`PLAN_SCOPE_IMPORT_FROM_EXPORTS.md`](completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md), [`PLAN_YAML_PLUGIN_SYSTEM.md`](PLAN_YAML_PLUGIN_SYSTEM.md).

| Sprint | Slice | Execution focus | Exit checklist | Status |
| ------ | ----- | --------------- | -------------- | ------ |
| S1 | **Bandit Phase 3 closure** | Triage low findings (`-i`) and keep strict gate (`-ll -ii`) clean with minimal-risk fixes / justified suppressions | `uv run bandit -r . -c pyproject.toml -ll -ii` green; low triage documented; `check-all` green; plan → `completed/` + `plans_hub_sync` | ✅ Done — [PLAN_BANDIT_SECURITY_LINTER.md](completed/PLAN_BANDIT_SECURITY_LINTER.md) |
| S2 | **Scope import Phase E (light)** | First vendor-shaped adapter (GLPI-like export to canonical CSV/schema), with fixtures/tests and docs | adapter + fixtures merged; pytest for adapter green; EN+pt-BR operator docs updated; no "live integration" overpromise | ✅ Done — `config/scope_import_glpi.py`, `scripts/scope_import_glpi.py`, 12 tests |
| S3 | **CNPJ Phase 5 (checksum layer)** | Design and optional opt-in checksum validation path (separate from regex compatibility) | Phase 5.1–5.3 addressed in plan; default behavior unchanged; tests/docs synced (EN + pt-BR) | ⬜ Pending |
| S4 | **YAML-Based Plugin System — Phase 1** | Centralized schema (`config/plugin_schema.yaml`), validator (`config/plugin_validator.py`), unified `patterns_plugin_file` key | `validate_plugin_file()` validates all example files; 14 tests green; `lint-only` green; ADR-0052 created | ✅ Done |
| S4b | **PCI-DSS v4 stress + YAML plugin Phase 1b (context gates)** | Extend ADR-0052 (`plugin_schema` / `plugin_validator`) and detector so optional fields (e.g. proximity keywords, metadata) are real gates—not YAML-only; PAN/Luhn path; reduce double-fire vs built-in `CREDIT_CARD`; align `docs/compliance-samples/compliance-sample-pci_dss.yaml` | `check-all` green; synthetic noisy financial corpus tests; EN operator doc touch (`SENSITIVITY_DETECTION` or compliance sample header); carryover row closed or dated defer | ⬜ Pending |

1. **Content type & cloaking detection – Step 1** *(small slice)*
   - Magic-byte table + read_magic / infer_content_type for supported formats; no connector change yet.

1. **Data source versions & hardening – schema and report design** *(AI-heavy design, light implementation)*
   - Use AI for: `data_source_inventory` schema, inventory/report sheet layout, design for one reference connector.
   - Do manually: implement that connector incrementally; add others in later cycles.

1. **Strong crypto & controls validation – criteria + wording** *(AI-heavy criteria/report, manual plumbing)*
   - Use AI for: strong-crypto matrix per connector type, “Crypto & controls” sheet layout, disclaimers.
   - Do manually: add CLI/config flag, implement persistence for one connector, basic tests.

1. **Additional detection techniques & FN reduction – next slices** *(mixed)*
   - Done in repo: MEDIUM threshold, suggested review, `column_name_normalize_for_ml`, multi-connector persist LOW ID-like.
   - Use AI for: fuzzy-match design (plan §3), aggregation wording, optional format hints.
   - Do manually: config + detector wiring, tests, docs (EN + pt-BR).

1. **Notifications (off-band + scan-complete) – Phase 1–3** *(config, `utils/notify.py`, scan-complete, `operator.channels`, `tenant.by_tenant`, dedupe per session)*
   - **Next optional:** audit log of sends, tighter per-channel caps, more unit tests ([PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md) Phase 4).

### H2/U2 B. Deferred to after billing reset (or if on-demand spend is enabled)

1. **LAB-OP — Firewall, access, observability (sequenced)** — **`[H2][U2]`** Master order **0→5**: L3/DHCP/DNS + firewall baseline → safe assistant access (API `.env`, scripts) → security posture cadence → optional metrics (Prometheus **or** Influx) → **syslog + Loki** → optional **Wazuh**. **Plan:** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) ([pt-BR](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md)). **Technical phases A–E:** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md). **Prereq:** [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §1–§3 for container anchor; do **not** run all heavy stacks on one **≤16 GB** laptop. ⬜ Backlog (operator-paced).
1. **LAB-OP — CAPEX/OPEX & procurement spine** — **`[H2][U2]`** Central budget-aware planning for hardware, storage, network redundancy, power/utility envelope, HVAC, software/subscriptions/tokens/training. Keep tracked rationale and priorities without prices; keep real costs and vendors private only. **Plan:** [PLAN_LAB_OP_CAPEX_OPEX_AND_PROCUREMENT.md](PLAN_LAB_OP_CAPEX_OPEX_AND_PROCUREMENT.md). ⬜ Backlog (operator-paced; promote P0 items by evidence).
1. **Next wave — Platform + GTM alignment** — **`[H2][U2]`** Execute the next three fronts after trust/procurement baseline: (N1) multi-format evidence outputs + trend delta metrics, (N2) modular connector/runtime architecture and dependency packs, (N3) academic-to-market evidence stream with public-safe artifacts. **Plan:** [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md). ⬜ Backlog (promote as current trio stabilizes).
1. **LAB-OP — Observability stack (optional)** — Phases A–E in [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md): Grafana + (Prometheus **or** InfluxDB); logs via (Loki **or** Graylog+OpenSearch); avoid running everything on a **≤16 GB** LAB-NODE-01 at once. **Prereq:** [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §1–§3; **§7** pointer. **Sequence:** prefer [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) **phase 4 before 5** (logs before Wazuh). ⬜ Backlog.
1. **LAB-OP — Wazuh rollout (optional)** — When resources and baseline allow: deploy Wazuh manager + enroll lab-op / Proxmox guests as agents for vuln and hardening telemetry. **Prereq:** [LAB_OP_MINIMAL_CONTAINER_STACK.md](../ops/LAB_OP_MINIMAL_CONTAINER_STACK.md) §6 sequence; **after** centralized logs per [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) **phase 4**. Operator runbook + retention/noise tuning stay in **`docs/private/homelab/`**. ⬜ Backlog.
1. **Corporate-Entity-C backlog (token-aware, non-blocking)** — **W-KPI baseline done** (manual KPI panel in readiness plan). Next optional slice: automate KPI extraction/export when maintenance is green. (W-CONTRACT already covered by existing contract tests for reports + OpenAPI responses.)
1. **PII guard expanded (documented)** — ✅ Implemented (2026-05): `tests/test_pii_guard.py` upgraded to also detect AWS AKIA keys, GitHub PATs, Slack tokens, Stripe keys, PEM headers, and Bearer tokens. No dedicated plan needed; CI-enforced via pre-commit and GitHub Actions. Workspace fact recorded in `AGENTS.md`.
1. **`scan_scope:` config key trap — deprecation notice** — ✅ **Done:** `config/loader.py` `normalize_config()` emits **`logging.WARNING`** when `scan_scope:` is present (ignored; use `targets:`). Test: `tests/test_database.py::test_scan_scope_key_emits_warning`. Workspace fact in `AGENTS.md`.
1. **Secrets vault – Phase B** – full vault implementation, re-import CLI/web, optional remove-from-config, and key management docs.
1. **Version check & self-upgrade** – version fetch, CLI/API, backup/restore, container detection, audit log.
1. **Selenium QA test suite** – full UI automation suite, stress tests, QA reports.
1. **Synthetic data & confidence validation** – fixtures across all formats, precision/recall tooling, confidence bands in reports (feeds **W-CONTRACT**).
1. **SAP connector** – research, connector module for HANA/OData/RFC, docs and tests.
1. **Dashboard i18n** – **M-LOCALE-V1** ✅ on **`main`** (**2026-04**); **D-WEB** ✅. **Next:** [#86](https://github.com/FabioLeitao/data-boar/issues/86) **Phase 1** (session/passwordless on **`/{locale}/…`**). Coordinate **#86** with [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md).

### H3/U3 C. Backlog (catalogue)

**Promotion rule:** Catalogue rows below (and similar **H3** items such as **Tier 1** soup formats, **data source versions**, **strong crypto** validation, **SAP** connector, **Selenium** QA) stay here until a **named issue**, plan subsection, or engagement promotes a **single** slice—avoid scheduling several unpromoted H3 threads into one release.

**Narrative & architecture history (single doc):** Placeholder [NARRATIVE_AND_ARCHITECTURE_HISTORY.md](../NARRATIVE_AND_ARCHITECTURE_HISTORY.md) ([pt-BR](../NARRATIVE_AND_ARCHITECTURE_HISTORY.pt_BR.md)) — **⬜ Pending operator material** (e.g. old blog export, timeline, or dictated milestones). **Cursor / agents:** when expanding onboarding, partner-facing story, or roadmap context, **ask the operator** to supply source narrative so it can be curated here; keep [TECH_GUIDE.md](../TECH_GUIDE.md) as the technical source of truth for current behaviour.

**Additional data soup formats:** [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](completed/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) – **Tier 3 rich media** and **Tier 1** + **opt-in stego hints** ✅ **on `main`** (optional **`[dataformats]`**, `scan_for_stego` / CLI / dashboard). **Still backlog:** **Tier 3b** embedded-tracker/heuristics and **Tier 4** doc-layer taxonomy (implementation phased per plan).

**Cloud object storage (S3-class):** [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) – **⬜ Plan only** (implementation backlog). **Corporate-Entity-C / reviewers:** expect **no** in-app S3/Azure/GCS connector until Phase 1 of that plan ships; compressed-file and share connectors remain the current path for file-like data.

**Static analysis (Semgrep):** [PLAN_SEMGREP_CI.md](completed/PLAN_SEMGREP_CI.md) – **✅ Complete** (CI workflow + Slack `workflow_run` for failures + optional smoke steps in plan).

**Bandit (Python security linter):** [PLAN_BANDIT_SECURITY_LINTER.md](completed/PLAN_BANDIT_SECURITY_LINTER.md) – **Dev + CI strict** (`ci.yml`); **Phase 3** low triage ✅ documented; plan archived under **`completed/`**.

**Unsupervised clustering (future — evaluate before a plan):** Consider whether **clustering** (e.g. grouping similar findings/columns, or **batch correction / control** workflows for operators) merits a dedicated plan. **Complements** existing **supervised** sensitivity ML/DL ([SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md)); **not** reinforcement learning. **⬜ No plan file** until product value and privacy/explainability are weighed.

**Enterprise back-office / SST / HR / ERP / CRM / helpdesk:** [PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md](PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md) – **⬜ Backlog (plan only).** Clarifies **SOC (software SST)** vs **SOX (Sarbanes-Oxley)**; phased **research-first** approach for APIs/DB/exports; data minimisation for health-like data; URM tools last. No implementation until pilot vendor is chosen.

**Brand micro-copy reminder (dashBOARd):** Revisit whether/how to label the **web dashboard** with the recommended sub-brand nickname `dashBOARd` (while keeping the decision-maker pitch unchanged). Keep changes low-noise and professional: prefer page title/header parenthetical (and minimal doc mentions in technical overview / USAGE / TECH_GUIDE). If we apply it, also update version bump / release notes accordingly. Status: ✅ Implemented (nav + About); revisit on next minor bump if needed.

**Website + extra doc languages (pre-GTM / production-ready):** ⬜ **Reminder only** — **not in active build** right now. When closer to **production-ready**, the **future public site** must **differ in depth** from (a) **stakeholder pitch** materials (private deck / `.pptx` / short narrative) and (b) GitHub’s **compliance-legal** docs: the **site** carries the **deep technical hub** — **USAGE**, **TECH_GUIDE**, **TESTING**, deploy/Docker guides, **scenarios**, **compliance-samples** entry points, **release notes**, a **roadmap with named active fronts**, prominent **Docker Hub** + **GitHub** links, and whatever else operators need to **install, tune, and audit** — all **kept in sync** with repo truth. Pitch and presentation stay **low-technical**; legal PDFs on GitHub stay **governance**-weighted. **i18n on the site** should follow the **same patterns** planned for **dashBOARd** ([PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md), [PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md](PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md) §2.2). **Cadence cue:** when you author a **new EN+pt-BR pitch deck generation**, treat it as a **reminder** to plan a **website content** update (roadmap + technical TOC + releases). Also consider (1) extra **doc locales** with justified maintenance cost (e.g. **Spanish**, **Japanese** — examples only); (2) **use cases** and short **how-tos** on the site that **link** canonical `docs/`. *Pillar inspiration:* **FreeBSD**, **Ubuntu**, **Snort**, **pfSense**. Detail: **[PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md](PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md)**; hosting: [HOSTING_AND_WEBSITE_OPTIONS.md](../HOSTING_AND_WEBSITE_OPTIONS.md); milestone: [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) **M-SITE-READY**.

- **H4/U3 far horizon (post-lato / master's scenario):** Master's degree path and related portfolio milestones can be tracked here when activated. Clojure/Lisp feasibility can be used as an optional applied-research lane once trust/commercial fronts are stable — [PLAN_CLOJURE_AUGMENTATION.md](PLAN_CLOJURE_AUGMENTATION.md). Status: ⬜ Backlog.
- **H5/U3 dream horizon (PhD thesis scenario):** PhD thesis-aligned research/roadmap items can be tracked here when activated. Status: ⬜ Backlog.

---

## Open plans and to-dos (summary)

### H3/U2 Release **1.6.4** milestone checklist (2026-03-20) — shipped

Counted rows below celebrate the **maintenance + publish** sprint; see **`docs/releases/1.6.4.md`**.

| Milestone                                                                                                              | Status | Notes                                                           |
| ---------                                                                                                              | ------ | -----                                                           |
| **VERSIONING** checklist → **1.6.4** (`pyproject.toml`, `core/about.py`, man pages, deploy/Docker examples, `uv.lock`) | ✅ Done | PR **#104**                                                     |
| **Release notes** + README “current release”                                                                           | ✅ Done | `docs/releases/1.6.4.md`                                        |
| **Git** tag + **GitHub Release**                                                                                       | ✅ Done | **`v1.6.4`**                                                    |
| **Docker Hub** `:1.6.4` + `:latest` (image matches app version)                                                        | ✅ Done | Same digest as tag above; base **`python:3.13-slim`** (**#99**) |
| **Ops docs** (merge→bump→build→push, Dependabot pyOpenSSL triage, `maintenance-check` alerts)                          | ✅ Done | **#100–#103** on `main`                                         |

### H3/U2 Release **1.6.5** — rich media (in-repo); publish checklist

**Shipped on `main`:** Tier 3 rich-media paths, docs, and app version **1.6.5** in **`pyproject.toml`** / **`core/about.py`** (see **`docs/releases/1.6.5.md`** + README).

| Milestone                                               | Status     | Notes                                                                                  |
| ---------                                               | ---------- | -----                                                                                  |
| **PR** green on `main`                                  | ✅ Done     | Rich media + follow-on merges                                                          |
| **VERSIONING** → **1.6.5**                              | ✅ Done     | In-repo                                                                                |
| **`docs/releases/1.6.5.md`** + README “current release” | ✅ Done     | Rich media flags + **`.[richmedia]`**                                                  |
| **Git tag `v1.6.5` + GitHub Release**                   | 🔄 Operator | Confirm on GitHub; create if missing                                                   |
| **Docker Hub** `:1.6.5` + `:latest`                     | 🔄 Operator | Build + push per [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md) |
| **`PLAN_ADDITIONAL_DATA_SOUP_FORMATS`** Tier 3 slice    | ✅ Done     | On **`main`**; Tier 3b/4 backlog per plan                                              |

### H3/U2 Release **1.6.6** (2026-03-25) — Band A dependency + doc sync; publish checklist

**In-repo:** **`requests>=2.33.0`** (CVE-2026-25645), **[DEPENDABOT_PYGMENTS_CVE.md](../ops/DEPENDABOT_PYGMENTS_CVE.md)** + **SECURITY** pointers, **PLANS_TODO** / Integration sync, **`pr-merge-when-green.ps1`** ASCII fix, version **1.6.6** per [`docs/releases/1.6.6.md`](../releases/1.6.6.md).

| Milestone                             | Status     | Notes                                                                            |
| ---------                             | ---------- | -----                                                                            |
| **VERSIONING** → **1.6.6**            | ✅ Done     | `pyproject.toml`, `core/about.py`, man pages, deploy examples, README            |
| **`docs/releases/1.6.6.md`**          | ✅ Done     | Highlights + publish commands                                                    |
| **Git tag `v1.6.6` + GitHub Release** | ✅ Done     | [v1.6.6 on GitHub](https://github.com/FabioLeitao/data-boar/releases/tag/v1.6.6) |
| **Docker Hub** `:1.6.6` + `:latest`   | ✅ Done     | Pushed **2026-03-25**; digest on Hub matches local build                         |
| **`uv.lock`**                         | ✅ Done     | Refreshed with version metadata                                                  |

### H3/U2 Release **1.6.7** (2026-03-25) — Remove `run.py`; VERSIONING + CHANGELOG — **shipped 2026-03-26**

**In-repo:** Legacy **`run.py`** removed; **`main.py`** only for CLI/API. **`CHANGELOG.md`** at repo root; **`docs/releases/1.6.7.md`**; USAGE (EN + pt-BR), Sonar sources, NEXT_STEPS history; **migrate** bind (`--host` / `api.host` / `API_HOST`) and transport (TLS certs or `--allow-insecure-http` / `api.allow_insecure_http`) per release note.

| Milestone                                         | Status     | Notes                                                                            |
| ---------                                         | ---------- | -----                                                                            |
| **VERSIONING** → **1.6.7**                        | ✅ Done     | `pyproject.toml`, `core/about.py`, man pages, deploy examples, README, `uv.lock` |
| **`docs/releases/1.6.7.md`** + **`CHANGELOG.md`** | ✅ Done     | Highlights + migration text                                                      |
| **Git tag `v1.6.7` + GitHub Release**             | ✅ Done     | [v1.6.7 on GitHub](https://github.com/FabioLeitao/data-boar/releases/tag/v1.6.7) (Latest **2026-03-26**) |
| **Docker Hub** `:1.6.7` + `:latest`               | ✅ Done     | Pushed **2026-03-26** per [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md) |

**Next patch:** **`1.7.4`** when the next bundle ships (after **`v1.7.3`** / **1.7.3**).

### **M-PILOT-READY** — First commercial pilot gate

**Exit criteria (all required):**

- [ ] `v1.7.4` tagged and published on Docker Hub ([#406](https://github.com/FabioLeitao/data-boar/issues/406))
- [x] Maestro Bug 1 fixed: SSH `ConnectTimeout` ([#403](https://github.com/FabioLeitao/data-boar/issues/403) — closed with evidence on **`main`**)
- [x] Maestro Bug 2 fixed: `--bench-config` argument ([#404](https://github.com/FabioLeitao/data-boar/issues/404) + [#408](https://github.com/FabioLeitao/data-boar/issues/408) — `lab-completao-host-smoke.sh` parses flag; container handlers pass `--bench-config` before `--lab-stack-up`)
- [x] Issue [#391](https://github.com/FabioLeitao/data-boar/issues/391) closed (**PII filter** toolchain / substring guard on **`main`** — 2026-05-16)
- [ ] Completão smoke-only clean on all four smoke hosts (private manifest: `docs/private/homelab/lab-op-hosts.manifest.json`) — lab-node disk hygiene ([#756](https://github.com/FabioLeitao/data-boar/issues/756) **`[U1]`**) before treating that node green
- [x] `docs/releases/1.7.4.md` created (**draft** checklist — set **Release date** and expand highlights at publish; see file banner)

**Commercial pipeline active (internal reference — no names):**

- Law firm pilot → [LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md](../use-cases/LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md)
- Pharma pilot → [PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md](../use-cases/PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md)
- EdTech pilot → [EDTECH_LMS_EXPORTS_AND_MINORS.md](../use-cases/EDTECH_LMS_EXPORTS_AND_MINORS.md)

### Additional detection techniques & false-negative reduction – [PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md](PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md)

| Priority | To-do                                                                                                                       | Status                                                                                                                                                                                                                                            |
| -------- | --------------------------------------------------------------------------------------------------------------------------- | ------                                                                                                                                                                                                                                            |
| 1        | Configurable MEDIUM threshold; “suggested review” in report for ID-like columns classified LOW                              | ✅ Done (MEDIUM via `sensitivity_detection.medium_confidence_threshold`; `detection.persist_low_id_like_for_review` on SQL, Snowflake, MongoDB, Redis, Dataverse, Power BI, REST + sheet **Suggested review (LOW)**; see SENSITIVITY_DETECTION.md) |
| 2        | Stemming/normalisation for column names in ML/term matching                                                                 | ✅ Done (`sensitivity_detection.column_name_normalize_for_ml`: accent + separators for ML/DL only; see SENSITIVITY_DETECTION.md, `tests/test_column_name_ml_normalize.py`)                                                                         |
| 3        | Optional fuzzy column name match (e.g. rapidfuzz) in confidence band 25–45 → MEDIUM + FUZZY_COLUMN_MATCH                    | ✅ Done (`sensitivity_detection.fuzzy_column_match`, extra `detection-fuzzy`, `FUZZY_COLUMN_MATCH`; see SENSITIVITY_DETECTION.md)                                                                                                                  |
| 4        | Data type/length hint from connectors → optional format hint in detector; MEDIUM suggestion when format suggests ID         | ✅ Done (initial slice: `connector_format_id_hint`, `FORMAT_LENGTH_HINT_ID`, `tests/test_format_length_hint.py`; extend INT/email/REST later)                                                                                                      |
| 5        | Embedding prototype similarity (reuse DL embedder) as optional semantic hint                                                | ⬜ Pending                                                                                                                                                                                                                                         |
| 6        | Region-specific column dictionaries (config); FK/table context where connector exposes schema                               | ⬜ Pending                                                                                                                                                                                                                                         |
| 7        | Validation: ground-truth fixtures, baseline recall; per-technique FN/FP metrics; docs                                       | ⬜ Pending                                                                                                                                                                                                                                         |
| 8        | Aggregated/incomplete: report wording – state results based on sampled data, human confirmation recommended                 | ✅ Done (first row on **Cross-ref data – ident. risk** + `AGGREGATED_IDENTIFICATION` recommendation text; `report/generator.py`)                                                                                                                   |
| 9        | Aggregated/incomplete: verify MEDIUM and PII_AMBIGUOUS contribute to aggregation; document                                  | ✅ Done (`PII_AMBIGUOUS` → `other` in `DEFAULT_PATTERN_CATEGORY_MAP`; documented in [Corporate-Entity-C_ANALISE_2026-03-18.md](Corporate-Entity-C_ANALISE_2026-03-18.md))                                                                                                  |
| 10       | Aggregated/incomplete: optional "incomplete data" mode (lower min_categories, report note)                                  | ⬜ Pending                                                                                                                                                                                                                                         |
| 11       | Aggregated/incomplete: optional single high-risk category "suggested review"                                                | ⬜ Pending                                                                                                                                                                                                                                         |
| 12       | **v1.8.0 #1056 — doc-first:** PLAN_ADDITIONAL + PLAN_EXTENDED wave 2; `plans_hub_sync` + this table ([#1056](https://github.com/FabioLeitao/data-boar/issues/1056)) | ✅ Done |
| 13       | **#1056 —** compliance-sample sketch (`global_identifiers` or pack extension); disclaimers + `recommendation_overrides` | ⬜ Pending |
| 14       | **#1056 —** entity-types (SWIFT, IBAN, VIN, MAC, CVV/expiry, AWS keys, PIN); UK NHS + CA SIN checksum gates | ⬜ Pending |
| 15       | **#1056 —** span-alignment post-proc in `boar_fast_filter`; registrable validators ([#865](https://github.com/FabioLeitao/data-boar/issues/865)) | ⬜ Pending |
| 16       | **#1056 —** SENSITIVITY_DETECTION FP-scope notes; tests + `check-all` | ⬜ Pending |

---

### Notifications (off-band + scan-complete) – [PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md)

| Phase   | To-do                                                                                                                                    | Status    |
| -----   | -----                                                                                                                                    | ------    |
| 1.1–1.3 | notifications config; notifier module (webhook, Slack, Teams, Telegram); doc Part A (task/milestone from CI or script)                   | ⬜ Pending |
| 2.1–2.4 | Scan-complete summary (totals, HIGH/MEDIUM/LOW, DOB minor, failures); trigger after report gen (CLI + web); “how to download” in message | ⬜ Pending |
| 3.1–3.3 | Tenant notification; multi-channel; retry and rate limit                                                                                 | ⬜ Pending |
| 4.1–4.4 | USAGE/SECURITY docs; optional audit log; recommendations; tests                                                                          | ⬜ Pending |

---

### Dashboard HTTPS-by-default (+ explicit HTTP risk mode) – [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md)

| Phase | To-do                                                                                                           | Status    |
| ----- | -----                                                                                                           | ------    |
| 1     | Transport args/config (`https` mode, cert/key, explicit insecure override flag)                                 | ✅ Done    |
| 2     | Secure-default runtime behavior + unmistakable warnings on stdout/stderr/logs in insecure mode                  | ✅ Done    |
| 3     | Dashboard warning banner + `/status`/health fields indicating insecure transport                                | ✅ Done    |
| 4     | Audit/export trail marks insecure dashboard traffic when override is enabled                                    | ✅ Done    |
| 5     | Tests for HTTPS + HTTP override paths (flags, warnings, status fields, banner rendering)                        | ✅ Done    |
| 6     | Docs sync (USAGE/TECH_GUIDE/SECURITY + pt-BR) and compliance/legal wording update after implementation baseline | ✅ Done    |
| 7     | Transport integrity/tamper trust state (certificate/trust monitoring; tinted runtime)                           | ⬜ Pending |

---

### Secrets and password protection (vault) – [PLAN_SECRETS_VAULT.md](PLAN_SECRETS_VAULT.md)

| Phase | To-do                                                                                                  | Status    |
| ----- | -----                                                                                                  | ------    |
| A1    | pass_from_env / password_from_env (all connectors); document                                           | ✅ Done    |
| A2    | Redact secrets in GET /config; POST merge/refs                                                         | ✅ Done    |
| A3    | Config permissions, .gitignore, release checklist                                                      | ✅ Done    |
| B1–B6 | Vault schema, local vault, loader @vault/@env, CLI reimport, web reimport, optional remove-from-config | ⬜ Pending |
| C1–C2 | Vault key management docs; release checklist                                                           | ⬜ Pending |

---

### Version check and self-upgrade – [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md)

Core flow first (sections 1–7); then optional Phase 9 (complexity/gain: high complexity, high gain for Linux/enterprise).

| #       | To-do                                                                                                                                                                                                        | Status    |
| -       | -----                                                                                                                                                                                                        | ------    |
| 1.1–1.3 | Repo URL, version fetch (GitHub API), expose current/latest/notes                                                                                                                                            | ⬜ Pending |
| 2.1–2.5 | CLI --check-update, --upgrade; API GET /check-update, POST /upgrade; schedule docs                                                                                                                           | ⬜ Pending |
| 3.1–3.5 | Backup, upgrade method, restore, upgrade_log, restart docs                                                                                                                                                   | ⬜ Pending |
| 4.1–4.4 | Container detection; message; Docker/Kubernetes commands                                                                                                                                                     | ⬜ Pending |
| 5.1–5.2 | No downgrade; --force flag                                                                                                                                                                                   | ⬜ Pending |
| 6.1–6.3 | No data loss; config/overrides backup; audit trail                                                                                                                                                           | ⬜ Pending |
| 7.1–7.3 | Tests; USAGE/DEPLOY docs; release notes                                                                                                                                                                      | ⬜ Pending |
| 9.1–9.5 | **Optional (after 1–7):** .deb package (ensure package name available; include/bundle deps for easy deployment), own apt repo, GPG signing, bytecode-only install (no raw .py), winget-like UX; see plan §9. | ⬜ Pending |

---

### Build identity, runtime version & release integrity – [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md)

**Do first:** Phase A (startup `INFO`, dashboard `build`, PEP 440 / git dirty). **Then:** C.1 manifest format → **Phase E** (SQLite anchor, survive `--reset-data`, startup re-verify, tamper → **`-alpha`** in reports/`/status`/logs) → Phase B/D as needed; C.2–C.4 signing optional.

| #        | To-do                                                                                                                                                              | Status                                           |
| -----    | -----                                                                                                                                                              | ------                                           |
| A.1–A.5  | `get_build_identity()`, CLI log line, dashboard/API, Docker labels                                                                                                 | ⬜ Pending                                        |
| B.1–B.2  | Pre-release convention + CI env / bump                                                                                                                             | ⬜ Pending                                        |
| C.1–C.4  | Optional manifest; signed manifest (stretch)                                                                                                                       | ⬜ Pending                                        |
| E.1–E.10 | SQLite `build_integrity_anchor`; first-run validate/import; **no wipe** on `--reset-data`; startup re-verify; tamper → trust level + Report info / status / health | ⬜ Pending                                        |
| E.11     | **`--export-audit-trail`** JSON: `runtime_trust`, `data_wipe_log`, `scan_sessions_summary`, placeholders for integrity; stdout or file; no DB mutation             | ✅ Done (baseline; see plan §E.6)                 |
| E.12     | Extend export with `integrity_events`, per-run version checks, optional execution-log pointers when tables exist                                                   | ⬜ Pending                                        |
| E.13     | Runtime trust warning surface in CLI `INFO` (stdout + stderr) for unexpected states                                                                                | ✅ Done (baseline message + audit export linkage) |
| D.1–D.4  | `scripts/release/` + `workflow_dispatch` + `docs/ops/RELEASE_TRAIN.md`                                                                                             | ⬜ Pending                                        |

---

### Compressed files (scan inside archives) – [PLAN_COMPRESSED_FILES.md](completed/PLAN_COMPRESSED_FILES.md)

| #    | To-do                                                                                                     | Status    |        |
| -    | -----                                                                                                     | ------    |        |
| 1    | Config: file_scan.scan_compressed, max_inner_size, compressed_extensions                                  | ✅ Done    |        |
| 2    | CLI --scan-compressed                                                                                     | ✅ Done    |        |
| 3    | Archive detection (magic bytes: zip, gz, 7z, tar, bz2, xz)                                                | ✅ Done    |        |
| 4    | Open-archive helper (zipfile, tarfile, py7zr optional)                                                    | ✅ Done    |        |
| 5    | FilesystemConnector: scan inside archives; path like archive\                                             | inner     | ✅ Done |
| 6    | Optional [compressed] extra; graceful skip if py7zr missing                                               | ✅ Done    |        |
| 7–11 | Engine/API/dashboard; share connectors; tests; docs (EN + pt-BR)                                          | ✅ Done    |        |
| 12   | Resource exhaustion: max_inner_size, temp caps; user warning when enabling (disk, I/O, run time)          | ✅ Done    |        |
| 13   | Follow-up: password-protected archive sample (or programmatic test) to validate file_passwords for ZIP/7z | ⬜ Pending |        |
| 14   | Follow-up: optional max members per archive (e.g. 1000) as extra guard                                    | ✅ Done (#1233 / [PLAN_ARCHIVE_BUDGET.md](PLAN_ARCHIVE_BUDGET.md)) |        |
| 15   | Aggregate budgets: max_total_uncompressed + max_expansion_ratio + `archive_budget_exceeded`               | ✅ Done (#1233 / [PLAN_ARCHIVE_BUDGET.md](PLAN_ARCHIVE_BUDGET.md)) |        |

---

### Aggregate archive decompression budgets – [PLAN_ARCHIVE_BUDGET.md](PLAN_ARCHIVE_BUDGET.md)

| # | To-do                                                                                         | Status  |
| - | -----                                                                                         | ------  |
| 1 | Choke-point budgets in `iter_archive_members` + reason `archive_budget_exceeded`              | ✅ Done |
| 2 | Connector defaults/clamp + config loader + SMB/SharePoint/WebDAV wiring                       | ✅ Done |
| 3 | Tests (members, ratio, config clamp) + USAGE / man                                           | ✅ Done |

---

### Content type & cloaking detection – [PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION.md](completed/PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION.md)

| #   | To-do                                                                                                                        | Status |
| --- | ---------------------------------------------------------------------------------------------------------------------------- | ------ |
| 1   | Magic-byte table + read_magic / infer_content_type for supported formats                                                     | ✅ Done |
| 2   | Config file_scan.use_content_type (default false); engine/connectors                                                         | ✅ Done |
| 3   | FilesystemConnector (and shares): use inferred type when option on; fallback to extension                                    | ✅ Done |
| 4   | CLI --content-type-check; API/dashboard checkbox + user warning (may increase I/O and run time)                              | ✅ Done |
| 5   | Tests: default unchanged; with option on, renamed PDF scanned by content; no regressions                                     | ✅ Done |
| 6   | Docs: option, benefit (renamed/cloaking), resource impact; steganography out of scope for v1                                 | ✅ Done |

---

### Data source versions & hardening – [PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md](PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md)

| Phase   | To-do                                                                                                                                                            | Status    |
| -----   | -----                                                                                                                                                            | ------    |
| 1.1–1.9 | Data model (data_source_inventory), save method; SQL/MongoDB/Redis/Power BI/Dataverse/REST version collection; Report "Data source inventory" sheet; tests; docs | ✅ Done    |
| 2.1–2.5 | Snowflake, SMB, SharePoint, WebDAV, NFS version/protocol collection; tests; docs                                                                                 | ⬜ Pending |
| 3.1–3.6 | CVE/hardening rules, hardening engine, "Hardening recommendations" sheet, mitigation from public docs only; tests; docs                                          | ⬜ Pending |
| 4.1–4.4 | Hardening summary in report; optional standalone guide; docs/hardening-guide.md; full regression                                                                 | ⬜ Pending |

---

### Strong crypto & controls validation – [PLAN_OPTIONAL_STRONG_CRYPTO_AND_CONTROLS_VALIDATION.md](PLAN_OPTIONAL_STRONG_CRYPTO_AND_CONTROLS_VALIDATION.md)

| Phase   | To-do                                                                                                                                 | Status    |
| -----   | -----                                                                                                                                 | ------    |
| 1.1–1.7 | CLI --validate-crypto; optional config scan.validate_crypto; API body validate_crypto; dashboard checkbox; engine wiring; tests; docs | ⬜ Pending |
| 2.1–2.8 | Strong-crypto criteria; SQL/Mongo/Redis/REST/SMB validation; persist results; "Crypto & controls" sheet; tests; docs                  | ⬜ Pending |
| 3.1–3.6 | Anonymisation/controls heuristics (column/field names, metadata); store summary; disclaimer in report; tests; docs                    | ⬜ Pending |
| 4.1–4.3 | Crypto failures do not fail scan; full regression; optional link to Data source inventory                                             | ⬜ Pending |

---

### CNPJ alphanumeric format validation – [PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md](completed/PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md)

| Phase   | To-do                                                                                                                            | Status |
| -----   | -----                                                                                                                            | ------ |
| 1.1–1.4 | Research and specify alphanumeric CNPJ format (IN RFB 2.229/2024); propose regex; document in SENSITIVITY_DETECTION (EN + pt_BR) | ✅ Done |
| 2.1–2.3 | Example regex_overrides + ML term; verify scan detects both legacy and alphanumeric; USAGE docs                                  | ✅ Done |
| 3.1–3.4 | Decide built-in vs flag vs override-only; optional built-in/flag; optional "CNPJ format compatibility" report summary            | ✅ Done |
| 4.1–4.3 | "How to get there" in plan; sync PLANS_TODO and plan; full regression                                                            | ✅ Done |

---

### Selenium QA test suite – [PLAN_SELENIUM_QA_TEST_SUITE.md](PLAN_SELENIUM_QA_TEST_SUITE.md)

| Phase   | To-do                                                                                                               | Status    |
| -----   | -----                                                                                                               | ------    |
| 1.1–1.6 | Optional [qa] deps (Selenium, webdriver-manager); tests_qa/ conftest + navigation + API baseline; runner stub; docs | ⬜ Pending |
| 2.1–2.5 | Buttons/forms; reports list; report/heatmap downloads; optional /logs; include in runner and report                 | ⬜ Pending |
| 3.1–3.4 | Report generator (pass/fail, duration, recommendations); configurable output dir; docs                              | ⬜ Pending |
| 4.1–4.3 | Optional stress tests; exclude QA from default pytest; final docs and PLANS_TODO                                    | ⬜ Pending |

---

### Synthetic data & confidence validation – [PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md](PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md)

| Phase   | To-do                                                                                        | Status    |
| -----   | -----                                                                                        | ------    |
| 1.1–1.5 | Fixture root; file-format coverage + ground-truth manifest; doc and optional tests           | ⬜ Pending |
| 2.1–2.4 | SQL/NoSQL fixtures (Docker or in-memory); manifest; doc and optional precision/recall script | ⬜ Pending |
| 3.1–3.3 | Shares fixtures or doc; Troubleshooting (timeouts, connectivity); optional timeout fixture   | ⬜ Pending |
| 4.1–4.5 | Confidence bands + operator guidance; report column/section; docs EN + pt_BR; tests          | ⬜ Pending |
| 5.1–5.3 | Optional validation scoring script; tune doc; PLANS_TODO update                              | ⬜ Pending |

---

### SAP connector – [PLAN_SAP_CONNECTOR.md](PLAN_SAP_CONNECTOR.md)

| Phase   | To-do                                                                                             | Status    |
| -----   | -----                                                                                             | ------    |
| 1.1–1.3 | Research SAP access (HANA/OData/RFC); decide primary path; define config shape                    | ⬜ Pending |
| 2.1–2.3 | Connector module (discovery, sampling, scan_column, save_finding); register; optional [sap] extra | ⬜ Pending |
| 3.1–3.3 | USAGE/TECH_GUIDE (EN + pt-BR); tests; pitch/roadmap update in README                              | ⬜ Pending |

---

### Enterprise HR / SST / ERP / CRM / helpdesk (umbrella) – [PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md](PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md)

**Status:** Planning / backlog catalogue only (no implementation commitment).

| Phase   | To-do                                                                                                                              | Status    |
| -----   | -----                                                                                                                              | ------    |
| A.1–A.4 | Research priority vendors per category; map API vs SQL vs export-folder; risk-only finding shape; SOX vs product SOC note for docs | ⬜ Pending |
| B.1–B.3 | Generic enablers (OAuth REST, entity allowlists, tiered sampling) when a pilot is chosen                                           | ⬜ Pending |
| C.1–C.3 | Pilot connector(s); report tags for source family; recommendation linkage                                                          | ⬜ Pending |
| D.1–D.2 | URM / productivity monitoring — policy checklist first; integration only with explicit legal basis                                 | ⬜ Pending |

---

### Dashboard i18n – [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md)

**Status:** **D-WEB** ✅ — **M-LOCALE-V1** ✅ on **`main`** (**2026-04**). **Next:** [#86](https://github.com/FabioLeitao/data-boar/issues/86) Phase 1 (session/passwordless) on **`/{locale}/…`**.

| Milestone         | Purpose                                                                                             | When                            |
| ---------         | -------                                                                                             | ----                            |
| **D-WEB**         | URL map + **middleware order** — **doc / diagram**; cross-link **#86** plan                       | ✅ Done (Phase 0)               |
| **M-LOCALE-V1**   | Path-prefixed HTML; **`en` + `pt-BR`** JSON; negotiation; switcher; tests; CI locale key parity     | ✅ Done (**2026-04** on **`main`**) |
| **M-LOCALE-PLUS** | Optional **`es` / `fr` / fifth** locale                                                             | Separate slices                 |
| **gettext**       | Revisit only if **many** locales or **heavy** translator process                                    | Months/years — not v1           |

**RBAC (#86):** Phase **1+** **after** **M-LOCALE-V1** (now on **`main`**) on **prefixed** paths — [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) § *Sequencing with dashboard i18n*.

**Full checklist:** [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md) (implementation section — run when milestone is **Selected**).

---

## [H3][U2] Branding rename — PyPI id **`data-boar`** (ADR 0014)

**ADR:** `docs/adr/ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md`

**Done in tree:** `pyproject.toml` **`name = "data-boar"`**, `core/about.py` metadata, docs/README/GLOSSARY/USAGE/SECURITY, Sonar default key, `requirements.txt` / `uv.lock`, release notes (Docker `fabioleitao/data_boar`).

**Optional follow-ups (non-blocking):** first **PyPI publish** under `data-boar`; collaborator `origin` URL check; optional removal of legacy second remote after [BRANCH_AND_DOCKER_CLEANUP.md](../ops/BRANCH_AND_DOCKER_CLEANUP.md) §7.

Historical mentions (ADRs, some completed plans) may still cite the **original** bootstrap name where they record history.

---

## Completed plans (reference)

- **Corporate compliance** – [.cursor/plans/](.cursor/plans/) (reference)
- **Minor data detection** – [completed/PLAN_MINOR_DATA_DETECTION.md](completed/PLAN_MINOR_DATA_DETECTION.md)
- **Aggregated identification** – [completed/PLAN_AGGREGATED_IDENTIFICATION.md](completed/PLAN_AGGREGATED_IDENTIFICATION.md)
- **Sensitive categories ML/DL** – [completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md](completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md)
- **Rate limiting** – [completed/PLAN_RATE_LIMIT_SCANS.md](completed/PLAN_RATE_LIMIT_SCANS.md)
- **Web hardening** – [completed/PLAN_WEB_HARDENING_SECURITY.md](completed/PLAN_WEB_HARDENING_SECURITY.md)
- **Logo and naming** – [completed/PLAN_LOGO_AND_NAMING.md](completed/PLAN_LOGO_AND_NAMING.md)
- **Security hardening** – [completed/PLAN_SECURITY_HARDENING.md](completed/PLAN_SECURITY_HARDENING.md)
- **Configurable timeouts** – [completed/PLAN_CONFIGURABLE_TIMEOUTS_AND_RATE_GUIDANCE.md](completed/PLAN_CONFIGURABLE_TIMEOUTS_AND_RATE_GUIDANCE.md)
- **Additional compliance samples** – [completed/PLAN_ADDITIONAL_COMPLIANCE_SAMPLES.md](completed/PLAN_ADDITIONAL_COMPLIANCE_SAMPLES.md)

---

## Readiness and operations (meta)

Goal categories (so we don’t forget). **Full prioritised checklist and to-dos:** [PLAN_READINESS_AND_OPERATIONS.md](PLAN_READINESS_AND_OPERATIONS.md). Status is updated only there.

| Category                | One-line summary                                                        | Status      |
| ----------              | ------------------                                                      | --------    |
| **Release**             | Checklist in CONTRIBUTING; history = git + `docs/releases/`.            | Done        |
| **Security response**   | Vulnerability and Dependabot security PR SLAs in SECURITY.md.           | Done        |
| **Runbooks**            | Operator runbook one-pager; backup and restore in USAGE/deploy.         | Not started |
| **Compliance evidence** | “Compliance and evidence” in SECURITY or doc; data retention mention.   | Not started |
| **Onboarding**          | Short onboarding checklist in CONTRIBUTING.                             | Not started |
| **Dependency policy**   | Python/platform support sentence; optional lockfile refresh policy.     | Not started |
| **Check-all script**    | One command (uv sync, ruff, pytest, pip-audit) approximates CI locally. | Not started |

See PLAN_READINESS for MCP recommendation, workflow automation, and when to revisit (release, onboarding, audit).

---

## Artifacts and portfolio (for thesis, evidence mapping, pitch)

**Full checklist (Docker Hub, Dockerfiles, GitHub, certifications, Ubuntu, private docs):** [PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md). Authoritative Docker list: **`docs/private/From Docker hub list of repositories.md`**. CV, TCC, LinkedIn in `docs/private/` (git-ignored). See [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) §3.

---

## How to use this list

1. **Execute to-dos** in the recommended sequence (or in dependency order within a plan).
1. **Mark done** in both this file and the plan file when a step is implemented, tested, and documented.
1. **After each step:** run `uv run pytest -v -W error` to ensure no regression.
1. **Documentation:** Update USAGE, TECH_GUIDE, SECURITY, or dedicated docs (EN + pt-BR) as features land; add new doc files to docs/README index and, if needed, to test_docs_markdown.
1. **New to-dos:** When adding a new to-do to any plan, add it here under the corresponding plan section so this remains the source of truth.

---

## Last synced with plan files. Update this doc when completing steps or when plans change.

---

## Backlog: Maestro script renames (houseclean, low priority)

- Renomear o script Ansible/podman apply com prefixo de host legado em `scripts/` →
  `scripts/labop-ansible-podman-apply.sh`
  — o prefixo de host no nome é artefato histórico; conteúdo é genérico para todos os hosts (usa
  `.labop-skip-lab-node-01-podman` file para skip em hosts sem Podman). Requer atualizar:
  sudoers em todos os hosts (`LABOP_ANSIBLE_PODMAN`), docs, e tests que referenciam o nome.
  Fazer numa sessão `houseclean` dedicada com `git mv` + atualização do sudoers via push + git pull nos hosts.

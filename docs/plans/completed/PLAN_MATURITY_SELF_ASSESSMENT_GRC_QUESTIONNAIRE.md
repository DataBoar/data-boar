# PLAN: Organizational maturity self-assessment (GRC-style questionnaire)

**Status:** Completed (archived under `docs/plans/completed/`)
**Date:** 2026-04-16
**Authors:** Fabio Leitao
**Priority:** H0
**Depends on:** ADR-0025

<!-- plans-hub-summary: POC on main: gated /{locale}/assessment + YAML rubric scores + SQLite + HMAC + post-submit summary + per-batch history table + GET /assessment/export (CSV/Markdown); evidence levels A/B/C (smoke vs full demo); SMOKE runbook; RBAC + report-bundle backlog; not legal audit. -->
<!-- plans-hub-related: PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md, LICENSING_OPEN_CORE_AND_COMMERCIAL.md (future tier features), PLAN_SCOPE_IMPORT_FROM_EXPORTS.md (inventory bootstrap narrative) -->

**Horizon / urgency:** `[H3]` or `[H4]` · `[U3]` for the **complete** product slice; next code slices: **tenant/history model** when clear, then **RBAC** (#86) alignment.

**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (Backlog catalogue entry).

### POC ready — minimum checklist (definition of done)

Use this list to declare the **maturity POC “ready”** for demos, beta notes, or a checkpoint before the **tier/JWT** slice and long before **[#86](https://github.com/FabioLeitao/data-boar/issues/86)**. All items are **verifiable**; none require production SSO, RBAC, or multi-tenant storage.

| # | Gate | How to verify |
| --- | --- | --- |
| 1 | **CI / tests** | `main` green: `pytest` coverage for assessment routes and DB (`tests/test_api_assessment_poc.py`, `tests/test_maturity_assessment_integrity.py`, `tests/test_database.py` batch summaries), plus repo-wide gate (`scripts/check-all.ps1` or CI **Lint** + **Test**). **Autonomous subset (fast):** `scripts/smoke-maturity-assessment-poc.ps1` (Windows) — same files as gate 1 minus full suite. |
| 2 | **Config documented** | `api.maturity_self_assessment_poc_enabled: true`, valid **`api.maturity_assessment_pack_path`** (YAML shape per `tests/fixtures/maturity_assessment/sample_pack.yaml`), and tier **Pro+** for this feature — in lab via `licensing.effective_tier: pro` in YAML ([docs/USAGE.md](../USAGE.md) table row). |
| 3 | **Happy path (manual smoke)** | Step-by-step: [docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.md](../../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) ([pt-BR](../../ops/SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md)) §D — browser flow (form → summary → history → export). |
| 4 | **Integrity (optional demo)** | Same runbook §E — **`DATA_BOAR_MATURITY_INTEGRITY_SECRET`** at submit time; **`GET /status`** and **`--export-audit-trail`** ([ADR 0015](../../adr/ADR-0015-poc-test-infrastructure-synthetic-corpus-and-api-testing.md) test posture). |
| 5 | **Docs / ADR** | Operator-facing text in [USAGE.md](../USAGE.md) (+ pt-BR) for assessment + batch history; [ADR 0032](../../adr/ADR-0032-maturity-assessment-batch-history-sqlite.md) for history behaviour. |

**Checkpoint closed:** run **`smoke-maturity-assessment-poc.ps1`** + complete runbook §D (and §E if you need integrity demo). Then proceed to **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** on a dedicated branch; **return** to maturity (DOCX→YAML per tenant, consultant UX) when packaging or customer needs require it — see § *Next steps* below.

### POC ready — evidence levels (what agents vs operators sign off)

| Level | What it proves | Typical evidence |
| ----- | ---------------- | ---------------- |
| **A — Automated gates** | Same pytest subset as checklist **gate 1** below — API, DB batch order, HMAC helpers, audit-export parity | `.\scripts\smoke-maturity-assessment-poc.ps1` exit **0** on current `main`; CI **Test** job green on the same files |
| **B — Docs / ADR** | Operator can configure flags + pack path + tier from [USAGE.md](../USAGE.md); history behaviour documented | Checklist **gate 5** below; [ADR 0032](../../adr/ADR-0032-maturity-assessment-batch-history-sqlite.md) |
| **C — Full (demo / beta)** | Real browser UX: redirects, downloads, locale — **not** replaceable by pytest alone | [SMOKE_MATURITY_ASSESSMENT_POC.md](../../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) §D checkboxes (§E optional); record date + commit in **`docs/private/`** or a dated **today-mode** note if you want a paper trail **without** editing public plans |

**Agent / CI:** Safe to claim **Level A + B** when smoke + USAGE + ADR match shipped code. **Level C** requires an **operator** pass — do not mark “full POC ready” in release prose without §D.

### Autonomous vs operator — closure boundary

Use this table so **agents / CI** do not promise what only a **human operator** can finish (browser session, lab config on disk).

| POC ready gate | Fully autonomous? | What actually happens |
| --- | --- | --- |
| **1** CI / smoke subset | **Yes** | `scripts/smoke-maturity-assessment-poc.ps1` (or full `check-all.ps1` / CI) runs `tests/test_api_assessment_poc.py`, `tests/test_maturity_assessment_integrity.py`, `tests/test_database.py::test_maturity_assessment_batch_summaries_newest_first`, `tests/test_audit_export.py::test_build_audit_trail_maturity_integrity_matches_verify`. |
| **2** Config documented | **Docs only** | [USAGE.md](../USAGE.md) (+ pt-BR) documents flags, pack path, tier; operator still applies a **local** `config.yaml` for manual §D. |
| **3** Happy path (§D) | **No** | Browser steps in [SMOKE_MATURITY_ASSESSMENT_POC.md](../../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) — **required** to declare **full** “POC ready” for demos. |
| **4** Integrity (§E) | **Partial** | HMAC + `/status` + audit export are **covered by tests**; **§E** remains the **live** lab check with env secret + running process. |
| **5** Docs / ADR | **Yes** | USAGE, [ADR 0032](../../adr/ADR-0032-maturity-assessment-batch-history-sqlite.md), this plan, runbook EN + pt-BR. |

**Working definitions:**

- **“POC ready — automated gates”** — gate **1** green on `main` + gate **5** satisfied (already true when docs match code). Safe for **release notes / CI** language.
- **“POC ready — full (demo/beta)”** — above + operator completes runbook **§D** (and **§E** if the story includes integrity demo).

**Mapping runbook §D to pytest:** see [SMOKE_MATURITY_ASSESSMENT_POC.md](../../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) § *Pytest coverage vs browser checklist* — API contract and templates are exercised without a browser; §D is still the **UX** gate.

**Explicitly not required for “POC ready”:** GitHub **#86** (session / WebAuthn / RBAC), **tenant-scoped** batch lists, **`licensing.mode: enforced`** + JWT in production, **DOCX→YAML** private import, legal/commercial one-pager, report-bundle annex.

### Next slice (sketch): tier / JWT alignment — **not** #86

**Intent:** Close the gap between **lab** tier simulation (`licensing.effective_tier` in YAML) and **enforced** mode where product tier comes from the **signed license JWT** (`dbtier` claim per [LICENSING_SPEC.md](../LICENSING_SPEC.md)), using the **same** runtime gate already wired for dashboard features: **`_runtime_tier_for_features`** in `api/routes.py` (JWT `dbtier` wins over YAML when enforcement and valid token).

| Topic | Boundary |
| ----- | -------- |
| **In scope for this slice** | Prove **`maturity_self_assessment_poc`** respects `Tier.PRO` when `licensing.mode: enforced` and token carries `dbtier` (e.g. community → **404** on assessment routes; pro → **200**). **Done:** `tests/test_api_assessment_poc.py` (`test_assessment_enforced_jwt_dbtier_*`). **USAGE** already states JWT `dbtier` when enforced; precedence over YAML is explicit there. Optional: cross-link from [LICENSING_SPEC.md](../LICENSING_SPEC.md) “future extensions” to this plan. |
| **Out of scope (still #86 / later)** | Browser **session**, **passwordless** / WebAuthn, **per-route RBAC**, **identity** for tenant-scoped history, **middleware** reorder — see [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md). |
| **Branch / merge discipline** | Implement on a **dedicated feature branch**; **do not** combine with **#86 Phase 1** PRs — merge order remains: maturity POC checkpoint **→** tier/JWT slice **→** **#86** when scheduled ([SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §4.2). |

**Code anchors:** `core/licensing/tier_features.py` (`maturity_self_assessment_poc` → **Pro**); `core/licensing/guard.py` (`dbtier` on context); tests in `tests/test_tier_features_open_core_subscription.py`, `tests/test_licensing.py`.

### Operator sequencing — prerequisites done; POC **A** shipped (SQLite + HMAC + scoring + history + export; **POC ready** = smoke + manual runbook)

**M-LOCALE-V1 (dashboard i18n):** ✅ **shipped on `main`** (**2026-04**) — path-prefixed HTML, `en` + `pt-BR` catalogs, negotiation. See [PLAN_DASHBOARD_I18N.md](PLAN_DASHBOARD_I18N.md) and [PLANS_TODO.md](../PLANS_TODO.md) (Dashboard i18n section).

**Version signal for testers (do not rely on git inference alone):** **Published** stable line is **`v1.7.3`** / Python **`1.7.3`** (Hub / GitHub Release); **`main`** after publish may already show the next **`-beta`** ([VERSIONING.md](../VERSIONING.md)). Callouts: [CHANGELOG.md](../../CHANGELOG.md), [docs/releases/1.7.3.md](../releases/1.7.3.md), README **Current release**. Prior golden: [docs/releases/1.7.2-safe.md](../releases/1.7.2-safe.md). Prior feature notes: [docs/releases/1.7.1.md](../releases/1.7.1.md). For a frozen tree, **`git checkout v1.7.3`** — not only `git log` on moving **`main`**.

**Are we on option A in code right now?** **Yes (POC):** `GET`/`POST /{locale}/assessment` and **`GET /{locale}/assessment/export`** when **`api.maturity_self_assessment_poc_enabled`** is on and tier allows it (`core/licensing/tier_features.py`); otherwise **404**. Optional YAML pack drives questions and optional rubric weights; answers persist to SQLite; optional **HMAC** seals rows when a secret is configured. **RBAC** and **bundling org answers into the technical report PDF** are still **not** implemented — the plan still compares full **A / B / C / D** product shapes for later evaluation.

**POC architecture A — progress:**

| Step | Architecture | Intent |
| --- | --- | --- |
| **1** | **A** — Routes under **`/{locale}/…/assessment`** + optional YAML pack ✅; **SQLite persistence + answers** ✅; **optional HMAC row integrity** ✅ (`GET /status`, **`--export-audit-trail`**) | **First** in-app spike: single app, same audit story; align with RBAC [#86](https://github.com/FabioLeitao/data-boar/issues/86) later. |
| **2** | **B** — Excel sheet + formula scoring | Fast tabular path; compare UX vs A for consultant workflows. |
| **3** | **C** — Companion app + API/SSO | Separation / white-label; evaluate **after** A/B learnings. |
| **4** | **D** — PDF/export-only narrative | Simplicity vs interactivity; last in the **comparison chain**, not “never”. |

**POC scaffolding (ongoing):** feature-flag + tier / JWT gates; optional YAML pack from **`api.maturity_assessment_pack_path`** — **no** proprietary questionnaire text in the **public** repo (curate privately; see `tests/fixtures/maturity_assessment/sample_pack.yaml` for shape). Routes use the same **`/{locale_slug}/…`** pattern as the rest of the dashboard HTML ([PLAN_DASHBOARD_I18N.md](PLAN_DASHBOARD_I18N.md)).

**Remember:** proceed **A → B → C → D** as **evaluation spikes**, not four full products—pick one shipping path after spikes unless counsel/commercial demands otherwise.

### After this track (operator sequencing — do not lose the thread)

1. **[PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](../PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md)** — **Technical enforcement roadmap:** only **Phase 0** is done (claims sketched in **LICENSING_SPEC**, JWT path exists). **Phases 1–6** ( **`dbtier` / `dbfeatures` in tokens**, `check_feature()`, gates in connectors/reports, Partner/Enterprise rules) are **not started** — depends on **legal review** and issuer work; promote when GRC/maturity and commercial packaging need real entitlements (not just `licensing.effective_tier` lab simulation).
2. **[PLAN_PDF_GRC_REPORT.md](../PLAN_PDF_GRC_REPORT.md)** — **Different artefact:** PDF “em prosa” for **technical scan findings** (exec summary, priority matrix like a **cyber/GRC vulnerability-style** report). **Not** the org questionnaire; it complements technical evidence. Priority band **B** in that plan; still **planned** (Phases 1–2 unchecked).
3. **[PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](../PLAN_SCOPE_IMPORT_FROM_EXPORTS.md)** — **After** maturity/DOCX is under control: bootstrap **customer asset inventory** from **exports** — **minimum** acceptable is a **manual CSV** (“everything the client remembers”: hosts, paths, tags) mapped to the **canonical schema** → merge-safe config fragments. Live ITSM APIs are **not** required for v1.
4. **Dashboard RBAC — [GitHub #86](https://github.com/FabioLeitao/data-boar/issues/86)** (still **OPEN** as of plan updates): **Phase 1** = browser **session** + **Bitwarden Passwordless.dev** (minimum viable human auth) on the same **`/{locale}/…`** paths as i18n; then role/group gates for `/reports` and downloads per [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md). **Order (2026-04):** **M-LOCALE-V1** ✅ → **maturity POC “POC ready” closure** (smoke + manual runbook) → **#86 Phase 1** on a dedicated branch → **scope import** — adjust only if a **security exception** forces early guards (then budget a migration slice).

## Problem statement

Operators and consultants need **organizational** visibility (roles, processes, awareness) alongside **technical** inventory from Data Boar. A structured **self-assessment** (not audit, not legal advice) can raise maturity and align teams (DPO, IT, cyber, compliance, HR, contracts, customer-facing) with preparation for LGPD and related frameworks—**if** answers are sincere and the instrument is clearly framed as **consciousness-raising** only.

**Source material:** Maintainer-authored questionnaire (historically a **DOCX** in an LGPD working folder, plus spreadsheet “gabarito” / scoring logic). **Not** in the public repo until curated; expect **`docs/private/`** or a licensed commercial content pack for paid tiers.

**Operator workspace (confirmed — not public Git):** `docs/private/raw_pastes/general/LGPD_DOCS/` contains the working **DOCX** (diagnóstico / índice de adequação à LGPD, level bands), **XLSX** metric/scoring example, and additional **inventory / mapping** spreadsheets usable as **design inspiration** for future report shapes and scope hints—**do not** paste proprietary wording into tracked files. For agent ingestion in future sessions: keep files in that folder or export **structured** excerpts (YAML/CSV of questions + weights) to the same tree; **DOCX/XLSX** are readable via tools/scripts on the workstation even when Cursor’s file **glob** skips gitignored paths.

**DOCX → YAML workflow (architecture A):** curate sections/questions **privately**, then author a **`maturity_assessment_pack_path`** YAML file matching `core/maturity_assessment/pack.py` (see `tests/fixtures/maturity_assessment/sample_pack.yaml` for shape). Point `api.maturity_assessment_pack_path` at that file; no proprietary strings belong in the public GitHub tree.

## Fit with Data Boar mission

- **Aligned:** Same “evidence and governance” story: technical scan shows **where** data lives; maturity form shows **how prepared** the organization claims to be—both feed the DPO/consultant narrative in sales and delivery.
- **Not aligned with open core:** This is **process/GRC content**, heavy UX, and ongoing content maintenance—natural fit for **commercial / partner** tier or a **separate product**, not the BSD AGPL community baseline.

**Branding:** Can share **Data Boar** / **dashBOARd** chrome if embedded; must not blur **legal conclusions**—copy must repeat that output is **self-reported maturity signal**, not certification (see [ADR 0025](../../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) posture).

## Architecture options (decision later)

| Option | Pros | Cons |
| --- | --- | --- |
| **A. New dashBOARd routes** (`/assessment` or similar), store in SQLite per tenant/session | Single login, same audit trail story, export to report | Couples release cadence to core app; RBAC/auth (#86) becomes more critical |
| **B. Extra Excel sheet + formula scoring** | Fast to ship if schema is tabular; familiar to Excel users | Weak for long text, branching logic, versioning of questions |
| **C. Companion web app** (“Boar Assess” or partner OEM) with API/SSO link to Data Boar | Clear separation; independent roadmap; optional white-label for partners | Two deployables, identity integration cost |
| **D. PDF/export-only** from a filled form (server generates narrative) | Simple | Less interactive; trend history needs storage anyway |

**Recommendation for first spike (when promoted):** prototype **A** (per **Operator sequencing** above) behind **feature flag + license claim**; keep question YAML/JSON in a **content pack** repo or private submodule so **LGPD vs ISO 27701 vs hybrid** = different packs without forking the engine. Revisit **C** after A/B learnings.

## Multi-“norm” adaptation

Feasible: treat **question banks** and **weights** as data (like **compliance samples**), keyed by `norm_tag` / selected **compliance profile** for the tenant. Scoring must stay **transparent** (documented weights, “fair if honest” disclaimer). **Not** mirabolante if scoped as **config-driven questionnaire + rubric**, not bespoke law engine.

## Tamper-evidence (POC) — HMAC on stored answers

- **What:** Each stored answer row can carry **`row_hmac`** = HMAC-SHA256 (hex) over a **canonical UTF-8 payload** (`core/maturity_assessment/integrity.py`, version prefix `maturity-answer-hmac-v1`). The **secret** is read from env (**`DATA_BOAR_MATURITY_INTEGRITY_SECRET`** by default, or the env var named by **`api.maturity_integrity_secret_from_env`**). If no secret is set at submit time, rows are stored **unsealed** (empty MAC).
- **Where to read:** **`GET /status`** → **`maturity_assessment_integrity`**; **`python main.py --export-audit-trail`** includes the **same** object for offline governance snapshots.
- **What it is not:** Not **encryption**; not proof against an attacker with the secret, the app process, or full disk control (“evil maid”). It **does** help demos and operators detect **casual SQLite edits** without updating the MAC.
- **Regression tests:** `tests/test_maturity_assessment_integrity.py` (golden HMAC vector, verify counts, DB tamper); `tests/test_api_assessment_poc.py`; `tests/test_audit_export.py` (export parity with `verify_maturity_assessment_integrity`).

## Risks and guardrails

- **Honesty / gaming:** Scores are only as good as inputs; position as **trend and conversation starter**, not compliance scorecard.
- **Scope creep:** Full GRC platforms are a product category—stay **thin**: questionnaire + export + optional history, not workflow replacement.
- **Legal:** Every surface: “not legal advice; not audit; not ANPD filing.”

## Open core vs commercial

- **Open core:** **No** — keep scanner/dashboard baseline OSS; ship assessment as **source-available / subscription** module, **or** separate paid app.
- **Subscription value:** Periodic re-assessment, trend charts, consultant “tenant” view—matches **partner SKUs** in [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md).

## Next steps (ordered; POC-first)

1. **POC A — done for persistence + integrity + rubric + download export + in-dashboard batch history:** SQLite + YAML pack (optional **`scores`**) + HMAC + `/status` + audit export ✅; **post-submit summary** on `GET /{locale}/assessment?saved=1&batch=…` (row count + rubric + HMAC counts for that batch) ✅; **recent submissions** table on `GET /{locale}/assessment` (per `batch_id`, newest first) ✅; **`GET /{locale}/assessment/export?batch=…&format=csv|md`** ✅; **tier/JWT** API tests ✅. **POC ready closure:** `scripts/smoke-maturity-assessment-poc.ps1` + [SMOKE_MATURITY_ASSESSMENT_POC.md](../../ops/SMOKE_MATURITY_ASSESSMENT_POC.md) manual §D (§E optional).
2. **Product sequencing (2026-04):** After the smoke checkpoint, **prioritise [GitHub #86](https://github.com/FabioLeitao/data-boar/issues/86) Phase 1** (session + passwordless on `/{locale}/…`) on a **dedicated branch** — see [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md). **Revisit maturity POC** only when needed (DOCX→YAML curation for a **tenant**, export annex, consultant UX).
3. **DOCX → YAML (private):** Curate sections/questions under **`docs/private/`**, then author YAML matching `core/maturity_assessment/pack.py` — **no** proprietary strings in public Git; promote when a **customer/tenant** pack is in scope (same workflow as § *DOCX → YAML workflow* above).
4. Legal/commercial one-pager: positioning vs audit; consent for storing responses.
5. **Architecture lock:** spike **A** remains default; revisit **C** only after A/B learnings — align with [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) and API key / future SSO (#86).
6. MVP: **bundle** org answers into report annex or narrative export (distinct from technical **[PLAN_PDF_GRC_REPORT.md](../PLAN_PDF_GRC_REPORT.md)** PDF stream).

## Relationship to other plans

- **[PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](../PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md)** — subscription / partner tier boundaries; maturity assessment is **not** open core — enforcement phases **1+** apply when moving past POC/lab gates.
- **[PLAN_PDF_GRC_REPORT.md](../PLAN_PDF_GRC_REPORT.md)** — **Scan output** PDF (exec + detailed + priority matrix); **not** the org self-assessment form — cross-sell in GRC narratives only.
- **[PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](../PLAN_SCOPE_IMPORT_FROM_EXPORTS.md)** — complementary “bootstrap from existing tools” story; assessment is **people/process**, scope import is **technical inventory**.
- **Dashboard RBAC / #86** — required if multi-user tenants fill forms.

---

*Created for operator recall after exploration in chat; revise or archive when superseded.*

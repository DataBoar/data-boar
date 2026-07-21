# Changelog

Human-readable summary of user-facing changes. **Detailed release notes:** [docs/releases/](docs/releases/) (full checklists, Docker publish commands, GitHub Release text).

## Unreleased (`main`)

- **Cursor rules — Tier B situationalization (#1154):** 14 workflow rules → `alwaysApply: false` + globs/tokens; merged `operator-chat-language` + `persona-rigor` duplicates; workstation rules reframed (main dev box / secondary, same rigor). Rollback: `git revert` the Tier B commit. Inventory: `docs/ops/CURSOR_RULES_PHASE2_SITUATIONALIZATION.md`.

**Targeting (next dev line):** **`1.8.0-beta`** (#772) — after operator **release-ritual** for **1.7.4** (PR **#1024**).

- **ADR governance (Phase 1, #1162):** deterministic tests T1/T2/T5/T6 for ADR-0045 (`tests/test_adr_governance_phase1.py`); pre-commit hook `adr-governance-phase1`; plan [PLAN_ADR_GOVERNANCE_ENFORCEMENT.md](docs/plans/PLAN_ADR_GOVERNANCE_ENFORCEMENT.md).

---

## 1.7.4.post6 (pending PyPI dispatch)

> Post-release on the **`1.7.4`** public line. **`[project] version = 1.7.4.post6`** and **`[tool.databoar] maturity_build = 241`** (`N=1` `fix(` commit since post5 `b7de32ba`, ADR-0073). **PyPI-only** — no Git tag, no GitHub Release, no container.

### Fixed / hardened (post6)

- **Integrity:** re-baseline the SQLite integrity anchor on a **legitimate** release upgrade — `pip install -U` / `pipx upgrade` reusing the same SQLite DB no longer false-tints as tampered/`-alpha`; same `release_label` + hash drift still = `tampered` (real detection preserved) (#1262, #1263).

### Notes (post6)

- Full `N=1` fix set and `postN` ↔ `maturity_build` map: [docs/releases/1.7.4.post6.md](docs/releases/1.7.4.post6.md).

---

## 1.7.4.post5 (pending PyPI dispatch)

> Post-release on the **`1.7.4`** public line. **`[project] version = 1.7.4.post5`** and **`[tool.databoar] maturity_build = 240`** (`N=14` `fix(` commits since post4 merge `656fdc3d`, ADR-0073). **PyPI-only** — no Git tag, no GitHub Release, no container.

### Fixed / hardened (post5)

- **Archives (.7z):** content scan via py7zr `BytesIOFactory` + pre-budget member extract (#1250, #1248).
- **Sessions:** orphan `running` reaper (PID liveness, TOCTOU-safe conditional UPDATE) + interrupt → `interrupted` (#1251).
- **CLI:** `--validate-config` **WARN** when optional SQL driver deps are missing (offline probe) (#1246).
- **Security:** standalone HTML form CSRF (#1231); Dataverse `org_url` / `token_url` SSRF guards (#1232); aggregate archive decompression budgets (#1233); secret-by-identity lock + reachable JWT GRACE (#1210, #1212); non-numeric / non-finite license/budget hardening; drop `Invoke-Expression` from `external-review-pack.ps1` (#1192).
- **Integrity:** honest `build_digest_matched` (no `signature_ok` overclaim) + legacy migrate zeroing (#1211).
- **OPSEC / lint:** LICENSING_SPEC evasion-vector redaction (#1234, #1235); markdown-lint git-tracked only (#1240); skills OPSEC / ATS footer path (#1191).

### Notes (post5)

- Full `N=14` fix set and `postN` ↔ `maturity_build` map: [docs/releases/1.7.4.post5.md](docs/releases/1.7.4.post5.md).
- **Accounting (ADR-0073):** `N` for post5 uses the **published** post4 row **`maturity_build = 226`** (`656fdc3d`), not the preceding unpublished fix row **`.225`** — hence `226 + 14 = 240` (not `225 + 15`).

---

## 1.7.4.post4 (pending PyPI dispatch)

> Post-release on the **`1.7.4`** public line. **`[project] version = 1.7.4.post4`** and **`[tool.databoar] maturity_build = 226`** (`N=15` fixes since post3 baseline, ADR-0073 dual counter policy).

### Fixed (post4)

- **API logs hardening / demo retrieval:** fixed `/logs` fallback path-injection sink and resolved demo session audit-log retrieval on `/logs/{session_id}`.
- **Help invocation contract:** aligned help text for dev (`python main.py`) vs installed (`data-boar`) usage surfaces.
- **Prefilter recall parity:** prefilter now preserves findings parity when profile signals are active.
- **Config redaction:** DSN/URL embedded credentials are now redacted in `/config`.
- **Web exposure hardening:** safe-by-default API exposure updates and follow-up import-cycle/logging remediations.
- **Report safety:** all XLSX exports route through formula-injection sanitization.
- **Detector hardening:** one-class compliance-term detection is stabilized.
- **SQL connector robustness:** sampling transaction isolation per connection.
- **CI governance:** operator-gated reopen action pins restored.
- **RBAC hardening:** default-deny route map and `compare_digest` byte-safe checks.

### Notes

- Full fix set used for `N=14` is listed in [docs/releases/1.7.4.post4.md](docs/releases/1.7.4.post4.md).

---

## 1.7.4.post3 (pending PyPI dispatch)

> Post-release on the **`1.7.4`** public line. **`[project] version = 1.7.4.post3`** and **`[tool.databoar] maturity_build = 211`** (ADR-0073 dual counter policy).

### Fixed (post3)

- **Dependency security:** `soupsieve` **2.8.3 → 2.8.4** to remove findings for **CVE-2026-49476** and **CVE-2026-49477** ([#1177](https://github.com/FabioLeitao/data-boar/pull/1177)).
- **SQL connector observability:** SQL sampling failures now surface in `scan_failures` (bundle includes [#1144](https://github.com/FabioLeitao/data-boar/pull/1144), issue [#1140](https://github.com/FabioLeitao/data-boar/issues/1140)).
- **Archive observability:** encrypted/corrupt archive members now surface in `scan_failures` (bundle includes [#1146](https://github.com/FabioLeitao/data-boar/pull/1146), issue [#828](https://github.com/FabioLeitao/data-boar/issues/828)).

### Changed (post3)

- **Onboarding docs (`pipx`):** RHEL9-family (`python3.12`) and Alpine/musl (toolchain prerequisites) edge cases documented ([#1175](https://github.com/FabioLeitao/data-boar/pull/1175)).
- **Contributor command docs:** canonical `uv export --frozen --no-emit-project -o requirements.txt` guidance applied in EN/pt-BR ([#1179](https://github.com/FabioLeitao/data-boar/pull/1179), issue [#1176](https://github.com/FabioLeitao/data-boar/issues/1176)).

---

## 1.7.4 (2026-06-26)

> **Stable GA** on the **`1.7.4` line** — release gate **#406** closed with Maestro Deep 5-host completão evidence ([#1021](https://github.com/FabioLeitao/data-boar/issues/1021)). **#970** was a **premature** stable bump/tag **without** the gate — corrected by **ADR-0072**; **`1.7.4` is not VOID**. Public version **`1.7.4`**; **`[tool.databoar] maturity_build = 201`** (side-channel per **ADR-0073** — #976, #977).

### Added

- **SQL sampling (SRE + audit):** connectors + timeouts + **`core/sampling_policy`** — [ADR 0043](docs/adr/ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md).
- **Lab lessons archive:** **`docs/ops/lab_lessons_learned/`** + **`LAB_LESSONS_LEARNED.md`** — [ADR 0042](docs/adr/ADR-0042-lab-lessons-learned-archive-contract.md); **`lab-lessons`** session token.
- **Cross-platform + POSIX gate helpers:** **`scripts/quick-test.sh`**, **`lint-only.sh`**, **`pre-commit-and-tests.sh`**, **`check-all.sh`** — [SCRIPTS_CROSS_PLATFORM_PAIRING.md](docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md).
- **Completão operator prompts:** **`completao-chat-starter.ps1`** + **[COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](docs/ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)** (tiers incl. **`release-master`** parametric semver).
- **Lab-OP personas hub:** **[LAB_OP_HOST_PERSONAS.md](docs/ops/LAB_OP_HOST_PERSONAS.md)** (+ pt-BR).
- **Five-minute onboarding:** **`QUICKSTART.md`** — **#609**.
- **Audience routing:** **`docs/AUDIENCE_GUIDE.md`** — **#595**.
- **Stakeholder pitch stubs + index:** **`docs/pitch/PITCH_STAKEHOLDER.md`**, **`docs/pitch/PITCH_DPO.md`**, **`docs/pitch/PITCH_CISO.md`**, **`docs/pitch/INDEX.md`** — **#586**, **#587**, **#588**, **#594**.
- **Use-case library:** **`docs/use-cases/USE_CASES_HUB.md`**, **`docs/use-cases/USE_CASE_SCAN_AND_REMEDIATE.md`**, **`docs/use-cases/USE_CASE_TOKENIZED_FINDINGS.md`**, **`docs/use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.md`** — **#605**, **#603**, **#602**, **#604**.
- **Plan bridge:** **`docs/plans/PLAN_REMEDIATION_INTERFACE.md`** — **#601**.
- **Privacy management primers:** **`docs/plans/PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md`**, **`docs/plans/PRIMERS_HUB.md`** — **#589**, **#593**.
- **Rules/skills navigator:** **`docs/RULES_AND_SKILLS_HUB.md`** — **#578**.
- **Governance ITSM diagrams (source companion):** **`docs/plans/GOVERNANCE_ITSM_DIAGRAMS_SOURCE.md`** — **#629**, **#630**.

### Changed

- **Governance surfaced copy:** **`CODE_OF_CONDUCT`** (**2.1**), **`TERMS_OF_USE`**, **`PRIVACY_POLICY`** (+ pt-BR; tier matrix, dashboard cues, maturity assessment storage) — **#419**, **#423**, **#424**.
- **Man pages:** **`docs/data_boar.5`** — **`locale`** + unified **`patterns_plugin_file`** — **#444**, **#431**.
- **PMO head-of-queue snapshot:** **`PLANS_TODO.md`** triage (**#483** contextual refresh).
- **Ops / Cursor policy ergonomics:** phase-2 situational **`*.mdc`** (`plans-archive`, **`release-ritual`**, **`es-find`**, **`private-stack-sync`**, homelab **`ssh`**, legal dossier, **`lab-completao`**); **[CURSOR_RULES_PHASE2_SITUATIONALIZATION.md](docs/ops/CURSOR_RULES_PHASE2_SITUATIONALIZATION.md)** Tier ritual (**EN**/pt-BR).
- **`AGENTS.md` / hubs / ladders:** VeraCrypt **`Z:`** default (**`notes-sync.git`**), **`completao`** latch, **`legal-dossier-update`**, homelab **`ssh`** §7.
- **Lab hybrid orchestration:** **`lab-completao-orchestrate-hybrid-v173.ps1`** manifest dispatch + **`1.7.3`** image baseline notes.
- **Lab-OP / Ansible ergonomics:** sudoers **`bash`** paths; **Void** **`xbps-install`** / **`fuse-sshfs`**; skip marker **`.labop-skip-lab-node-01-podman`**.
- **`private-git-sync.ps1`:** bare mirror probe **`Z:`** → **`Y:`** guard + **`git push`** exit semantics (stderr MOTD).
- **Completão archived master tiers:** **`COMPLETAO_MESTRE`** + parametric **`release-master`** semver in **`completao-chat-starter`**.
- **ADR governance hubs:** **[ADR 0056](docs/adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)**, **[ADR 0057](docs/adr/ADR-0057-lightweight-hub-index-co-located-links.md)**, **[ADR 0058](docs/adr/ADR-0058-primer-hub-registration-ritual.md)** — **#582**, **#583**, **#626**.
- **Contributing ergonomics:** venv **`Activate.ps1`** guidance (**EN**/pt-BR); **`tests/test_pwsh_venv_activate_docs.py`**.

### Fixed

- **Maestro / completão Deep smoke:** **`--bench-config`** before **`--lab-stack-up`** — **#404**, **#408**.
- **Docs headings (MD024):** **`TESTING_POC_GUIDE`**, **`TROUBLESHOOTING_MATRIX`** pseudo-heading uniqueness.

### Removed

- **Legacy typo filename:** **`db/databasse.py`** → **`db/database.py`** — **#488**.

### Security

- **Config redaction API:** substring key matching (**`telegram_bot_token`**, **`file_passwords`**, …) on **`GET /config`** — **#622**.
- **Excel export:** formula / **DDE** injection sanitisation — **#547**.
- **`public-tracked-pii-zero-tolerance.mdc`:** placeholder slug hygiene for **`test_pii_guard`**.
- **Timing-safe API key + MAC comparison:** `hmac.compare_digest` in `api/routes.py` and `core/maturity_assessment/integrity.py` — **#825**.
- **Chart.js vendored** (`api/static/chart.umd.min.js`); CSP `script-src 'self'` — no CDN dependency — **#825**.
- **rsync excludes `.env` / `.env.*`** in `Sync-WorkingTree.ps1` — **#825**.
- **Maestro exits non-zero on real handler failures** (`$realFailCount`); offline-skips excluded — **#825**.
- **Maestro Linux-compat:** `-WindowStyle Hidden` guarded by `$IsWindows`; `Start-Process` wrapped in `try/catch` to propagate spawn failures — **#827**.
- **Smoke handlers: base64-encoded `tmux` payloads** eliminate shell-quoting injection; `-Ref` allowlist in all 10 handlers — **#830**.
- **Sentinel result propagation:** all 10 handlers write `/tmp/databoar_handler/<persona>_sentinel.txt`; `Wait-HandlerSentinel.ps1` generalises polling + exit aggregation — **#831**.

---

Full release notes and Docker publish commands: **[docs/releases/1.7.4.md](docs/releases/1.7.4.md)**.

---

## 1.7.3 (2026-04-22)

- Maintenance release to establish stable versioning baseline post-sanitization.
- **Stable semver baseline** after **`1.7.2+safe` / `v1.7.2-safe`**: normalised **PEP 440** **`1.7.3`** for PyPI, docs, and Docker **`1.7.3`** + **`latest`**. Checklist: [docs/releases/1.7.3.md](docs/releases/1.7.3.md).

## 1.7.2+safe (2026-04-22) — Security & Sanitization (Golden / Clean Slate)

**Distribution milestone.** Package version **`1.7.2+safe`** is **PEP 440** (local segment `safe`); **Git** and **Docker Hub** use tag **`v1.7.2-safe`** for parity with the validated slim image.

- **Sanitized publish surface:** **Docker Hub** now standardises on **`fabioleitao/data_boar:v1.7.2-safe`** and **`latest`** (single digest); **all prior Hub tags for this repository were removed** — do not pin deprecated tags in runbooks.
- **Git / history narrative:** Positions the repo after **PII-sensitive history remediation**; external consumers should clone from **`v1.7.2-safe`** onward for the clean baseline story.
- **Feature baseline:** Same application line as **1.7.1** plus subsequent `main` development (WebAuthn phases, RBAC **#86** Phase 2, data-soup Tier 1 + stego hints, etc.); see **1.7.1** below for feature notes. Full operator checklist: [docs/releases/1.7.2-safe.md](docs/releases/1.7.2-safe.md).

### Carryover (was `1.7.2-beta` on `main` before this tag)

- **Dashboard auth (Phase 1a — WebAuthn JSON core):** Optional **`api.webauthn`** + **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`** — [ADR 0033](docs/adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md), `tests/test_webauthn_rp.py`, **`scripts/smoke-webauthn-json.ps1`** + [SMOKE_WEBAUTHN_JSON.md](docs/ops/SMOKE_WEBAUTHN_JSON.md). Default **disabled**.
- **Dashboard auth (Phase 1b — HTML session + CSRF minimal):** WebAuthn session + CSRF on gated routes — `tests/test_webauthn_html_gate.py`, `tests/test_html_csrf.py`.
- **Dashboard RBAC (Phase 2 — GitHub [#86](https://github.com/FabioLeitao/data-boar/issues/86)):** Optional **`api.rbac.enabled`** — `tests/test_rbac.py`. **Phase 3** (enterprise SSO/OIDC) remains future work.
- **Filesystem “data soup” Tier 1 + stego hints:** **`SUPPORTED_EXTENSIONS`** + **`file_scan.scan_for_stego`** / CLI **`--scan-stego`**; import fix in **`connectors/filesystem_connector._read_text_sample`** for **`RICH_MEDIA_SCAN_EXTENSIONS`**.

## 1.7.1 (2026-04-21)

- **Scope import (CSV):** `scripts/scope_import_csv.py` + `config/scope_import_csv.py` emit a YAML **`targets`** fragment from a canonical CSV for operator review and merge; see [USAGE.md](docs/USAGE.md#scope-import-from-csv-config-fragment), `deploy/scope_import.example.csv`, [docs/ops/SCOPE_IMPORT_QUICKSTART.md](docs/ops/SCOPE_IMPORT_QUICKSTART.md), [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](docs/plans/completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md).
- **Ops (maturity POC):** [docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.md](docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.md) (+ pt-BR) documents **autonomous** pytest smoke (`scripts/smoke-maturity-assessment-poc.ps1`) and **manual** browser/integrity steps for the **POC ready** checklist; indexed from [docs/ops/README.md](docs/ops/README.md).
- **Dashboard (maturity POC):** `GET /{locale}/assessment` shows a **recent submissions** table (per **batch**, newest first) when the SQLite DB has stored answers; links reuse the post-submit summary URL and CSV export. Documented in [ADR 0032](docs/adr/ADR-0032-maturity-assessment-batch-history-sqlite.md). Per-tenant RBAC for this list remains **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** follow-up.
- **Licensing / maturity POC:** API tests assert **`licensing.mode: enforced`** + JWT **`dbtier`** (community vs pro) gates `/{locale}/assessment` (and export) consistent with YAML `effective_tier` override — see `tests/test_api_assessment_poc.py` (`test_assessment_enforced_jwt_dbtier_*`).

## 1.7.0 (2026-04-17)

- **Minor release:** detector **format hints** (REST JSON scalars, **email**/**UUID** `VARCHAR` hints), **HEIC** / Apple images when optional deps are present; reporting/security fixes (heatmap path guard, report import hygiene).
- **Compliance & docs:** **GLOSSARY** and **COMPLIANCE_AND_LEGAL** expanded (US healthcare adjacency, **Corporate-Entity-C/WRB**, **VBA** disambiguation, minors/criminal-record **context** — not legal conclusions); alignment with **ADR 0025** evidence positioning.
- **Repository:** PII guards, CI/deps, Semgrep/Bandit posture; operator **Ansible**/homelab scripts and runbooks (see [docs/releases/1.7.0.md](docs/releases/1.7.0.md) for full checklist).

## 1.6.8 (2026-04-02)

- **Ops automation:** added reusable token-aware wrappers for session bootstrap, progress snapshots, and external review package generation (`scripts/auto-mode-session-pack.ps1`, `scripts/progress-snapshot.ps1`, `scripts/external-review-pack.ps1`).
- **Review reliability:** hardened Gemini bundle verification logic to avoid false mismatches when marker-like text appears inside documentation examples (`scripts/export_public_gemini_bundle.py`).
- **Runbooks and governance:** expanded today/next-day/carryover discipline, reinforced Corporate-Entity-C/Gemini source-of-truth framing, and added Time Machine USB recovery and repurpose playbook for urgent storage/backup recovery.
- **Hardening and lab-op docs:** integrated LMDE/LAB-NODE-01 and Ansible hardening baselines, validation checklists, and CAPEX/OPEX planning outputs aligned to current roadmap.

## 1.6.7 (2026-03-25)

- **Removed** legacy **`run.py`**. Use **`python main.py`** only, with the correct **bind** flags (`--host`, `api.host`, `API_HOST`) and **dashboard transport** (`--https-cert-file` / `--https-key-file`, or `--allow-insecure-http` / `api.allow_insecure_http`). See [docs/releases/1.6.7.md](docs/releases/1.6.7.md) and [docs/USAGE.md](docs/USAGE.md).
- **Docs / tooling:** `docs/USAGE.md` (+ pt-BR), `sonar-project.properties`, `docs/plans/completed/NEXT_STEPS.md` updated accordingly.

## Earlier versions

See [docs/releases/](docs/releases/) (e.g. `1.6.6.md`, `1.6.5.md`, …).

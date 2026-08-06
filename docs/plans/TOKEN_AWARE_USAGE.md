# Token-aware usage – short and long-term goals

**Purpose:** Keep progress effective when **token/context limits** apply (e.g. after an initial Pro+ burst). Use this doc and [PLANS_TODO.md](PLANS_TODO.md) as the main entry points so sessions stay focused and avoid loading the whole repo.

**Readable view in Cursor:** Say **`pmo-view`** in chat for a reminder to open plan/PMO Markdown in **Preview** (`Ctrl+Shift+V` / `Ctrl+K` `V` on Windows). See [docs/ops/README.md](../ops/README.md) § *pmo-view*.

**Policy:** Prefer **one plan or one feature at a time**; open only the files needed for that slice. Update PLANS_TODO and the relevant plan file when a step is done.

**Sprints / milestones / Gantt–Kanban / SRE (light PM):** To time-box themes (hygiene → lab → Tier-2 slices), optional Mermaid Gantt, Kanban columns, milestones (**M-TRUST**, **M-OBS**, …), and SRE-style guardrails (toil, error budget, blameless retro pointers), see **[SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)** ([pt-BR](SPRINTS_AND_MILESTONES.pt_BR.md)). For **how to combine** milestones into narrative vs commercial posture (without alternate stage naming), see **SPRINTS_AND_MILESTONES.md** section **5** subsection **Composing milestones (release lifecycle map)**.

**When to pause token-saving mode:** If **Docker Hub exposure**, **issuer keys**, **dependency CVEs**, or **commercial/IP posture** need attention first, open **[PLANS_TODO.md](PLANS_TODO.md)** and run the table **“Priority band A”**, then use **[CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md)** for copy-paste prompts. After **A1–A3** (minimum), return to one-row-per-session feature work.

---

## 1. Short-term vs long-term (at a glance)

| Horizon                | Focus                                                                                                                                                                                                                                                                                                                                                                                                            | Where it lives                                                                                                                                                                                                                                      |
| --------               | -----                                                                                                                                                                                                                                                                                                                                                                                                            | ---------------                                                                                                                                                                                                                                     |
| **Short (this cycle)** | High-value slices: maintenance (–1/–1b), **home lab –1L** (manual, after maintenance), FN reduction (slices 1–4 baseline done; next optional aggregation/incomplete-data options), Strong crypto Phase 1, Data source inventory Phase 1, Notifications Phase 1; content-type optional follow-ups. **If critical:** Priority band A first.                                                                        | PLANS_TODO § “Priority band A”, § “What to start next” (**–1L**), § “A. Near-term focus”                                                                                                                                                            |
| **Medium**             | Readiness: runbooks, compliance evidence subsection, data retention note, onboarding checklist, dependency policy sentence. Milestone **bundles** for storytelling vs commercial posture: [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §5 (*Composing milestones*).                                                                                                                                      | [PLAN_READINESS_AND_OPERATIONS.md](PLAN_READINESS_AND_OPERATIONS.md); [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §5                                                                                                                                                                                       |
| **Long (academic)**    | Lato sensu thesis (framing, case studies, evidence mapping); stricto sensu research path; compliance evidence mapping table. **After lato sensu:** choose one path when ready (stricto sensu, Faculdade HUB MBA IA, Universidade do Intercâmbio, or other) – see [PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md) §4.2; open only that one plan or program link per session (token-aware). | [PLAN_LATO_SENSU_THESIS.md](PLAN_LATO_SENSU_THESIS.md), [PLAN_STRICTO_SENSU_RESEARCH_PATH.md](PLAN_STRICTO_SENSU_RESEARCH_PATH.md), [PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](PLAN_COMPLIANCE_EVIDENCE_MAPPING.md); post-lato options in PORTFOLIO §4.2 |
| **Deferred / backlog** | Secrets Phase B, Version check, Selenium QA, Synthetic data, SAP, Dashboard i18n, Additional data soup formats.                                                                                                                                                                                                                                                                                                  | PLANS_TODO § “B. Deferred”, § “C. Backlog”                                                                                                                                                                                                          |

---

## 2. Working under token constraints

- **Chat language:** Operator preference is **concise pt-BR** in assistant replies with **English** for paths, commit types, and code identifiers—see **`AGENTS.md`** and **`docs/PRIVATE_OPERATOR_NOTES.md`** §5.1. Mixing languages in one message is fine; asking for **`short`** / **`token-aware`** (English tokens) saves tokens more than picking EN vs pt-BR for prose.
- **Session shorthand:** Taxonomy keywords (`deps`, `feature`, `homelab`, `docs`, `houseclean`, `backlog`, `pmo-view`, …) are **English-only** in chat and in **`.cursor/rules/session-mode-keywords.mdc`**—see **`AGENTS.md`**. Grouping + LAB-OP SSH naming (**`lab-op`**): **`docs/ops/OPERATOR_SESSION_SHORTHANDS.md`** ([pt-BR](../ops/OPERATOR_SESSION_SHORTHANDS.pt_BR.md)).
- **Single-context rule:** For each session, choose **one** of: (a) one plan’s next to-do, (b) one readiness item, or (c) one academic-plan section. Open only that plan file + the code/docs files you need to edit.
- **Milestone / sprint theme vs token-cherry-picking:** Token-aware work means **chunking the active theme** (PLANS_TODO + Kanban **Selected** / **In progress** in [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)), not hopping to an unrelated “cheap” task every session **only** to save tokens. If the **operator** reprioritises, switch theme explicitly. Same policy as **`.cursor/rules/execution-priority-and-pr-batching.mdc`** §3.
- **Low complexity / high gain bias:** Prefer small-scope, high-value slices **inside** that theme (see PLANS_TODO "What to start next"). For study: one cert at a time (CWL order in PORTFOLIO §3.2 and `docs/private/Learning_and_certs.md`); post-lato choice (stricto sensu vs MBA HUB vs Intercâmbio) is a separate, low-frequency decision – PORTFOLIO §4.2 has the comparison; open only one option per session.
- **Entry point:** Start from [PLANS_TODO.md](PLANS_TODO.md). Use the “What to start next” table and the “Order” column to pick the next step.
- **AI-heavy vs manual-friendly:** PLANS_TODO marks which tasks benefit from AI (research, wording, design) vs which you can do by hand (regex wiring, tests, config). Use AI for the former; do the latter in small, focused sessions.
- **After each step:** Run `uv run pytest -v -W error` (or `.\scripts\check-all.ps1` on Windows), update the plan and PLANS_TODO, then commit. Avoid stacking many uncommitted changes.
- **Before a PR (token-saving checklist):** [docs/ops/README.md](../ops/README.md) § *Before you open a PR* (EN) · [docs/ops/README.pt_BR.md](../ops/README.pt_BR.md) § *Antes de abrir um PR* (pt-BR): run **check-all**, never commit **`docs/private/`** or **`git add -f config.yaml`**, use **`docs/private.example/`** for layout. Optional echo-only reminder: **`scripts/pr-hygiene-remind.ps1`**.
- **Operator LinkedIn profile (ATS / SLI refresh):** LinkedIn does not expose a **general-purpose public API** for “full profile JSON” to personal automation—that does **not** block the assistant: the operator authorizes **live review** via the **Cursor embedded browser** (warm session or **Google SSO** on LinkedIn). For **token-efficient structured diff**, the repo uses **`scripts/extract_cv_pdf.py`** on profile PDFs (same as talent CVs). **Token-aware flow:** (1) save profile PDF under **`docs/private/author_info/`**, (2) run **`.\scripts\operator-linkedin-profile-extract.ps1`** from repo root — JSON + text land in **`docs/private/author_info/career/exports_linkedin_snapshot/`**. Prefer **`read_file` on that JSON** when diffing long static text; use the **browser** for live-only fields and when refreshing talent-pool docs from **linkedin.com**. Policy: **`docs/private/author_info/career/README.pt_BR.md`** § *Automação* · private **`docs/private/commercial/ats_sli_hub/LIVE_LINKEDIN_REFRESH_POLICY.pt_BR.md`**.

---

## 3. Artifacts and evidence (for narrative and thesis)

**Full checklist (URLs, Dockerfiles, GitHub, certifications, community):** [PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md). Use it when drafting thesis, evidence mapping, or pitch so you open one source at a time.

Summary:

- **This repo (Data Boar):** Main compliance/LGPD artifact; Docker image `fabioleitao/data_boar`; Dockerfile in repo root.
- **Docker Hub:** Public pages fetched for data_boar, wildfly_t1r, uptk (tags, sizes, links). Authoritative list: `docs/private/From Docker hub list of repositories.md`.
- **GitHub:** DataBoar/data-boar, wf_t1r, and other public repos; profile and repo list in PORTFOLIO_AND_EVIDENCE_SOURCES.
- **Certifications / community:** LPIC-1 (101); Ubuntu tester/collaborator. Add others in PORTFOLIO_AND_EVIDENCE_SOURCES §3.
- **CWL courses (paid, in progress):** Listed and prioritised in PORTFOLIO_AND_EVIDENCE_SOURCES §3.2 (from `docs/private/` images). **Study is your task;** use the recommended order there (BTF → C3SA → MCBTA → PTF → …) and slot fixed study blocks after Dependabot/Scout and one feature slice; one cert at a time for max value.
- **Private docs (git-ignored):** CV, TCC, LinkedIn PDFs in `docs/private/`; reference by filename only.
- **Home lab validation:** Second machine checks (Docker deploy, synthetic filesystem/SQL targets)—manual playbook [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md) ([pt-BR](../ops/HOMELAB_VALIDATION.pt_BR.md)); run between releases or before demos without burning agent tokens on ad-hoc steps. On Windows, prefer repo scripts **`scripts/docker-lab-build.ps1`**, **`scripts/docker-hub-pull.ps1`**, **`scripts/docker-prune-local.ps1 -WhatIf`** ([scripts/docker/README.md](../../scripts/docker/README.md)) so agents and operators reuse one flow and keep local image tags bounded.

Optional: add Dockerfiles (or a short note) for wildfly_t1r/uptk in `docs/private/Dockerfiles_used.md` or in the wf_t1r repo so “Dockerfiles I created and used” is easy to cite.

When you add new evidence, list it in PORTFOLIO_AND_EVIDENCE_SOURCES or in this section so the next session knows what to use.

---

## 4. One-session recipe (example)

1. Open **PLANS_TODO.md** and pick one row from “What to start next” (e.g. Content-type Step 2).
1. Open **PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION.md** and the one or two source files you need (e.g. config schema, filesystem connector).
1. Implement the step; add tests; update USAGE or TECH_GUIDE if needed.
1. Mark the to-do done in both the plan and PLANS_TODO; run tests; commit.
1. Next session: repeat with the next row or the next step in the same plan.

---

## 5. Sync and maintenance

- **PLANS_TODO** is the single source of truth for execution order and status. When a plan file’s to-dos change, sync PLANS_TODO so the “What to start next” table and open-plan sections stay accurate.
- This file (TOKEN_AWARE_USAGE) should be updated when: (1) short vs long-term priorities change, (2) a new artifact or doc is added to `docs/private/`, or (3) you adopt a new “one-session” pattern.

---

## 6. Security-first burst vs token-aware pace

| Mode                    | When to use                                                                                              | What you ask the agent                                                                                                                                                                                              |
| ----                    | ------------                                                                                             | ----------------------                                                                                                                                                                                              |
| **Security / IP burst** | Stale public images, open Dependabot alerts, or issuer/commercial boundary is blocking trust or revenue. | One step at a time: *“Priority band A, step A2: help triage Dockerfile / Scout output and propose minimal changes.”* Full prompts: [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md). |
| **Token-aware pace**    | After A1–A3 (or when nothing above is urgent).                                                           | *“PLANS_TODO order N only”* or *“Content-type Step 4 only; don’t load other plans.”*                                                                                                                                |

**Rule of thumb:** If skipping A1–A3 could leave **known-bad dependencies** or **easy pull of obsolete images** in the wild, do the burst first; profitability follows **trust + hygiene**, not only feature velocity.

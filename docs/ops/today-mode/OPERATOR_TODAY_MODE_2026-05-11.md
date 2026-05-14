# Operator today mode — 2026-05-11 (post **v1.7.4-rc**; lab metrics + short-sprint closure)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md)

**Theme:** **`main`** carries **`1.7.4-rc`** with GitHub pre-release **`v1.7.4-rc`**; **consumer Docker Hub** stays **`1.7.3`** / **`latest`**. **Today:** close **CI/workflow hygiene** (uncommitted **`zizmor`** workflow), then **controlled lab timing** (**`1.7.3`** Hub baseline vs current line) before promoting **almost-done** product slices (**CNPJ Phase 5**, **Bandit Phase 3**, **Scope import Phase E**). **First:** **`git fetch origin`** · **`git checkout main`** · **`git pull origin main`** · **`git status -sb`**.

---

## Block 0 — Morning reality check (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** fast-forward if behind; confirm **`pyproject.toml`** **`1.7.4-rc`** matches intent.
2. **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) — stable **Latest** = **`v1.7.3`**; pre-release = **`v1.7.4-rc`** (no Hub marketing refresh for RC unless you deliberately publish a lab-only tag).
3. **Open PRs:** triage **Dependabot** / **deps** drafts (**#348** open; **#349–#352** draft) — merge or defer with date; do not stack unrelated product work on the same branch.
4. **Stacked private (`docs/private/`):** schedule **`.\scripts\private-git-sync.ps1`** (**`-Push`** per policy) after lab evidence or social edits.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **Alvo editorial** matching **2026-05-11** / **2026-05-12** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — from 2026-05-10 session

- [ ] **Maestro / completão evidence:** archive read — [`LAB_LESSONS_LEARNED_2026_05_10.md`](../lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md); hub [`LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md). **Maestro hardening rows 1–6** in **`PLANS_TODO.md`** are **done** on **`main`**.
- [ ] **Cross-host DB matrix:** one consolidated round with per-host config proving each runtime can query deployed synthetic DB targets (still open in lessons snapshot).
- [ ] **WSL2 Mongo placement:** accepted scope — Mongo on secondary x86 lab host while designated WSL2 stays ICMP-only; optional infra follow-up only if you move Mongo back to WSL2.
- [ ] **Performance narrative:** treat **Rust/PyO3 regression** claims in older lessons as **stale until re-measured** — run controlled **`1.7.3`** vs **`1.7.4-rc`** lab timing (parallelism + throttling included in current line).
- [ ] **Workflow security lint:** commit + PR **`.github/workflows/zizmor.yml`** (advisory default; **`ZIZMOR_ENFORCE=true`** or **`workflow_dispatch`** **`enforce=true`** when ready to block).

---

## Focus A — CI / pipeline hygiene (≤1 h)

| # | Activity | Done when |
| - | -------- | --------- |
| A1 | Land **`zizmor`** workflow on **`main`** (warn-first; optional enforce later) | PR merged; workflow visible on GitHub Actions |
| A2 | Confirm **`v1.7.4-rc`** pre-release on GitHub; **no** accidental Hub **`latest`** move | **`gh release view v1.7.4-rc --json isPrerelease`**; Hub tags unchanged |
| A3 | Optional: refresh [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) **Verified** row after A2 | Date + prerelease pointer accurate |

---

## Focus B — Controlled lab metrics (**1.7.3** vs **`1.7.4-rc`**) (half day when LAB slot exists)

| # | Activity | Done when |
| - | -------- | --------- |
| B1 | Pull **`fabioleitao/data_boar:1.7.3`** (Hub baseline) + build/run **`1.7.4-rc`** from **`main`** (local **`data_boar:lab`** or agreed tag) | Two reproducible run configs documented in **private** notes |
| B2 | Run **`.\scripts\benchmark-ab.ps1`** (or project benchmark ritual) on **same synthetic corpus** / DB fixture | **`benchmark_runs/`** or private report with wall-clock + throughput |
| B3 | Update **public-safe** lessons hub only if numbers are verified — otherwise keep claims in **`docs/private/homelab/reports/`** | No invented metrics in tracked docs |
| B4 | Decide whether **lessons-learned** performance bullets need rewrite | One line in **`PLANS_TODO.md`** or dated lab archive if stale |

**Chat token:** **`completao`** / **`homelab`** when orchestrating multi-host smoke; not a substitute for A/B timing.

---

## Focus C — Almost-done plans (pick **one** primary slice)

Source: **`docs/plans/PLANS_TODO.md`** *Post-`1.7.4` short-sprint closure queue*.

| Sprint | Slice | Exit checklist (summary) | Plan |
| ------ | ----- | ---------------------- | ---- |
| **S3** | **CNPJ Phase 5 (checksum layer)** | Opt-in checksum path; phases **5.1–5.3**; default regex behaviour unchanged; EN + pt-BR docs | [PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md](../../plans/PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md) |
| **S1** | **Bandit Phase 3 closure** | **`-ll -ii`** gate green; low findings triaged; plan → **`completed/`** when done | [PLAN_BANDIT_SECURITY_LINTER.md](../../plans/completed/PLAN_BANDIT_SECURITY_LINTER.md) |
| **S2** | **Scope import Phase E (light)** | First GLPI-like adapter + fixtures + tests; no live-integration overpromise | [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](../../plans/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) |

**Secondary (if energy):** **Content type Step 1** (magic-byte table) · **Notifications Phase 4** (audit log of sends) — see **`PLANS_TODO.md`** H1/U1.

**Gate before PR:** **`.\scripts\check-all.ps1`**.

---

## Backlog — promote or defer (do not silent-carry)

| Item | Default | Promote when |
| ---- | ------- | ------------ |
| **–1L** second-environment matrix | Defer | Hardware calendar or explicit lab day |
| **S2a** transport + trust (**#86** Phase 1) | After RC lab metrics | Demo-ready trust story selected in sprints |
| **Dependabot** draft cluster **#349–#352** | Triage | **`deps`** session with **`check-all`** |
| **Corporate-Entity-C WRB** | Carryover | Comms window — [CARRYOVER.md](CARRYOVER.md) |
| **LAB observability / Wazuh** | H2 backlog | Firewall + minimal stack prerequisites met |

---

## End of day

- **`block-close`** when pausing lab / VC — private **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`**
- **`eod-sync`** or **`.\scripts\operator-day-ritual.ps1 -Mode Eod`** — deferrals with **date** into [CARRYOVER.md](CARRYOVER.md) or **`PLANS_TODO.md`**
- Skim **`OPERATOR_TODAY_MODE_2026-05-12.md`** next (copy from [OPERATOR_TODAY_MODE_TEMPLATE.md](OPERATOR_TODAY_MODE_TEMPLATE.md) if missing)

---

## Quick references

- Release notes: **`docs/releases/1.7.4-rc.md`** · **`docs/VERSIONING.md`**
- Lab lessons: **`docs/ops/lab_lessons_learned/`** · ADR **0042** archive ritual (**`lab-lessons`**)
- Session keywords: **`feature`**, **`deps`**, **`homelab`**, **`completao`**, **`backlog`**, **`eod-sync`**

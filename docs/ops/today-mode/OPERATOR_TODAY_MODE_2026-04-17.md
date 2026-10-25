# Operator today mode — 2026-04-17 (stable beta lane, CI fix, synthetic tests + lab-op)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-17.pt_BR.md)

**Theme:** Confirm **`main`** is **green on GitHub Actions** after the **`ci.yml`** Sonar job fix (job-level `secrets` `if` removed). **Pull** locally. Position **v1.7.0** + **FCPA policy sample** + **jurisdiction hints** as the **beta-stable** baseline for **IDENTIDADE_COLABORADOR_A** and **IDENTIDADE_COLABORADOR_B** to start **synthetic / structured tests**, and for **lab-op** smoke when you choose. **Triage** carryover from **2026-04-16** without abandoning **Corporate-Entity-C / WRB** rhythm.

### Full day ritual (2026-04-17)

1. **Morning:** **`carryover-sweep`** — or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`** — plus skim **[CARRYOVER.md](CARRYOVER.md)** and **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** if you use them.
2. **Sync git:** **`git fetch origin`**, **`git checkout main`**, **`git pull origin main`** (fresh advice needs fresh refs — see **COMMIT_AND_PR** / git sync habit).
3. **Run this file top to bottom:** **Block A** (gates) → **B** (testers) → **C** (lab-op) as time allows.
4. **Evening:** **`eod-sync`** — or **`.\scripts\operator-day-ritual.ps1 -Mode Eod`** — then **[End of day](#end-of-day)** below.

**Resume with low risk (after sleep / before deep work):** `git status -sb` (clean or intentional WIP) → `git fetch origin && git pull origin main` → skim **[CARRYOVER.md](CARRYOVER.md)** → **Block A** (CI green + optional `check-all`). If you **closed 2026-04-16** with **`eod-sync`**, you already have log/PR snapshot; if not, run **`eod-sync` once** before merging risky work. **ADR / licensing docs:** [ADR 0027](../../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md); private example: `docs/private/commercial/LICENSING_TIER_EXAMPLE_FEDERATED_OPERATOR.pt_BR.md`.

---

## Session handoff (2026-04-17 morning)

- **`origin/main`:** Shipped **v1.7.0** earlier; **2026-04-17** commits: **`docs(compliance): FCPA internal policy sample…`**, **`feat(report): optional jurisdiction hints…`**, **`ci(workflow): fix Sonar gate scheduling`** (if merged after this file was written — verify with `git log -3`).
- **Local sync:** `git fetch origin && git pull origin main` — working tree clean after merge.
- **CI:** Open **Actions** → workflow **CI** — expect **test**, **lint**, **bandit**, **audit** jobs; **Sonar** job should **skip steps** when `SONAR_TOKEN` is absent (no failure), or **run scan** when token is set.
- **Compliance:** New sample **`docs/compliance-samples/compliance-sample-us_fcpa_internal_policy_pack.yaml`** — merge into config with **counsel** for employer-specific wording; **not** a violation engine.
- **Beta testers:** Share **install path** (Docker Hub **`fabioleitao/data_boar:1.7.0`** / `latest`), **`check-all`** bar for changes, and **USAGE** + dashboard **jurisdiction hints** (opt-in) for DPO triage narratives.

---

## Block A — Verify gates (15–20 min)

1. `git status -sb` · `gh run list -L 5 --workflow ci.yml` — latest **push** to `main` **success** (or identify failing job).
2. **`.\scripts\maintenance-check.ps1`** (optional) — Dependabot + alerts snapshot.
3. **`.\scripts\check-all.ps1`** on **`main`** after pull — local parity with CI.
4. If **Sonar** home lab is up: skim **new** issues on `main` (optional).

---

## Block B — Stable beta for synthetic tests (IDENTIDADE_COLABORADOR_A / IDENTIDADE_COLABORADOR_B)

- [ ] **Scope doc:** one short message or checklist — **what to test** (dashboard scan, sample config, **metadata-only** reports, **optional** `compliance-sample-us_fcpa_internal_policy_pack.yaml` only on a **copy** of config with counsel approval).
- [ ] **No PII in issues:** feedback stays **generic** or **private** git per **AGENTS.md**.
- [ ] **Next patch version** only if hotfix needed — else stay on **1.7.0** until the next planned release (**PUBLISHED_SYNC.md**, **VERSIONING.md**).

---

## Block C — Lab-op (optional same day)

- [ ] **`docs/private/homelab/lab-op-hosts.manifest.json`** present → **`.\scripts\lab-op-sync-and-collect.ps1`** when you want a fresh inventory log (SSH from dev PC).
- [ ] **Docker smoke:** **`docker pull fabioleitao/data_boar:1.7.0`** on target host — align with **HOMELAB_VALIDATION** if you run full checklist.

---

## Carryover (from 2026-04-16 + queue)

See **[CARRYOVER.md](CARRYOVER.md)** — update rows when **Corporate-Entity-C**, **Dependabot**, or **WRB** move. **Priority today:** **CI green**, **tester onboarding**, **no silent backlog**.

---

## End of day

- **`eod-sync`** or **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- **`gh pr list --state open`** — close or supersede stale branches.

---

## Quick references

- **Release truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) · **v1.7.0** notes: [releases/1.7.0.md](../../releases/1.7.0.md)
- **PLANS:** [PLANS_TODO.md](../../plans/PLANS_TODO.md) · [PLANS_HUB.md](../../plans/PLANS_HUB.md)
- **ADR:** [0026 Jurisdiction hints](../../adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) · [0025 Compliance ceiling](../../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)
- **Corporate-Entity-C:** [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](../Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md)

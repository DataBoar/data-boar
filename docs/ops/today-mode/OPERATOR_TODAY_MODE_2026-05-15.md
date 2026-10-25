# Operator today mode — 2026-05-15 (carryover + governance closure)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-15.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-15.pt_BR.md)

**Note:** This file was drafted **after** the calendar evening of **2026-05-14**; Block 0 still wins for “what to run first” on **2026-05-15**.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — snapshot **`main`** CI (**`ci.yml`**) before deep work.
2. **Open PRs (deps / workflow):** triage with a **`deps`** or focused pass — current open set includes **#374** (ebcdic/chardet caps), **#365** (Slack CI mute switch), **#355**, **#348**, **#347**, **#346**. Merge or defer with date; avoid chore-bundling unrelated constitutional doc changes into the same PR as ADR ratification.
3. **VeraCrypt `Z:` / private stack:** if **fsync** or mount issues persist from **2026-05-14**, remount and rerun **`.\scripts\private-git-sync.ps1 -Push`** per **[ADR 0040](../../adr/ADR-0040-assistant-private-stack-evidence-mirrors-default.md)** habit.
4. **Governance in flight:** **[ADR 0055](../../adr/ADR-0055-adr-bar-nontrivial-architecture-only.md)** is **`Proposed`** until **you** ratify (**explicit chat for that ADR** **or** **authored** `Status` / `Deciders:` edit) — **merge alone does not promote**; see **`.cursor/rules/adr-trigger.mdc`** and **`AGENTS.md`** ADR habit bullet.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for editorial targets on **2026-05-15** / **2026-05-16** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — same spine as **2026-05-14**

| Track | Item | Notes |
| ----- | ---- | ----- |
| Strategy / plans | **PCI-DSS v4 / S4b** (context gates; **ADR-0052** phase 2) | Rolling row in [CARRYOVER.md](CARRYOVER.md) — owner in **`PLANS_TODO.md`**. |
| Lab | **Maestro DB matrix (all-to-all)** | Per-host reports under **`docs/private/homelab/reports/`**; fix **sudo**/NFS/CIFS prerequisites. |
| Product | **Sprint closure** — pick **one** | S3 CNPJ phase 5 **or** S1 Bandit phase 3 **or** S2 Scope import phase E — then **`feature`** + **`check-all`**. |
| Maestro hardening | **Bugs 1–3** (SSH timeout, positional YAML arg, collect race) | See **2026-05-14** checklist; promote fixes with tests or runbook notes. |
| Social | **L3 LinkedIn**, **X5** | Catch up overdue editorial rows; permalinks in private hub only. |

---

## Optional Focus — ADR / agent contract (if you have a short block)

- [ ] **Decide ADR-0055:** **`Accepted`** / **`Rejected`** / **`Deferred`** + real **`Deciders:`** only after **your** explicit ratification — update **`docs/adr/README.md`** index row to match file.
- [ ] **Skim new always-on rule** **`.cursor/rules/agent-project-contract-binding.mdc`** — confirms merge ≠ law; no chore-bundle ratification hacks.

---

## End of day (**2026-05-15**)

- **`eod-sync`** (or lighter **`block-close`** if pausing mid-week) — see [README.md](README.md) *Morning readiness* / private VeraCrypt policy.
- If anything under **`docs/private/`** moved: **`.\scripts\private-git-sync.ps1 -Push`** to mirrors you use.

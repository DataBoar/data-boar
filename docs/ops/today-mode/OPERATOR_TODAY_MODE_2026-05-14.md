# Operator today mode — 2026-05-14 (carryover + focus)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-14.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-14.pt_BR.md)

---

## Block 0 — Morning reality (10–15 min)

1. **`origin/main`:** `git pull origin main` — confirm latest **`main`** CI with `gh run list` / Actions (many commits landed earlier in the week; verify green before deep work).
2. **Dependabot / deps:** open PRs to triage in a **`deps`** session — e.g. **#355** (uv minor/patch group), **#348** (hatchling), **#347** (chardet), **#346** (**ebcdic** — may conflict with cap work), plus **#374** (consolidate ebcdic/chardet caps) and **#365** (Slack CI kill-switch). Reconcile with ADR/supply story before merge.
3. **VeraCrypt `Z:`:** private push reported **fsync** error **2026-05-14** ~00:01 — confirm volume mounted; rerun **`.\scripts\private-git-sync.ps1 -Push`** when healthy.
4. **Working tree:** `git status -sb` — expect clean after prior session; fix stray WIP before new slices.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

---

## Carryover (from 2026-05-13 snapshot)

### Real open items (narrow list)

- [ ] **Maestro DB matrix (all-to-all)** — one consolidated round; per-host configs under **`docs/private/homelab/reports/`**. Unblock NFS/CIFS / **sudo** where `sudo: password required` still blocks.
- [ ] **Short sprint closure post-`1.7.4`** — pick **one**: S3 CNPJ phase 5, S1 Bandit phase 3, or S2 Scope import phase E — then **`feature`** + **`check-all`**.

### Maestro bugs (high priority when LAB session opens)

- [ ] **Bug 1 — SSH without `ConnectTimeout`** — add **`-o ConnectTimeout=15`** (or project default) in handlers.
- [ ] **Bug 2 — `benchmark-rc.yaml` passed as stray positional** in `Handle-baremetal.ps1` / `Handle-docker.ps1` → smoke **exit 2**.
- [ ] **Bug 3 — `SleepBeforeCollect` race** — replace 120s workaround with sentinel under **`$LC_BENCH_ROOT`** + proper wait helper.

### Social / editorial (still due)

- [ ] **L3 LinkedIn (lab-op Ansible)** — target **2026-05-13**; publish + capture permalink in private hub.
- [ ] **X5 relaunch** — overdue (target **2026-05-10**); six-tweet thread — validate with `uv run python scripts/social_x_thread_lengths.py`.

---

## What shipped 2026-05-13 (reference)

- Quality: Gemini P0/P1 + Warm fixes; CPF/CNPJ FP work + tests; Bandit/Ruff coverage extended; B608 narrowed to inline justifications.
- Docs: ADR-0050 plan-metadata guard improvements; carryover table trimmed with operator confirmation.
- Infra: many commits on **`main`**; private sync mostly OK except **`Z:`** fsync — investigate.

---

## End of **2026-05-15** (next calendar day)

- **`eod-sync`** + confirm CI for anything merged **2026-05-14** / **15**.
- After Maestro / lab: **`private-stack-sync`** when private reports change.
- **`block-close`** + VeraCrypt / volume policy per private runbook if **`Z:`** still flaky.

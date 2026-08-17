# Operator today mode — 2026-08-16 (two-week cycle refresh + #1602)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-16.pt_BR.md)

**Headline:** Refresh **two-week** cycle (**2026-08-16 → 2026-08-29**) → land **[#1602](https://github.com/DataBoar/data-boar/pull/1602)** when green → Dependabot triage → continue **#1586** when capacity allows.

**Workstation clock (this file):** `2026-08-16` (−03).

**Two-week plan:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md)

---

## Block 0 — Reality

1. **`main`:** `git fetch` + `git pull origin main`.
2. **Open PRs (product / docs):**
   - [#1602](https://github.com/DataBoar/data-boar/pull/1602) — cross-surface observability gates (docs/backlog) — **merge when Tests green**.
3. **Open PRs (Dependabot — do not blind-merge):**
   - [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7** (Actions major)
   - [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25**
4. - [ ] **`carryover-sweep` / `morning-readiness`** at start · **`block-close`** / **`eod-sync`** at boundaries.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · Prior day: [OPERATOR_TODAY_MODE_2026-08-15.md](OPERATOR_TODAY_MODE_2026-08-15.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-16** / **2026-08-17**).

---

## Suggested sequencing

### A — Close the cycle anchor

| Step | Item | Notes |
| ---- | ---- | ----- |
| 1 | Refresh two-week plan | EN + pt-BR cycle table (**2026-08-16 → 2026-08-29**) — this session |
| 2 | Land **#1602** | Hub row must **not** include untracked local-only plans |
| 3 | Confirm `main` green | `gh run list --workflow ci.yml -L 3` after merge |

### B — Dependabot (`deps`)

Triage with **`.cursor/skills/dependabot-recommendations/SKILL.md`**. Prefer **Actions** before **major** Python.

| Order | PR | Notes |
| ----- | -- | ----- |
| 1 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) | Major Actions — changelog + CI matrix |
| 2 | Majors **#1487 / #1485 / #1484** | One at a time; `check-all` + smoke |

### C — #1586 TCP pin (if energy left)

| Step | Item | Notes |
| ---- | ---- | ----- |
| 1 | Redis subclass pin | Next after Postgres/Mongo on `main` |
| 2 | MySQL / Oracle | Case-by-case |
| — | mssql | Deferred → [#1588](https://github.com/DataBoar/data-boar/issues/1588) |

### D — Not default today

- Full **#1601** RUM runtime (Week 2 after #1602)
- Maestro **#32** OTel preflight unless lab focus wins

---

## Carryover — day rows

- [ ] Two-week cycle docs on a **docs** branch/PR (or fold after #1602 merges)
- [ ] Merge **#1602** when green
- [ ] Triage **≥1** Dependabot PR (prefer Actions)
- [ ] Update **CARRYOVER** if #1586 / deps status changes
- [ ] No product commit without `check-all` / CI green on that PR

---

## End of day

- **`block-close`** + VeraCrypt (private policy) when leaving a deep block
- **`eod-sync`** for git/gh/PR + tomorrow pointer
- Tomorrow file: **`OPERATOR_TODAY_MODE_2026-08-17.md`** (create from this if needed)

---

## Quick refs

- [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md)
- Issue [#1586](https://github.com/DataBoar/data-boar/issues/1586) · [#1601](https://github.com/DataBoar/data-boar/issues/1601) · skill **dependabot-recommendations**
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · session: **`deps`**, **`feature`**, **`today-mode`**, **`pmo-view`**, **`carryover-sweep`**

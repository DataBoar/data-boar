# Operator today mode — 2026-08-16 (two-week cycle refresh + #1602)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-16.pt_BR.md)

**Headline (close):** Two-week cycle docs + **#1602** on `main` (**#1604**). **#1586** TCP peer-pin matrix **closed** (**#1603**). Next focus: Dependabot (**#1573** / majors) → Week-2 slice (**#1601** or named M-PILOT).

**Workstation clock (this file):** `2026-08-16` (−03). Issue **#1586** closed **2026-08-17** UTC (same evening −03).

**Two-week plan:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md)

---

## Block 0 — Reality

1. **`main`:** synced through **`88249008`** (`docs(ops): two-week cycle…` **#1604**).
2. **Product / docs PRs:** **#1602** ✅ merged. No open product PR required for this day close.
3. **Open PRs (Dependabot — do not blind-merge):**
   - [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7** (Actions major)
   - [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25**
4. - [x] **`carryover-sweep` / reality refresh** · use **`block-close`** / **`eod-sync`** at boundaries.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · Prior day: [OPERATOR_TODAY_MODE_2026-08-15.md](OPERATOR_TODAY_MODE_2026-08-15.md) · Next: [OPERATOR_TODAY_MODE_2026-08-17.md](OPERATOR_TODAY_MODE_2026-08-17.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-16** / **2026-08-17**).

---

## Suggested sequencing (outcome)

### A — Cycle anchor — ✅

| Step | Item | Notes |
| ---- | ---- | ----- |
| 1 | Refresh two-week plan | EN + pt-BR (**2026-08-16 → 2026-08-29**) — **#1604** |
| 2 | Land **#1602** | ✅ merged |
| 3 | Confirm `main` green | Re-check after late merges (`gh run list --workflow ci.yml -L 3`) |

### B — Dependabot (`deps`) — still open

Triage with **`.cursor/skills/dependabot-recommendations/SKILL.md`**. Prefer **Actions** before **major** Python.

| Order | PR | Notes |
| ----- | -- | ----- |
| 1 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) | Major Actions — changelog + CI matrix |
| 2 | Majors **#1487 / #1485 / #1484** | One at a time; `check-all` + smoke |

### C — #1586 TCP pin — ✅ Done

Closed via **#1603** (Oracle). Full matrix: **#1589–#1603** (incl. SSOT **#1598** / **#1588**). No residual slices on this mother issue.

### D — Not default this day (carry to Week 2 / tomorrow)

- Full **#1601** RUM runtime
- Maestro **#32** OTel preflight unless lab focus wins

---

## Carryover — day rows

- [x] Two-week cycle docs on `main` (**#1604**)
- [x] Merge **#1602**
- [ ] Triage **≥1** Dependabot PR (prefer Actions **#1573**) — deferred to **2026-08-17**
- [x] Update **CARRYOVER** for **#1586** Done + deps refresh
- [x] No product commit without `check-all` / CI green on that PR

---

## End of day

- **`block-close`** + VeraCrypt (private policy) when leaving a deep block
- **`eod-sync`** for git/gh/PR + tomorrow pointer
- Tomorrow file: **[OPERATOR_TODAY_MODE_2026-08-17.md](OPERATOR_TODAY_MODE_2026-08-17.md)**

---

## Quick refs

- [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md)
- Issue [#1586](https://github.com/DataBoar/data-boar/issues/1586) (closed) · [#1601](https://github.com/DataBoar/data-boar/issues/1601) · skill **dependabot-recommendations**
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · session: **`deps`**, **`feature`**, **`today-mode`**, **`pmo-view`**, **`carryover-sweep`**

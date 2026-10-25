# Operator today mode — 2026-08-17 (deps + Week-2 primary)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-17.pt_BR.md)

**Headline:** After **#1586** close + cycle docs on `main` → triage **Dependabot** (Actions **#1573** first) → pick **one** Week-2 delivery (**#1601** RUM pilot **or** **#1453** CMMC sample **or** named M-PILOT blocker).

**Workstation clock (this file):** create/confirm with `date` / `Get-Date` on the workstation (−03).

**Two-week plan:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md) (cycle **2026-08-16 → 2026-08-29**)

---

## Block 0 — Reality

1. **`main`:** `git fetch` + `git pull origin main` (expect **#1586** / **#1602** / **#1604** already landed).
2. **Open product PRs:** none required; open only for the slice you start today.
3. **Open Dependabot (do not blind-merge):**
   - [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7**
   - [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25**
4. - [ ] **`carryover-sweep` / `morning-readiness`** · **`block-close`** / **`eod-sync`** at boundaries.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · Prior day: [OPERATOR_TODAY_MODE_2026-08-16.md](OPERATOR_TODAY_MODE_2026-08-16.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-17** / **2026-08-18**).

---

## Suggested sequencing

### A — Dependabot (`deps`)

| Order | PR | Notes |
| ----- | -- | ----- |
| 1 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) | Prefer first — Actions major |
| 2 | One of **#1487 / #1485 / #1484** | Skill + `check-all`; one PR only |

### B — One Week-2 primary (`feature`)

Pick **one** (operator names if unclear):

| Candidate | Issue / plan | Notes |
| --------- | ------------ | ----- |
| RUM pilot | [#1601](https://github.com/DataBoar/data-boar/issues/1601) · [PLAN_CROSS_SURFACE_OBSERVABILITY.md](../../plans/PLAN_CROSS_SURFACE_OBSERVABILITY.md) | Privacy-first; default OFF |
| CMMC sample | [#1453](https://github.com/DataBoar/data-boar/issues/1453) | Docs/config sample |
| Lab / license | [#756](https://github.com/DataBoar/data-boar/issues/756) / [#719](https://github.com/DataBoar/data-boar/issues/719) | Only if operator names as M-PILOT |

### C — Optional (not default)

- Maestro [maestro#32](https://github.com/DataBoar/maestro/issues/32) OTel preflight (sibling repo)
- [#1427](https://github.com/DataBoar/data-boar/issues/1427) Windows CI (blocks MSI/winget **#1467**)

---

## Carryover — day rows

- [ ] Triage **≥1** Dependabot PR
- [ ] Start **or** explicitly defer Week-2 primary with date
- [ ] Update **CARRYOVER** if deps / #1601 status moves
- [ ] No product commit without `check-all` / CI green

---

## End of day

- **`block-close`** / **`eod-sync`**
- Tomorrow file: **`OPERATOR_TODAY_MODE_2026-08-18.md`** (create from this if needed)

---

## Quick refs

- [CARRYOVER.md](CARRYOVER.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md) · skill **dependabot-recommendations**
- Session: **`deps`**, **`feature`**, **`today-mode`**, **`carryover-sweep`**

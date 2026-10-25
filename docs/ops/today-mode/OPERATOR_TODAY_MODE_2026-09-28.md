# Operator today mode — 2026-09-28 (re-anchor: RC + security landed, GA path)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-09-28.pt_BR.md](OPERATOR_TODAY_MODE_2026-09-28.pt_BR.md)

**Headline:** **`main`** absorbed a heavy **BFF / RC / security** day: **[#2011](https://github.com/DataBoar/data-boar/pull/2011)** (Maestro RC smoke + sentinel extras, closes data-boar side of maestro#91) and **[#2012](https://github.com/DataBoar/data-boar/pull/2012)** (**#2006** REST `pass_from_env` gate, **#2007** Microsoft token URL allowlist). **[#1992](https://github.com/DataBoar/data-boar/issues/1992)** closed **completed** (trust anchor / #1994). Maestro: **#92** closed; **#82** CREDIT_CARD → **Covered**. **Next:** close the loop on **maestro#91** (issue still open), **lab host smoke** (podman images; [#756](https://github.com/DataBoar/data-boar/issues/756)), **carrion-crow** queue (**#99** then security lot), **1.8.0 GA** thread **[#1980](https://github.com/DataBoar/data-boar/issues/1980)**.

**Workstation clock:** `2026-09-28` (Sunday) · confirm with `date` on the dev workstation.

**Two-week plan (this cycle):** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md) — **2026-09-28 → 2026-10-11**

**Token posture:** Normal execution; full **`./scripts/check-all.sh`** before any publish/merge.

---

## Block 0 — Morning reality (Tier A, ~10 min)

Run **`carryover-sweep`** or **`./scripts/operator-day-ritual.ps1 -Mode Morning`**.

1. **`git fetch`** + **`git checkout main`** + **`git pull origin main`** (tip at write: merge **#2012** → `f9d36617`)
2. **`gh pr list -R DataBoar/data-boar`** — product PRs clear; open queue is mostly **Dependabot** (**#1997–#2001**)
3. **`gh pr list -R DataBoar/maestro`** / **`carrion-crow`** — **[crow #99](https://github.com/DataBoar/carrion-crow/pull/99)** still the GA-neighbor epic gate per operator queue
4. Sync sibling clones: **`../maestro`**, **`../carrion-crow`** on `main` after pulls
5. - [ ] **Social skim** (~2 min): `docs/private/social_drafts/editorial/SOCIAL_HUB.md`

**Not default today:** blind-merge Dependabot majors; new CRM connector implementation (**#2014–#2018** are backlog filing, not sprint scope).

---

## Wins already on `main` (do not re-litigate)

| Item | State |
| ---- | ----- |
| **#2011** — RC `uv sync` extras + `missing_optional_dependency` sentinel | ✅ Merged **2026-09-28** |
| **#2012** — REST env-secret egress + Microsoft `login.microsoftonline.com` token URL | ✅ Merged **2026-09-28** |
| **#1995** — `filesystem_credit_card` sentinel + Luhn fixture | ✅ Merged (earlier) |
| **#1994** — license cross-sign / no raw key override | ✅ Merged; **#1992** closed |
| **maestro#92** — CREDIT_CARD e2e assertion | ✅ Closed (code via #1995; #82 comment) |
| **Slowdown / Ultra refill ~2026-09-09** | ✅ **Expired** — resume normal **`feature`** cadence |

---

## If you have one focused block (pick **one** primary)

| Priority | Slice | Repo | Notes |
| -------- | ----- | ---- | ----- |
| **P1** | Close **maestro#91** with evidence | maestro | Fix is on data-boar **#2011**; optional **lab host** smoke after podman image restore ([#756](https://github.com/DataBoar/data-boar/issues/756)) |
| **P2** | **carrion-crow #99** → merge | carrion-crow | Operator queue: before security lot **#94–#101** |
| **P3** | **maestro#82** gap closure | maestro + data-boar | CREDIT_CARD done; Mongo/smoke path + remaining §B rows |
| **P4** | Dependabot **one** PR | data-boar | Prefer **#1999** / **#1998** (Actions pins); skill **`deps`** |
| **Defer** | `engine/` mirror of RC `uv sync` | maestro | Explicitly deferred post-#2011 |
| **Defer** | CRM connectors **#2014–#2018** | data-boar | P2 backlog — no implementation this cycle unless operator re-points |

---

## Carryover — today rows

- [ ] **`git pull`** on **data-boar**, **maestro**, **carrion-crow** `main`
- [ ] **maestro#91:** comment + close referencing **data-boar#2011** (or run lab host smoke first if operator wants lab proof)
- [ ] **Lab host:** restore podman smoke images before RC host-smoke (`postgres`, `mariadb`, `oracle-xe`, `mssql`) — [#756](https://github.com/DataBoar/data-boar/issues/756)
- [ ] **carrion-crow:** land **#99**, then security batch per operator order
- [ ] Refresh [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) if milestone mix shifted (`uv run python scripts/issue_queue_sequencing_map.py --write`)
- [ ] **`eod-sync`** if you merged or moved issues today

---

## End of day

- **`block-close`** / **`eod-sync`** when leaving a work block
- Skim **`OPERATOR_TODAY_MODE_2026-09-29.md`** tomorrow or carry one line in [CARRYOVER.md](CARRYOVER.md)

---

## Quick refs

- [CARRYOVER.md](CARRYOVER.md) · [WORKBOARD.md](WORKBOARD.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md) · [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md)
- Session: **`today-mode`**, **`carryover-sweep`**, **`pmo-view`**, **`feature`**, **`deps`**, **`eod-sync`**

---

## PMO view (2026-09-28)

| Lane | Now | Next | Blocker |
| ---- | --- | ---- | ------- |
| **data-boar `main`** | **1.8.0-rc** working line; **#2011/#2012** merged | **1.8.0 GA** narrative **[#1980](https://github.com/DataBoar/data-boar/issues/1980)**; **#1984** Amex/Diners docs | Lab proof + Maestro e2e **#82** |
| **Maestro** | **#92** closed; **#82** partial | Close **#91**; **#87** evidence; engine mirror deferred | Lab podman images; **#99** crow gate |
| **carrion-crow** | **#99** open (GA neighbor M1) | **#94–#101** security lot after **#99** | Operator sequencing |
| **Supply chain** | 5 Dependabot PRs open | Triage **one** Actions pin PR | No blind major bumps |
| **Published** | **1.7.4.post12** / Hub | Next horizon **1.8.0** stable | GA checklist + BFF validation |

**Milestones (GitHub SoT):** refresh [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) — do not schedule **v1.8.1** work as **v1.8.0** in prose.

**Plans mirror:** [PLANS_TODO.md](../../plans/PLANS_TODO.md) active threads — RC sentinel **#1985**, CREDIT_CARD **#1984**, engineering doctrine manifestos, **S2a** transport/trust.

**Risk register (short):**

1. **E2e drift** — maestro#82 still open while product moved fast on RC/security.
2. **Lab fidelity** — smoke truth requires lab podman stack + optional Maestro harness run.
3. **PR fan-out** — Dependabot + new CRM issues **#2014–#2018** add noise; keep **one slice / one PR** discipline.

# Operator today-mode — 2026-06-27 (post-1.7.4 GA · pre-epic housekeeping)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-06-27.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-27.pt_BR.md)

**Headline:** **1.7.4 GA shipped** (2026-06-26). Today = **housekeeping / chore** on `main` before the **A.I.I.D.C.O.B.P.P. v2** epic (governance + vault + ADR — **serious slice**, not mixed with deps typo passes). **Composer-only** in Cursor until Ultra premium refill (**2026-07-09**).

**`main` anchor:** `1a8d954d` — **`ci.yml` success** on merge of **#1033** (2026-06-26). **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) (**v1.7.4**, Hub **:1.7.4** + **:latest**).

**Private pre-epic queue:** see **`docs/private/ops/`** (auditor handoff — details stay private; ask Cursor for mechanical slices when you pick a row).

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** / **`./scripts/operator-day-ritual.sh -Mode Morning`** (or `.ps1`). Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · confirm **`ci.yml`** green on latest `main`.
2. **Open PRs:** `gh pr list --state open` — Dependabot queue (**#1025**, **#1029**, **#1011**, **#1010**, **#975**, **#974**, **#915**, **#912**, …) — **`deps`** / **`houseclean`** only; **no blind-merge** (see `.cursor/skills/dependabot-recommendations/SKILL.md`).
3. **Stacked private git:** if `docs/private/` changed overnight, `./scripts/private-git-sync.sh -Push` (EOD **2026-06-26** sync already ran — commit **`689261e`** on private `main`).

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **Alvo editorial** matching **today** / **tomorrow** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Priority — pre-epic housekeeping (before A.I.I.D.C.O.B.P.P.)

**Rule:** **A.I.I.D.C.O.B.P.P. v2** (vault `project_aiidcobpp_pattern`, ADR-0062 amend, issue-bus) = **operator Gate** + **Tier 2+** — **not** today's default unless you explicitly promote it.

| Track | Intent | Notes |
| ----- | ------ | ----- |
| **Pre-epic chores** | Close stale **public** pointers + small **code** housekeeping the auditor listed | Composer + `lint-only` / `check-all`; one PR per coherent batch |
| **Optional docs** | `PLANS_TODO.md` **~L621** (M-PILOT / “next patch” still says 1.7.3→1.7.4) · **CARRYOVER** row “v1.7.4-rc on main” → mark shipped | Doc-only; pair with **#1032** spirit |
| **Dependabot** | Triage **one** PR if bandwidth (e.g. **#974** `py7zr` aligns with lab G1 narrative) | Held until bench stable if Maestro work resumes |
| **Epic (defer)** | **A.I.I.D.C.O.B.P.P. v2 FINAL** capture + ADR | After Gate: `private-stack-sync` + `new-adr.ps1` amend **ADR-0062** |

**Yesterday closed (do not reopen):** **#1024** release · **#1026** Docker daemonless · **#1031** man `data-boar` · **#1033** `PUBLISHED_SYNC` · **#406** gate close on `main`.

---

## Carryover — secondary

- [ ] **Pre-epic list (private):** pick **one** row from auditor handoff; Cursor executes diff/tests/PR body.
- [ ] **Maestro / #968 / R12.2** — post-gate backlog; not blocking 1.7.4 publish (see **#1021** / **PLANS_TODO**).
- [ ] **Premium model roster (2026-07-09):** Codex 5.3 default slot **O** in Cursor Ultra — planning only today.
- [ ] Rolling: [CARRYOVER.md](CARRYOVER.md) — refresh stale **1.7.4-rc** row when convenient.

---

## End of day (2026-06-27)

- **`eod-sync`** + **`private-stack-sync`** if private or homelab evidence changed.
- Next checklist: **`OPERATOR_TODAY_MODE_2026-06-28.md`** (create at next `eod-sync` if missing).

---

## Quick references

- Session keywords: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `carryover-sweep`, `eod-sync`, `houseclean`, `deps`, `private-stack-sync`)
- Governance (defer epic): ADR-0062 · A.I.I.D.C.O.B.P.P. v2 FINAL (operator Gate pending)
- Token-aware: `docs/plans/TOKEN_AWARE_USAGE.md`

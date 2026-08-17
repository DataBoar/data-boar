# Operator today mode — 2026-08-15 (deps triage + #1586 sequences)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-15.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-15.pt_BR.md)

**Headline:** Morning carryover refresh → **Dependabot** triage (Actions first) → continue **#1586** TCP-pin sequences. Cursor = executor; **Claude Code** = token-aware RO auditor; **Codex on the lab audit node** optional second audit when a slice is PR-ready.

**Workstation clock (this file):** `2026-08-15` (−03).

---

## Block 0 — Reality (evening refresh / next morning)

1. **`main`:** `git fetch` + `git pull origin main` (post-**#1591** Mongo pin, **#1593** urlsplit SQL test, **#1572** zizmor-action; CI on `main` may still be settling).
2. **Open PRs (product / security):**
   - [#1594](https://github.com/DataBoar/data-boar/pull/1594) — fail-closed `HostResolutionPin` conflict (**merge when CI green**; Security Agent asked re-audit).
3. **Do not reopen:** Postgres pin **#1589** · Mongo pin **#1591** · urlsplit test **#1593** (already on `main`).
4. - [ ] **`carryover-sweep` / `morning-readiness`** at start of next block · **`block-close`** / **`eod-sync`** at boundaries.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · Prior day: [OPERATOR_TODAY_MODE_2026-08-13.md](OPERATOR_TODAY_MODE_2026-08-13.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-15** / **2026-08-16**).

---

## Suggested sequencing

### A — Dependabot (`deps`) — do soon, not blind-merge

Triage with **`.cursor/skills/dependabot-recommendations/SKILL.md`** + **`SECURITY.md`**. Prefer **Actions** bumps before **major** Python majors.

| Order | PR | Notes |
| ----- | -- | ----- |
| 1 | [#1574](https://github.com/DataBoar/data-boar/pull/1574) codeql-action/init **4.37.0 → 4.37.6** | Patch Actions; MERGEABLE — low blast radius |
| 2 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **6.3.0 → 7.0.0** | Major Actions — read changelog / CI matrix before merge |
| 3 | [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25** | **Major** uv — one at a time; `check-all` + smoke; ADR-0069 / rpds caps still apply |

Optional auditor pass: Claude Code (token-aware RO) or **Codex on the lab audit node** on the Dependabot diff before merge.

### B — #1586 TCP pin sequences (after / between deps)

| Step | Item | Notes |
| ---- | ---- | ----- |
| 0 | Land **#1594** | Fail-closed pin conflict — closes Security Agent HIGH from Mongo slice |
| 1 | Redis subclass pin | Design matrix slice (after postgres + mongo) |
| 2 | MySQL / Oracle | Case-by-case; spike TLS identity |
| — | mssql | Deferred → [#1588](https://github.com/DataBoar/data-boar/issues/1588) |

**AI roles:** Cursor implements; Claude Code audits token-aware (issues/prompts only); Codex on the **lab audit node** optional second vendor when gate/security sign-off matters (ADR-0062).

### C — Not default today

- Maestro **#32** OTel preflight (carryover — only if lab focus wins over A/B)
- Research waves / inspiration issues without AIIDCOBPP + P*

---

## Carryover — day rows

- [ ] Refresh **CARRYOVER** Dependabot row (Actions PRs added)
- [ ] Merge or schedule **#1594**
- [ ] Triage **≥1** Dependabot PR (prefer **#1574**)
- [ ] If energy left: start **Redis** #1586 slice **or** park with explicit next date
- [ ] No product commit without `check-all` / CI green on that PR

---

## End of day

- **`block-close`** + VeraCrypt (private policy) when leaving a deep block
- **`eod-sync`** for git/gh/PR + tomorrow pointer
- Tomorrow file: **`OPERATOR_TODAY_MODE_2026-08-16.md`** (create from this if needed)

---

## Quick refs

- Issue [#1586](https://github.com/DataBoar/data-boar/issues/1586) · skill **dependabot-recommendations**
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · ADR-0062 (executor × auditor)
- Session: **`deps`**, **`feature`**, **`today-mode`**, **`carryover-sweep`**

# Operator today mode — 2026-08-28 (late-day capture: #552/#553 + #1061)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-28.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-28.pt_BR.md)

**Headline:** Written at **end of Friday** (operator remembered then). Land **#552** (PR **#1816**) when CI is green; finish **#553** Part A (ODS + path allowlist) then Part B; **#1061** already closed as not-planned → [tidy-tortoise#14](https://github.com/DataBoar/tidy-tortoise/issues/14). Two-week cycle **2026-08-16 → 2026-08-29** ends **tomorrow**.

**Workstation clock (this file):** `2026-08-28` (Friday, −03) from `date` on the Linux primary.

**Two-week plan:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](../../plans/PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md)

---

## Block 0 — Reality (written late)

This file is a **same-day recap + carryover**, not a morning plan. Still run **`eod-sync`** / **`block-close`** before leaving.

1. **`main`:** `git fetch` + `git pull origin main` when switching off feature branches (`origin/main` tip at write: **#1801** SMB SSRF).
2. **Open product PR:** [#1816](https://github.com/DataBoar/data-boar/pull/1816) — findings sink **#552** + ADR batch + SSRF URL parse fix (`7d6eb387`). Merge when checks green (`pr-merge-when-green`).
3. **Local WIP (do not mix with #1816):** branch **`feat/report-multiformat-553`** — ODS Part A uncommitted; Bugbot HIGH allowlist `.ods` already patched in the working tree.
4. **Dependabot (do not blind-merge):** new queue **2026-08-28** — **#1802** setup-uv **10**, **#1803** claude-code-action, **#1805** CodeQL analyze, **#1804** distroless pin, **#1807** uv-minor-patch group, **#1808** sentence-transformers **6**, **#1810** types-pyyaml. Prefer Actions pin **#1802** / **#1805** after **`deps`** skill; **#1808** is a major.
5. - [ ] **`block-close`** / **`eod-sync`** at the boundary (this *is* the end of the day).

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · Last dated file before this: [OPERATOR_TODAY_MODE_2026-08-17.md](OPERATOR_TODAY_MODE_2026-08-17.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` — **no** inventory **Alvo editorial** matching **2026-08-28** / **2026-08-29** at write time (process: [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md)).

---

## Suggested sequencing (tonight / Saturday)

### A — Close #552 (`feature`)

| Step | Notes |
| ---- | ----- |
| CI on **#1816** | Full `check-all` already run locally before the SSRF follow-up push |
| Merge | `Closes #552` (and ADR issues named in the PR body) — do **not** `gh issue close` by hand |

### B — Finish #553 (`feature`)

| Slice | Notes |
| ----- | ----- |
| Part A | ODS spreadsheet + **`_REPORT_FILENAME_PATTERN`** `.xlsx`\|`.ods` + heatmap stem; commit on **`feat/report-multiformat-553`** after `check-all` |
| Part B | pandoc GRC DOCX/ODT/PDF — fail-soft; PDF Enterprise + lualatex; **not** stacked on #1816 |

### C — Docs drift from #1061

- [ ] `PLANS_TODO.md` still lists **#1061** as remaining v1.8.0 survey — one **`docs`** commit (not mixed with ODS). Pointer: tortoise **#14**.

### D — Optional (not default tonight)

- Dependabot **one** PR (`deps`) — queue reopened
- Two-week wrap **2026-08-29**: pick remaining Week-2 item or explicit defer with date ([#1601](https://github.com/DataBoar/data-boar/issues/1601) / [#1453](https://github.com/DataBoar/data-boar/issues/1453))

---

## Carryover — day rows

- [ ] Merge **#1816** when green → **#552** auto-close
- [ ] Commit + PR **#553** Part A (ODS + path allowlist); Part B next
- [ ] **`docs`:** drop **#1061** from v1.8.0 remaining survey in `PLANS_TODO.md` (`plans-stats.py --write` if dashboard rows change)
- [ ] Re-open Dependabot carryover row until the **2026-08-28** PRs are triaged
- [ ] Create or skim **`OPERATOR_TODAY_MODE_2026-08-29.md`** (last day of the two-week cycle)

---

## End of day

- **`block-close`** + VeraCrypt (private homelab policy) · **`eod-sync`** for git/gh
- Tomorrow: **`OPERATOR_TODAY_MODE_2026-08-29.md`** (create from this if needed)

---

## Quick refs

- [CARRYOVER.md](CARRYOVER.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md) · [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)
- Session: **`feature`**, **`deps`**, **`today-mode`**, **`eod-sync`**, **`block-close`**, **`pmo-view`**

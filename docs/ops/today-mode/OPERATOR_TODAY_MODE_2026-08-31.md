# Operator today mode — 2026-08-31 (slowdown — Tier A + merge docs)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-31.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-31.pt_BR.md)

**Headline:** **Sunday** in **slowdown** mode until **2026-09-09** (Cursor Ultra refill). Morning = **Tier A** only. **`main`** already has **#1832** / **#1838**; active queue: [PR #1841](https://github.com/DataBoar/data-boar/pull/1841) (**#1840** — refresh `ISSUE_QUEUE_SEQUENCING_MAP` + generator script).

**Workstation clock:** `2026-08-31` (Sunday) · confirm with `date` on the dev workstation.

**Token posture:** No agent marathon; `lint-only` / `quick-test` for docs slices; full **`check-all`** only before merge if you touch code.

---

## Block 0 — Morning reality (Tier A, ~10 min)

Run **`carryover-sweep`** or **`./scripts/operator-day-ritual.ps1 -Mode Morning`** (Linux: `git` + `gh` direct is fine).

1. **`git fetch`** + **`git checkout main`** + **`git pull origin main`**
2. **`gh pr list`** — expect **[#1841](https://github.com/DataBoar/data-boar/pull/1841)** open (`chore/1840-issue-queue-map-refresh`)
3. **`gh pr checks 1841`** / **`gh run list --branch chore/1840-issue-queue-map-refresh --limit 3`** — merge when green (`Closes #1840`)
4. **Ruleset `main-gate-pii` (operator-only, when ready):** add required check **`SSHSIG attestation when gated`** — [PLAN_OPERATOR_GATED_PR_GUARD.md](../../plans/PLAN_OPERATOR_GATED_PR_GUARD.md) phase 4
5. - [ ] **Social skim** (~2 min): `docs/private/social_drafts/editorial/SOCIAL_HUB.md` — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md)

**Not today:** Dependabot batch, completão, new gate hardening, large **`feature`** PRs — unless **U0** on `main`.

---

## Wins already on `main` (do not re-litigate)

| Item | State |
| ---- | ----- |
| **#1709 / PR #1832** — operator-gated PR guard | ✅ Merged **2026-08-30** |
| **#1835 / PR #1838** — BACKLOG_GTD | ✅ Merged |
| **#552 / PR #1816** — findings sink | ✅ Merged; **#552** **CLOSED** |
| **Open-issue mirror** | 🔄 **#1840** / PR **#1841** (260 open; v1.8.0–v1.8.4) |

---

## If you have one calm hour (optional — pick **one**)

| Priority | Slice | Notes |
| -------- | ----- | ----- |
| **O1** | Merge **#1841** when CI green | Docs + `scripts/issue_queue_sequencing_map.py`; `Closes #1840` |
| **O2** | Ruleset **SSHSIG attestation when gated** | GitHub UI only |
| **O3** | Milestone hygiene **#696**, **#697**, **#1538** | 3 open without milestone — [#1522](https://github.com/DataBoar/data-boar/issues/1522) protocol |
| **Defer** | **`feat/report-multiformat-553`** Part A | After refill or explicit energy for `check-all` |
| **Defer** | Heptapod / Codeberg give-back | [data-boar-shared#63](https://github.com/DataBoar/data-boar-shared/issues/63) — no contact until **≥ 2026-09-09** |

---

## Carryover — today rows

- [ ] **`git pull` on `main`** after **#1841** merges
- [ ] Skim refreshed [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) (post-merge)
- [ ] Ruleset **`main-gate-pii`** SSHSIG check (when ready)
- [ ] Optional: assign **`#696` / `#697` / `#1538`** to v1.8.x milestone
- [ ] **`block-close`** if low-energy day — skip heavy **`eod-sync`**

---

## End of day

- **`eod-sync`** only if you merged PRs or moved backlog today
- Skim **`OPERATOR_TODAY_MODE_2026-09-01.md`** tomorrow (or carry one line in [CARRYOVER.md](CARRYOVER.md))
- Product **`feature`** / **`deps`** default resumes after **2026-09-09** unless **U0**

---

## Quick refs

- [CARRYOVER.md](CARRYOVER.md) · [WORKBOARD.md](WORKBOARD.md) · [PLANS_TODO.md](../../plans/PLANS_TODO.md) · [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md)
- Regenerate map: `uv run python scripts/issue_queue_sequencing_map.py --write`

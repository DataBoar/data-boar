# Operator today mode — 2026-08-07 (post–Actions outage + HITL merges)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-07.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-07.pt_BR.md)

**Headline:** GitHub Actions incident resolved (~2026-08-07 02:04 UTC). Landed org-path + Windows quickstart + product-facts; site FAQ CI green — HITL merges + clear real reds (#1476 was re-greened; site #55 needs review).

---

## Block 0 — Morning reality check (10–15 min)

- Clock (workstation): **2026-08-07** (−03).
- Open PRs (refresh): **data-boar** `#1476` (CLEAN) · **data-boar-site** `#55` (checks green; `BLOCKED` = review/protection).
- Latest `main` CI: **success** (post-rerun after outage).

Then:

1. **`git checkout main && git pull origin main`** on data-boar (and site if working there).
2. Working tree: discard leftover feature branches only after confirming merged (`docs/quickstart-windows-1128`, `chore/canonicalize-org-path`, etc.).
3. Stacked private: **`private-stack-sync`** if private notes changed during the outage day.
4. - [ ] **Block close (lab / VC)** later via chat token **`block-close`**.

**Canonical rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for Alvo **2026-08-07** / **2026-08-08**.

---

## Carryover — today (session + rolling)

### HITL / merge (this window)

- [ ] **data-boar-site [#55](https://github.com/DataBoar/data-boar-site/pull/55)** — FAQ SEO; CI green after guardrails fix (`canonical` ≠ loaded asset). **Merge when ready** (review/protection).
- [ ] **data-boar [#1476](https://github.com/DataBoar/data-boar/pull/1476)** — ADR-0085 install ladder; checks **CLEAN**. Audit + merge HITL (or close if superseded).

### Deferred from org-path / packaging (not forgotten)

- [ ] **PORTFOLIO** — `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` still has **3×** `FabioLeitao/data-boar` (left out of #1473: gatekeeper / third-party names). Micro-PR after allowlist vs redact decision.
- [ ] **ADR Status-history** — no blind sed on `docs/adr/ADR-*.md` (ADR-0045); section-aware pass later if still needed.
- [ ] **[#1467](https://github.com/DataBoar/data-boar/issues/1467)** — Windows MSI + winget embed `cp314`/`cp314t` (ADR-0084); pointed from Windows quickstart.
- [ ] **[#1127](https://github.com/DataBoar/data-boar/issues/1127)** — `--install-shortcut` (docs mention only; feature still open).

### Rolling CARRYOVER (pick ≤1 deep item)

- [ ] One active row from [CARRYOVER.md](CARRYOVER.md) (e.g. Maestro private migration, Dependabot triage, LAB-OP #756) — do not expand the immortal queue.

---

## Done recently (do not reopen)

- **#1473** org-path canonicalize — merged (incl. PLANS_HUB regenerate fix).
- **#1474** Windows non-techie quickstart (no Docker) — merged.
- **#1475** canonical product facts (#1470) — merged.
- Actions outage revalidation — #1474/#1475 green; real reds classified (#1476 lint/fixture at the time; site #55 allowlist false positive on `canonical`).

---

## End of day

- **`block-close`** / **`eod-sync`** as needed.
- Prepare **`OPERATOR_TODAY_MODE_2026-08-08.md`** if work continues tomorrow.

---

## Quick references

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.md`

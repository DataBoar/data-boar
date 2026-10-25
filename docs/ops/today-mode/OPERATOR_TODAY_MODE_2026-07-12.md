# Operator today-mode - 2026-07-12 (carryover-sweep + deps queue)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-07-12.pt_BR.md](OPERATOR_TODAY_MODE_2026-07-12.pt_BR.md)

**Headline:** `carryover-sweep` executed; PR **#1209** is merged on `main`; active queue is now Dependabot triage plus rolling carryover commitments.

---

## Block 0 - Morning reality check (10-15 min)

`carryover-sweep` status (executed):

- Branch state: `fix/prefilter-recall-parity-1198...origin/fix/prefilter-recall-parity-1198`
- Open PRs: **#1178**, **#1107**, **#975**
- Latest `main` CI: newest run in progress after merge of **#1209**
- Today-mode file for today: now present

Then:

1. **Sync to canonical branch:** `git checkout main && git pull origin main`.
2. **Branch hygiene:** if no extra work remains on `fix/prefilter-recall-parity-1198`, close local branch after sync.
3. **Deps triage (thin slices):** decide order and strategy for **#1178**, **#1107**, **#975** (`deps` mode; no blind merge).
4. **Rolling carryover alignment:** review [CARRYOVER.md](CARRYOVER.md) and pick one cross-day item to move forward today.
5. - [ ] **Block close (lab / VC):** when pausing later, run `block-close` and follow private VeraCrypt policy in `docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md)
**Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` for rows due today/tomorrow.

---

## Carryover - today

- [ ] **Dependabot queue:** triage/open-plan for **#1178**, **#1107**, **#975**.
- [ ] **Long-running carryover:** keep momentum on the active item from [CARRYOVER.md](CARRYOVER.md) (Maestro/private stack or security queue).
- [ ] **Private sync boundary:** if private notes changed today, schedule `private-stack-sync` before final close.

---

## End of day

- Use `block-close` for work-block/lab boundary and VeraCrypt hygiene.
- Use `eod-sync` (or `.\scripts\operator-day-ritual.ps1 -Mode Eod`) for git/gh refresh and tomorrow pointer.
- Prepare or skim `OPERATOR_TODAY_MODE_2026-07-13.md`.

---

## Quick references

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.md`

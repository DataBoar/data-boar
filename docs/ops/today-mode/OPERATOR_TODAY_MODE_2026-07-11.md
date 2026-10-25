# Operator today-mode - 2026-07-11 (docs split gate + RBAC track hygiene)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-07-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-07-11.pt_BR.md)

**Headline:** docs-only split for two-tier gate is ready in **#1185**; RBAC remains canonical on **#1143**; **#1124** stays blocked after merge-main-in until ADR inventory hash follow-up.

---

## Block 0 - Morning reality check (10-15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. `git fetch` + `git status -sb` + ensure branch intent is explicit before edits.
2. Review PR **#1185** checks and prepare operator gate decision path (no auto-merge).
3. Keep **#1143** untouched (canonical RBAC draft track) while docs split lands.
4. Confirm **#1124** remains parked (no force-push path; merge-main-in already applied).
5. - [ ] **Block close (lab / VC):** when pausing later, run **`block-close`** and follow VeraCrypt private policy in `docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md)
**Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` for entries due today/tomorrow.

---

## Carryover - today

- [ ] **PR #1185** (`[P3][docs] docs(cursor): two-tier check-all gate`) - await operator gate and merge decision.
- [ ] **PR #1156** already closed as superseded - keep audit trail linked to #1185 and #1143.
- [ ] **PR #1143** remains canonical RBAC track (draft) - do not mix with docs-only slices.
- [ ] **PR #1124** remains blocked by CI (`tests/test_scripts.py::test_inv_adr_inventory_hash_matches_data_lines`) after merge-main-in; no tripwire signature request in current state.

---

## End of day

- Use **`block-close`** for work-block/lab boundary and VeraCrypt hygiene.
- Use **`eod-sync`** (or `.\scripts\operator-day-ritual.ps1 -Mode Eod`) for git/gh refresh and tomorrow pointer.
- Prepare or skim **`OPERATOR_TODAY_MODE_2026-07-12.md`**.

---

## Quick references

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.md`

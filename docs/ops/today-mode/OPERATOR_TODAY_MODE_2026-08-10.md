# Operator today mode — 2026-08-10 (label hygiene + post-Claude-pause sequencing)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-10.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-10.pt_BR.md)

**Headline:** ~38 new org issues (mostly R&D in `data-boar-shared`); P1 **#1515** already closed; Claude paused (~96% weekly → refill ~17h); adversarial lab in parallel; **title↔label hygiene** + sequencing below **without derailing** carryover / deps / bestiary.

---

## Block 0 — Reality (now / afternoon)

1. **`main`:** sync before code edits (`git fetch` / `git pull origin main`).
2. **In-flight (do not abandon):**
   - Bestiary / Maestro / private stack — [CARRYOVER.md](CARRYOVER.md)
   - Open Dependabot on core (#1492, #1487, #1485, #1484…) — `deps` triage, no blind merge
   - Adversarial lab (Strix + Caido + qwen / `--demo` 1.7.4-post12) — promote to issue/lesson only when stable
3. **Stripe MCP:** plugin installed; desktop OAuth still needed for live tools.
4. - [ ] **`block-close`** when pausing lab/VC; **`eod-sync`** for calendar EOD.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (today/tomorrow targets).

---

## Hygiene done (labels ↔ titles) — 2026-08-10

| Repo | Action |
| ---- | ------ |
| `data-boar` | #1517/#1526 → `P3`+docs; #1518/#1520/#1521 → `P2`+`no-code-yet`; #1527 → `P3`; #1525 → `no-code-yet` |
| `data-boar-shared` | #34–51: `P2`/`P3` + `doutrina`/`governanca`/`documentation` per title |
| `data-boar-sdk` | #7–9 → `P2` (created `P2`/`P3` labels on repo) |
| `sage-remora` | #20 → `P3` + **title clarified** (conclusion age ≠ Remora mission) + comment |
| `tidy-tortoise` / `design-system` / `homing-robin` | #13–14 / #9 / #27 → `P2` |
| `data-boar-site` | #67 already `P3` (+ documentation when accepted) |

---

## Suggested sequencing (after refill / rest of day)

Stay in-band; finish current “other fronts” slices before new R&D.

### A — Finish in-flight first

1. One **carryover** slice (bestiary PR/repo **or** Maestro private **or** private-stack-sync if dirty).
2. Adversarial lab: one evidence paragraph → shared **#46** *or* public lesson — **only** if the run stabilizes.
3. Optional thin `deps`: one Dependabot PR if green + triage skill.

### B — Thin core ship (Claude-light / Cursor)

| Order | Issue | Why |
| ----- | ----- | --- |
| B1 | [#1517](https://github.com/DataBoar/data-boar/issues/1517) UID 65532 | Obvious doc drift; tiny PR |
| B2 | [#1526](https://github.com/DataBoar/data-boar/issues/1526) methodology cross-links | HITL already; closes #1525 docs slice |
| B3 | [#1524](https://github.com/DataBoar/data-boar/issues/1524) Mermaid map | Only if PMO visual is blocking |

### C — One doctrine slice (not all 18)

| Order | Issue | Why |
| ----- | ----- | --- |
| C1 | shared [#37](https://github.com/DataBoar/data-boar-shared/issues/37) → [#50](https://github.com/DataBoar/data-boar-shared/issues/50) | Negative capability → tests |
| C2 | sdk [#7](https://github.com/DataBoar/data-boar-sdk/issues/7) + Remora↔Ferret handoff | Envelope; orthogonal missions |
| C3 | tortoise [#13](https://github.com/DataBoar/tidy-tortoise/issues/13) | Destructive preview |

### D — Explicitly **not** today

- core #1518 / #1520 / #1521 (research)
- remora #20 full body (title hygiene already done)
- shared #34–36, #39–42, #45, #48, #51 — labeled R&D backlog, no commitment

---

## Carryover — day rows

- [x] Label hygiene (above) — this Cursor session
- [x] Remora #20 title/comment
- [ ] Pick **one** from A + at most **one** from B or C after ~17h
- [ ] No new “inspiration” issues without AIIDCOBPP trailing + P* label

---

## End of day

- `block-close` / `eod-sync` per boundary
- Draft `OPERATOR_TODAY_MODE_2026-08-11.md` only if A–C sequencing changes

---

## Quick refs

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.md`

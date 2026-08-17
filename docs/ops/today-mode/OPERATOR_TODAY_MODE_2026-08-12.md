# Operator today mode — 2026-08-12 (OTel product ship + Maestro #8 spinout close)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-12.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-12.pt_BR.md)

**Headline (EOD):** Product OTel gaps **#1529 / #1535 / #1540** closed on data-boar; **Maestro spinout companion** [PR #1551](https://github.com/DataBoar/data-boar/pull/1551) merged (`69c8ee0d`) — `scripts/maestro/` purged; [DataBoar/maestro#8](https://github.com/DataBoar/maestro/issues/8) **CLOSED**; [#32](https://github.com/DataBoar/maestro/issues/32) unblocked for OTel preflight **code**. Operator still owns **ADR-0001 Proposed → Accepted**.

---

## Block 0 — Reality (EOD)

1. **`main`:** at merge of #1551 — pull before next edits (`git pull origin main`).
2. **Closed today (do not reopen):**
   - [#1529](https://github.com/DataBoar/data-boar/issues/1529) LoggerProvider → PR **#1544**
   - [#1535](https://github.com/DataBoar/data-boar/issues/1535) CLI oneshot OTel → PR **#1547**
   - [#1540](https://github.com/DataBoar/data-boar/issues/1540) Maestro OTel preflight **plan** → PR **#1548** (implementation = maestro#32)
   - [#1541](https://github.com/DataBoar/data-boar/issues/1541) native packages plan links → closed
   - [#1542](https://github.com/DataBoar/data-boar/issues/1542) lab observability plan Status → PR **#1545**
   - Dependabot **#1492** virtualenv → merged earlier
   - **Maestro** [#8](https://github.com/DataBoar/maestro/issues/8) incomplete spinout → companion **data-boar#1551** + parity **maestro#33/#34**
3. **Still open / next:** see carryover + sequencing below.
4. - [x] **`eod-sync`** this boundary · **`block-close`** if pausing lab/VC after.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (today/tomorrow targets).

---

## Mid-flight inventory (after today's ships)

| Band | Item | State | Next thin slice |
| ---- | ---- | ----- | --------------- |
| **Maestro OTel** | [maestro#32](https://github.com/DataBoar/maestro/issues/32) preflight code | OPEN · unblocked | Implement in DataBoar/maestro `core/`/`engine/` (not data-boar) |
| **ADR human gate** | Maestro ADR-0001 | Proposed | Operator: **Accepted** when ready |
| **Docs drift** | [#1538](https://github.com/DataBoar/data-boar/issues/1538) product tiers / open-core | OPEN · `no-code-yet` | Thin docs when band allows |
| **Packaging P1** | [#1427](https://github.com/DataBoar/data-boar/issues/1427) Windows CI zero jobs | OPEN · P1 | Blocks MSI/winget with [#1467](https://github.com/DataBoar/data-boar/issues/1467) |
| **Partial product** | [#828](https://github.com/DataBoar/data-boar/issues/828) scan_failures Pro residual | Partial on `main` | Fixtures / plan close when sequenced |
| **Lab hygiene** | [#756](https://github.com/DataBoar/data-boar/issues/756) disk ~90% + `bw` Ansible | Pending | SSH free-space before completão on that host |
| **deps dangling** | PRs **#1487** reportlab · **#1485** webauthn · **#1484** pyarrow | OPEN | Triage skill — **no blind merge** |
| **Bestiary** | #994 sidequest (7 repos left) | In progress | One PR/repo when focus returns |
| **Research park** | #1518 / #1520 / #1521 | `no-code-yet` | **Not** default tomorrow unless reprioritized |
| **Lab deploy** | Hosts still on pre-#1551 trees | Ops | Pull data-boar + set `MAESTRO_ROOT` / sibling `../maestro` |

---

## Suggested sequencing (tomorrow / next block)

### A — Maestro follow-through

1. Operator: **ADR-0001 → Accepted** (if decision is locked).
2. [maestro#32](https://github.com/DataBoar/maestro/issues/32) OTel preflight implementation (thin PR in maestro repo).
3. Lab hosts: pull `main` + ensure Maestro clone path for wrappers.

### B — Packaging / deps (when not on Maestro)

1. [#1427](https://github.com/DataBoar/data-boar/issues/1427) Windows CI job — or one Dependabot if skill says go.
2. Optional thin: [#1538](https://github.com/DataBoar/data-boar/issues/1538) docs drift.

### C — Explicitly **not** default

- Research waves #1518 / #1520 / #1521
- Full bestiary burn-down (unless one named repo)
- Reintroducing `data-boar/scripts/maestro/` (forbidden — closed #8)

---

## Carryover — day rows

- [x] Sync `main` / land observability docs (#1542 / #1545)
- [x] Ship OTel product slices (#1529 / #1535 / #1540 plan)
- [x] Maestro companion purge #1551 + close maestro#8 + ping #32
- [x] Refresh [CARRYOVER.md](CARRYOVER.md) (this EOD)
- [ ] Operator: ADR-0001 Accepted
- [ ] At most **one** of: maestro#32 code · deps triage · #1427
- [ ] No new inspiration issues without AIIDCOBPP trailing + P* label

---

## End of day

- `eod-sync` / `block-close` as needed
- Draft `OPERATOR_TODAY_MODE_2026-08-13.md` if A sequencing is the next day focus

---

## Quick refs

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · `scripts/Resolve-MaestroRoot.ps1`
- `.cursor/rules/session-mode-keywords.mdc` (`pmo-view`, `today-mode`, `eod-sync`)
- `docs/ops/COMMIT_AND_PR.md`
- [DataBoar/maestro](https://github.com/DataBoar/maestro)

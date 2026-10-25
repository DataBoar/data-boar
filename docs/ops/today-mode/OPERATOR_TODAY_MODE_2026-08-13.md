# Operator today mode — 2026-08-13 (Maestro #32 + packaging/deps)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-08-13.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-13.pt_BR.md)

**Headline:** Yesterday closed Maestro spinout **#8** + product OTel. Default focus: **maestro#32** preflight code **or** one Dependabot / **#1427** Windows CI — not research waves.

---

## Block 0 — Reality (morning)

1. **`main`:** `git pull origin main` (post-#1551).
2. **Do not reopen:** data-boar OTel **#1529/#1535/#1540** · maestro **#8** · packaging docs **#1541/#1542**.
3. **Human gate:** Maestro **ADR-0001** still Proposed until you Accept.
4. - [ ] **`carryover-sweep` / `morning-readiness`** · **`block-close`** / **`eod-sync`** at boundaries.

**Live queue:** [CARRYOVER.md](CARRYOVER.md) · Yesterday: [OPERATOR_TODAY_MODE_2026-08-12.md](OPERATOR_TODAY_MODE_2026-08-12.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (today/tomorrow Alvo).

---

## Suggested sequencing

### A — Maestro (preferred if lab focus)

1. Operator: ADR-0001 → Accepted (if locked).
2. [maestro#32](https://github.com/DataBoar/maestro/issues/32) thin implementation PR.
3. Lab: ensure `MAESTRO_ROOT` / sibling clone after data-boar pull.

### B — data-boar packaging / deps

1. One of: Dependabot **#1487 / #1485 / #1484** (skill triage) · [#1427](https://github.com/DataBoar/data-boar/issues/1427).
2. Optional thin: [#1538](https://github.com/DataBoar/data-boar/issues/1538).

### C — Not default

- #1518 / #1520 / #1521 research
- Reintroducing `scripts/maestro/` under data-boar

---

## Carryover — day rows

- [ ] Pick **one** from A or B
- [ ] Refresh CARRYOVER if a row closes
- [ ] No inspiration issues without AIIDCOBPP + P*

---

## Quick refs

- `scripts/Resolve-MaestroRoot.ps1` · [DataBoar/maestro](https://github.com/DataBoar/maestro)
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`

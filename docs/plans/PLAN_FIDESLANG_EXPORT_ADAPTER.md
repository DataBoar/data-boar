# Plan: Fideslang export adapter (optional output interop)

<!-- plans-hub-summary: Hybrid slice 3 (#1071): optional lossy Fideslang data_category on export only; no runtime dep; closes SWOT catalog-tagging W-novo-1 when customer demands. -->
<!-- plans-hub-related: PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md, PLAN_DATA_USE_AXIS.md, PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md -->

**Status:** Pending
**Date:** 2026-06-30
**Authors:** Fabio Leitao
**Priority:** H3 · **customer-pull** (slice **3 of 3** — hybrid #1071)
**Tags:** interop, fideslang, export, catalog-tagging, taxonomy, IAB
**GitHub evaluation:** [#1071](https://github.com/FabioLeitao/data-boar/issues/1071) (closed — hybrid approved)
**GitHub implementation:** [#1076](https://github.com/FabioLeitao/data-boar/issues/1076)
**SWOT:** closes **W-novo-1** (catalog-tagging output) when shipped
**Depends on:** Internal taxonomy from [PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md](PLAN_NORM_TAG_HIERARCHY_AND_DATA_SUBJECT.md) (slice 1 minimum); [PLAN_DATA_USE_AXIS.md](PLAN_DATA_USE_AXIS.md) optional for richer mapping

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Motivation

**Evaluation [#1071](https://github.com/FabioLeitao/data-boar/issues/1071):** **Direction A** alone is **lossy** for BR tags (CPF → generic `user.government_id`). **Hybrid:** keep **full internal model** (Direction B) and add **border adapter** (Direction A) — optional `data_category` (and related fields) in **export JSON/CSV only**, mapped from internal `norm_tag` / hierarchy.

**Credibility:** Fideslang (Ethyca → **IAB Tech Lab**) is an industry taxonomy reference — emitting compatible fields helps customers with Fides-class governance stacks **without** adopting the ethyca-fides **platform**.

---

## Design principles

1. **Export-only** — no change to core detection or SQLite required fields; adapter runs at export/report boundary.
2. **Default off** — `export.fideslang.enabled: false` or CLI flag `--fideslang-export` (exact UX TBD).
3. **Zero new PyPI deps** — mapping table in YAML/JSON in repo; **no** `fideslang` or `ethyca-fides` in `pyproject.toml`.
4. **Documented lossy mapping** — export manifest notes which BR tags collapse to generic Fideslang ids.
5. **Golden-standard + sauce** — internal tags remain authoritative; Fideslang fields are **secondary view**.

---

## Mapping table (illustrative — not normative)

| Internal (leaf) | Fideslang `data_category` (export) | Lossy? |
| --------------- | ---------------------------------- | ------ |
| `LGPD_CPF` | `user.government_id` | Yes |
| `LGPD_CNPJ` | `user.government_id` | Yes |
| `phone` | `user.contact.phone_number` | Partial |
| PEP (risk flag) | _(document as extension or custom; no false claim of native Fideslang PEP)_ | — |

Full table lives in config `export/fideslang_mapping.yaml` (path TBD) with version pin to **documented** Fideslang release operator targets.

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Plan + impl issue (#1071 slice 3) | ✅ Done |
| 1 | Mapping config + unit tests (internal tag → export field) | ⬜ Pending |
| 2 | CLI/report/JSON export hook; optional `data_category` column | ⬜ Pending |
| 3 | USAGE “interop” section + lossy-mapping appendix; pt-BR sync | ⬜ Pending |
| 4 | Customer-pull gate: ship when catalog/RoPA integration request exists | ⬜ Pending |

---

## Non-goals

- Importing Fideslang YAML as scan input (inbound).
- Running ethyca-fides DSR engine or Postgres catalog store.
- Claiming full Fideslang certification or IAB endorsement.

---

## Acceptance

- [ ] Adapter off → exports unchanged
- [ ] Adapter on → sample export includes `data_category` per mapping; lossy rows logged in export metadata
- [ ] No new dependencies in `pyproject.toml` / `uv.lock`
- [ ] SWOT **W-novo-1** marked addressed in plan close note when merged

---

## Audit trail

- **2026-06-30:** #1071 hybrid approved; slice 3 plan opened (customer-pull).

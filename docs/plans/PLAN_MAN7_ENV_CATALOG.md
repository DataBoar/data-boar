# Plan: `data_boar(7)` environment catalog and regression guard

**Status:** In progress (documentation, guard and packaging; no runtime behaviour change)
**Date:** 2026-11-11
**Authors:** Fabio Leitao
**Priority:** H1 (proposed, to be confirmed by the operator)
**GitHub:** [#1990](https://github.com/DataBoar/data-boar/issues/1990) · milestone v1.8.1

<!-- plans-hub-summary: New data_boar(7) man page cataloguing the environment variables the product reads (operator-facing and internal "do not set"), a static-analysis guard that fails when production code reads a variable that is neither documented nor excluded with a reason, and packaging of the page in the wheel, nfpm and Void outputs. -->
<!-- plans-hub-related: PLAN_NATIVE_PACKAGES.md, PLAN_PACKAGING_EXTRAS.md -->

## Context

Production code reads 56 environment variables (AST inventory of 2026-09-26, #1990). The ENVIRONMENT
section of `docs/data_boar.1` covers only a few, and the same defect (a variable or config key
missing from a man page) was fixed repeatedly (#440-#456). Names chosen by `*_from_env`
configuration keys make a fixed list impossible to keep complete by hand.

## Decisions (operator, 2026-11-12)

- Licensing variables (bucket C) and issuer variables (bucket D) are **not** documented in the page.
  They sit in an exclusion list with reasons `licensing-pending` and `vendor-issuer`.
- `DATA_BOAR_GRC_JSON` is an exclusion with reason `lab`.
- Document bucket A (operator-facing) and bucket B (internal, "do not set"). The ENVIRONMENT
  section of `data_boar(1)` is **not** reduced to pointers in this plan.

## Scope (one PR)

1. `docs/data_boar.7` from the 2026-09-26 draft, every `VERIFY` mark closed against the code.
2. Cross-references in `data_boar(1)` and `data_boar(5)` (SEE ALSO, "two man pages", installation).
3. Guard: `tests/test_man7_env_catalog.py` + `tests/man7_env_exclusions.txt` (reason mandatory);
   `tests/test_operator_help_sync.py` and `tests/test_native_package_manpages.py` extended.
4. Packaging: `man7/data-boar.7` plus aliases `data_boar.7` and `lgpd_crawler.7` in the wheel, nfpm
   and Void outputs (sources edited, generated files regenerated).

## To-dos

| # | To-do | Status |
| - | ----- | ------ |
| 1 | PLAN and hub entry | ✅ Done |
| 2 | `data_boar.7` with VERIFY marks closed against code | ⬜ Pending |
| 3 | Guard (AST inventory, exclusions with reason) and sync tests | ⬜ Pending |
| 4 | Packaging in wheel, nfpm and Void | ⬜ Pending |

## Risks

- #2189 (apk/musl, rc=127) may disturb the apk install smoke; reported, not hidden.
- Moving the ENVIRONMENT content out of `data_boar(1)` is deliberately deferred until the guard has
  been green for a while.

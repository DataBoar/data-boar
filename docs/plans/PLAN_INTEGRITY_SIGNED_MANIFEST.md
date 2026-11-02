# Plan: Release-signed integrity manifest (#2168)

**Status:** In progress — runtime trust root landed in this slice; operator TTY signing remains a release step.
**Date:** 2026-11-02
**Authors:** Fabio Leitao
**Priority:** P1 (integrity trust root)
**GitHub:** [#2168](https://github.com/DataBoar/data-boar/issues/2168)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) · [INTEGRITY_CHECK_ALPHA_LOGIC.md](../ops/INTEGRITY_CHECK_ALPHA_LOGIC.md)

<!-- plans-hub-summary: Runtime integrity trust root is a release-signed CRITICAL_MODULES manifest verified with the packaged license Ed25519 public key; SQLite and --reconcile are forensic only (#2168). -->
<!-- plans-hub-related: PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md, PLAN_INTEGRITY_HARDENING.md -->

## Problem

Local SQLite hashes, operator reconcile, and installed wheel `RECORD` cannot prove release origin. `validated` must come from a signed allowlist.

## This slice

| # | Deliverable | Status |
| - | ----------- | ------ |
| 1 | `core/integrity_signed_manifest.py` + evaluate fail-closed | ✅ #2168 |
| 2 | Anchor becomes forensic; reconcile re-evaluates only | ✅ #2168 |
| 3 | Tests invert RECORD/reconcile-as-root; adversarial signed cases | ✅ #2168 |
| 4 | ADR 0093 + INTEGRITY_CHECK_ALPHA_LOGIC honest limits | ✅ #2168 |
| 5 | `scripts/sign-integrity-manifest.py` (TTY sign / CI `--verify-only`) | ✅ #2168 |
| 6 | Operator TTY: sign and package `integrity_manifest.json` per release | ⬜ Pending |

## Honest limits

- Proves match to a manifest signed by the packaged license verify key.
- Does not prove resistance if that packaged public key is replaced.
- Unsigned 1.8.0-class trees stay `tampered` until a matching signed file is present.

## Acceptance

- [x] Matching signed manifest → `validated`
- [x] Absent / invalid / hash miss / downgrade → `tampered`
- [x] Reconcile after module drift stays `tampered`
- [ ] First tagged release includes a TTY-signed packaged manifest

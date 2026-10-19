# Plan: Canonical org-wide license JWT path fallback

<!-- plans-hub-summary: LicenseGuard reads ~/.config/databoar/license.jwt when env and config paths are unset and the file exists (#1940). -->

**Status:** Done
**Date:** 2026-10-12
**Authors:** Fabio Leitao
**Priority:** P3
**GitHub:** [#1940](https://github.com/DataBoar/data-boar/issues/1940)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Goal

Align `data-boar` with `license-studio` deploy auto and sibling bestials: when
neither `DATA_BOAR_LICENSE_PATH` nor `licensing.license_path` is set, use the
org canonical JWT path if present — without overriding explicit configuration
(#719).

## Done

| Step | Status |
| ---- | ------ |
| `core/licensing/paths.py` + `LicenseGuard._evaluate` precedence | ✅ Done |
| Hermetic tests (`tests/test_license_canonical_path_fallback.py`) | ✅ Done |
| `docs/ops/QA_LOCAL_LICENSE.md` (+ pt-BR) | ✅ Done |
| `docs/LICENSING_SPEC.md` (+ pt-BR) + CHANGELOG path precedence | ✅ Done (#2073) |
| Fail-then-pass evidence in PR (revert fallback, confirm UNLICENSED, restore) | ✅ Done (local epic) |

## Out of scope

- ML-DSA / hybrid verification changes ([#2042](https://github.com/DataBoar/data-boar/issues/2042), [#2043](https://github.com/DataBoar/data-boar/issues/2043)).
- Promoting `platformdirs` to a direct dependency (hand-rolled XDG/Darwin/Windows).

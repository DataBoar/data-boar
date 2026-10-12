# Plan: Case-collision guard for tracked paths

<!-- plans-hub-summary: Fail check-all and the CI lint job when two tracked paths differ only by case (#2044). -->

**Status:** Done
**Date:** 2026-10-11
**Authors:** Fabio Leitao
**Priority:** P3
**GitHub:** [#2044](https://github.com/DataBoar/data-boar/issues/2044)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Goal

Two tracked paths that differ only by letter case coexist on Linux and break checkout on Windows and default macOS. `scripts/check_case_collisions.py` groups `git ls-files` by the lowercased path and fails when a group has more than one distinct path.

## Done

| Step | Status |
| ---- | ------ |
| Guard + unit test (pair `A.md`/`a.md` fails and names both; unique paths pass; space and accent pass) | ✅ Done |
| `scripts/check-all.sh` and `scripts/check-all.ps1` | ✅ Done |
| Step in the existing `lint` job of `.github/workflows/ci.yml` (no new workflow) | ✅ Done |

## Out of scope

A pre-commit hook was not added. `.pre-commit-config.yaml` is a gate file under the tripwire, and the lint job plus both check-all twins already run the guard.

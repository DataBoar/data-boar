# Plan: check-all gitleaks + OSV scanner parity (#1933)

<!-- plans-hub-summary: Backport keen-platypus strict gitleaks (pinned binary SHA256, no root allowlist bypass) and OSV dependency scan into CI and check-all security tier. -->

**Status:** Active (implementation slice on branch `docs/1933-gitleaks-osv-parity`)
**Date:** 2026-09-17
**Authors:** Fabio Leitao
**Priority:** P1
**GitHub:** [#1933](https://github.com/DataBoar/data-boar/issues/1933)
**Related ADR:** [ADR 0080](../adr/ADR-0080-local-validation-gate-inviolable.md) · [ADR 0005](../adr/ADR-0005-github-actions-pin-third-party-actions-to-commit-shas.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

CI already ran **Gitleaks** via `.github/workflows/gitleaks.yml`, but install verified the release **checksums.txt** (self-referential) and the scan used **repo-root** `.gitleaks.toml`, which a PR could weaken. **OSV-Scanner** was absent. **keen-platypus** pins bootstrap CLIs under `scripts/.cache/` and runs strict gitleaks without root bypass files.

## Decision

| Item | Choice |
| ---- | ------ |
| Gitleaks version | **8.30.1** (unchanged; CI ↔ local parity) |
| Binary trust | Hardcoded **linux_x64** SHA256 in `scripts/tool-pins.sh` + workflow `run` blocks |
| Allowlist / kombi | **`security/gitleaks.toml`** (maintainer path); CI removes **`.gitleaks.toml`** / **`.gitleaksignore`** before scan |
| Strict flags | `--ignore-gitleaks-allow`; full history `gitleaks git .` |
| OSV-Scanner | **2.6.0**, SHA256 pin; `osv-scanner scan source -r` + **`security/osv-scanner.toml`** (PYSEC-2026-217 ignore aligns with `pip-audit` in ci.yml) |
| Local bootstrap | `scripts/db-tool-bootstrap.sh` → `scripts/.cache/` (gitignored) |
| check-all tier | **Gitleaks** default security tier; **OSV** only with **`--enforced`** / **`-Enforced`** (ADR-0080 publish gate) |

## Implementation checklist

| Phase | Task | Status |
| ----- | ---- | ------ |
| 1 | Strict `gitleaks.yml` + `ci.yml` install (binary SHA256) | ✅ |
| 2 | `db-tool-bootstrap.sh` + `run-gitleaks-strict.sh` / `run-osv-scanner.sh` | ✅ |
| 3 | OSV job in `gitleaks.yml` | ✅ |
| 4 | Wire `check-all-security-scans.sh` / `.ps1` + parity message in `check-all` | ✅ |
| 5 | Tests (`test_github_workflows`, `test_tool_pins_gitleaks_osv`, kombi config path) | ✅ |
| 6 | `./scripts/check-all.sh` green on branch | ✅ |
| 7 | Operator review → push / PR | ⬜ |

## References

- `scripts/tool-pins.sh` — single source for version + SHA256 constants
- [PLAN_NO_COAUTHORSHIP_GATE.md](PLAN_NO_COAUTHORSHIP_GATE.md) — kombi layer (pytest + `security/gitleaks.toml`)
- keen-platypus: `scripts/lib/kp-tool-bootstrap.sh`, `.github/workflows/security.yml`

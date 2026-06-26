# Release gate #406 — close evidence (1.7.4 GA)

**Gate issue:** [GitHub #406](https://github.com/FabioLeitao/data-boar/issues/406)

**Close train:** PR **#1024** (`release/1.7.4`)

**Operator close trailer:** `Gate-Close-Approved-By: @FabioLeitao` (ADR-0072)

**Machine guard:** `security/version_policy.yaml` → `release_gate.open: false`

## Criteria met

| Criterion | Evidence |
| --- | --- |
| **Finding parity** | A/B benchmark 2026-05-13: v1.7.3 vs v1.7.4-rc — **26 findings each**, zero regression |
| **No regression in CI** | `check-all` green on release branch; ratio 0.955x on 10-file corpus (above Safe-Hold 0.574x — small corpus, not threshold breach) |
| **Maestro / completão (5 hosts)** | [#1021](https://github.com/FabioLeitao/data-boar/issues/1021) / PR #1022 — Maestro Deep 5-host gate: **4 SUMMARY passes**, idempotency match, DB oracle live |
| **ADR-0073 ratified** | Accepted in release train; public **`1.7.4`** + `[tool.databoar] maturity_build = 201` |
| **Version bump authorized** | Stable **`1.7.4`** in `pyproject.toml` (FASE 2–3 commits) |

## #406 checklist (final)

- [x] Maestro handler bugs (SSH timeout, `--bench-config`) — addressed in Maestro gate bundle (#1021 / #1022)
- [x] Bug 3 collect race — `-SleepBeforeCollect` workaround in prod; sentinel hardening deferred to post-GA
- [x] Completão smoke on **5 hosts** — Maestro Deep 5-host evidence (#1021)
- [x] `py7zr` / NFS gaps — documented expected degradations on designated nodes (lab lessons)
- [x] `$HOME=root` in ensure scripts — handler passes operator home explicitly (AGENTS.md)
- [x] **Stable bump** `1.7.4-rc-2` → **`1.7.4`** — this PR (#1024)
- [x] `CHANGELOG.md`, `docs/releases/1.7.4.md` — release train commits
- [ ] **Tag + Docker Hub + GitHub Release** — operator **release-ritual** post-merge (not agent-autonomous)

## Non-blockers (post-gate)

| Issue | Disposition |
| --- | --- |
| **#968** | Maestro `Collect-Artifacts.ps1` backslash / empty coleta dirs — **post-gate** hygiene; does not block 1.7.4 GA |

## Related

- **#970** — premature bump corrected; **`1.7.4` is not VOID**
- **#976**, **#977**, **#971** — versioning / ADR-0073 hygiene closed in PR #1024 body

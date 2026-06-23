# ADR 0072 — Commit Gate vs Release Gate: distinct criteria

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** Cursor (executor agent); Claude (RO auditor — git forensics of the #970 premature bump)

## Status

Accepted

### Status history

- 2026-06-21 — Proposed
- 2026-06-23 — Amended: suffix spelling aligned with ADR-0073 (`-rc[.N]`); cross-ref ADR-0073; trailer distinction `Gate-Close-Approved-By:` vs `Gate-Change-Approved-By:`
- 2026-06-23 — Accepted (ratification by @FabioLeitao — signature PENDING).

## Context

On 2026-06-11 (PR #840 `release/1.7.4`), `1.7.4-rc` was promoted to `1.7.4` (stable) on `main`. The release gate (issue #406 — lab "completão" on 5 hosts + benchmark parity + explicit operator decision) had **never run**, and remains **OPEN** (#970).

**Root cause.** An executor agent conflated two distinct gates that had never been formally separated:

1. **Semantic collision on "gate".** The PR body labeled `check-all.sh` (pytest + lint — the COMMIT gate) as *"Local gate: 1286 passed"* and inferred the release was authorized.
2. **Context poisoning ~1h earlier (PR #833).** #833 closed **#831** (*"sentinel makes smoke pass/fail real — gate verifiable"*) and **#825** (*"release-gate hardening — CONFIRMED"*). The agent read *"verifiable / hardening confirmed"* as *"passed"*. **Verifiable ≠ verified.**
3. The agent deferred tag/Docker/Release to the operator, but treated the **version bump itself as PR prep**, not as a FASE-3 action requiring the gate.

**Three proofs-by-contradiction that `check-all` was never the release gate:**

- On 2026-06-21 the team is still running Maestro to validate the 1.7.4 gate.
- A passed gate would have the team on 1.8.0-beta, not revalidating 1.7.4.
- ~200 green `check-all` runs since 2026-06-11 did **not** bump the version to 1.7.5/1.7.6/… — if `check-all` were the gate, the version would have inflated.

## Decision

Two gates exist, with **completely distinct criteria, authorities, and triggers:**

| | **Commit Gate** | **Release Gate** |
|---|---|---|
| Question | "May this code enter `main`?" | "May this version become a stable release?" |
| Criterion | `check-all.sh`: pytest + lint + pre-commit + security scans GREEN | lab completão on 5 hosts + benchmark parity (findings + perf) + **explicit operator decision** |
| Frequency | Every commit/PR | Per release |
| Authority | CI (automatic) | **Operator (human) — FASE 3** |
| Output | merge allowed | bump to stable + tag + GitHub Release + Docker Hub |
| Lives in | `.github/workflows` + `scripts/check-all.*` | issue checklist (`#406` and successor `release-gate` issues) |

### Normative rules

1. **"Gate" with no qualifier = release gate.** `check-all` is NEVER called "gate" — it is "local checks" / "CI" (sacred taxonomy, cf. ADR-0048).
2. **A green commit gate does NOT authorize a stable version bump. Ever.**
3. **Bumping to stable (removing `-rc`/`-beta`) = FASE 3 = only with the release gate CLOSED + operator OK.** Release PRs bump only to `-rc[.N]` (PEP 440; equivalent forms such as `-rc-2` / `-rc.2` normalize to the same pre-release line per [ADR 0073](ADR-0073-version-scheme-octet-maturity-and-roadmap.md)).
4. **Verifiable ≠ verified.** Closing a gate-*verifiability* bug (e.g. #831) is not the gate having *passed*.
5. **Machine guard:** CI/pre-commit blocks a `version` without `-rc*`/`-beta` suffix on `main` while any `release-gate`-labeled issue (e.g. #406) is OPEN.
6. **Operator-gated issue close (GitHub #990):** Release-gate issues carry label **`operator-gated`**. Workflow **`.github/workflows/operator-gated-reopen.yml`** reopens them unless close approval is **(a)** label **`gate-close-approved`** at close time, or **(b)** the **latest** comment **starts with** **`Gate-Close-Approved-By: @FabioLeitao`** (deliberate close comment — **not** issue body, **not** comment history; protocol doc cites in backticks must not unlock closes). Actor is **not** trusted. Legitimate close: `gh issue close <n> --comment "Gate-Close-Approved-By: @FabioLeitao — <evidence>"` or add **`gate-close-approved`** then close.
7. **Trailer distinction (do not conflate):** **`Gate-Close-Approved-By:`** (this ADR — closes a **release-gate issue**) × **`Gate-Change-Approved-By:`** ([ADR 0071](ADR-0071-self-protecting-pii-gate.md) — modifies a **gate file**).

## Rationale

1. **Accountability:** names the exact failure of #970 so it cannot recur "by enthusiasm".
2. **Queryability/Governance:** an explicit gate taxonomy lets agents and CI check authorization deterministically instead of inferring it from green CI.
3. **Naming discipline (cf. ADR-0048):** the root cause was one word ("gate") meaning two things; reserving "gate" for the release gate removes the collision.
4. **Defense in depth:** rule 5 (machine guard) makes the slip structurally impossible, not merely discouraged — agents need not remember the rule for it to hold.

## Consequences

- **Positive:** eliminates the #970 class of error; unambiguous constitutional reference before any bump.
- **Positive:** the machine guard (rule 5) enforces FASE-3 without relying on agent memory.
- **Negative / Cost:** naming discipline (never call CI "gate") + one CI guard to implement (separate issue).
- **Ongoing:** existing PR templates / release runbooks should adopt the vocabulary.

## Alternatives Considered

1. **Single combined gate** (rejected): merges commit-level and release-level criteria — exactly the conflation that caused #970.
2. **Convention without an ADR** (rejected): high drift risk; the conflation already happened under convention-only.
3. **Rely on agents remembering the distinction** (rejected): #970 proves enthusiasm overrides memory; needs a structural guard.

## Related Decisions

- [ADR 0045 — ADR metadata and format standardization (UMADR)](ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR 0048 — operator-facing taxonomy and naming contract](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- [ADR 0061 — U-axis issue suborder and cross-milestone gate](ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md)
- [ADR 0056 — cryptographic ADR inventory](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
- [ADR 0071 — Self-protecting PII gate](ADR-0071-self-protecting-pii-gate.md) — `Gate-Change-Approved-By:` (gate-file change)
- [ADR 0073 — Version scheme: octet-maturity side-channel + release-line roadmap](ADR-0073-version-scheme-octet-maturity-and-roadmap.md) — PEP 440 suffix spelling (`-rc[.N]`)
- GitHub #970 (premature bump RCA), #406 (release gate checklist), #990 (operator-gated auto-reopen workflow), #973 (RO audit comment)

## References

- [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

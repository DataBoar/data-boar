# ADR 0073 — Version scheme: octet-maturity side-channel + release-line roadmap

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** Claude (RO auditor); Steve Gibson / GRC (Engineering Craft Inspiration)

## Status

Proposed

### Status history

- 2026-06-21 — Proposed
- 2026-06-23 — Proposed (amended): destensionar octeto da versão pública; regras (1)–(4) abaixo; TBD pós-GA aberto (#977 auditoria RO)

## Context

Versioning today is governed by `docs/VERSIONING.md` (**major.minor.build** + `-beta`/`-rc`). Two LLM naive-default slips:

1. Premature promotion `1.7.4-rc → 1.7.4` (#970) — stable bump without the **release gate** (ADR-0072, GitHub #406).
2. Phantom roadmap `1.7.5-beta` (#772) — agents inferred "next = 1.7.5" by naive increment, against the real roadmap (1.8.x).

A richer scheme (vault `self-upgrade-beacon-heartbeat-design-2026-06-15`, Gibson-style) carries **octet-maturity** bands (**0–127** beta · **128–199** rc · **200–255** release). An early draft of this ADR wrongly placed that octet **inside** the public version (`1.7.4.201`, `1.7.4` VOID). RO audit on #977 flagged the contradiction: even as **Proposed**, that wording risks agent improvisation. **Do not bump `pyproject.toml` until this ADR is amended and ratified.** Working line today: **`1.7.4-rc-2`**.

## Decision

1. **Public version (all artifacts — `[project] version`, About, Git tag, Docker tag, README, man pages):** `major.minor.build` (**three segments only**) + optional PEP 440 pre-release suffix (`-beta[.N]` / `-rc[.N]`) or **none**. **Never a fourth segment** (e.g. `1.7.4.201` is invalid).
2. **Octet-maturity (Gibson DNS-beacon bands):** lives in a **separate derived field** — `[tool.databoar] maturity_build` — a **side-channel** (release notes, beacon, operator tooling). Bands: **0–127** beta · **128–199** rc · **200–255** release (`.200` = GA maturity, `.201` = fix-1 maturity, …). **Never** copy this octet into `[project] version` or the About surface.
3. **`-alpha` suffix:** tamper-detection axis only (GitHub #856), **not** a maturity band — separate from beta/rc/release.
4. **`1.7.4` is not VOID:** #970 was a **premature tag/bump** without release-gate approval; discipline is restored by **ADR-0072** + gate **#406**, not by "burning" the public number.

### OPEN / TBD (operator HITL — do not decide by agent inference)

How to version **post-GA public fixes** under rule (1) — **without** a fourth segment. The pre-amend draft used `1.7.4.x` / `1.7.4.201`, which **violates** rule (1). **Status: OPEN** until the operator decides and ratifies this ADR.

5. **Release-line roadmap (semver intent):** `1.7.4` line = open-core maturity + commercial JWT protection; `1.8.x` = augmented corporate capacities (re-ID, sidecars, plugins/Clojure — **new architecture**, not a 1.7 minor). **`1.7.5` does not exist.** Next dev milestone: **`1.8.0-beta`**; horizon: `1.9.x`. `docs/VERSIONING.md` documents (1)–(4) + (5); full DNS-beacon/heartbeat/kill-switch lifecycle = 1.8.x roadmap (PLAN_SELF_UPGRADE), out of scope here.

## Rationale

- **Separation of concerns:** public PEP 440 version stays three-segment + suffix; maturity octet informs operators/beacon without polluting customer-facing numbers.
- Explicit roadmap (no 1.7.5) → kills the #772 class.
- Release gate (ADR-0072) → kills the #970 class without inventing VOID numbers or four-segment versions.
- Gibson lineage: proven band discipline (SpinRite/DNSBench), kept as **side-channel** per operator design.

## Consequences

- **Positive:** agents cannot invent `1.7.5`, four-segment versions, or naive stable bumps; maturity remains traceable via `maturity_build` when wired.
- **Cost:** `VERSIONING.md` + issue hygiene (#971, #406); future `pyproject.toml` `[tool.databoar]` field; CI guards must align (no `1.7.4.201` / VOID strings in policy).
- **Pairs with ADR-0072 (release gate)** — together they surround the release surface.
- **Blocked until ratified:** stable semver bump from `1.7.4-rc-2`; post-GA fix numbering (TBD above).

## Alternatives Considered

1. **Pure semver suffix-only (status quo on `main`):** retained for **public** version until this ADR is **Accepted** and TBD is closed.
2. **Octet inside public version (`1.7.4.201`, VOID `1.7.4`):** rejected — contradicts three-segment rule; caused agent hesitation (#977).
3. **Octet internal-only with no `maturity_build` field:** deferred — operator chose explicit side-channel over hiding bands entirely.

## Related Decisions

- [ADR 0072 — Commit Gate vs Release Gate](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md)
- [ADR 0045 — ADR metadata and format standardization (UMADR)](ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR 0048 — operator-facing taxonomy and naming contract](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- GitHub #970 (premature bump), #971 (VERSIONING + `maturity_build`), #977 (ADR + audit), #772 (`1.7.5` → `1.8`), #406 (release gate), #717 (kill-switch), PLAN_SELF_UPGRADE

## References

- Steve Gibson / GRC versioning (DNSBench `1.3.6668.0`-style) — Engineering Craft Inspiration (vault `_inspirations/SECURITY_INSPIRATION_GRC_SECURITY_NOW.md`)
- RO audit comment on #977 (2026-06-23) — destensionar rules (1)–(4)

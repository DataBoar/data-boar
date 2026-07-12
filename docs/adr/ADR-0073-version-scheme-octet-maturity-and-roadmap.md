# ADR 0073 — Version scheme: octet-maturity side-channel + release-line roadmap

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** Claude (RO auditor); Steve Gibson / GRC (Engineering Craft Inspiration)

## Status

Accepted

### Status history

- 2026-06-21 — Proposed
- 2026-06-23 — Proposed (amended): destensionar octeto da versão pública; regras (1)–(4) abaixo; TBD pós-GA aberto (#977 auditoria RO)
- 2026-06-25 — Accepted: resolve #977 — post-GA public fixes stay on the **same public line** (`1.7.4`); **`maturity_build`** octet distinguishes fix maturity; **`1.7.5` does not exist**; next **public** line = **`1.8.0`** (#971)
- 2026-06-27 — Amended: cláusula de distribuição PyPI (#1047) — post-release como publish-counter. (ratificado pelo operador)
- 2026-07-01 — Amended: reset de `maturity_build` em nova linha semver; octeto na fix-line avança por **fix discreto** (não por merge/build/docs) — ver `docs/releases/1.7.4.post2.md`.
- 2026-07-01 — Amended (band-fix): contador Gibson **começa em 1** (primeiro beta = `.1`; **0** não usado); tetos de faixa **forgiving** (overflow → TXT beacon). Corrige redação 0-based que derivara do `.mdc` em vez desta ADR.

## Context

Versioning today is governed by `docs/VERSIONING.md` (**major.minor.build** + `-beta`/`-rc`). Two LLM naive-default slips:

1. Premature promotion `1.7.4-rc → 1.7.4` (#970) — stable bump without the **release gate** (ADR-0072, GitHub #406).
2. Phantom roadmap `1.7.5-beta` (#772) — agents inferred "next = 1.7.5" by naive increment, against the real roadmap (1.8.x).

A richer scheme (vault `self-upgrade-beacon-heartbeat-design-2026-06-15`, Gibson-style) carries **octet-maturity** bands (**0–127** beta · **128–199** rc · **200–255** release). An early draft of this ADR wrongly placed that octet **inside** the public version (`1.7.4.201`, `1.7.4` VOID). RO audit on #977 flagged the contradiction: even as **Proposed**, that wording risks agent improvisation. **Ratified 2026-06-25** with rules (1)–(4) below and post-GA fix policy in §Decision. Working line before GA release PR: **`1.7.4-rc-2`**.

## Decision

1. **Public version (release line):** `major.minor.build` (**three segments only**) + optional PEP 440 pre-release suffix (`-beta[.N]` / `-rc[.N]`) or **none**. **Never a fourth semver segment** (e.g. `1.7.4.201` is invalid). PEP 440 **`.postN`** on PyPI is **not** that fourth segment — see § *PyPI dual counters* below.
2. **Octet-maturity (Gibson DNS-beacon bands):** lives in a **separate derived field** — `[tool.databoar] maturity_build` — a **side-channel** (release notes, beacon, operator tooling). Counter **starts at 1** (first beta = `.1`; **0** unused). Bands (ceilings **forgiving** — overflow → TXT): **1–126** beta · **127–199** rc · **200–254** GA + fix (`.200` = GA maturity on that line, `.201` = fix-1, …; e.g. `.208` valid) · **255** = overflow sentinel (consult TXT). **Never** copy this octet into `[project] version` or any version string. **`.postN` is never the octet** — rule (1) stays intact.

   **New public line (e.g. `1.8.0`):** `maturity_build` **resets into the band** matching the pre-release suffix — beta → **1–126** (starts at **`1`**), rc → **127–199**, GA → **`.200`** anchor — it does **not** continue from the previous line (e.g. `.208` on `1.7.4`). **`.postN`** applies only on the **release band** of a given public line.

   **On a fix-line (post-GA):** octet **+1 per discrete fix** to installed/runtime behavior (bug, CVE, dangling feature completion); **not** docs/ADR/chore/ci/test/rito-only. **`postN`** advances only on PyPI upload when fixes warrant republication.
3. **`-alpha` suffix:** tamper-detection axis only (GitHub #856), **not** a maturity band — separate from beta/rc/release.
4. **`1.7.4` is not VOID:** #970 was a **premature tag/bump** without release-gate approval; discipline is restored by **ADR-0072** + gate **#406**, not by "burning" the public number.

### Post-GA public fixes (#977 — resolved)

Under rules (1)–(4), a **post-GA public fix** on the `1.7.4` line:

- **Does not** create **`1.7.5`** (that number **does not exist** on the roadmap — #772).
- **Keeps** the **public** semver at **`1.7.4`** (three segments, no fourth segment).
- **Distinguishes** fix maturity via **`[tool.databoar] maturity_build`** (side-channel only — e.g. `.200` consumed by the voided #970 GA attempt; the real GA uses `.201`).
- **Next public line** after `1.7.4` GA work completes: **`1.8.0`** (new architecture — not a naive `1.7.x` increment).

### PyPI dual counters (#1047 — ratified 2026-06-27)

PyPI indexes are **immutable per uploaded version string**; there is **no** `maturity_build` side-channel on the index. A **packaging fix** on the **`1.7.4` line** that must reach PyPI consumers uses **two independent counters**:

| Counter | Where it lives | Increments when | Example |
| ---- | ---- | ---- | ---- |
| **Publication** | PEP 440 **`.postN`** in `[project] version`, About, User-Agent, PyPI | Each **PyPI upload** — **not** each local build | `1.7.4.post1`, `1.7.4.post2` |
| **Maturity / fix** | `[tool.databoar] maturity_build` (Gibson octet side-channel) | Each **discrete fix** to installed/runtime behavior (published or not) | `.201`, `.202`, `.208` |

**Rule (1) intact:** **`.postN` is never the octet**; `1.7.4.202` (fourth semver segment) remains invalid.

**Divergence (expected):** Counters may diverge when `maturity_build` advances without a PyPI upload — e.g. `1.7.4.post1` ↔ `.202`, fixes `.203`–`.207` unpublished, next PyPI upload `1.7.4.post2` ↔ `.208`. Map: [`docs/releases/1.7.4.post2.md`](../releases/1.7.4.post2.md).

**Surfaces (honest split):**

| Surface | Shows |
| ---- | ---- |
| **Public line** — README, man `.TH`, marketing copy | **`1.7.4`** (release line; no `.postN` where stakeholders expect a clean semver) |
| **Build** — `[project] version`, About API/UI, PyPI, User-Agent | **`1.7.4.postN`** (publish counter; **does not leak** the octet — **not a bug**) |

**Mandatory traceability:** Maintain an explicit **`postN ↔ maturity_build` map** in release notes and/or a version manifest — e.g. `1.7.4=.201 · 1.7.4.post1=.202 · …` Without this map, the two counters diverge **without audit trail**.

| Policy | Detail |
| ---- | ------ |
| **Not** | `1.7.5`; Gibson octet in the version string; fourth semver segment |
| **Defer to `1.8.0`** | Architecture-line changes only — not lean-core / extras packaging fixes on `1.7.4` |
| **Git tag / Docker** | Operator **release-ritual** may tag `v1.7.4.postN`; map must record octet pairing |

Canonical example: [#1047](https://github.com/FabioLeitao/data-boar/issues/1047) — SQL drivers moved to extras; first PyPI republication **`1.7.4.post1`** with **`maturity_build = 202`**. Map: [`docs/releases/1.7.4.post1.md`](../releases/1.7.4.post1.md).

Beacon mechanics (DNS bands, TXT, anti-fraud) remain **1.8.x** roadmap scope (#717, PLAN_SELF_UPGRADE) — out of scope for the 1.7.4 GA release slice.

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
- **Ratified:** stable semver bump from `1.7.4-rc-2` to **`1.7.4`** authorized only with release gate **#406** closed per operator FASE 3 (#976, release PR #1024).

## Alternatives Considered

1. **Pure semver suffix-only (status quo on `main`):** retained for **public** version until this ADR is **Accepted** and TBD is closed.
2. **Octet inside public version (`1.7.4.201`, VOID `1.7.4`):** rejected — contradicts three-segment rule; caused agent hesitation (#977).
3. **Octet internal-only with no `maturity_build` field:** deferred — operator chose explicit side-channel over hiding bands entirely.

## Related Decisions

- [ADR 0071 — Self-protecting PII gate](ADR-0071-self-protecting-pii-gate.md) — `Gate-Change-Approved-By:` (gate-file change) vs `Gate-Close-Approved-By:` (release-gate issue close)
- [ADR 0072 — Commit Gate vs Release Gate](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md)
- [ADR 0045 — ADR metadata and format standardization (UMADR)](ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR 0048 — operator-facing taxonomy and naming contract](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- GitHub #970 (premature bump), #971 (VERSIONING + `maturity_build`), #977 (ADR + audit), #772 (`1.7.5` → `1.8`), #406 (release gate), #717 (kill-switch), PLAN_SELF_UPGRADE, [#1047](https://github.com/FabioLeitao/data-boar/issues/1047) (PyPI post-release on `1.7.4` line)

## References

- Steve Gibson / GRC versioning (DNSBench `1.3.6668.0`-style) — Engineering Craft Inspiration (vault `_inspirations/SECURITY_INSPIRATION_GRC_SECURITY_NOW.md`)
- RO audit comment on #977 (2026-06-23) — destensionar rules (1)–(4)

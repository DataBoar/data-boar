# ADR 0085 — Install priority ladder (native-first when shipped; pipx today)

- **Date (UTC):** 2026-08-06
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** operator session threads on [#1467](https://github.com/DataBoar/data-boar/issues/1467), [#1470](https://github.com/DataBoar/data-boar/issues/1470)

## Status

Proposed

### Status history

- 2026-08-06 — Proposed (born Proposed per ADR-0045; records maintainer install-order convention from [#1467](https://github.com/DataBoar/data-boar/issues/1467) / [#1470](https://github.com/DataBoar/data-boar/issues/1470). Accepted only via HITL ratification per ADR-0056; Date (UTC) immutable; Status history append-only).
- 2026-08-12 — Clarifying amendment (still Proposed): hedge `brew` in Decision §1.2 as **when published**, matching §1.1 macOS wording and [#1478](https://github.com/DataBoar/data-boar/issues/1478); cross-links [#1425](https://github.com/DataBoar/data-boar/issues/1425) / [#1427](https://github.com/DataBoar/data-boar/issues/1427). Plan hub: [PLAN_NATIVE_PACKAGES.md](../plans/PLAN_NATIVE_PACKAGES.md) ([#1541](https://github.com/DataBoar/data-boar/issues/1541)).

## Context

Onboarding and AI-generated advice often invert the install story: Docker or “call IT” first, invent CLIs, or treat personal-namespace GitHub paths as current. Field evidence ([#1126](https://github.com/DataBoar/data-boar/issues/1126), non-tech Windows) shows that missing a zero-prerequisite Windows installer is fatal for the ICP, while `pipx` + `--demo` already works when documented honestly.

Native packaging is in flight on two tracks:

- **Linux:** nfpm foundation and CI ([#1403](https://github.com/DataBoar/data-boar/issues/1403), [#1437](https://github.com/DataBoar/data-boar/issues/1437)) with embed policy [ADR 0084](ADR-0084-native-package-embedded-cpython-by-channel.md); consumer-stable **Release** assets are still the docs gate (CI artifact ≠ stable URL).
- **Windows:** MSI + winget with embed `cp314`/`cp314t` ([#1467](https://github.com/DataBoar/data-boar/issues/1467)) — not shipped yet.

Without a written ladder, docs and agents either overclaim natives that do not exist or bury the practical `pipx` path under Docker.

Product facts for agents already state Docker is optional and `pipx install data-boar` is the current native-until-MSI path: [CANONICAL_PRODUCT_FACTS.md](../CANONICAL_PRODUCT_FACTS.md). This ADR is the **normative install-order decision**; it does not rewrite README/QUICKSTART in the same change set.

## Decision

1. **Canonical install ladder (policy — when the artifact exists)**
   Prefer, in order:
   1. **OS-native product packages** (self-contained where ADR 0084 applies) — **committed** platforms only:
      - Windows: MSI and/or winget pointing at the **product** MSI (not winget-as-Python-dependency).
      - Linux: deb / rpm (and apk / other families when published).
      - macOS: pkg / Homebrew cask (or formula) when published.
      - FreeBSD: native packages when published.
   2. **Non-container fallbacks:** `pipx` → `pip` → `brew` **(when a product formula/cask is published — none yet; see [#1425](https://github.com/DataBoar/data-boar/issues/1425) / [#1478](https://github.com/DataBoar/data-boar/issues/1478))** → `git clone` + `uv sync` (dev/contributor checkout) → other managers only if needed.
   3. **Virtualization / orchestration last** (documented for deploy/lab, not the default “start here”): Docker → Podman → Compose/Swarm → Kubernetes-class.

2. **Platform presentation order in guides**
   When listing **committed** platforms: **Windows → Linux → macOS → FreeBSD**.
   Illumos/Solaris (and derivatives) are **aspirational / future** only — do not present them as a committed install channel until packages and docs exist (overclaim guard).

3. **Honesty rule (critical — what to recommend *today*)**
   Docs and agents **must recommend what exists today**:
   - **Current practical top:** `pipx install data-boar`, then `data-boar --demo` for safe first contact; site [windows.html](https://databoar.com.br/windows.html) for non-tech Windows.
   - **Native-first becomes the documented top only after** the relevant package is published with a **stable public URL** (typically GitHub Release assets + checksums), not merely a CI Actions artifact.
   - Until then, native channels may appear as **roadmap / forthcoming**, never as the default click-path.

4. **Docker is never the default non-tech path**
   Containers remain supported for TI/lab/enterprise deploy; they stay **below the fold** of quick-start / “start here” surfaces. Aligns with CANONICAL_PRODUCT_FACTS (Docker optional).

5. **Scope of this ADR**
   Normative order for onboarding and agent guidance. **Does not** by itself edit README or QUICKSTART; those surfaces consume this ladder in later slices ([#1470](https://github.com/DataBoar/data-boar/issues/1470), [#1474](https://github.com/DataBoar/data-boar/pull/1474) — PR in progress / consumer / out of scope for this ADR file). Packaging delivery remains [#1467](https://github.com/DataBoar/data-boar/issues/1467) and [#1403](https://github.com/DataBoar/data-boar/issues/1403)/[#1437](https://github.com/DataBoar/data-boar/issues/1437).

## Rationale

- Matches maintainer-confirmed convention (2026-08-06) on [#1467](https://github.com/DataBoar/data-boar/issues/1467) / [#1470](https://github.com/DataBoar/data-boar/issues/1470).
- Separates **policy** (native-first when real) from **current truth** (pipx), preventing overclaim.
- Keeps ADR 0084 commercial clause intact: embed / installer ≠ Enterprise entitlement ([#551](https://github.com/DataBoar/data-boar/issues/551)).
- `brew` before `git+uv` **once published**: brew is a user-oriented install path; until a formula/cask exists, agents must skip it (honesty rule / [#1478](https://github.com/DataBoar/data-boar/issues/1478)). `git clone` + `uv sync` remains the developer checkout.

## Consequences

- Future onboarding edits should cite this ADR and CANONICAL_PRODUCT_FACTS rather than invent Docker-first or stale-repo paths.
- When MSI or Linux Release packages ship, flip the **documented** top of the ladder in the same release window as the stable URL — not before.
- Agents that ignore the honesty rule are wrong even if they correctly recite “native-first” as abstract policy.

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| Docker-first for all personas | Contradicts field ICP and CANONICAL_PRODUCT_FACTS; raises false “need IT” barrier. |
| Document native-first as current top before Release URLs exist | Overclaim; CI artifacts are not user-stable. |
| pip-only (no pipx) as default | Weaker isolation for CLI apps; pipx is the agreed non-native default. |
| Commit Illumos/Solaris as equal native tier today | Overclaim — no published channel; keep aspirational only. |

## Related Decisions

- [ADR 0084](ADR-0084-native-package-embedded-cpython-by-channel.md) — embed CPython by native channel.
- [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md) — ADR format / Proposed birth / en_US.
- [ADR 0056](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md) — inventory / HITL ratification ritual.

## References

- [#1467](https://github.com/DataBoar/data-boar/issues/1467) — Windows MSI + winget (canonical packaging tracker).
- [#1425](https://github.com/DataBoar/data-boar/issues/1425) — macOS Homebrew tap (planned; not published).
- [#1427](https://github.com/DataBoar/data-boar/issues/1427) — Windows CI (`windows-latest`) blocker for MSI/winget.
- [#1478](https://github.com/DataBoar/data-boar/issues/1478) — `brew` in §1.2 must stay hedged until published (fixed in this ADR).
- [#1403](https://github.com/DataBoar/data-boar/issues/1403) / [#1437](https://github.com/DataBoar/data-boar/issues/1437) — nfpm Linux foundation + CI.
- [#1470](https://github.com/DataBoar/data-boar/issues/1470) — docs/discoverability; install-order convention thread.
- [#1474](https://github.com/DataBoar/data-boar/pull/1474) — Windows non-tech quickstart (**PR in progress**; consumer of this ladder; out of scope for this ADR file).
- [#1126](https://github.com/DataBoar/data-boar/issues/1126) — first non-tech Windows field evidence.
- [CANONICAL_PRODUCT_FACTS.md](../CANONICAL_PRODUCT_FACTS.md) — agent-facing install/identity facts.
- Site: <https://databoar.com.br/windows.html>

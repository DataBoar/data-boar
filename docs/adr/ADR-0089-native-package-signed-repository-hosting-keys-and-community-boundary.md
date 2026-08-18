# ADR 0089 — Native package signed repository: hosting, signing keys, and community boundary

- **Date (UTC):** 2026-08-18
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-18 — Proposed (records operator decisions on [#1405](https://github.com/DataBoar/data-boar/issues/1405); born Proposed per ADR-0045. **This ADR does not generate keys, publish repos, or ship package indexes.**)

## Context

[#1405](https://github.com/DataBoar/data-boar/issues/1405) requires a **signed package repository** for native OS packages (deb / rpm / apk / pacman) so install paths use `gpgcheck=1` / `SigLevel = Required` (and apk equivalents) — not “download a loose `.deb` and hope.” Loose artifacts without a signed index are not the taught product channel.

Related posture already locked:

- [ADR 0084](ADR-0084-native-package-embedded-cpython-by-channel.md) — embed CPython by channel (a)/(b); native packaging target **1.8.x**.
- Wheelhouse [#1182](https://github.com/DataBoar/data-boar/issues/1182) — **hybrid** publish: binary assets on GitHub Releases + machine-readable index on `databoar.com.br` (PEP 503 `/simple/`), with parity gates (e.g. [#1410](https://github.com/DataBoar/data-boar/issues/1410)).
- License **golden key** (Ed25519 / JWT issuer on the primary Linux workstation) must **never** sign OS packages — distinct purpose, rotation, and blast radius.
- Alpine is on the release gate ([#821](https://github.com/DataBoar/data-boar/issues/821)); apk is not optional packaging theater.

Operator answered three design questions in [#1405](https://github.com/DataBoar/data-boar/issues/1405) comments (2026-08-17/18). Options matrix: [comment](https://github.com/DataBoar/data-boar/issues/1405#issuecomment-5321883037).

### Hard constraints (carried forward)

| # | Constraint |
| - | ---------- |
| H1 | Package-release signing key ≠ license golden key. |
| H2 | License golden key does not leave the primary Linux workstation and is **not** reused for `InRelease` / `repomd` / `APKINDEX` / `.pkg.sig`. |
| H3 | Loose artifact without a signed repo is not the taught install channel. |
| H4 | Delivered `.repo` / configs require verification (`gpgcheck=1`, `SigLevel = Required`, apk equivalents) — no optional trust. |
| H5 | Package-signing key fingerprint published on a channel **independent** of the repository tree (site + README). |
| H6 | Target **1.8.x**; align with ADR-0084 channel (a)/(b). |

## Decision

### 1. Hosting — hybrid **1E** (same pattern as the wheelhouse)

- **Binary packages** (`.deb` / `.rpm` / `.apk` / `.pkg.tar.zst`, …) live as **GitHub Release** assets (auditable tags, same family as the wheelhouse).
- **Signed indexes** for each format are generated in CI and **served on `databoar.com.br`** — apt `dists/` + `Release`/`InRelease`, dnf `repodata/`, apk `APKINDEX.tar.gz`, pacman `.db` — analogous to `https://databoar.com.br/simple/` for wheels, with format-specific index trees instead of PEP 503.
- **Reject as Done criteria for #1405:** GitHub Releases alone without indexes (**1A**); LAN-only lab mirrors as the public channel (**1F**). Lab may prove metal first; public AC needs the hybrid public path.
- Object storage / SaaS package hosts (**1C** / **1D**) remain future scale options; **1.8.x Community** starts on **1E**.

### 2. Signing material — **two** keys for Linux package formats (not one)

- **Key A — GPG packaging key:** signs the classical repo metadata paths used by **deb**, **rpm**, and **pacman** (one documented fingerprint for that family).
- **Key B — Alpine-specific key material:** apk historically expects its own **RSA-style `-keys`** material; **do not** reuse Key A as Key B. Alpine is release-gate-critical (#821).
- **Prohibited (2Z):** license golden key, SSH commit keys, app deploy keys — for package-repo signatures.
- **Sigstore/cosign (2C):** may appear later as a **parallel** transparency layer; it does **not** replace GPG/`InRelease` / `gpgcheck=1` for this ADR’s Done bar. OIDC-only / Sigstore-only without classical repo signatures (**2D**) is **rejected** as the sole #1405 mechanism.

#### Rotation / future platforms (scope fence — record now, implement later)

When rotation policy is written after keys exist:

- **In scope for #1405 / this ADR’s key model:** the **two** Linux-repo keys above (GPG family + apk).
- **Out of scope as “just another GPG key”:** **winget / MSI** (Authenticode / paid CA X.509) and **macOS** (Apple Developer ID / notarization) use **different PKI**, cost, and acquisition processes. **BSD-style ports** may be closer to RSA-like conventions (apk-adjacent), but still need their own decision when that milestone opens.
- Do not let a rotation doc imply those platforms are a trivial extension of Key A/B.

### 3. Community × commercial boundary — **3B**

- The **public signed repository** ships **Community** (open-core / caps per licensing matrix) **only**.
- **Commercial / Enterprise** does **not** share that public apt/dnf/apk/pacman feed — avoids accidental `apt install` of a paid tier without the commercial channel.
- **3B does not cancel commercial distribution.** Commercial remains a **separate** deliverable (authenticated download / JWT-gated artifact), sequenced **after** this milestone — not “forgotten.”
- **Acceptance follow-up (sub-item of #1405 close):** when the Community signed repo is live, **open a dedicated issue** for the commercial distribution channel; do not treat “3B decided” as closing both sides.

## Consequences

### Positive

- Reuses a **proven** publish pattern (GH Releases + site indexes + parity gates) instead of inventing a third hosting architecture for 1.8.x.
- Keeps Alpine first-class without forcing a single crypto material onto every ecosystem.
- Clear messaging: public repo = Community; paid tier stays off the free feed.

### Costs / follow-through (after this ADR is Accepted)

1. Ceremony to generate **new** Key A and Key B (never the license golden key); document fingerprints on site + README (H5).
2. CI publish of indexes to `databoar.com.br` + Release assets; **parity gate** (wheelhouse/#1410-class) so index entries match published packages.
3. Operator docs (EN + pt-BR): install **from the signed repo**, not from a local loose package, as the taught path.
4. Lab proof: install via configured repo URLs with verification required.
5. Open commercial-channel issue when #1405’s Community repo AC is met.

### Explicitly not decided / not blocked by this ADR

- [#1622](https://github.com/DataBoar/data-boar/issues/1622) (`Test Windows` as a **required** check on `main`) is a related trust hygiene item for later **Windows / MSI** (#1467) work. It does **not** block accepting or implementing this Linux signed-repo ADR; it **does** matter before treating Windows CI as merge-protected truth for MSI.

## References

- [#1405](https://github.com/DataBoar/data-boar/issues/1405) — Signed native package repositories (decisions recorded in comments).
- [#1403](https://github.com/DataBoar/data-boar/issues/1403) · [#1404](https://github.com/DataBoar/data-boar/issues/1404) · [#1437](https://github.com/DataBoar/data-boar/issues/1437) — native package build / CI.
- [#1182](https://github.com/DataBoar/data-boar/issues/1182) · [#1410](https://github.com/DataBoar/data-boar/issues/1410) — wheelhouse hosting + SHA256SUMS parity.
- [#821](https://github.com/DataBoar/data-boar/issues/821) — Alpine on release gate.
- [#1622](https://github.com/DataBoar/data-boar/issues/1622) — Windows required check (related note only).
- [ADR 0084](ADR-0084-native-package-embedded-cpython-by-channel.md) — embed vs distro Python by channel.
- [ADR 0085](ADR-0085-install-priority-ladder.md) — install priority ladder.
- `docs/plans/PLAN_NATIVE_PACKAGES.md` · `docs/plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md` (when present).

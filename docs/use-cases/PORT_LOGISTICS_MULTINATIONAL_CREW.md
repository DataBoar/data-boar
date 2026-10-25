# Use-case storyboard — port logistics, multinational crew (metadata tension)

**Português (Brasil):** [PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md](PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md)

This is a **documentation storyboard** for workshops and POC narratives. It is **not** exhaustive legal analysis and **not** a guarantee that any specific deployment matches the scenario.

## Cast (generic roles)

- **Host state:** Brazil — customs-controlled or port-adjacent operations (LGPD applies to local processing; additional sector/security rules may apply).
- **Data subjects:** Seafarers and visitors with **diverse national documents** (passports, seafarer IDs, visas).
- **Systems:** Access logs, gate photos, manifests, crew lists—often **one** row linking **many** jurisdictions by **document type**, **phone prefix**, **address fragments**, and **employer HR** identifiers.

## Storyboard (flow)

1. **Vessel arrives** — port operations generate structured and semi-structured records.
2. **Crew disembarks** — identity and access events are logged (names, document numbers, photos where policy requires).
3. **Log lands in enterprise stores** — databases, shares, or ticketing; becomes a **Data Boar target** under governance-approved scope.
4. **Boar sniffs (configured scan)** — regex/ML surface **identifiers** and **sensitive categories**; **norm tags** reflect inventory language.
5. **Optional jurisdiction hints** — metadata may trigger **zero, one, or several** Report info rows (e.g. US-style tokens vs JP-style tokens in the same session’s column/path text—**heuristic**).
6. **“Collision” moment (human)** — DPO sees **tension**: multiple hints or strong foreign-document signals against a **Brazil-anchored** operation; **cannot** choose applicable law in the tool.
7. **Action (organisational)** — **Counsel** maps lawful basis, minimisation, retention, and cross-border posture; **CISO** aligns access controls and evidence handling. Data Boar supplies **inventory evidence**, not the filing order for regulators.

## How Data Boar helps without deciding

- **Surfaces** where **multinational identifiers** and **regional tokens** cohabit in the same tables/files.
- **Flags** possible regime relevance via **hints** (when enabled)—always with **false positive/negative** caveats.
- **Does not** replace customs/security legal frameworks or DPO workflow software.

## Partner opportunity

Integrators and compliance consultancies use this narrative for **port-adjacent** or **logistics hub** buyers who already speak “manifest + crew list” language and need a **first collision map** before funding a multi-year GRC programme.

## Product alignment (maintainers)

Stress-test **jurisdiction hints**, **collision** copy in reports, and **multilingual** token surfaces—without implying customs filing completeness. Maintainer sequencing: [docs/README.md](../README.md) *Internal and reference*.

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md)) — hub with other mid-market storyboards (law, accounting, pharma).
- [THE_WHY.md](../philosophy/THE_WHY.md) ([pt-BR](../philosophy/THE_WHY.pt_BR.md)) — evidence-over-theatre positioning (public-safe).
- [ADR 0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) — retention/evidence boundary in customs-adjacent contexts.
- [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md) ([pt-BR](../JURISDICTION_COLLISION_HANDLING.pt_BR.md))
- [MINOR_DETECTION.md](../MINOR_DETECTION.md) ([pt-BR](../MINOR_DETECTION.pt_BR.md)) — when crew or visitor data may include minors’ metadata
- [MAP.md](../MAP.md) ([pt-BR](../MAP.pt_BR.md))
- [ADR 0038](../adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md)

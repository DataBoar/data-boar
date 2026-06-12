# Plan: ADR governance lifecycle (ADR 0045 amendment)

<!-- plans-hub-summary: UMADR constitution — append-only Status history, Obsolete/Quarantined/Duplicate statuses, en_US ADRs; GitHub #803 -->

**Status:** Active
**Date:** 2026-06-09
**Authors:** Fabio Leitao
**Priority:** P0
**GitHub:** [#803](https://github.com/FabioLeitao/data-boar/issues/803)
**Related ADR:** [ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

[ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) is the repository
constitution for Architecture Decision Records. Issue **#803** enriches it in-place after
a real edge case (stale duplicate ADR file during Windows-to-Linux workstation migration) showed gaps in
Nygard/MADR defaults: no **Duplicate** status, mutable genesis date, and no explicit
**never delete** rule.

## Scope

| Track | Deliverable |
| ----- | ----------- |
| ADR | **ADR 0045** amendment (en_US, in-place): Status history, immutable Date, enum extension, locale, immutability |
| Tooling | **`scripts/inv-adr.ps1`** — parse `## Status` (compound statuses) + legacy fallback |
| Inventory | **`docs/adr/INVENTORY.txt`** regenerated |
| Plan | This file + **PLANS_TODO** row + **PLANS_HUB** sync |

**Out of scope:** Applying `Duplicate of ADR-NNNN` to the stale `0044-*.md` file; editing any other ADR body.

## Implementation checklist

| Phase | Task | Status |
| ----- | ---- | ------ |
| 1 | Enrich **ADR 0045** per #803 AC (dogfood Status history) | ✅ |
| 2 | Update **`inv-adr.ps1`** + inventory row regex in tests | ✅ |
| 3 | Regenerate **`INVENTORY.txt`** | ✅ |
| 4 | **`plans_hub_sync.py --write`** + **PLANS_TODO** entry | ✅ |
| 5 | **`./scripts/check-all.sh`** green; signed commit + PR `Closes #803` | ⬜ |

## Status lifecycle (summary)

- **`Date (UTC)`:** genesis, immutable.
- **`## Status`:** current state (inventory reads this).
- **`### Status history`:** append-only dated lines.
- **Never delete** ADR files; transition status only.
- **Locale:** ADRs are **en_US** only; see **`.cursor/rules/docs-pt-br-locale.mdc`**.

## UMADR manifesto

**UMADR** (Unified MADR) is the name for this repository's ADR constitution ([ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md)).
It is an **in-house extension** of [MADR](https://adr.github.io/madr/) and [Nygard (2011)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions),
not a community standard — deliberately small-team, **human-in-the-loop**.

### Origin (serendipitous)

The shape emerged from a **real migration edge case** (2026-06-09): a stale pre-0045 duplicate
of ADR 0044 resurfaced during primary-workstation migration churn, while the tracked constitution had
no status for "same decision, wrong file" and MADR's mutable **`date`** would have erased
genesis. Fixing hygiene without deleting history forced explicit lifecycle vocabulary.

### What **U** means (and does not)

- **Primary reading:** **U = Human-in-the-Loop** — one maintainer curates amendments;
  mutability is allowed when **recorded** in append-only Status history (dogfood on 0045).
- **Secondary resonance (not normative):** "Unified" MADR + Nygard in one named contract;
  "Unilateral" in the sense of solo-maintainer governance. Do **not** treat **U** as a
  fourth axis in the H/U/A/P priority taxonomy ([ADR 0055](../adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md)).

### Analogies (intuition, not law)

| UMADR concept | Rough analogy |
| ------------- | ------------- |
| Append-only Status history | VeraCrypt header chain / append-only audit log — past lines stay, new events append |
| **Quarantined** | Antivirus quarantine — suspicious file isolated until triage resolves to clean or remove |
| **Obsolete** | Prohibition repeal — the rule existed; context ended; no "successor statute" required |
| **Duplicate of ADR-NNNN** | Two copies of the same deed in the filing cabinet — one authoritative, one shredder fodder |
| Never delete ADR | Court record retention — vacate a ruling, do not burn the docket |

### Why prose lives here

The ADR body stays **concise en_US** for agents and CI. This plan section holds manifesto
and metaphor so [ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) remains
a constitution, not an essay.

## References

- [ADR 0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR 0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
- **ADR 0068** (temporary primary Linux workstation — edge-case context; may land via #801)
- GitHub [#803](https://github.com/FabioLeitao/data-boar/issues/803)

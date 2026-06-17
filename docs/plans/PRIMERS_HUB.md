# Primers hub — frameworks, norms, and regulations

<!-- plans-hub-summary: Central index of all primers — frameworks, norms, regulations -->

Educational **plan-tier** documents that explain how Data Boar aligns with external standards. They do **not** replace [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) (product configuration) or [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) (legal positioning).

**Navigation:** [docs/hubs/INDEX.md](../hubs/INDEX.md) · [AUDIENCE_GUIDE.md](../AUDIENCE_GUIDE.md) (compliance engineer trail)

---

## Privacy and data management

| Primer | Summary |
| ------ | ------- |
| [PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md](PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md) | ISO/IEC 27701, ISO/IEC 27018, NIST Privacy Framework |
| HEALTH_SECTOR_COMPLIANCE_PRIMER.md *(planned — #591)* | HIPAA/PHI, ANS, ANVISA, CFM |
| GLOBAL_PRIVACY_REGULATIONS_PRIMER.md *(planned — #600)* | PIPEDA, POPIA, APPI, Vietnam PDPD, FELCA |

## Governance and risk

| Primer | Summary |
| ------ | ------- |
| IT_GOVERNANCE_FRAMEWORKS_PRIMER.md *(planned — #629)* | ISO/IEC 38500, COBIT 2019 — EDM cycle; diagram companion [GOVERNANCE_ITSM_DIAGRAMS_SOURCE.md](GOVERNANCE_ITSM_DIAGRAMS_SOURCE.md) |
| ITSM_FRAMEWORKS_PRIMER.md *(planned — #630)* | ITIL 4, ISO/IEC 20000 — service practices mapping; same diagram companion |
| ITSM_GOVERNANCE_ALIGNMENT.md *(planned — #554)* | ITIL 4, ISO 38500, COBIT 2019, ISO 27014, ISO 20000 — alignment tables (product docs tier when promoted) |

## Audit and assurance

| Primer | Summary |
| ------ | ------- |
| SOC2_COMPLIANCE_PRIMER.md *(planned — #598)* | SOC 2 Privacy Trust Services Criteria |

## Financial sector

| Primer | Summary |
| ------ | ------- |
| FINANCIAL_SECTOR_COMPLIANCE_PRIMER.md *(planned — #590)* | PCI DSS v4.0, SOX, BACEN CMN 4.893/2021 |

## AI and emerging tech

| Primer | Summary |
| ------ | ------- |
| AI_COMPLIANCE_PRIMER.md *(planned — #592)* | EU AI Act, ISO/IEC 42001, NIST AI RMF |

## Technical / onboarding primers (`docs/primers/`)

Thematic knowledge transfer (KT) for integrators and contributors — distinct from the
compliance/framework primers above. Per [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md)
(amends [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md)) these live under
`docs/primers/` with a local index, and are surfaced here in the single central hub.

| Primer | Summary |
| ------ | ------- |
| [AI_EVOLUTION_PRIMER.md](../primers/AI_EVOLUTION_PRIMER.md) | AI history for integrators (winters, expert systems, ML/DL, LLMs — no hype) |
| [DECISION_RECORDS_PRIMER.md](../primers/DECISION_RECORDS_PRIMER.md) | ADR → MADR → UMADR onboarding |
| Local index | [docs/primers/INDEX.md](../primers/INDEX.md) |

## Related (not primers)

| Doc | Role |
| --- | ---- |
| [GOVERNANCE_ITSM_DIAGRAMS_SOURCE.md](GOVERNANCE_ITSM_DIAGRAMS_SOURCE.md) | Mermaid/tables companion for **#629** / **#630** (not a standalone primer) |
| [completed/PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md](completed/PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md) | Shipped doc-only alignment (27701 + FELCA narrative) |

---

## How to contribute (anti-drift)

1. Add or update `docs/plans/<NAME>_PRIMER.md` with a `<!-- plans-hub-summary: ... -->` line.
1. Register the row in **this hub** (active link only when the file exists).
1. Run `python scripts/plans_hub_sync.py --write` and `.\scripts\check-hubs.ps1` (or `./scripts/check-hubs.sh`).
1. Run `.\scripts\check-all.ps1` before merge.

Planned primers stay **plain text** in the table until the file lands — do not add broken markdown links.

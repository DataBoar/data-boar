# Pitch and executive decks — index

**Português (Brasil):** [INDEX.pt_BR.md](INDEX.pt_BR.md)

Audience-specific **two-page** narratives for workshops, procurement, and leadership briefings. They complement the product index in [docs/README.md](../README.md) and the role map in [AUDIENCE_GUIDE.md](../AUDIENCE_GUIDE.md). They stay **free of internal plan links** (see [ADR 0004](../adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).

## Decks (by role)

| Role | Deck | When to use |
| ---- | ---- | ----------- |
| Board, GM, COO, procurement sponsor | [PITCH_STAKEHOLDER.md](PITCH_STAKEHOLDER.md) | First conversation: value, shared responsibility, 30/60/90 outcomes |
| DPO, privacy counsel, compliance lead | [PITCH_DPO.md](PITCH_DPO.md) | Lawful basis, DSAR support, minors, multinational hints |
| CISO, security architect, GRC lead | [PITCH_CISO.md](PITCH_CISO.md) | Controls, **evidence automation**, integration posture; CFO-safe ranges; KPIs by source/session |
| CDO, Data Steward, senior data engineer | [PITCH_DATA_OFFICER.md](PITCH_DATA_OFFICER.md) | Inventory before GGD: DMBOK store/use, maturity of existing PII |
| CIO, IT manager, IT governance lead | [PITCH_IT_GOVERNANCE.md](PITCH_IT_GOVERNANCE.md) | Evaluate–Direct–Monitor with evidence, not policy-only |
| PMO, programme / project lead | [PITCH_PMO.md](PITCH_PMO.md) | Delivery cadence; risk by **configured source/session**; sprint/repo heatmap is GitHub [#677](https://github.com/DataBoar/data-boar/issues/677) |
| CFO, finance, procurement sponsor | [PITCH_CFO.md](PITCH_CFO.md) | Financial exposure; statutory % + cap; shared responsibility; no hardcoded vendor USD |
| CCO, General Counsel | [PITCH_COMPLIANCE_OFFICER.md](PITCH_COMPLIANCE_OFFICER.md) | Liability, audit trail, multi-regime inventory language, M&A DD — distinct from DPO |

## Planned decks (issues still open)

IT Governance ([#631](https://github.com/DataBoar/data-boar/issues/631)) and CDO ([#639](https://github.com/DataBoar/data-boar/issues/639)) already have decks in the table above; close those issues when their remaining AC is verified. No additional role decks are queued in this index beyond the shipped files.

## Related product docs (deeper than a deck)

| Topic | Link |
| ----- | ---- |
| One-page leadership brief | [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md) |
| Legal / DPO non-technical summary | [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) |
| Framework profiles and samples | [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) |
| Security posture (public) | [SECURITY.md](../SECURITY.md) |
| Use-case storyboards | [use-cases/USE_CASES_HUB.md](../use-cases/USE_CASES_HUB.md) |
| Concern-first navigation | [MAP.md](../MAP.md) |

## Language

- **English** files in this folder are canonical for integrators and international buyers.
- **pt-BR** mirrors use the `*.pt_BR.md` suffix.

## Maintenance

When README stakeholder boundaries or compliance samples change, refresh deck **claims** to match [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) and root [README](../README.md) *For decision-makers* — do not introduce deck-only legal promises.

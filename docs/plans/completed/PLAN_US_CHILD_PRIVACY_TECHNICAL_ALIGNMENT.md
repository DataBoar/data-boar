# Plan: U.S. child and minor privacy — technical mapping (samples + docs)

**Status:** Phase 1 complete (archived under `docs/plans/completed/`; later phases if any stay in PLANS_TODO / new plan rows).
**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md)

## Purpose

Give U.S. (and multi-jurisdictional) teams **config-first** artefacts to align discovery and report language with **technical and operational** questions that often arise in **DPO review**, **audit preparation**, **incident scoping**, or **court-ordered technical assistance**—without offering **legal advice**, **age verification**, or a claim that any scan **proves** COPPA, CPA, or state-law compliance.

This plan tracks **documentation and sample YAML only** unless a future phase explicitly adds product behaviour.

## Scope and boundaries

| In scope                                                                                                                                                                                                                     | Out of scope                                                             |
| --------                                                                                                                                                                                                                     | ------------                                                             |
| Optional `compliance-sample-*.yaml` profiles (regex, ML terms, recommendation overrides)                                                                                                                                     | Stating that Data Boar “complies with” COPPA, AB 2273, or Colorado rules |
| EN + pt-BR updates to **COMPLIANCE_FRAMEWORKS**, **compliance-samples README**, **README** pitch line, and a **short, careful** paragraph on **COMPLIANCE_AND_LEGAL** (external audience — **no** `docs/plans/` links there) | Platform design guidance, parental-consent UX, or litigation strategy    |
| Explicit disclaimers: **human/DPO/counsel review** remains required; **possible minor** / DOB heuristics **do not** equal verified child status                                                                              | Certification, FTC or state attestation language                         |

## Frameworks covered by samples (informational)

Samples **name** common U.S. reference points so teams can tag findings consistently. **Laws and rules evolve and vary by facts and venue**; maintainers do not warrant completeness or currentness of statutory citations in YAML comments.

1. **FTC COPPA (Children’s Online Privacy Protection Act and Rule)** — federal framing for operators of websites/services directed to children and certain collections from children under 13. Sample: [compliance-sample-us_ftc_coppa.yaml](../../compliance-samples/compliance-sample-us_ftc_coppa.yaml).
1. **California AB 2273 (Age-Appropriate Design Code Act)** — California statute; **applicability and enforcement have seen legal challenge**; sample is for **technical labelling** when organisations voluntarily map systems. Sample: [compliance-sample-us_ca_ab2273_caadca.yaml](../../compliance-samples/compliance-sample-us_ca_ab2273_caadca.yaml).
1. **Colorado Privacy Act (CPA) and Colorado Attorney General rules on consumers under 18** state-law framing for **known minors** and related processing constraints in reporting text. Sample: [compliance-sample-us_co_cpa_minors.yaml](../../compliance-samples/compliance-sample-us_co_cpa_minors.yaml).

**Interaction with built-in detection:** Continue to use product **minor / DOB** behaviour (see [MINOR_DETECTION.md](../../MINOR_DETECTION.md)) as configured; these samples add **norm tags and narrative** that legal/compliance stakeholders may ask for in U.S. threads.

## Implementation to-dos

| # | To-do                                                                                                   | Status |
| - | -----                                                                                                   | ------ |
| 1 | Add three compliance sample YAML files under `docs/compliance-samples/`.                                | ✅ Done |
| 2 | Extend **COMPLIANCE_FRAMEWORKS.md** and **.pt_BR.md** (table + short US subsection or cross-reference). | ✅ Done |
| 3 | Extend **compliance-samples/README.md** and **README.pt_BR.md**.                                        | ✅ Done |
| 4 | Add concise paragraph to **COMPLIANCE_AND_LEGAL.md** and **.pt_BR.md** (external-safe; no plan links).  | ✅ Done |
| 5 | Extend roadmap sentence in **README.md** and **README.pt_BR.md**.                                       | ✅ Done |
| 6 | Register plan in **PLANS_TODO.md** (status line, dependency row, optional “What to start next” note).   | ✅ Done |

## Future phases (optional, not committed)

- Narrow regex packs for common **schema labels** (e.g. parental/guardian columns) behind **opt-in** config to reduce noise.
- Report filter or sheet grouping for **minor-related** + **US norm tag** (only if customer demand is clear).
- Refresh samples if AG **final rules** or federal preemption landscape shifts materially.

## Conflict and placement

- **Depends on:** Nothing (additive docs + samples).
- **Conflicts with:** None.
- **Tests:** Existing `tests/test_compliance_samples.py` discovers new `compliance-sample-*.yaml` files automatically.

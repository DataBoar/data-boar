# PLAN: Compliance Expansion — Global Jurisdiction Coverage

<!-- plans-hub-summary: Roadmap for extending Data Boar compliance coverage to 20+ new global privacy jurisdictions across three priority groups. Covers YAML sample creation, regex/ML term enrichment, documentation, and sprint sequencing. Replaces ad-hoc per-jurisdiction notes. -->
<!-- plans-hub-related: PLAN_FERPA_AND_EDTECH_COMPLIANCE.md, PLAN_YAML_PLUGIN_SYSTEM.md -->

Status: Draft
Date: 2026-05-14
Authors: Fabio Leitao
Priority: H1
Tags: compliance, global, jurisdictions, privacy, yaml, expansion, gdpr, hipaa, pipl, ferpa, latam, apac, emea
Depends on: PLAN_YAML_PLUGIN_SYSTEM.md

---

## Motivation

Data Boar already covers a strong base of regulations (LGPD, EU GDPR, UK GDPR, PIPEDA, POPIA, APPI,
Singapore PDPA, Australia Privacy, Russia 152-FZ, India DPDP, CPRA, AB 2273, VCDPA, and others).
Expanding coverage to additional jurisdictions broadens the serviceable market, enables operators to
serve multinational clients, and strengthens Data Boar's positioning as a **global-first** privacy
inventory tool.

This plan tracks the **global jurisdiction expansion roadmap** in three priority groups, aligned with
the on-going geolocation enrichment series (A1–A8) and the new B-series slices.

---

## Series A — Geolocation enrichment backfill (in-progress)

These files already exist and are receiving the four-pattern geolocation geometry from
`compliance-sample-us_va_vcdpa.yaml` as the canonical reference:

| Slice | File | Status |
|---|---|---|
| A1 | `compliance-sample-india_dpdp.yaml` | ✅ Done (commit `0e953fa`) |
| A2 | `compliance-sample-popia.yaml` | ✅ Done (commit `9b4c3c5`) |
| A3 | `compliance-sample-turkey_kvkk.yaml` | ✅ Done |
| A4 | `compliance-sample-uae_pdpl.yaml` | ✅ Done |
| A5 | `compliance-sample-new_zealand_privacy.yaml` | ✅ Done |
| A6 | `compliance-sample-philippines_dpa.yaml` | ✅ Done |
| A7 | `compliance-sample-us_co_cpa_minors.yaml` | ✅ Done |
| A8 | `compliance-sample-us_ftc_coppa.yaml` | ✅ Done |

---

## Group 1 — Priority (large markets, high probability clients)

| Regulation | Jurisdiction | YAML file (target) | Why prioritize |
|---|---|---|---|
| **HIPAA / PHI** | US — Health | `compliance-sample-us_hipaa_phi.yaml` | P0 vertical: pharma, hospitals, insurance. Core in code; YAML overrides needed. |
| **China PIPL** | China | `compliance-sample-china_pipl.yaml` | 1.4 B people; data localisation obligations; any China-adjacent client |
| **South Korea PIPA** | South Korea | `compliance-sample-south_korea_pipa.yaml` | Top-15 economy; PIPA stricter than GDPR on biometrics; K-diaspora cloud ops |
| **FERPA** | US — Education | `compliance-sample-us_ferpa.yaml` | EdTech / EAD vertical; K-12, HEI, LMS exports; see `PLAN_FERPA_AND_EDTECH_COMPLIANCE.md` |
| **Quebec Law 25** | Canada (Québec) | `compliance-sample-canada_qc_law25.yaml` | Stricter than PIPEDA; in force since 2023; francophone market |
| **Mexico LFPDPPP** | Mexico | `compliance-sample-mexico_lfpdppp.yaml` | Largest LATAM economy after Brazil; shared language / professional services |
| **Thailand PDPA** | Thailand | `compliance-sample-thailand_pdpa.yaml` | Southeast Asia hub; in force 2022 |
| **Indonesia PDP** | Indonesia | `compliance-sample-indonesia_pdp.yaml` | 270 M people; law enacted 2022 |

---

## Group 2 — Medium-term (specific verticals or strategic regions)

| Regulation | Jurisdiction | YAML file (target) | Notes |
|---|---|---|---|
| **Vietnam PDPD** | Vietnam | `compliance-sample-vietnam_pdpd.yaml` | Decree 13/2023; cross-border consent; Southeast Asia supply chain |
| **Malaysia PDPA 2024** | Malaysia | `compliance-sample-malaysia_pdpa.yaml` | 2024 amendment converges towards GDPR |
| **Ukraine PDP (Law 2297-VI)** | Ukraine | `compliance-sample-ukraine_pdp.yaml` | GDPR-convergent; IPN (10-digit taxpayer ID); EU candidate status |
| **Egypt Law 151/2020** | Egypt | `compliance-sample-egypt_pdpl.yaml` | First African country with full national PDP law |
| **Argentina PDPA (reform)** | Argentina | `compliance-sample-argentina_pdpa.yaml` | File exists (basic); 2024 reform bill in progress; LATAM expansion |
| **Colombia Ley 1581** | Colombia | `compliance-sample-colombia_ley1581.yaml` | Similar to LGPD; professional services LATAM |
| **Chile Law 21.719** | Chile | `compliance-sample-chile_pdp.yaml` | Constitutionalised; new comprehensive law enacted 2024 |
| **COPPA 2.0 / FTC Rule** | US — Children | Update `compliance-sample-us_ftc_coppa.yaml` | FTC rulemaking in progress; complements AB 2273 and FERPA |

---

## Group 3 — Radar (no urgent YAML; track for legislative developments)

| Regulation | Jurisdiction | Notes |
|---|---|---|
| **NY SHIELD Act** | US — New York | Strengthens breach notification; layer over federal |
| **Texas TDPSA** | US — Texas | Enacted 2023; in force Jul 2024 |
| **Connecticut CTDPA** | US — Connecticut | In force Jan 2023 |
| **Montana MTCDPA** | US — Montana | In force Oct 2024 |
| **Iowa ICDPA** | US — Iowa | In force Jan 2025 |
| **Pakistan PDP Bill** | Pakistan | Parliamentary process ongoing |
| **Nigeria NDPR + 2023 Guidelines** | Nigeria | NDPR 2019; amended guidelines 2023; growing enforcement |
| **Kenya Data Protection Act** | Kenya | 2019; actively enforced |
| **Sri Lanka PDP Bill** | Sri Lanka | Draft stage |
| **Bangladesh PDP Bill** | Bangladesh | Draft stage |
| **Lebanon PDPL** | Lebanon | Law 81/2018 (partial); regulatory body pending |
| **Bahrain / Qatar / Kuwait PDPL** | Gulf (GCC) | Regional frameworks; co-applicable with UAE PDPL |

---

## YAML creation standard

All new YAML samples **must** follow the canonical geometry established across the existing samples:

1. **Header comments**: legal scope, detection thresholds note, regex design rationale, audience note.
2. **Regex section**: national identifier patterns + four precise geolocation patterns (canonical names from `compliance-sample-us_va_vcdpa.yaml`).
3. **ML terms**: minimum 30 entries; EN + native language where regulation is non-English; cover special categories, cross-border transfer, consent, rights.
4. **`recommendation_overrides`**: one entry per distinct `norm_tag`; include `base_legal`, `risk`, `recommendation`, `priority`, `relevant_for`.
5. **Tests**: `tests/test_compliance_samples.py` must pass with ≥2 collected items per file.
6. **Docs**: update `compliance-samples/README.md`, `COMPLIANCE_FRAMEWORKS.md`, and their pt-BR mirrors.

---

## Sprint sequencing (proposed)

```
Sprint A (done):  A1 India → A2 POPIA → A3 Turkey → A4 UAE → A5 NZ → A6 PH → A7 CO → A8 COPPA
Sprint B (next):  B1 Ukraine ✅ → B2 HIPAA → B3 FERPA → B4 China PIPL → B5 Korea PIPA
Sprint C:         B6 Mexico → B7 Thailand → B8 Indonesia → B9 Quebec Law 25
Sprint D:         Group 2 remaining (Vietnam, Malaysia, Argentina reform, Colombia, Chile)
Sprint E:         Group 3 monitoring + ML/DL backfill
```

---

## Acceptance criteria (overall plan)

- [ ] All A-series slices (A3–A8) committed with four-pattern geolocation and expanded ML terms
- [ ] All Group 1 YAML files created (B1–B8)
- [ ] All Group 2 YAML files created
- [ ] `COMPLIANCE_FRAMEWORKS.md` and `README.md` tables updated for each new file
- [ ] pt-BR mirrors updated for each documentation change
- [ ] `plans_hub_sync.py --check` passes after each sprint
- [ ] `tests/test_compliance_samples.py` green for all new files

---

## Related docs

- [`docs/COMPLIANCE_FRAMEWORKS.md`](../COMPLIANCE_FRAMEWORKS.md) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md))
- [`docs/compliance-samples/README.md`](../compliance-samples/README.md) ([pt-BR](../compliance-samples/README.pt_BR.md))
- [`docs/plans/PLAN_FERPA_AND_EDTECH_COMPLIANCE.md`](PLAN_FERPA_AND_EDTECH_COMPLIANCE.md)
- [`docs/plans/PLAN_YAML_PLUGIN_SYSTEM.md`](PLAN_YAML_PLUGIN_SYSTEM.md)

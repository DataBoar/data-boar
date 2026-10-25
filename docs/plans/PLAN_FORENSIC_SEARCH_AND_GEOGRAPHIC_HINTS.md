# Plan: Forensic search and geographic breadcrumb hints (breach investigation + intra-Brazil jurisdiction)

**Status:** Pending
**Date:** 2026-05-13
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0025, ADR-0048, PLAN_COMPLIANCE_EVIDENCE_MAPPING.md

<!-- plans-hub-summary: Two adjacent product capabilities surfaced by commercial prospects: (1) targeted breach forensics scan for a specific identifier across all data sources; (2) intra-Brazil geographic breadcrumb detection for multi-jurisdiction incident analysis. Both fit the existing chassis without new connectors. -->
<!-- plans-hub-related: PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md, PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md -->

## Context — how these use cases emerged

Two concrete requests from potential commercial partners and talent pool candidates surfaced
in May 2026:

1. **Breach forensics ("where is this CPF?"):** A prospective consultant asked whether
   Data Boar can search for a *specific* identifier (e.g., a leaked CPF, a customer email)
   across all configured data sources to help determine where the data lives, who had
   access, and through which path it might have leaked.

2. **Intra-Brazil jurisdiction breadcrumbs:** A legal/compliance scenario where a single
   incident spans multiple Brazilian states and courts (TJ estaduais). Example: company
   registered in BH, PEP partner from RJ living in BSB, incident during vacation in
   Porto Seguro, client from Campinas served by SP branch, Porto Alegre connection.
   Can Data Boar surface the geographic breadcrumbs that a legal analyst or DPO would
   need to map the jurisdictional exposure?

Both capabilities fit the existing product chassis with configuration — not new code.

---

## Use case 1: Targeted breach forensics

### What Data Boar can do today (use case 1) using a custom `regex_overrides`
entry in config with high sensitivity and a unique `norm_tag`. Example:

```yaml
sensitivity_detection:
  regex_overrides:
    - pattern: "123\\.456\\.789\\-09"
      label: BREACH_TARGET_CPF
      norm_tag: BREACH_INVESTIGATION
      sensitivity: CRITICAL
targets:
  - name: "AllSources"
    type: filesystem
    path: "/data"
```

This turns every Data Boar connector into a forensic search tool: scan all configured
sources and flag every occurrence of the target identifier. Works across filesystem,
SQL databases, MongoDB, SharePoint, REST APIs — any configured connector.

### What is missing

1. **Positioning:** This capability is not documented as a use case. DPOs and forensic
   consultants would not know to use it this way.
2. **Cross-source correlation report:** The current report shows findings per source but
   does not produce a "timeline of appearances" or "access graph" for a specific
   identifier. That would require a post-processing step.
3. **Operator guide:** A "how to configure a breach investigation scan" guide does not
   exist.

### Slices (use case 1) `docs/compliance-samples/breach-forensics-template.yaml` with documented regex override pattern for targeted identifier search; linked from USAGE.md |
| **2 — Positioning** | README + DECISION_MAKER_VALUE_BRIEF | Add "breach forensics / data leak investigation" to use case list; non-legal language; "find where a specific piece of data lives across your data soup" |
| **3 — Cross-source report** | Post-scan correlation | Script or report sheet that groups findings by identifier pattern across all sources — timeline-style; H3 complexity |

---

## Use case 2: Intra-Brazil geographic breadcrumbs

### What Data Boar can do today (use case 2) regulatory framework signals. For
intra-Brazil geographic forensics, the same pattern-detection infrastructure can
surface geographic indicators:

| Indicator | Pattern | Coverage today |
| --------- | ------- | -------------- |
| Brazilian area codes (DDD) | `\(21\)`, `\(31\)`, `\(11\)`, `\(61\)`, `\(19\)`, `\(51\)`, `\(73\)` | Via phone regex — detects presence, not geography |
| CEP range by state | `01000-000` to `09999-999` = SP capital; `20000-000` to `28999-999` = RJ, etc. | Not mapped today |
| CNPJ + state | The 3rd–5th digits of a CNPJ encode the filing state | Not decoded today |
| PEP terminology | `"Pessoa Politicamente Exposta"`, `"PEP"` in context | Partial — ML would flag, not structured |
| Court identifiers | `"TJ/SP"`, `"TJ/RJ"`, `"TJ/MG"`, `"STJ"`, `"STF"` | Regex override, not default |

### Positioning (honest scope)

Data Boar **finds breadcrumbs** — it does not draw legal conclusions. The output
("this file contains a Campinas DDD, a RJ CNPJ, and a PEP reference") is the
**structured triage signal** that a legal analyst uses to decide which documents
to review and which jurisdictions to flag for counsel.

This is consistent with the existing positioning: *technical inventory and triage,
not a legal-conclusion engine* (ADR-0025).

### Slices (use case 2) Area code → state mapping | `compliance-samples/` entry with DDD regex overlays and `norm_tag: GEO_BR_<STATE>` labels; operator can combine with LGPD scan to see geographic spread |
| **2 — CNPJ state decoder** | Extract filing state from CNPJ structure | Detector enhancement: when CNPJ is found, decode digits 3–5 → Brazilian state code → add `GEO_BR_CNPJ_<UF>` norm_tag to the finding |
| **3 — PEP + court term detector** | Named entity proximity | Config template with PEP terminology + Brazilian court abbreviations as sensitivity triggers; labels for `PEP_REFERENCE`, `COURT_BR_<TJ>` |
| **4 — Cross-finding geographic report** | Multi-jurisdiction summary | Post-scan report section: "geographic exposure map" — list of states/jurisdictions found across all sources, by norm_tag |
| **5 — Jurisdiction conflict hint** | Multi-TJ incident flag | When multiple `GEO_BR_*` norm_tags appear in the same session AND the data involves LGPD-sensitive fields, emit a `JURISDICTION_TENSION_BR` aggregate hint for operator review |

---

## Acceptance criteria (Slice 1, both use cases)

- [ ] `docs/compliance-samples/breach-forensics-template.yaml` exists and is tested
  by `tests/test_compliance_samples.py`.
- [ ] README "Typical scenarios" includes "breach investigation / targeted identifier
  search".
- [ ] `docs/compliance-samples/lgpd-intra-brazil-geo.yaml` exists with at least 5 DDD
  regex overrides and corresponding `GEO_BR_*` norm_tags.
- [ ] Both templates produce findings on the `tests/data/bench/` corpus (confirmed
  manually during development).

## Related plans and ADRs

- [ADR-0025 — Compliance positioning: evidence and inventory, not a legal-conclusion engine](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)
- [ADR-0048 — Operator-facing taxonomy and naming contract preservation](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- [PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md](PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md)
- [PLAN_COMPLIANCE_EVIDENCE_MAPPING.md](PLAN_COMPLIANCE_EVIDENCE_MAPPING.md)

# Vision: Evidence First

**Status:** Strategic doctrine — non-binding product direction  
**Horizon:** Foundational invariant across all Data Boar capabilities  
**Parent vision:** [Data Exposure Intelligence](VISION_DATA_EXPOSURE_INTELLIGENCE.md)  
**Related work:** #1169, #1525, #1527, #2273, #2342, ADR-0017

## Purpose

Evidence First is the product invariant that every Data Boar claim must be traceable to the evidence that supports it, with provenance, integrity, scope, time and limitations preserved.

It applies to discovery, classification, identity correlation, access inventory, exposure analysis, risk aggregation, reporting and governance assist.

Evidence is not an export format added at the end. It is part of the data model and the contract for every conclusion.

## The claim-to-evidence chain

Every material output should be traceable through a chain such as:

1. **Declared scope:** what source, target and population were intended to be examined.
2. **Acquisition attempt:** which connector operation was attempted, under which configuration and capability.
3. **Source response:** what the source actually returned or asserted.
4. **Observation:** the normalized record, retaining source-native values and provenance.
5. **Derivation:** the deterministic rule, correlation or transformation applied.
6. **Finding/profile:** the conclusion, reason codes and contributing evidence references.
7. **Coverage state:** what was reached, partial, inaccessible, unsupported or not assessed.
8. **Presentation:** the claim shown to an operator, including uncertainty and limitations.

A downstream claim must not be stronger than its weakest material dependency.

## Minimum evidence attributes

The exact schema is implementation-specific, but evidence should carry or reference the following attributes where applicable:

- stable evidence and observation identifiers;
- source, tenant/domain and target identifiers;
- connector name/version and capability identifier;
- run/execution identifier and relevant configuration version;
- source event/modified timestamp when available;
- collection timestamp and clock/ordering caveats;
- original source value or source-native reference;
- normalized representation and normalization version;
- operation outcome and coverage state;
- provenance chain and derivation/rule version;
- integrity digest or signed-manifest reference where supported;
- limitations, exclusions, errors and unresolved references;
- retention/custody metadata consistent with local policy.

Do not fabricate source timestamps, stable identifiers, signatures or integrity guarantees when the source or execution path does not provide them.

## Observation is not inference

Data Boar must label epistemic status explicitly:

| Status | Meaning |
|---|---|
| Observed | Directly collected from a source under a documented operation |
| Source asserted | Declared by the source; not independently verified |
| Deterministically derived | Reproducible result over identified inputs |
| Inferred candidate | Evidence-backed hypothesis requiring qualification or review |
| Unknown | Evidence is insufficient to resolve the question |
| Partial | Relevant acquisition or analysis completed only in part |
| Unsupported | Required source capability or semantics are unavailable |
| Not assessed | The relevant operation or evaluation did not occur |
| Conflicting | Available evidence disagrees |
| Stale | Evidence is outside the applicable freshness policy |

A user interface, API or report must not erase these distinctions for convenience.

## Coverage is evidence

Coverage Attestation describes the boundary of what the run can support. It must distinguish declared, attempted, reached, partially reached, inaccessible, unsupported and not-assessed scope.

Important consequences:

- A connector being installed does not prove a source was reached.
- A successful authentication does not prove all resources were enumerated.
- An empty result is meaningful only when the relevant scope was actually and successfully enumerated.
- A source not reached produces no inferred findings.
- Partial enumeration must remain partial in all downstream rollups.
- Target-level outcomes must not disappear inside run-level success summaries.

Coverage reports should expose their eligible population and counting rules. Percentages without denominators and terminal-state definitions are not evidence.

## Derived claims and explainability

A deterministic result should identify:

- the input observation/evidence references;
- the rule or algorithm identifier and version;
- relevant configuration and thresholds;
- reason codes or derivation trace;
- unresolved inputs and excluded scope;
- output state, including abstention where inputs are insufficient.

Risk aggregation must be reversible to underlying findings. Correlation must preserve ambiguous and unresolved links. An exposure profile must not invent a numeric score when required inputs are missing or uncalibrated.

## Integrity, custody and reproducibility

Evidence custody remains local by default. On-premises and air-gapped operation must preserve the ability to collect, retain, inspect and verify evidence without mandatory external services.

Where integrity mechanisms are used, their scope and guarantees must be explicit. A digest detects changes relative to a trusted digest; it does not by itself establish source authenticity. A signature establishes a relationship to a signing key; it does not prove the underlying source assertion was true.

Reproducibility requires retaining or referencing the rule/configuration versions and evidence inputs necessary to reconstruct a derived result, subject to retention and privacy constraints.

## Reporting contract

Reports should make it easy to answer:

- What exactly was examined?
- What was not examined, and why?
- Which source observations support this statement?
- Which parts are source assertions versus Data Boar derivations?
- When was the evidence collected, and how stale might it be?
- Which rule/version produced the result?
- What assumptions, exclusions or conflicts remain?
- What conclusions are explicitly not supported?

Reports must not imply legal compliance, certification, effective access, breach impact or complete coverage without evidence appropriate to that exact claim.

## Doctrine tests

A feature is inconsistent with Evidence First if it:

- emits a material claim without a traceable evidence path;
- silently upgrades inference to observation;
- hides partial, inaccessible, unsupported or not-assessed scope;
- treats missing records as proof of absence;
- drops provenance or source semantics during normalization;
- produces non-reproducible derived risk without rule/version references;
- exports evidence outside the configured custody boundary;
- uses an integrity term more strongly than the implemented guarantee supports.

**The governing rule: no claim without evidence, no evidence without provenance, and no coverage claim without an explicit boundary.**

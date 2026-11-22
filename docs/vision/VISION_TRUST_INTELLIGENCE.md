# Vision: Trust Intelligence

**Status:** Strategic doctrine — non-binding product direction
**Horizon:** Emerges after evidence, coverage and source semantics are mature
**Parent vision:** [Data Exposure Intelligence](VISION_DATA_EXPOSURE_INTELLIGENCE.md)
**Related work:** #1169, #1525, #1527, #2342, #2343, #2344, #2346, ADR-0017

## Purpose

Trust Intelligence is the discipline of making Data Boar's conclusions inspectable: what was observed, what was derived, what remains unknown, how complete the evidence is, and which limitations constrain the conclusion.

It does not mean assigning a universal numerical trust score. Trust is a property earned through evidence quality, provenance, coverage honesty, reproducibility and explicit abstention—not a label produced by an opaque formula.

Trust Intelligence answers:

> What supports this conclusion, how strong is that support, what is missing, and what must we not conclude?

## Trust is multidimensional

The product must not collapse distinct dimensions into one score:

| Dimension | Question | Example evidence |
|---|---|---|
| Provenance | Can the observation be traced to its source and collection context? | Source ID, connector version, run ID, timestamp |
| Integrity | Can evidence alteration be detected? | Digest, signed manifest, integrity verification |
| Coverage | What portion of declared and eligible scope was actually reached? | Declared/attempted/reached/partial/inaccessible states |
| Freshness | How old is the observation relative to its source and collection time? | Source timestamp, collection timestamp, staleness policy |
| Semantic fidelity | Were source meanings preserved during normalization? | Native permission type, principal namespace, source assertion |
| Reproducibility | Can the result be reconstructed from evidence and versioned rules? | Rule version, configuration reference, evidence references |
| Correlation quality | How reliable are joins and inferred relationships? | Stable identifiers, explicit mappings, unresolved/ambiguous counts |
| Explainability | Can a reviewer understand why a conclusion was emitted? | Reason codes, contributing observations, limitations |

These dimensions may be reported independently. A single composite must not conceal a weak dimension behind a strong one.

## Evidence states and epistemic boundaries

Data Boar must distinguish:

- **Observed:** directly returned or measured by the source under a documented operation.
- **Source asserted:** a statement or label supplied by the source, not independently verified by Data Boar.
- **Deterministically derived:** a reproducible transformation or rule over identified inputs.
- **Inferred candidate:** a hypothesis supported by evidence but not directly established.
- **Unknown:** the available evidence does not resolve the question.
- **Partial:** only part of the relevant scope or relationship was observed.
- **Unsupported:** the connector/source does not expose the required capability or semantics.
- **Not assessed:** the operation was not performed or the required input was not evaluated.
- **Conflicting:** evidence sources disagree and the conflict remains unresolved.
- **Stale:** evidence exists but falls outside a declared freshness policy.

These states are not interchangeable. In particular, unknown, unsupported, partial and not assessed must never silently map to a favorable or low-risk result.

## Confidence, risk and coverage are separate

Risk, confidence and coverage answer different questions:

- **Risk** expresses the significance of a condition under a documented rule or model.
- **Confidence** expresses the strength of support for a specific conclusion.
- **Coverage** expresses how much of the relevant declared/eligible scope was actually observed.

A high-risk observation may have low confidence or incomplete coverage. A low-risk result over a narrow scope does not imply that the wider estate is low risk.

ADR-0017's quasi-identification risk/confidence contract remains distinct from any future Exposure Profile. New exposure semantics must not overload existing fields or silently change their meaning.

## Measurement before scoring

Any aggregate indicator requires:

1. a precise definition and intended decision use;
2. numerator, denominator and eligible population;
3. source, observation time, freshness and version;
4. explicit handling of missing, conflicting, stale and unsupported inputs;
5. representative positive and negative fixtures;
6. ground truth where available;
7. false-positive, false-negative and abstention measurements;
8. sensitivity analysis and reviewer agreement;
9. a documented threshold policy and versioned change history.

Until these exist, report the underlying dimensions and evidence rather than manufacturing a score.

## Trust Score is deferred

A universal Trust Score is not a current product requirement. It may be reconsidered only if a concrete user decision cannot be served by separate evidence dimensions and if calibration demonstrates that aggregation improves rather than obscures interpretation.

No score may imply legal compliance, certification, breach impact, absence of risk or complete discovery.

## Trust in identity and access relationships

Identity and access evidence requires special care:

- Namespace identifiers by source, tenant and identity domain.
- Never join principals by display name alone.
- Preserve unresolved, cyclic, stale and conflicting membership relationships.
- Distinguish direct grants, inherited permissions, group membership, sharing links and source-specific role assignments.
- An observed grant or membership edge does not prove effective authorization.
- Effective reachability, where computed, must be labeled as a deterministic analysis under stated assumptions—not as proof of successful access.
- Audience or blast-radius estimates must disclose incomplete traversal and excluded populations.

## Human accountability

Ownership inference is a candidate for review, not a fact. Preserve source-declared owner, inferred owner candidate, evidence, confidence/limitations and unknown as separate states.

Human acceptance, exception or accountability decisions must remain attributable and evidence-linked. Trust Intelligence does not autonomously accept risk or determine legal responsibility.

## Doctrine tests

A design violates this vision if it:

- emits a composite score without documented semantics and calibration;
- treats missing evidence as evidence of safety;
- conflates confidence with coverage or risk;
- presents inferred ownership as declared ownership;
- describes observed permissions as proven effective access;
- hides stale, conflicting or partial observations;
- makes a compliance or certification claim from technical inventory alone.

## Trust is not asserted by Data Boar. It is made inspectable.

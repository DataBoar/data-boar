# PLAN: Data Exposure Intelligence (1.9+)

<!-- plans-hub-summary: Evidence-first data exposure intelligence: discover data, understand observed access relationships, prioritize explainable exposure, and prove coverage. -->
<!-- plans-hub-related: PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md, PLAN_MULTIFRAMEWORK_OVERLAY.md -->

**Status:** Proposed strategic plan; staged and evidence-gated
**Date:** 2026-11-22
**Strategic umbrella:** [#2342](https://github.com/DataBoar/data-boar/issues/2342)

## Product thesis

> Data Boar helps organizations discover where their data exists, understand who may be able to reach it, measure observable exposure, and produce auditable evidence of coverage and risk.

**Positioning:** Data Exposure Intelligence
**Progression:** **DISCOVER → UNDERSTAND → PRIORITIZE → PROVE**

| Question | Capability | Evidence boundary |
|---|---|---|
| Where does data exist? | Data Soup / discovery and connectors | Direct observations and source assertions remain distinct |
| Who or what may reach it? | Identity, resource and access inventory; logical Exposure Graph | Observed grants and membership do not prove successful or effective access |
| Which exposure deserves review? | Risk Intelligence / exposure profiles | Deterministic prioritization; unknown is never silently low |
| What can we prove? | Evidence, provenance and Coverage Attestation | Declared, attempted, reached, partial, inaccessible, unsupported and unassessed scope |

This is a product-direction statement, not a claim that every connector currently exposes permissions or that Data Boar calculates effective access in every target system.

## Category and competitive boundaries

Data Exposure Intelligence is the proposed category. Data Boar should not become a clone of a broad DSPM/data-governance suite or a workflow-heavy GRC/ITSM platform.

| Adjacent category | Learn from | Do not become |
|---|---|---|
| Data discovery/catalog (e.g. BigID) | Classification vocabulary, asset inventory, useful metadata | Heavyweight enterprise catalog or broad governance workflow suite |
| Privacy operations (e.g. OneTrust) | Business-readable privacy and risk language | Consent, questionnaire and policy-workflow system |
| DSPM/exposure (e.g. Thales CipherTrust) | Exposure context and prioritization | Cloud-only product or assume every access plane is observable |
| RiskOps/GRC (e.g. Archer, MetricStream, AuditBoard, LogicGate) | Executive accountability and risk aggregation | Control questionnaire, ticketing, approval or workflow engine |
| SIEM/EDR | Clear boundary between data posture and security telemetry | Threat detection, endpoint response or behavioral monitoring |

These are positioning boundaries, not a current competitive feature audit. Vendor capabilities vary by product, edition and deployment; external claims require separate, current market research before publication.

**Differentiation hypothesis:** Data Boar connects heterogeneous discovery with source-aware access context and coverage/evidence honesty, while remaining deployable on-premises and in constrained or air-gapped environments.

## Five product pillars

1. **Data Soup — discover.** Modular ingestion across filesystems, network shares, databases, business systems, collaboration platforms, cloud and legacy sources.
2. **Exposure Graph — understand.** A logical, source-aware model of resources, identities, groups, grants, links and relationships. This is a data model, not a graph-database commitment or a requirement for a graph-navigation UI in 1.9.
3. **Risk Intelligence — prioritize.** Deterministic, explainable exposure profiles and, later, aggregation; outputs remain reversible to underlying findings and evidence.
4. **Coverage Attestation — prove the boundary.** Show declared, attempted, reached, partially reached, inaccessible, unsupported and not-assessed scope. Unreached sources produce no inferred findings.
5. **Evidence First — prove each claim.** Preserve provenance, timestamps, source semantics, limitations, integrity and reproducibility. Claims must not exceed observed evidence.

## Architectural invariants

- On-prem-first, air-gap-capable, local custody; no external egress of collected data/evidence.
- Deterministic-first; no LLM dependency in discovery, correlation, scoring, evidence generation or governance decisions.
- Read-only by default. No permission changes, remediation, retention enforcement, workflow execution or customer-environment mutation.
- Distinguish observed facts, source assertions, deterministic correlations, inferred candidates, unknown, unsupported and not-assessed states.
- Preserve source-native identifiers and namespace them by source/tenant/domain. Never join identities by display name alone.
- Directory membership or ACL metadata does not prove effective authorization or successful access.
- Least-privilege credentials. Additional scopes, APIs or data-plane probes require explicit opt-in and documented justification.
- Bounded pagination, retries, graph traversal, memory, attachment sizes and query budgets; cycle-safe traversal and explicit partial results.
- Every risk/profile result is traceable to contributing findings, source observations, rule version and known limitations.
- Technical evidence and review signals, not legal conclusions or compliance certification.

## Staged roadmap (indicative, not calendar commitment)

### Stage A — Foundation completion

Stabilize Data Soup and evidence/coverage contracts before expanding the intelligence layer. Reuse #1667, #1169, #1527, #2273, connector research #2326–#2341, and existing run-manifest, evidence-envelope, integrity and provenance contracts.

Exit evidence: source capability matrices; declared-vs-reached states; target-level terminal outcomes; provenance; bounded/resumable ingestion; local-custody tests; synthetic fixtures; explicit connector limitations.

### Stage B — Exposure foundation

The only initial 1.9 capability candidates are the following three contract/specification slices. They are not unconditional release commitments; implementation must pass the dependency gates below.

1. **Identity inventory contract:** normalize source-aware identity and group records while preserving provider semantics and unresolved/cyclic/partial edges. Connector acquisition remains in #2327 and the contract is #2343.
2. **Resource/access inventory contract:** represent resources, principals, grants/permissions, links, source, observation time and limitations. Reuse #1083 and connector-native permission metadata; do not imply universal ACL coverage. Contract: #2344.
3. **Exposure Profile v1 specification:** only after the first two contracts are sufficiently stable. Define dimensions, missing-value semantics, rule versioning, confidence/coverage presentation and calibration before selecting a formula. Specification: #2346.

#### Release-scope guardrails

- The 1.9 candidate scope is Identity Inventory, Access Inventory and Exposure Profile v1, with Data Soup and Coverage Attestation as prerequisites—not six independent feature epics.
- The Exposure Graph is a logical model and traceability structure in this increment. A graph browser, visualization or graph database is not part of the 1.9 definition of done.
- Risk aggregation and Blast Radius remain later-stage capabilities. They require validated identity/access semantics, cycle-safe traversal, explicit unknowns, reproducible calculations and curated evaluation fixtures.
- Governance Assist, ownership inference, risk acceptance workflows, approvals, ticketing and remediation remain deferred.
- HTML reports and JSON export should reuse existing reporting/export infrastructure. First verify actual gaps; do not create a parallel reporting subsystem merely to satisfy a proposal.
- Connector acceptance is source-specific. M365 SharePoint/OneDrive, SMB, local filesystem and object storage do not share a universal identity or ACL model. Each connector must declare exactly what it observes and what it cannot establish.

#### Dependency gates (must pass before implementation is promoted)

| Gate | Required evidence | If not met |
|---|---|---|
| G0 — Source capability | Connector capability declaration, supported scopes, source semantics, rate/volume limits and explicit unsupported states | Keep the source out of the evaluated population; do not infer coverage |
| G1 — Identity contract | Stable source/tenant-namespaced IDs, provenance, membership semantics, unresolved references, cycle handling and partial enumeration tests | Do not claim a consolidated or complete identity inventory |
| G2 — Access contract | Resource/principal identity, direct/inherited/link semantics where exposed, source timestamp, provenance and limitations | Do not claim effective access or universal ACL normalization |
| G3 — Exposure Profile | Versioned deterministic rules, explicit missing-value/abstention behavior, separate risk/confidence/coverage, reproducibility and curated calibration results | Emit not-assessed/partial/unsupported; do not manufacture a numeric score or rank |
| G4 — Reporting | Traceable profile/evidence references and coverage limitations; reuse verified existing report/export paths | Do not add new reporting infrastructure without a demonstrated gap |

### Stage C — Risk intelligence (post-foundation)

- Reversible, explainable aggregation of findings into reviewable risk candidates.
- Deterministic evidence-linked narratives, including unknowns and conflicting evidence.
- Bounded potential audience/reachability analysis only after identity and access semantics are validated.
- Estimated reachability is not actual incident impact or number of affected people.

Risk Aggregation and Blast Radius are separate capabilities with separate validation requirements. They must not be bundled into the 1.9 foundation merely because they share the Exposure Graph model.

### Stage D — Governance assist

Later 1.9.x or subsequent planning, after evidence/risk contracts are stable:

- Distinguish source-declared owner, inferred ownership candidate and unknown.
- Human-controlled risk acceptance/exception records with rationale, scope, accountable person, timestamps, expiry/review date and evidence references.
- Accountability reporting without becoming a workflow/ticketing platform.
- No automatic acceptance, legal determination or remediation.

## Exposure Profile decision gates

Potential dimensions: (a) sensitivity evidence, keeping Data Boar detections distinct from source-declared labels; (b) observed reachability/access breadth, using only supported source semantics; and (c) audience scope, preserving unknown and incomplete membership.

Do not adopt a multiplicative Sensitivity × Reachability × Audience formula (or another composite) until there are documented scales/normalization, explicit missing-value semantics, versioned deterministic rules, separate risk/confidence/coverage outputs, curated synthetic calibration fixtures, and measurements of false positives, false negatives, abstention and reviewer agreement.

Do not conflate an exposure profile with the quasi-identification risk_score/confidence_score contract in ADR-0017. Exposure Profile v1 may initially be a categorical, reason-coded assessment; a numeric score is not a prerequisite.

## Logical Exposure Graph — not a database mandate

The first graph is a conceptual entity/relationship model reconstructible from source evidence. Candidate nodes include resources, identities, groups, grants, links, findings and source systems; candidate edges include membership, grant, ownership assertion, containment and lineage.

Every edge needs source, observation time, provenance, semantics and completeness state. Support cycles, unresolved endpoints, stale data, conflicting assertions and partial traversal. A graph database is not a prerequisite; storage choice follows measured query, scale and operational requirements. A navigable graph UI is a separate product decision, not implied by this model.

## Evidence and coverage measurement

Do not publish target percentages or a composite Trust Score before measurement contracts exist. Candidate metrics require explicit numerator, denominator, eligible population, source, freshness, version and blind spots:

- Discovery coverage: reached / declared sources, with terminal states reported separately.
- Attested coverage: eligible runs with valid attestation / eligible runs.
- Resource metadata coverage: resources with required metadata observed / eligible declared resources.
- Access metadata coverage: resources with supported access metadata observed / resources whose connector declares that capability.
- Identity correlation quality: precision, recall/coverage where ground truth exists, and abstention rate separately.
- Exposure explainability: profiles with complete evidence references, limitations and reproducible rule version / all profiles emitted.
- Risk aggregation quality: false merges, missed groupings, duplicate retention and reviewer agreement on curated fixtures.
- Accountability: risk candidates with a recorded human decision / eligible risk candidates; inferred ownership is not a human decision.

A future dashboard must be generated from inspectable project data. Never hand-author example percentages as current state.

## Explicit non-goals

- Replacing BigID, OneTrust, a full DSPM suite, SIEM/EDR, Archer or ServiceNow.
- Full enterprise data catalog, universal lineage or universal effective-access computation.
- Trust Score or a single composite enterprise score; market benchmarking or peer scoring.
- LLM-generated risk narratives or governance decisions.
- Automatic remediation, permission mutation, retention enforcement or deletion.
- Breach-impact, legal-compliance or certification claims unsupported by direct evidence.
- Mandatory graph database, heavyweight graph infrastructure, graph-navigation UI in 1.9, or broad workflow engine.

## Existing work and dependencies

#2342 strategic umbrella; #2327 directory/IAM acquisition; #1083 audit-first sensitivity × excessive-permission signal; #1169 declared-sources vs reached Coverage Attestation; #1527 target-level attempted/findings/failures rollup; #2273 source inventory completeness; #2297 M365/Copilot permission research; #2301 stale ownership signals; #2331 catalog/lineage acquisition; #1667 Data Soup gap map; ADR-0017 risk/confidence contract.

Initial child work is limited to #2343, #2344 and #2346. Risk aggregation, blast radius, graph navigation, narratives and governance remain deferred until upstream evidence contracts are validated. Do not create duplicate epics where existing acquisition or foundation issues already own the work.

## Acceptance criteria for the 1.9 direction

- [ ] Product language consistently communicates Discover → Understand → Prioritize → Prove.
- [ ] No duplicate connector work is created where source acquisition is already tracked.
- [ ] Identity and access contracts preserve source-native semantics, stable IDs and provenance.
- [ ] Unknown, unsupported, partial and not-assessed states remain explicit.
- [ ] Exposure profiles are deterministic, explainable, versioned and calibrated before prioritization; unsupported inputs result in abstention, not a fabricated score.
- [ ] Risk outputs are reversible to source findings and observations.
- [ ] Coverage/evidence metrics have explicit denominators, freshness and eligibility rules.
- [ ] No unsupported claim of effective access, breach impact, legal compliance or complete coverage.
- [ ] No Trust Score, mandatory graph database, graph UI commitment, LLM dependency or workflow-engine expansion is introduced.
- [ ] Each proposed release capability passes its dependency gate and is reflected in the relevant issue/milestone before being called committed scope.

**Planning note:** Quarter-by-quarter sequencing is not adopted as a commitment. Schedule against dependencies, actual capacity, existing milestone status and implementation evidence.

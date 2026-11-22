# Vision: Data Exposure Intelligence

**Status:** Visionary — strategic direction, not a committed delivery plan  
**Horizon:** 12–36 months; post-Data Soup foundation  
**Related:** #2342 · #2343 · #2344 · #2346 · #2347

## Executive Summary

Most data-discovery products answer:

> Where does sensitive data exist?

Data Boar aims to answer a broader question:

> Where does sensitive data exist, who can reach it, how exposed is it, and how confidently can that conclusion be proven?

This evolution is called **Data Exposure Intelligence**.

The objective is not to become a full DSPM, GRC or workflow platform. It is to connect discovery, exposure analysis, risk prioritization and evidence in a single observable model.

**DISCOVER → UNDERSTAND → PRIORITIZE → PROVE**

This vision describes a direction and capability hypotheses. It does not assert that every capability below is currently implemented or committed to a release.

## Principles

### Evidence First

Every claim must derive from observed evidence or be explicitly identified as a source assertion, deterministic correlation, inference or unknown.

### Coverage Honesty

What was declared, attempted, reached, partially reached, inaccessible, unsupported or not assessed must remain visible. A source not reached produces no inferred findings.

### Read-Only Discovery

Observation comes before intervention. No permission changes, remediation, retention enforcement or customer-environment mutation is implied.

### Explainable Risk

Risk prioritization must be deterministic, versioned and traceable to its evidence. Unknown or incomplete input must never silently become low risk.

### Trust Through Evidence

Trust is earned through provenance, integrity, reproducibility and explicit limitations—not through a composite Trust Score without calibration.

### Local-First Operation

On-premises, air-gap-capable operation and local evidence custody remain product constraints, not optional deployment afterthoughts.

## Evolution

### Phase 1 — Discovery

**Question:** Where is the data?

Examples include filesystems, SMB/NFS/WebDAV, databases, M365, Google Workspace, object storage, CRM, ERP, collaboration systems and legacy repositories.

Data Soup is the acquisition and discovery fabric. Connector capability, coverage and source semantics must remain explicit.

### Phase 2 — Exposure

**Question:** Who or what may be able to reach the data?

Examples include users, guests, groups, service/workload identities, ACLs, grants, inherited permissions and sharing links.

The Exposure Graph is initially a logical, source-aware entity/relationship model. Observed membership or permission metadata is not automatically proof of effective authorization or successful access.

### Phase 3 — Risk

**Question:** Which observed exposures deserve attention first?

Examples include sensitive content with broad access, external sharing, stale access metadata, unresolved principals and conflicting source assertions.

Risk aggregation and blast-radius estimates are later capabilities. They must be reversible to source evidence and must expose uncertainty and incomplete coverage.

### Phase 4 — Governance Assist

**Question:** Who should review or own the risk?

Examples include source-declared ownership, ownership candidates, stewardship hints, human risk acceptance and exception records.

Governance assist supports accountability; it does not become an approval workflow engine, ticketing platform or legal decision-maker.

## Strategic Differentiation

Data Boar does not aim to compete as:

- a full GRC or RiskOps platform;
- a workflow/ticketing system;
- a universal enterprise data catalog;
- a SIEM or EDR;
- a cloud-only DSPM suite.

Instead, it focuses on four connected capabilities:

1. **Discovery** — locate data across heterogeneous environments.
2. **Exposure** — represent observed identity, resource and access relationships.
3. **Risk** — prioritize explainable exposure without hiding unknowns.
4. **Evidence** — prove what was observed and what was not.

Coverage Attestation and Evidence First are intended to be first-class product capabilities, not merely implementation details.

## Competitive Capability Matrix — Directional Hypothesis

**Important:** This matrix records the supplied strategic hypothesis for discussion. It is not a verified competitive benchmark, vendor feature audit or statement of current Data Boar implementation. Ratings must be validated by product/edition, deployment model, documentation and hands-on research before external publication.

Legend: 🟢 hypothesized strong · 🟡 partial · ⚪ initial · ❌ outside intended focus

| Capability | Data Boar current* | Data Boar 1.9 direction* | BigID | OneTrust | Thales DSPM | GRC/RiskOps |
|---|---:|---:|---:|---:|---:|---:|
| PII discovery | 🟢 | 🟢 | 🟢 | 🟡 | 🟢 | ❌ |
| On-prem filesystem | 🟢 | 🟢 | 🟡 | ❌ | 🟡 | ❌ |
| SMB/NFS/WebDAV | 🟢 | 🟢 | 🟡 | ❌ | 🟡 | ❌ |
| M365 discovery | 🟡 | 🟢 | 🟢 | 🟡 | 🟢 | ❌ |
| Google Workspace | 🟡 | 🟢 | 🟢 | 🟡 | 🟢 | ❌ |
| Object storage | 🟡 | 🟢 | 🟢 | ❌ | 🟢 | ❌ |
| Exposure context | ⚪ | 🟢 | 🟡 | ❌ | 🟢 | 🟡 |
| Identity context | ⚪ | 🟡 | 🟢 | 🟡 | 🟡 | 🟡 |
| Risk aggregation | ⚪ | 🟡 | 🟡 | 🟢 | 🟡 | 🟢 |
| Governance workflow | ❌ | ⚪ | 🟢 | 🟢 | 🟡 | 🟢 |
| Evidence and attestation | 🟢 | 🟢 | ⚪ | ⚪ | ⚪ | ⚪ |
| Coverage attestation | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ |
| Honest partial coverage | 🟢 | 🟢 | 🟡 | ⚪ | 🟡 | ⚪ |
| Offline / air-gapped | 🟢 | 🟢 | 🟡 | ⚪ | 🟡 | 🟡 |
| Small-team friendliness | 🟢 | 🟢 | ❌ | ❌ | ❌ | ❌ |

*Data Boar columns are hypotheses from the supplied strategy draft, not a substitute for checking the current main branch, connector capability declarations and release behavior. Competitor columns are unverified directional assumptions. Do not quote this matrix as externally substantiated market research.*

## Prioritized Capability Gaps

### Priority 1 — Exposure foundation

Highest strategic return, subject to upstream contract validation:

- **Identity Inventory:** represent source-aware identities and group relationships so discovery can be connected to principals without name-only joins.
- **Access Inventory:** preserve observed permissions, ACLs, grants, groups, guests and sharing links with connector-specific semantics.
- **Exposure Profile:** initial deterministic prioritization using sensitivity and observed access context, with explicit unknown/partial states and calibrated rules.

These correspond to #2343, #2344 and #2346. They are specifications/contracts first; implementation sequence depends on the existing connector and evidence foundations.

### Priority 2 — Risk intelligence

- **Risk Aggregation:** turn large finding sets into a smaller number of evidence-linked, reviewable risk candidates. Aggregation must be reversible; it must not erase individual findings.
- **Blast Radius:** estimate potentially affected resources or principals only where identity/access relationships support the calculation. Clearly label estimates and incomplete graph traversal.

### Priority 3 — Governance assist

- **Ownership candidates:** infer possible owners from source evidence, while distinguishing declared, inferred and unknown ownership.
- **Governance assist:** support human review, accountability, risk acceptance and exceptions without building a generic GRC workflow engine.

## What Not to Prioritize

- Workflow engine competing with ServiceNow, Archer or Jira.
- Full enterprise catalog competing with BigID, Collibra or Purview.
- Questionnaire-driven risk as the primary risk model.
- Universal effective-access claims across every connector.
- A mandatory graph database before scale and query requirements justify it.
- A Trust Score or composite score without validated semantics and calibration.

## 1.9 MVP — Deliberately Narrow

The proposed first increment is limited to three capability slices:

### Feature 1 — Identity Inventory

Example shape (illustrative only; not a committed schema):

```json
{
  "identity": "source-namespaced-identity-id",
  "source": "m365",
  "groups": [],
  "observation_state": "observed"
}
```

The contract must preserve immutable provider IDs, tenant/source namespace, membership provenance, cycles, partial enumeration and unresolved references. Display names are not stable identity keys.

### Feature 2 — Access Inventory

Example shape (illustrative only; not a committed schema):

```json
{
  "resource": "source-namespaced-resource-id",
  "principal": "source-namespaced-principal-id",
  "permission": "read",
  "source": "sharepoint",
  "evidence_ref": "..."
}
```

The contract must preserve inherited/direct permission semantics, link audience, source timestamps and limitations. It must not imply that a permission was exercised successfully.

### Feature 3 — Exposure Profile

Example shape (illustrative only; not a committed schema):

```json
{
  "resource": "source-namespaced-resource-id",
  "profile_state": "evaluated",
  "exposure_level": "high",
  "reason_codes": [
    "high_sensitivity",
    "broad_access",
    "external_sharing"
  ],
  "evidence_refs": [],
  "limitations": []
}
```

The output should be an explainable profile, not an arbitrary numeric score presented with false precision. A numeric scale may be considered only after calibration and documented missing-value semantics.

## MVP Acceptance Hypotheses — Require Feasibility Validation

The following are candidate acceptance targets, not current commitments:

- **CA-1:** Identity/access inventory can represent relevant principals and relationships for M365, SMB, filesystem and object-storage contexts where the source exposes such metadata. These sources do not all provide the same identity plane; distinguish local principals, directory references, object ACLs and unsupported semantics rather than claiming identical coverage.
- **CA-2:** M365 SharePoint and OneDrive produce normalized access evidence with source-specific semantics retained. Do not generalize this acceptance criterion to every Microsoft 365 workload.
- **CA-3:** A sensitive discovery can receive an Exposure Profile when required inputs are available. Otherwise emit an explicit not-assessed/partial/unsupported state; never manufacture a score.
- **CA-4:** Every evaluated profile has deterministic reason codes, evidence references, rule version and limitations.
- **CA-5:** Evidence First remains invariant: no unmarked estimate, no inference presented as observation, no claim beyond coverage.

Feasibility, credential scopes, API behavior, rate limits and operational cost must be assessed before converting these hypotheses into release commitments.

## Long-Term Outcome

Organizations should be able to answer:

- Where is our sensitive data?
- Who or what may be able to reach it?
- Why is it considered exposed?
- How serious is the observed exposure?
- Who may own the issue or should review it?
- How certain are we about the answer?
- Which sources were not reached, and what does that prevent us from concluding?

The combination of those answers forms the foundation of Data Exposure Intelligence.

## Relationship to Delivery Planning

This vision is deliberately broader than a release plan. The staged, dependency-aware 1.9 plan belongs in `docs/plans/PLAN_1_9_DATA_EXPOSURE_INTELLIGENCE.md`; execution status remains in `PLANS_TODO.md` and milestones. This vision does not create calendar commitments or override existing issues.

Strategic umbrella: #2342  
Initial contract/spec issues: #2343, #2344, #2346  
Plan materialization and index synchronization: #2347

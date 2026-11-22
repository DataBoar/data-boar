# Vision: Data Soup

**Status:** Strategic doctrine — non-binding product direction  
**Horizon:** Foundational capability; evolves with connector and evidence contracts  
**Parent vision:** [Data Exposure Intelligence](VISION_DATA_EXPOSURE_INTELLIGENCE.md)  
**Related work:** #1667, #1169, #1527, #2273, #2326–#2341

## Purpose

Data Soup is the acquisition and discovery fabric through which Data Boar observes heterogeneous data estates. It makes data sources discoverable through bounded, source-aware, evidence-producing connectors without pretending that every source exposes the same information or semantics.

Data Soup answers:

> What sources and resources did we declare, what could we reach, what did we observe, and what remains outside the evidence boundary?

It is not a universal enterprise catalog, a data lake, an ETL platform or a workflow orchestrator.

## Product principles

### Source-aware by construction

A connector preserves the source's native identifiers, object model, permission model, timestamps, pagination behavior and limitations. Normalization creates a common envelope; it must not erase source semantics.

### Coverage is a first-class output

Every run distinguishes at least:

- declared scope;
- attempted scope;
- reached scope;
- partially reached scope;
- inaccessible scope;
- unsupported scope;
- not-assessed scope.

A source that was not reached produces no inferred findings. Empty results are not proof of absence unless the relevant scope was successfully enumerated and the evidence says so.

### Evidence accompanies observations

An observation carries provenance sufficient to explain where it came from, when it was collected, under which connector/capability version, and with what limitations. Evidence must be locally retained and integrity-protected under the product's custody model.

### Read-only and least privilege

Discovery is read-only by default. Credentials and API scopes are bounded to the declared acquisition purpose. Additional scopes, data-plane probes or elevated permissions require explicit justification and opt-in.

### Bounded operation

Pagination, retries, concurrency, traversal depth, attachment sizes, memory and query budgets are bounded. Partial and interrupted collection must produce explicit terminal states rather than silently presenting incomplete results as complete.

### Portable deployment

On-premises, air-gap-capable and constrained environments are design inputs. A connector must not require external data egress or a heavyweight control plane to preserve core discovery and evidence behavior.

## Conceptual model

Data Soup treats these as distinct concepts:

| Concept | Meaning |
|---|---|
| Source | A system or repository declared for acquisition |
| Target | A bounded addressable scope within a source |
| Resource | An observed object, location, record set or data-bearing entity |
| Observation | A source-derived fact or assertion captured at a point in time |
| Finding | A detector or rule result linked to one or more observations |
| Capability | A documented operation the connector can perform under stated conditions |
| Coverage state | The terminal or intermediate state describing what happened to declared scope |
| Evidence reference | A stable link from a claim/result to its supporting evidence |

These concepts should remain independently addressable. A resource is not a source; a finding is not an observation; a declared capability is not proof that a run successfully exercised it.

## Connector contract expectations

Each connector should declare, where applicable:

1. supported source/product editions and API versions;
2. supported object types and scopes;
3. required and optional credentials/scopes;
4. read-only guarantees and any exceptions;
5. pagination, rate-limit and retry behavior;
6. source identity and resource identifier semantics;
7. metadata and access-control fields actually observable;
8. known blind spots, unsupported states and partial-result conditions;
9. data-volume, concurrency and resource limits;
10. test fixtures covering positive, negative, empty, partial, stale and inaccessible outcomes.

A connector capability matrix is an inspectable contract, not marketing copy.

## Normalization without semantic flattening

A common envelope may normalize timestamps, provenance, resource references and observation state. It must preserve original source values and semantics alongside normalized fields.

Examples:

- A filesystem local SID, an Entra object ID and an object-storage canonical user are not interchangeable identities.
- An ACL entry, a sharing link and a directory group membership are different relationship types.
- A source-declared sensitivity label is not the same thing as a Data Boar detector result.
- A successful API enumeration is not proof that all underlying data-plane objects were visible.

Cross-source correlation must use stable, namespaced identifiers or explicit evidence-backed mappings. Display-name equality is insufficient.

## Relationship to Exposure Intelligence

Data Soup supplies the observations from which Identity Inventory, Access Inventory, Exposure Profiles and the logical Exposure Graph may be built. It does not itself claim effective access, successful access, incident impact or a complete view of an estate.

The intelligence layer must abstain or report partial/unknown when the source evidence does not support a conclusion.

## Explicit non-goals

- Full enterprise data catalog, business glossary or universal lineage platform.
- ETL, replication, data lake or data warehouse functionality.
- Write-capable remediation or permission management.
- Universal identity resolution across unrelated providers.
- Universal effective-access computation.
- Claims of complete coverage based solely on connector availability.
- LLM dependency for acquisition, classification, correlation or evidence generation.

## Doctrine tests

A Data Soup design is inconsistent with this vision if it:

- reports a source as covered merely because a connector exists;
- treats an unattempted or inaccessible source as empty;
- discards source-native identifiers or permission semantics during normalization;
- emits findings for scope that was not reached;
- silently converts partial enumeration into complete coverage;
- requires collected data to leave the customer's custody;
- expands into a general-purpose catalog or workflow product.

The governing rule is simple: **acquire what can be observed, preserve how it was observed, and state precisely what could not be observed.**

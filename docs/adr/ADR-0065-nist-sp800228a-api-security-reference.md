# ADR 0065 — NIST SP 800-228A as REST API security hardening reference

- **Date (UTC):** 2026-06-11
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Deferred

### Status history

- 2026-06-11 — Deferred: NIST SP 800-228A still in public comment (deadline 2026-07-02); ADR to be written post final publication — GitHub #710

## Context

NIST SP 800-228A ("Secure Deployment of RESTful Web APIs") is in public comment until 2026-07-02. When finalised it will be the most current NIST normative reference for REST API security — directly relevant to the Data Boar API, which exposes PII scan findings.

The base document SP 800-228 (final) is already available. The architectural decisions around adopting SP 800-228A have concrete consequences:

- Authentication and authorisation of findings endpoints
- Required security headers (`Content-Security-Policy`, `Strict-Transport-Security`, etc.)
- Rate limiting and injection protection
- PII handling in API responses (masking, pagination, access scope)

Adopting the standard as a hardening reference affects the public API contract and `docs/ENTERPRISE_INTEGRATION_GUIDE.md`.

## Decision

**Deferred** until NIST SP 800-228A final publication (expected Q3/Q4 2026). Do **not** draft the decision based on the Initial Public Draft (IPD) — the final text may change.

Once published, this ADR will be amended to:

1. Adopt SP 800-228A as the primary hardening checklist for `api/routes.py` and the API documentation.
2. Document which OWASP API Security Top 10 / RFC 9110 controls are already satisfied and which require new work.
3. Open a follow-up implementation issue with a control-by-control checklist derived from the final text.

## Rationale

Drafting an ADR from an IPD risks locking in controls that change in the final publication, or missing additions that the public comment period introduces. A Deferred ADR records the decision-making intent and prevents duplicate investigation while avoiding premature commitment.

## Alternatives Considered

| Alternative | Why not |
|-------------|---------|
| Draft now from IPD | Risk of invalidated controls; rework cost after final publication |
| OWASP API Security Top 10 only | Less formally normative; no NIST alignment for government/regulated clients |
| RFC 9110 (HTTP semantics) | Covers semantics, not security hardening posture |
| No formal reference | Leaves hardening decisions undocumented; harder to audit |

## Related Decisions

- [ADR-0056](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md) — ADR inventory policy
- Issue #599 — `ENTERPRISE_INTEGRATION_GUIDE.md` (API surface context)
- Issue #561 — `SECURITY.md` hardening (adjacent scope)

## References

- SP 800-228 (final): <https://csrc.nist.gov/pubs/sp/800/228/final>
- SP 800-228A (IPD): <https://csrc.nist.gov/pubs/sp/800/228/a/ipd>
- Public comment deadline: 2026-07-02

# ADR 0094 — Forensic-acquisition posture of scan_manifest (ISO/IEC 27037 alignment, deliberate absence of source hash / bit-for-bit image)

- **Date (UTC):** 2026-11-10
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-11-10 — Proposed — records the acquisition posture for [#759](https://github.com/DataBoar/data-boar/issues/759).

## Context

A comparison of `scan_manifest` with the acquisition form in ISO/IEC 27037:2012 revealed that `scan_manifest` is conceptually a forensic-acquisition record, but with deliberate omissions:

- **No hash of the original** (the scanned system)
- **No bit-for-bit image**
- **Sampling, not copying**

The ADR-0025 covers "evidence and inventory, not legal conclusion". No ADR documents the **FORENSIC ACQUISITION POSTURE** specifically — why these omissions are *correct decisions*, not accidental limitations.

ISO/IEC 27037:2012 defines the process for identification, collection, acquisition, and preservation of digital evidence. Data Boar operates in a different context:

- **Live production systems**: imaging and hashing the source would be destructive or invasive
- **No forensic lab environment**: Data Boar is a discovery tool, not a forensic workstation
- **Sampling preserves context**: the scan captures evidence *about* the data without *copying* it

## Decision

1. **Document the deliberate omissions** — `scan_manifest` intentionally does not include:
   - Source system hash
   - Bit-for-bit image
   - Full file copy

2. **Align with ISO/IEC 27037 where applicable**:
   - ISO/IEC 27037 permits "Hash of the original (if applicable)" — Data Boar documents this as `N/A` with justification
   - The ed25519 signature on the `scan_manifest` provides acquisition integrity (covers the manifest, not the source)

3. **Mapping Data Boar evidence to ISO/IEC 27037 controls**:

| ISO/IEC 27037 Control | Data Boar Evidence | Status |
|------------------------|-------------------|--------|
| Hash of acquisition | ed25519 on scan_manifest | Partial — signs manifest, not source |
| Chain of custody | statement attribution | OK |
| Time synchronization | timestamp UTC | Gap — NTP not documented |
| Isolated environment | sample caps + NOLOCK | OK |
| Documentation | scan_manifest | OK |

4. **Add explicit limitations field to scan_manifest schema** — a machine-readable section that declares:
   - `limitations: ["no source hash", "no bit-for-bit image", "sampling only"]`
   - `justification: "Data Boar operates on live production systems; full acquisition would violate no-surprise side effects principle (MANIFESTO §1)"`

## Consequences

- **Audit readiness**: Forensic auditors can immediately see that acquisition parameters are documented and intentional, not missing
- **Schema clarity**: The `limitations` field makes acquisition posture machine-readable
- **Gap handling**: NTP synchronization remains undocumented; future version may add `timing_ntp_offset` field
- **Positioning preservation**: ADR-0025 posture maintained (evidence for governance review, not legal conclusion)

## References

- ISO/IEC 27037:2012 — Guidelines for identification, collection, acquisition and preservation of digital evidence
- RFC 3227 — Order of volatility for digital evidence
- [ADR-0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)
- [#759](https://github.com/DataBoar/data-boar/issues/759)
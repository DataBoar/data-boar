# Data Boar | Release Integrity and Security Specification

This document defines integrity, security, and resilience requirements for Data Boar
releases, with explicit focus on Pro+ paths.

## 1) Code and binary integrity

- Deterministic Rust build evidence must be captured in isolated environments.
- Produced binaries (`.pyd` / `.so`) and generated reports (`.pdf` / `.json`) must
  be accompanied by SHA-256 hashes.
- Production Rust binaries should be stripped from debug symbols.

## 2) Operational resilience (SRE)

- Auto-throttling must reduce worker concurrency when moving average latency exceeds
  configured `target_latency_ms`.
- Scan state must be persisted with atomic write-replace in `.data_boar_state.json`.
- Resume after interruption must continue from last validated offset/id.
- Rust pre-filter path must remain panic-free on malformed inputs.

## 3) GRC taxonomy and compliance

- Credit-card findings are valid only when Luhn (Mod 10) passes.
- Risk scoring baseline:
  - Common identifiers: weight 10
  - Financial data: weight 30
  - Sensitive data (LGPD Art. 5, II): weight 80
- Executive artifacts must include immutable timestamp and `scan_id` traceability.

## 4) Release integrity checklist

- [ ] Deterministic Rust build evidence recorded.
- [ ] SHA-256 hashes generated for runtime binaries and report artifacts.
- [ ] Symbol stripping policy applied for distributable binaries.
- [ ] Throttling behavior verified under synthetic latency pressure.
- [ ] Checkpoint resume verified after simulated crash/interruption.
- [ ] Luhn gate verified for valid and invalid card candidates.

## 5) Related specifications

- [INTEGRITY_HUB.md](INTEGRITY_HUB.md) ([pt-BR](INTEGRITY_HUB.pt_BR.md)) — **start here** for tamper detection, runtime modules, scripts, and ADR inventory.
- [RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) ([pt-BR](../RELEASE_INTEGRITY.pt_BR.md)) — **product** licensing tamper-evidence (build digest, optional manifest); distinct scope from this ops release spec.
- [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md) ([pt-BR](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md)) — optional runtime integrity defense (design).
- [SPRINT_GREAT_LEAP_POSTMORTEM.md](SPRINT_GREAT_LEAP_POSTMORTEM.md) ([pt-BR](SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md)) — verified vs aspirational lab metrics.

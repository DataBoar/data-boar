# Integrity check and alpha-logic (design specification)

**Português (Brasil):** [INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md)

**Integrity navigation hub:** [INTEGRITY_HUB.md](INTEGRITY_HUB.md) ([pt-BR](INTEGRITY_HUB.pt_BR.md)) — full map of runtime, release, and ADR integrity surfaces.

This document is a **design specification** for optional **runtime integrity verification** of critical Data Boar artifacts (Python sources, optional native extensions, and signed reference hashes). It is **not** a guarantee that every behavior below is implemented in the main product path until an ADR and code land explicitly.

## Goals

- Detect unexpected modification of shipped or deployed bits before high-trust reporting.
- Fail safe: prefer **degraded / clearly labeled** output over silent wrong compliance claims.
- Produce **auditable evidence** (structured log) for security review.

## Pseudo-specification

### 1) Hashing at startup

On controlled startup (optional feature flag, e.g. `DATA_BOAR_INTEGRITY_CHECK=1`):

1. Enumerate **critical paths** (configurable list), for example:
   - selected `core/*.py`, `pro/*.py`, and packaged extension modules (e.g. `boar_fast_filter` when present).
2. Compute **SHA-256** per file (or per canonical wheel digest for extensions).
3. Compare against a **known-good manifest** (JSON or signed document) shipped or loaded from a secure path.

The manifest must be **maintained by the release engineer** and versioned with the release.

### 2) Cross-check

- **Match:** continue normal operation; optionally log `integrity_ok` at debug level.
- **Mismatch:** enter **tinted state** (see below).

### 3) Tinted state (mismatch)

When any critical hash fails verification:

- Set a process-level flag (conceptually `__IS_TINTED__ = True`; implementation may use a module singleton or env export).
- Surface **explicit version / build metadata** indicating tamper suspicion (exact string is a product decision; must not impersonate a stable release).
- Enable **cripple mode** for report generators:
  - cap exported narrative length (e.g. first N lines);
  - inject a visible **non-trust** watermark in human-readable outputs;
  - avoid claiming regulatory completeness.

### 4) Audit log

Append a structured record to `security_alert.log` (or SIEM sink):

- timestamp, hostname, Data Boar version, list of paths with expected vs observed hashes;
- no raw customer data.

## Operational notes

- **Performance:** hashing large trees on every process start can be expensive; scope the file list narrowly or run on a schedule.
- **Extensions:** native modules may live in `site-packages`; hash the **installed** artifact path resolved at runtime, not only `pro/*.pyd` in the source tree.
- **Signing:** “known-good” manifests should be **signed** or distributed via a channel the operator trusts (out of scope for this text).

## Related

- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) ([pt-BR](RELEASE_INTEGRITY.pt_BR.md))

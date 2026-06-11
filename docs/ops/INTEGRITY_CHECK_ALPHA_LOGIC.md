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

## Implemented: Phase E — SQLite integrity anchor (#856)

`core/integrity_anchor.py` implements the Alpha-detection spine:

1. **First run (E.1–E.2):** SHA-256 of the behaviour-critical allowlist
   (`main.py`, `core/detector.py`, `core/engine.py`, `core/integrity_anchor.py`,
   `core/licensing/guard.py`, `api/routes.py`) → persisted in the
   `build_integrity_anchor` SQLite table (`release_label`, per-file hashes,
   `validated_at`, `signature_ok`, `validator_version`). The anchor **survives
   `--reset-data`**: `wipe_all_data()` clears scan tables only.
2. **Startup re-verify (E.3):** every start (CLI and web, **any** licensing
   mode including `open`) recomputes the hashes and compares to the anchor.
   Mismatch → `integrity_state=tampered` / `trust_level=adulterated`.
3. **TINTED / `-alpha` (E.4):** the adulterated state forces the
   `-alpha (development / not CI-validated)` label on the report Info sheet
   (`Build trust` / `Integrity state` rows), dashboard footer, `GET /about`,
   `GET /status`, `/health`, and startup logs (CRITICAL log + stderr banner).
   `enterprise_surface` severity goes `elevated` with reason
   `integrity_tampered` (ADR-0066 alignment).
4. **Open-mode worker clamp:** `core/engine.py` caps `scan.max_workers` at
   `OPEN_MODE_WORKER_CAP = 2` in open mode. The clamp lives inside the hashed
   allowlist — removing it changes `core/engine.py` and tints the build.
5. **Forensics (E.5):** `integrity_events` is an append-only table
   (validation / re-verify / tamper) preserved across data wipes.

### Honest threat model (E.6)

This is **tamper-EVIDENT, not tamper-PROOF.** An attacker with write access to
both the code tree **and** the SQLite anchor file can delete or re-baseline the
anchor (the app then re-runs first validation or shows `unknown`). Mitigations:
file permissions, read-only DB mounts in high-assurance deploys, and the
**signed manifest** (Sigstore / CI OIDC — Phase C.4 of
`PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY`) as the next hardening layer. The local
anchor reliably catches casual edits, forks with gates removed, and silent
deploy drift — which is the Alpha-detection goal.

## Related

- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) ([pt-BR](RELEASE_INTEGRITY.pt_BR.md))

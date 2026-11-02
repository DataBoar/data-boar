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

## Implemented: Phase E — signed-manifest trust + SQLite forensics (#856 / #2168)

`core/integrity_anchor.py` plus `core/integrity_signed_manifest.py`
implement the Alpha-detection spine:

1. **Trust root (#2168):** SHA-256 of the behaviour-critical allowlist
   (spine + `connectors/*.py` + `core/licensing/*.py` + explicit extras —
   see `resolve_critical_modules()` in `core/integrity_anchor.py` and
   [PLAN_INTEGRITY_HARDENING.md](../plans/PLAN_INTEGRITY_HARDENING.md) § *behaviour-critical criterion*)
   is compared to a **release-signed** manifest packaged as
   `core/licensing/integrity_manifest.json`. The signature is Ed25519 over a
   canonical JSON payload and is verified with the existing license public
   key (`core/licensing/license-pub-v1.pem`). `validated` / `expected` only
   when that signature verifies **and** every allowlisted hash matches.
   Absent, unsigned, unreadable, wrong-key, hash-mismatched, or downgrade
   trees are `tampered`. Unsigned 1.8.0-class trees are **not** `validated`
   by omission.
2. **SQLite is forensic, not the arbiter:** `build_integrity_anchor` stores
   last-seen hashes, `signed_release_label`, `validated_at`, and
   `build_digest_matched`. **`build_digest_matched` is a build-digest match
   flag, not a cryptographic signature** (#1211): `True` only when
   `DATA_BOAR_EXPECTED_BUILD_DIGEST` was set and matched the embedded digest;
   unset env → `False`. The row **survives `--reset-data`**.
3. **Startup re-verify:** every start (CLI and web, **any** licensing mode
   including `open`) re-evaluates the signed manifest.
   - **Legitimate signed upgrade:** matching signed files for the new label
     → `validated` (no operator command, no `-alpha`).
   - **`--reconcile-integrity-anchor --confirm-upgrade-to=<installed-version>`**
     records a `reconcile` event and re-evaluates the same signed manifest.
     It cannot mint `validated` by itself.
4. **TINTED / `-alpha` (E.4):** the adulterated state forces the
   `-alpha (development / not CI-validated)` label on the report Info sheet
   (`Build trust` / `Integrity state` rows), dashboard footer, `GET /about`,
   `GET /status`, `/health`, startup logs (CRITICAL log + stderr banner), and
   **`--version`** / **`--validate-config`** CLI preflight ([#1298](https://github.com/DataBoar/data-boar/issues/1298)).
   `enterprise_surface` severity goes `elevated` with reason
   `integrity_tampered` (ADR-0066 alignment).
5. **Open-mode worker clamp:** `core/engine.py` caps `scan.max_workers` at
   `OPEN_MODE_WORKER_CAP = 2` in open mode. The clamp lives inside the hashed
   allowlist — removing it changes `core/engine.py` and tints the build.
6. **Forensics (E.5):** `integrity_events` is an append-only table
   (validation / re-verify / reconcile / tamper) preserved across data wipes.

### Honest threat model (E.6)

This is **tamper-EVIDENT, not tamper-PROOF.** The check proves that
behaviour-critical files match a manifest signed by the **packaged** license
verify key. It does **not** prove resistance if that packaged public key is
replaced. SQLite, wheel `RECORD`, and `--reconcile-integrity-anchor` are not
trust roots. Same-version hash drift still tints. Mitigations: file
permissions and a TTY-signed packaged manifest on each release
(`scripts/sign-integrity-manifest.py`). The runtime reliably catches casual
edits, forks with gates removed, and silent deploy drift — which is the
Alpha-detection goal.

## Related

- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) ([pt-BR](RELEASE_INTEGRITY.pt_BR.md))

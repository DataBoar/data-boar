# ADR 0066 — TAMPERED state behavior (fail-closed in enforced mode)

- **Status:** Accepted
- **Date (UTC):** 2026-05-25
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Release integrity checks (`DATA_BOAR_EXPECTED_BUILD_DIGEST`, optional release manifest)
can set `LicenseGuard.state` to **TAMPERED** when embedded digests or manifest hashes
diverge from policy. Issues **#711** and **#712** showed that **TAMPERED** did not
consistently constrain commercial features: runtime tier logic could still expose
Pro/Enterprise capability paths, weakening tamper-evidence in **`licensing.mode: enforced`**.

Operators need a single, auditable rule for what **TAMPERED** means in production vs
developer **open** mode, aligned with commercial tier boundaries in
[ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md).

| Option | Behavior | Trade-off |
| --- | --- | --- |
| **A — Fail closed (tier cap)** | **TAMPERED** caps effective tier at **Community** in **enforced** mode; Pro/Enterprise features denied with a clear message | Real protection; customer must redeploy a clean build or fix digest/manifest policy |
| **B — Safe-Hold total** | **TAMPERED** blocks scan start, exit code 1, CRITICAL log | Maximum protection; higher false-positive cost if digest/manifest drifts operationally |
| **C — Warn only** | **TAMPERED** logs CRITICAL + watermark; process continues at licensed tier | Tamper-evident but not tamper-proof; acceptable only when enforcement is off |

## Decision

1. **`licensing.mode: enforced` + `state == TAMPERED` → fail closed at tier boundary (Option A).**
   Effective runtime tier for feature gates is **`Tier.COMMUNITY` maximum** regardless of
   JWT `dbtier` or config hints. Pro/Enterprise features are denied through existing
   `is_allowed()` / feature-gate paths with an operator-visible reason tied to integrity
   detail (digest mismatch, manifest mismatch, etc.).

2. **`licensing.mode: open` + `state == TAMPERED` → warn and continue (Option C).**
   The process **continues operating** at open-mode semantics (no commercial token required).
   A **CRITICAL** log line records tamper evidence (state, detail, watermark when set)
   so operators and log pipelines can alert without blocking local development trees
   that intentionally skip release digest/manifest policy.

3. **Logging:** emit **CRITICAL** when **TAMPERED** is entered in **either** mode
   (enforced or open). Enforced mode additionally applies the tier cap in (1).

4. **Documentation (no `docs/ENTERPRISE_INTEGRATION_GUIDE.md` in-tree):** describe
   enforced vs open **TAMPERED** behavior in
   [`docs/RELEASE_INTEGRITY.md`](../RELEASE_INTEGRITY.md) (EN + pt-BR) and
   [`docs/LICENSING_SPEC.md`](../LICENSING_SPEC.md) lifecycle table — integrators
   configure `DATA_BOAR_EXPECTED_BUILD_DIGEST` / `DATA_BOAR_RELEASE_MANIFEST_PATH`
   per those guides.

5. **Implementation contract:** enforce (1) in
   `core/licensing/runtime_feature_tier.py` (`get_runtime_tier_for_features()`)
   and/or centralized allow checks used by `LicenseGuard`; add tests for
   **TAMPERED+enforced** (Pro blocked) and **TAMPERED+open** (not tier-blocked).

## Rationale

- **Enforced mode is a commercial trust boundary.** Allowing Pro/Enterprise features
  while integrity checks report **TAMPERED** negates the purpose of digest/manifest
  wiring ([ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md),
  release manifest generator, build digest).
- **Open mode serves development.** Hard-blocking scans on every digest drift would
  break local clones; CRITICAL logging preserves evidence without Safe-Hold exit (Option B).
- **Tier cap (A) vs process halt (B):** Option A matches existing feature-gate UX
  (deny capability with message) and avoids surprising exit-code changes for batch/CLI
  operators who still need read-only diagnostics.

## Consequences

- **Positive:** Deterministic, reviewable behavior for **TAMPERED** across API, CLI,
  and dashboard feature gates.
- **Positive:** Enforced deployments cannot silently run Pro/Enterprise surfaces on
  modified builds when digest/manifest policy is active.
- **Negative:** Enforced customers with misconfigured `DATA_BOAR_EXPECTED_BUILD_DIGEST`
  or stale manifest see Community-only capability until redeploy — intentional fail-closed.
- **Ongoing:** Code and tests implementing (5) must cite this ADR in the PR; docs
  updates in (4) ship with or immediately after that implementation slice.

## Alternatives Considered

1. **Option B — Safe-Hold total halt** (rejected for default): maximum protection but
   brittle when digest/manifest policy lags image promotion; reserved for future
   operator opt-in if product adds a explicit Safe-Hold flag.
2. **Option C for enforced mode** (rejected): leaves commercial features exposed while
   claiming tamper detection — contradicts audit posture for Pro/Enterprise.
3. **No ADR — fix only in code** (rejected): #711/#712 showed behavior drift without
   a durable decision record; integrators need a stable contract.

## Related Decisions

- [ADR 0027 — Commercial tier boundaries — licensing docs and future JWT claims](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md)
- [ADR 0045 — ADR metadata and format standardization](ADR-0045-adr-metadata-and-format-standardization.md)

## References

- [`docs/RELEASE_INTEGRITY.md`](../RELEASE_INTEGRITY.md) · [pt-BR](../RELEASE_INTEGRITY.pt_BR.md)
- [`docs/LICENSING_SPEC.md`](../LICENSING_SPEC.md) — lifecycle state **TAMPERED**
- [`core/licensing/guard.py`](../../core/licensing/guard.py) · [`core/licensing/runtime_feature_tier.py`](../../core/licensing/runtime_feature_tier.py)
- GitHub issues **#711**, **#712**, **#715**

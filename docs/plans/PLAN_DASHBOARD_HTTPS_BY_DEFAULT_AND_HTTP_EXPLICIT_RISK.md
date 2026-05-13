# Plan: Dashboard HTTPS-by-default with explicit HTTP risk mode

**Status:** Completed
**Date:** 2026-03-25
**Authors:** Fabio Leitao
**Priority:** H2

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Purpose

Make dashboard traffic **encrypted by default** (TLS >= 1.2) even without an upstream reverse proxy/load balancer, while preserving a deliberate HTTP mode for constrained environments with strong warnings and explicit operator responsibility.

## Why this matters

- Prevent accidental plaintext dashboard traffic on internal networks.
- Keep secure-by-design posture independent of external infra quality.
- Preserve compatibility with existing deployments behind reverse proxy / load balancer.
- Improve compliance/legal narrative with explicit secure defaults and auditable opt-out.

## Scope and boundaries

| In scope                                                             | Out of scope                                                       |
| ---                                                                  | ---                                                                |
| Native HTTPS listener option for dashboard app (TLS >= 1.2 baseline) | Replacing upstream WAF/reverse-proxy hardening responsibilities    |
| Redirect or force behavior toward HTTPS by default                   | Full PKI lifecycle automation beyond practical local cert handling |
| Explicit HTTP opt-in flag with risk warnings and audit trail         | Claiming transport-security compliance by itself                   |
| UI banner + logs + status/health + audit signals for insecure mode   | Eliminating ability to run HTTP in all environments                |

## Target behavior (operator experience)

1. **Default posture:** dashboard starts in HTTPS-capable mode (either direct TLS or explicit requirement that TLS is enabled in config/flags).
1. **Unsafe override:** operator must explicitly pass an HTTP flag (example: `--allow-insecure-http`) to run plaintext.
1. **Clear warnings:** startup stdout/stderr + logs + API health/status + dashboard banner show that traffic is not cryptographically protected in insecure mode.
1. **Audit visibility:** scan/session or runtime audit surfaces indicate insecure dashboard transport when enabled.
1. **Reverse proxy compatibility:** app still works correctly when TLS is terminated upstream; docs keep this as recommended enterprise pattern.

## Proposed implementation phases

| Phase                                     | To-do                                                                                                                                                                                                                      | Status                                                                                 |
| ---                                       | ---                                                                                                                                                                                                                        | ---                                                                                    |
| 1. Transport config and flags             | Add explicit dashboard transport mode (`https`, `http`), cert/key parameters, and insecure override flag (`--allow-insecure-http` style). Keep backwards-compatible defaults during rollout with deprecation warning path. | Done (`core/dashboard_transport.py`, `main.py`, Docker `CMD`)                          |
| 2. Runtime enforcement and warnings       | Enforce secure default behavior; on insecure override, print unmistakable warning on stdout/stderr and structured log fields (`transport_security=insecure_http`).                                                         | Done (stderr banner + `[INFO] dashboard_transport=…`; structured log field can follow) |
| 3. UX warning surfaces                    | Add high-visibility dashboard banner (top half area) for insecure mode and surface same state in API `/status` and health output.                                                                                          | Done                                                                                   |
| 4. Audit trail and evidence               | Record insecure transport mode in audit trail / exported audit JSON so risk acceptance is traceable.                                                                                                                       | ✅ Done (export-audit-trail includes `dashboard_transport`)                             |
| 5. Tests (both scenarios)                 | Add tests for HTTPS mode and HTTP override mode, including warning text, status flags, and banner rendering. Keep CI stable and deterministic.                                                                             | Done (unit + CLI subprocess smoke)                                                     |
| 6. Docs and legal/compliance wording      | Update USAGE/TECH_GUIDE/SECURITY (+ pt-BR), COMPLIANCE_AND_LEGAL wording, and operator runbooks with concrete setup and risk statements.                                                                                   | USAGE + man + help done; broader legal/compliance pass optional                        |
| 7. Transport integrity/tamper trust state | Detect unexpected changes in cert/crypto runtime capability and mark runtime as untrusted/tinted (logs, status, dashboard, DB/audit, report output restrictions, version marker).                                          | ⬜ Pending                                                                              |

### Phase 4 — Audit trail (implemented)

**Goal:** `python main.py --export-audit-trail` (and any future DB-persisted audit row) should include **dashboard transport posture** so risk acceptance is **traceable** in exported JSON.

## Suggested shape (extend `core/audit_export.py`):

- At export time, call `get_dashboard_transport_snapshot()` from `core.dashboard_transport` (same dict as `/status`).
- Add top-level key **`dashboard_transport`** to the payload (or nest under **`runtime_context`** next to `runtime_trust` if you prefer one bucket).
- Fields to persist: at minimum `mode`, `tls_active`, `insecure_http_explicit_opt_in`, `summary` (already in snapshot); omit file paths to certs in export if policy prefers **boolean only** (`cert_configured: true`).
- If **`AUDIT_TRAIL_SCHEMA_VERSION`** bumps, document in release notes and [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) if integrity signing references the export.
- **Tests:** extend `tests/test_audit_export.py` (or add) to set env vars before `build_audit_trail_payload` and assert `dashboard_transport["mode"]` matches.

**Note:** Snapshot reflects **process env** at export time. For one-shot CLI export without starting `main.py --web`, expect `mode: not_configured` unless you later set env in a documented operator workflow.

---

## Concrete technical checklist

1. Add transport args/config:
   - `--https-cert-file`, `--https-key-file` (or equivalent config keys).
   - `--allow-insecure-http` (explicit risk acceptance).
   - Optional `--https-port` and redirect behavior if dual-port is supported.
1. Force clear startup messaging:
   - Secure mode: “Dashboard transport: HTTPS (TLS>=1.2 expected)”.
   - Insecure mode: multi-line warning including interception risk.
1. Add machine-readable indicators:
   - `/status` and health include transport mode + security level.
   - structured logs include `dashboard_transport_mode`.
1. Add UI warning banner:
   - visible in dashboard header/top half while insecure mode is active.
1. Extend tests:
   - unit tests for flag parsing and warning paths.
   - API/status tests for security-state fields.
   - dashboard rendering test for insecure banner.

## Transport integrity and tamper evidence

When secure mode is enabled, the app should detect if TLS/certificate capabilities appear altered by untrusted actors and propagate a **trust downgrade** signal.

### Signals to monitor

- Unexpected certificate/fingerprint change relative to expected baseline (when baseline is configured).
- Unexpected protocol/cipher capability downgrade below configured secure baseline.
- Runtime crypto library/capability mismatch against expected secure profile.

### Required reaction on suspicious state

1. Emit clear warnings to **stdout**, **stderr**, and structured logs.
1. Expose security/trust state on `/status` and health output.
1. Show a prominent dashboard warning banner.
1. Persist trust/tamper event in internal DB/audit trail.
1. Mark generated reports as **tinted/untrusted** and restrict output content (summary-only mode) per existing tamper-response direction.
1. Mark runtime/build identity with a downgraded suffix/state (for example, force `-alpha`-style trust marker) aligned with [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md).

### Non-goal

- This does not guarantee nation-state tamper-proofing by itself; it provides practical detection/evidence and operator-visible blast-radius reduction.

## Rollout strategy

- **Step A (safe introduction):** add feature behind explicit flags and status signals.
- **Step B (default tightening):** switch docs and startup defaults to HTTPS-first.
- **Step C (legacy assist):** keep insecure flag available with strong warnings for controlled exceptions.

## Certificate strategy by environment

### Dev / local testing

- Use a local trusted development CA flow (for example `mkcert`) to avoid browser noise while staying close to HTTPS behavior.
- Keep local certs out of git; load by path/env only.
- Allow `--allow-insecure-http` for quick local troubleshooting, but keep warnings loud.
- Never auto-install a custom root CA into client trusted root stores from the app runtime or installer.

### QA / UAT

- Prefer non-self-signed certificates issued by:
- internal corporate PKI/private CA, or
- ACME-issued certs (for publicly reachable or DNS-validated environments).
- Validate hostname/SAN correctness and renewal process before production.
- Test both direct HTTPS mode and reverse-proxy TLS termination mode.

### Production

- Prefer CA-issued certificates (no self-signed for normal production).
- **Let's Encrypt is a valid option** when DNS/routing and automation fit your environment.
- Also valid: enterprise/commercial CAs or internal PKI, depending on trust model and governance.
- Minimum baseline:
- TLS >= 1.2 (prefer 1.3 where available),
- strong cipher configuration via app/proxy runtime,
- renewal automation and expiry monitoring.

## Explicit anti-pattern (must not do)

Do **not** "fix browser warnings" by misissuing/misdeploying a custom root certificate and pushing it into client machine trusted root stores as an app shortcut.

- This creates broad trust blast radius and weakens endpoint trust boundaries.
- It can make unsafe cert Colleague-Nns appear valid and hides real TLS problems from operators/users.
- It conflicts with secure-by-design goals and auditable trust posture.

## Safer recommendation path

1. Use publicly trusted certs (or enterprise PKI with proper governance), not ad-hoc root trust injection.
1. If private PKI is required, distribute trust via controlled endpoint management policy (IT/MDM/GPO), never app self-install behavior.
1. Keep certificate lifecycle explicit: issuance authority, rotation, revocation, expiry monitoring, and incident response ownership.
1. Preserve clear warnings/failures when trust is invalid; do not suppress trust errors to "look clean."

## CA/provider options (practical)

1. **Let's Encrypt (ACME)**
   - Good default for internet/DNS-validatable deployments.
   - Use `certbot`, `acme.sh`, Traefik, Caddy, or LB-native ACME.
1. **Cloud/LB-managed certificates**
   - AWS ACM, GCP Certificate Manager, Azure Key Vault + App Gateway/Front Door, Cloudflare-managed certs.
   - Excellent when TLS terminates at managed edge/load balancer.
1. **Commercial/public CAs**
   - DigiCert, Sectigo, GlobalSign, Entrust, etc., when policy/procurement requires.
1. **Internal enterprise PKI**
   - Good for private networks and zero-trust internal service patterns; requires proper trust distribution to clients.

## Mandatory crypto baseline (non-negotiable)

When HTTPS-first is implemented, **do not allow weak/legacy crypto** in secure mode.

- **Protocols:**
- deny TLS 1.0 and TLS 1.1;
- require TLS >= 1.2 (prefer TLS 1.3 where possible).
- **Cipher suites / key exchange:**
- deny known weak suites (`NULL`, `aNULL`, `eNULL`, `RC4`, `3DES`, `DES`, `MD5`, export-grade suites);
- deny weak key exchange paths (legacy RSA key exchange without forward secrecy, weak/obsolete DH params);
- prefer modern ECDHE suites with AEAD ciphers.
- **Certificates:**
- deny expired, weak-signature, or weak-key certificates (for example SHA-1-signed leaf certs, RSA < 2048);
- enforce hostname/SAN validation;
- fail closed on certificate validation errors in secure mode.
- **Deprecation / EOL posture:**
- no EOL crypto libraries/tools in the HTTPS path for supported releases;
- treat crypto stack EOL as maintenance priority (same critical-first posture as dependency/security alerts).

## Acceptance criteria (transport security)

Secure mode is only accepted when all checks pass:

1. Runtime refuses insecure protocol versions and weak cipher configurations.
1. Health/status exposes transport security mode and protocol summary.
1. Tests validate rejection of weak/legacy protocol/suite combinations.
1. Docs explicitly state denied legacy crypto and supported baseline.
1. Insecure HTTP override does **not** downgrade secure mode defaults when HTTPS is enabled.
1. Suspicious transport-integrity state triggers trust downgrade and warning surfaces consistently across logs/status/dashboard/audit/report.

## Risks and mitigations

- Risk: cert/key setup friction for local labs.
- Mitigation: provide minimal local certificate quickstart and clear fallback with warning.
- Risk: false sense of security if users rely only on app TLS.
- Mitigation: docs state reverse proxy/network controls still recommended.
- Risk: CI instability with TLS tests.
- Mitigation: deterministic local cert fixtures and scoped tests.

## What else is missing for "secure by design" (beyond HTTPS default)

- **Auth by default path:** converging toward API auth secure defaults with migration-safe rollout.
- **Session/cookie hardening (if applicable):** secure/httponly/samesite and anti-CSRF controls for dashboard flows.
- **Trusted proxy handling:** correct `X-Forwarded-*` usage only from trusted upstreams.
- **Rate limit and abuse controls:** align dashboard/API paths with existing scan rate-limiting strategy.
- **Security headers:** HSTS (when safe), CSP continuity, frame/options and content-type protections.
- **Secrets lifecycle:** no static secrets in tracked config; rotation and env/secret store usage.
- **Observability for security posture:** explicit runtime/security mode in logs/status/audit export.
- **Release gates:** tests for both secure and insecure modes, plus documentation gates to avoid drift.
- **Runtime tamper trust model:** align HTTPS transport signals with build-integrity trust state (`-alpha`/adulterated semantics) to avoid "false confidence" outputs.

## Notes for roadmap/pitch/legal

- **Compliance/legal docs:** good candidate for a short statement about secure transport by default + explicit insecure override risk.
- **Decision-maker pitch:** optional short mention only after baseline implementation lands (avoid promising before behavior is shipped).
- **External security rationale source:** Security Now episode archive and referenced episode discussion on certificate trust misuse vs correct deployment patterns ([GRC Security Now archive](https://www.grc.com/securitynow.htm), [YouTube episode link](https://www.youtube.com/watch?v=JebKuiHu5mg&t=2850s)).

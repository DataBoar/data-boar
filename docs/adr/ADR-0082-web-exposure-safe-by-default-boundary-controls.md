# ADR 0082 — Web exposure safe-by-default boundary controls

- **Date (UTC):** 2026-07-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-07-12 — Proposed.
- 2026-08-13 — Amended: Decision #6 (bootstrap/first-use auth boundary — apparent
  network position is not enough for security-sensitive first-use ceremonies);
  Consequences and References updated for GitHub `#1553`/`#1564` and `#1552`/`#1563`
  (issue [#1567](https://github.com/DataBoar/data-boar/issues/1567)). Status remains
  Proposed; genesis Date (UTC) unchanged.

## Context

Issue [#1202](https://github.com/DataBoar/data-boar/issues/1202) confirmed a set of
web-exposure risks on the community surface:

1. Non-loopback API binds could run without a resolved auth boundary, enabling a
   confused-deputy posture.
2. `POST /scan_database` accepted ad-hoc targets by default.
3. `/logs` and `/logs/{session_id}` were broadly reachable as dashboard routes.
4. `X-Forwarded-Proto` was trusted without explicit proxy trust declaration.
5. Connector inventory snapshots persisted broad probe dumps (`str(info)`) that mixed
   executive and technical details.

The project doctrine is safe-by-default for community deployments: loopback-first, explicit
opt-in for remote-risk surfaces, and auditable access for sensitive operational artifacts.

## Decision

1. **Startup bind gate:** non-loopback bind now requires a resolved built-in auth boundary
   (API key or WebAuthn token secret); otherwise startup aborts.
2. **Ad-hoc target gate:** `api.allow_adhoc_targets` defaults to `false`; when disabled,
   `POST /scan_database` accepts only payloads that match pre-configured targets.
3. **Audit logs hardening:** `/logs` and `/logs/{session_id}` are disabled by default and
   require:
   - `api.audit_logs.enabled: true`;
   - explicit `api.audit_logs.directory`;
   - authenticated role `audit_logs.read` (or `admin`) **only when RBAC enforcement is
     active** — same condition as the dashboard RBAC middleware
     (`api.rbac.enabled` and tier allows `dashboard_rbac`). When RBAC is not active,
     `/logs` follows the same auth posture as `/findings` / `/report` (still subject to
     optional `api.require_api_key`); Community cannot enable in-product RBAC (#1190);
   - best-effort audit event on download.
4. **Forwarded header trust boundary:** `X-Forwarded-Proto` is only trusted when request
   client IP matches `api.trusted_proxy_cidrs`; trust posture is exposed in `/status`.
5. **Inventory detail separation:** Redis/Mongo inventory metadata is reduced to allowlisted
   fields, split between executive and technical views; internal technical sheet is opt-in
   in reports.
6. **Bootstrap/first-use auth boundary:** code paths that grant a key-free exemption based on
   apparent network position (loopback peer IP, `Host` header, resolved DNS) must not do so for
   security-sensitive first-use ceremonies — a same-host reverse proxy or DNS rebinding after
   validation can present attacker-controlled remote traffic as if it were local, without
   forwarded-client headers. First-passkey WebAuthn registration always requires a configured
   API key (`#1553`); outbound connection targets are pinned to pre-validated IPs and never
   re-resolved after the SSRF guard runs (`#1552`). Ongoing authentication ceremonies and other
   already-established trust relationships are unaffected — this applies specifically to the
   bootstrap/first-use window, where there is no existing credential to check against.

## Consequences

- **Positive:** remote exposure without auth is blocked at process start.
- **Positive:** ad-hoc DB scan abuse surface is closed by default.
- **Positive:** audit logs become explicit, opt-in (`audit_logs.enabled`), and role-gated
  when RBAC is active; Community/OPEN are not permanently locked out of their own trail.
- **Positive:** proxy-header spoofing risk is reduced to explicit trusted CIDR chains.
- **Positive:** inventory snapshots avoid over-collection while preserving diagnostics.
- **Positive:** first-use/bootstrap ceremonies can no longer be hijacked by same-host proxy
  or DNS-rebinding trust confusion; outbound connections cannot be redirected post-validation.
- **Trade-off:** operators must explicitly configure `audit_logs` and trusted proxies for
  reverse-proxy deployments; defaults now fail closed.
- **Trade-off:** operators must configure an API key before exposing WebAuthn bootstrap behind
  any reverse proxy, even a trusted same-host one — no loopback-only fast path remains.

## Related Decisions

- [ADR 0049 — No brittle mitigations — robust input handling over symptom suppression](ADR-0049-no-brittle-mitigations-robust-input-handling.md)
- [ADR 0071 — Self-protecting PII gate](ADR-0071-self-protecting-pii-gate.md)

## References

- GitHub issue [#1202](https://github.com/DataBoar/data-boar/issues/1202)
- GitHub issue [#1135](https://github.com/DataBoar/data-boar/issues/1135)
- GitHub issue/PR [#1553](https://github.com/DataBoar/data-boar/issues/1553) / [#1564](https://github.com/DataBoar/data-boar/pull/1564)
- GitHub issue/PR [#1552](https://github.com/DataBoar/data-boar/issues/1552) / [#1563](https://github.com/DataBoar/data-boar/pull/1563)

# ADR 0082 — Web exposure safe-by-default boundary controls

- **Date (UTC):** 2026-07-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

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
   - authenticated role `audit_logs.read` (or `admin`);
   - best-effort audit event on download.
4. **Forwarded header trust boundary:** `X-Forwarded-Proto` is only trusted when request
   client IP matches `api.trusted_proxy_cidrs`; trust posture is exposed in `/status`.
5. **Inventory detail separation:** Redis/Mongo inventory metadata is reduced to allowlisted
   fields, split between executive and technical views; internal technical sheet is opt-in
   in reports.

## Consequences

- **Positive:** remote exposure without auth is blocked at process start.
- **Positive:** ad-hoc DB scan abuse surface is closed by default.
- **Positive:** audit logs become explicit, role-gated, and auditable.
- **Positive:** proxy-header spoofing risk is reduced to explicit trusted CIDR chains.
- **Positive:** inventory snapshots avoid over-collection while preserving diagnostics.
- **Trade-off:** operators must explicitly configure `audit_logs` and trusted proxies for
  reverse-proxy deployments; defaults now fail closed.

## Related Decisions

- [ADR 0049 — No brittle mitigations — robust input handling over symptom suppression](ADR-0049-no-brittle-mitigations-robust-input-handling.md)
- [ADR 0071 — Self-protecting PII gate](ADR-0071-self-protecting-pii-gate.md)

## References

- GitHub issue [#1202](https://github.com/DataBoar/data-boar/issues/1202)
- GitHub issue [#1135](https://github.com/DataBoar/data-boar/issues/1135)

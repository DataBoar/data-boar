# ADR 0059 — Remediation plugin architecture (minimal host hook)

- **Date (UTC):** 2026-08-03
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-03 — Proposed (materializes reserved slot for GitHub #606)
- 2026-08-05 — Amended: host writes findings JSONL from SQLite before `remediate` (#1443; Phase 2 host-export start)

## Context

Open-core discovery and reporting ship in Community/Pro. Enterprise post-scan
**remediation** (tokenize, mask, encrypt) is partner-specific IP and must not
fork core scan paths. Partners need a **stable host hook** before demos and
before L2/L3 isolation layers (#865 epic).

Prior related decisions:

- [ADR 0052](ADR-0052-yaml-plugin-system-centralized-schema.md) — YAML pattern plugins (detection terms), not remediation.
- [ADR 0075](ADR-0075-plugin-auth-file-based-vs-bearer.md) — auth boundary for future L2/L3 (orthogonal to this host hook).

## Decision

1. **Protocol-based contract** — `RemediationPlugin` (`typing.Protocol`,
   `@runtime_checkable`) in `core/plugins/base.py` with `remediate(findings_path,
   config) -> Path`, plus `name` / `version` for Audit Trail. Findings JSONL is
   **read-only** to the plugin; the plugin returns a `remediation_report.json`
   path and must not modify `findings_path` in place.

2. **In-process L1 loading** — `load_remediation_plugin("module.path:ClassName")`
   via `importlib` + protocol check. This slice is **L1 only** (same process).
   L2/L3 isolation, language stubs, and JSON Schema contracts remain in epic #865
   / later issues (#611 SDK docs, etc.).

3. **Fail-graceful host** — `PluginError` (and any `remediate()` failure) is
   logged to stderr; the scan worker **never** aborts because of a missing,
   invalid, or non-conformant plugin (Safe-Hold of the scan outcome).

4. **Enterprise-gated** — feature key `remediation_plugin` in
   `FEATURE_TIER_MAP` requires `Tier.ENTERPRISE`. Lab `Tier.OPEN` continues to
   bypass gates per existing licensing policy. Config opt-in:
   `remediation.enabled` + `remediation.plugin` in YAML.

5. **Host-written findings JSONL (Phase 2 start — #1443)** — When the post-scan
   hook runs with a `db_manager`, the host **materializes**
   `{report.output_dir}/findings_{session_id}.jsonl` from SQLite **before**
   calling `remediate()`. Each line is one metadata-only
   `remediation_targets` object (same taxonomy as the #649 remediation
   manifest). Unknown or empty `session_id` is Safe-Hold (skip + stderr; never
   invent a ghost path). Tokenization / FPE of samples remains a later Phase 2
   deliverable — this decision only binds the **host export wiring**.

## Consequences

**Positive:**

- Third-party remediators load at runtime without core forks.
- Tier COMMUNITY/PRO skip with stderr warning; no exception into the scan path.
- Foundation for partner POC before L2/L3 and SDK docs (#611).
- Plugins receive a real findings path when remediation is enabled on a normal
  scan (no convention-only ghost file).

**Negative / Trade-offs:**

- L1 in-process plugins share the host process address space (mitigated later by L2/L3).
- Import/load failures raise `PluginError` at the loader; the host catches them —
  never silent success when `enabled: true` and the plugin cannot run.
- Call sites must pass `db_manager` into `maybe_run_remediation_hook` for automatic
  JSONL write; without it the hook skips unless an operator-supplied file already
  exists at the conventional path.

## Review trigger

When [PLAN_REMEDIATION_INTERFACE.md](../plans/PLAN_REMEDIATION_INTERFACE.md)
phases **2–3** (tokenized export / re-scan verify) land further (FPE / verify
job), revise this ADR again for the final plugin architecture (including any
L2/L3 promotion). Host JSONL wiring (#1443) is recorded in Decision §5.

## References

- GitHub #606 (minimal hook), #601 (plan), #649 (manifest export), #1443 (findings JSONL wiring), #653 (verify stub follow-up)
- Epic #865 (broader plugin SDK — out of scope for this ADR slice)

# Internal diagnostic aesthetics (Data Boar doctrine)

> **Seed:** [Mark Russinovich / Sysinternals](https://learn.microsoft.com/en-us/sysinternals/)
>
> *"A good diagnostic tool teaches you the system every time you run it."*

This is a **doctrinal manifesto** about how Data Boar's diagnostic surfaces —
`--verbose`, `completão -Privileged`, audit JSON, and the executive report's
methodology section — should *feel*. The bar is **Sysinternals**: dense,
honest, and educational, not a wall of noise.

---

## 1. The Sysinternals bar

Process Explorer, Process Monitor, Autoruns, and ProcDump earned trust over
two decades by doing three things:

1. **Show, don't summarise.** A column exists for everything that matters; the
   user decides what to look at.
2. **Name the unknown explicitly.** When a value is unverified, it says so
   ("not verified"), not a confident lie.
3. **Teach the OS along the way.** Reading the Sysinternals output is a
   short lesson in how the kernel actually works.

Data Boar's diagnostic surfaces aim for the same bar — translated to "the
database kernel" the customer cares about.

---

## 2. The three diagnostic surfaces

### 2.1 `--verbose` (developer / operator console)

**Purpose:** explain what the scanner is doing, in real time, while it is
doing it. Bench tool, not stakeholder doc.

**Bar:**

- Each connector announces dialect, sample limit, statement timeout, and
  fallback strategy *before* running the first sample.
- Every sampling decision logs the strategy label
  (`TOP_NOLOCK_SQLSERVER`, `TABLESAMPLE_SYSTEM_POSTGRESQL`,
  `LIMIT_BASELINE_MYSQL`) — see
  [`connectors/sql_sampling.py`](../../../connectors/sql_sampling.py).
- Demotion events from the fallback hierarchy print one line each, aligned
  ([`THE_ART_OF_THE_FALLBACK.md`](THE_ART_OF_THE_FALLBACK.md) §3).
- No invented metrics. If a number is an estimate, the line says
  `~estimate=...` not `count=...`.

### 2.2 `completão -Privileged` (lab orchestration)

**Purpose:** prove the lab still mirrors the customer environment. SRE
observability, not marketing copy.

**Bar:**

- Each lab host prints its inventory header (OS, kernel, Docker, Python, free
  disk) before any test runs.
- Each step prints `[k/N] <step>` plus its measured wall time and exit code.
- Failures emit an **RCA block** modelled on Cloudflare post-mortems: which
  step, which host, what the next manual command would be (see
  [`DEFENSIVE_SCANNING_MANIFESTO.md`](DEFENSIVE_SCANNING_MANIFESTO.md) §1).
- Privileged steps say `sudo -n` or "interactive" — never silently fall
  through.

### 2.3 Audit JSON / scan manifest

**Purpose:** evidence-grade artefact. The DPO, CISO, or auditor reads this in
six months without the operator on call.

**Bar:**

- Schema-validated. Field names are stable; new fields are additive.
- Sampling caps, statement timeouts, dialect posture, and `safety_tags` are
  always present, even when the scanner did not actually trip them.
  *Absence of a key is a bigger problem than a non-default value.*
- Every audit entry carries `session_id` so the row is reproducible.
- See [`report/scan_evidence.py`](../../../report/scan_evidence.py) and
  [`report/evidence_collector.py`](../../../report/evidence_collector.py).

---

## 3. Voice and density (style)

The diagnostic voice is **Russinovich**, not **status page**:

- **Short, technical, factual.** No exclamation marks. No "everything
  is fine!". Either it is fine and we say so once, or it isn't and we say
  exactly what is wrong.
- **One concept per line.** Multi-clause lines are for prose, not logs.
- **Numbers with units.** `wall_time=14.2s`, not `time=14.2`.
- **Dialect-aware vocabulary.** Use `WITH (NOLOCK)` for SQL Server,
  `TABLESAMPLE SYSTEM` for PostgreSQL — the right name for the right engine,
  always.

Counter-example (don't):

```text
✨ Scan completed successfully!! 🚀
Tables: a lot
Findings: many
```

Better (do):

```text
scan finished
  session_id        2026-04-27_lab_node_01_a993c0dc
  tables_visited    248 / 248
  rows_sampled      18_412 (cap=10000/col, no overrun)
  fallback_demotions 3   (see scan_manifest_2026-04-27.yaml#fallbacks)
  safety_tags       NOLOCK_SQLSERVER, TABLESAMPLE_PG, COMPLIANCE_COMMENT
```

---

## 4. The "no invented numbers" rule

This is borrowed from
[`.cursor/rules/publication-truthfulness-no-invented-facts.mdc`](../../../.cursor/rules/publication-truthfulness-no-invented-facts.mdc)
and applies hard inside diagnostic output:

- Never round to a confidence we did not measure.
- Never print a percentile from fewer than the documented minimum samples.
- Never quote a "compliance score" the scanner did not derive deterministically
  from its own audit log.

If the data is not there, the line says so. That is more useful than a
confident average.

---

## 5. Do / don't (review checklist)

### Do

- Add a column when a real signal exists and the user might filter on it.
- Write the diagnostic line as if a DBA will paste it into a ticket.
- Surface the **last** demotion reason from the fallback hierarchy in the
  methodology section of the executive report (see
  [`ACTIONABLE_GOVERNANCE_AND_TRUST.md`](ACTIONABLE_GOVERNANCE_AND_TRUST.md)).

### Don't

- Don't add emojis to logs that auditors will read. Emojis live in chat and
  README pitch, not in `scan_manifest_*.yaml` or `--verbose` output.
- Don't truncate sampling statements in audit JSON. Truncation is what causes
  reviewers to mistrust the artefact.
- Don't ship a new `--verbose` line without checking that
  `tests/test_scan_audit_log.py` still passes.

---

## 6. Where this is enforced

| Surface | File | Test |
| ------- | ---- | ---- |
| Sampling label and SQL composition | [`connectors/sql_sampling.py`](../../../connectors/sql_sampling.py) | `tests/test_sql_sampling.py` |
| Audit log shape | [`core/scan_audit_log.py`](../../../core/scan_audit_log.py) | `tests/test_scan_audit_log.py` |
| Scan manifest | [`report/scan_evidence.py`](../../../report/scan_evidence.py) | `tests/test_scan_evidence.py` |
| Executive report methodology section 3 | [`report/executive_report.py`](../../../report/executive_report.py) | `tests/test_executive_report*.py` |

---

## 7. Related

- [`DEFENSIVE_SCANNING_MANIFESTO.md`](DEFENSIVE_SCANNING_MANIFESTO.md) — what we
  show is what we promised.
- [`THE_ART_OF_THE_FALLBACK.md`](THE_ART_OF_THE_FALLBACK.md) — every demotion
  is logged.
- [`ACTIONABLE_GOVERNANCE_AND_TRUST.md`](ACTIONABLE_GOVERNANCE_AND_TRUST.md) —
  these surfaces feed the stakeholder narrative.

A diagnostic that does not teach is a diagnostic that will not be trusted.

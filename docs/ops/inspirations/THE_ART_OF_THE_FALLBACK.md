# The art of the fallback (Data Boar doctrine)

> **Seeds:** [Usagi Electric](https://www.youtube.com/@UsagiElectric) ·
> [The 8-Bit Guy](https://www.youtube.com/@The8BitGuy)
>
> *"If the component is old and dirty, the system has to know how to handle it."*

This is a **doctrinal manifesto** — not a tone reference and not a roadmap. It
describes how Data Boar must behave when a "Data Soup" input is unfamiliar,
malformed, or partially readable.

---

## 1. Why this exists

Customer environments are never as clean as a developer laptop. Database
exports come with corrupted UTF-8 sequences, `.docx` files masquerading as
`.zip`, vintage spreadsheets with mixed cell encodings, and SQL dialects that
the parser was never tested against. **Data Boar must keep going and emit a
diagnostic** — silent failure is a worse outcome than degraded coverage.

Two restorers inspire this posture:

- **Usagi Electric** documents reverse-engineering machines that "should not
  boot anymore" — and books every dead end as evidence. Patience plus an
  honest log are the deliverables.
- **The 8-Bit Guy** restores 8-bit machines on tight constraints, with cheap
  tools and methodical narration. Resource scarcity is not an excuse to skip
  the diagnostic.

Together: **resilience all the way to the silicon, with a paper trail**.

---

## 2. The fallback hierarchy (canonical order)

When parsing a customer payload — SQL dialect, semi-structured export, raw
text blob — Data Boar tries the **strongest** strategy first, then degrades:

1. **Parser SQL** (preferred).
   Use SQLAlchemy / sqlparse / dialect-aware AST when the source declares a
   known dialect. Strongest signal, smallest false positive surface.

2. **Regex pattern** (degraded but bounded).
   When the AST cannot consume the payload (e.g. mixed-dialect dump), fall
   back to anchored regex with documented patterns. Patterns must be
   reviewed and never run unbounded over arbitrary memory.

3. **Raw string heuristics** (last resort).
   Token-frequency / dictionary scoring, leading-byte checks for binary
   formats, encoding-resilient byte scans for sensitive markers. Used only
   when steps 1 and 2 declined to commit, and explicitly labeled as
   `"strategy": "raw_string_heuristic"` in audit output.

The hierarchy is **monotonic**: a connector never tries `raw_string` before
attempting (and refusing) `regex`, and never tries `regex` before attempting
(and refusing) `parser`. Skipping levels hides bugs.

---

## 3. The "diagnostic on fall" rule

> **Data Boar never falls through to a weaker level silently.**

Every fallback step **must** produce an audit entry containing:

- The level tried (`parser_sql`, `regex`, `raw_string`).
- A short, factual reason for the demotion (e.g. `"sqlparse: unrecognized
  dialect"`, `"regex: anchor budget exceeded"`).
- The next level chosen.
- A correlation id (`session_id` + table/column when applicable).

These entries are surfaced through
[`core/scan_audit_log.py`](../../../core/scan_audit_log.py) and
[`report/scan_evidence.py`](../../../report/scan_evidence.py); the executive
report quotes the **last** demotion reason in its methodology section.

Operator-facing example:

```text
[fallback] table=customers column=notes
  parser_sql      → declined (dialect=mixed_postgres_mssql)
  regex           → declined (budget=512 KiB exceeded)
  raw_string      → engaged (heuristic=cpf_proximity, samples=200)
```

---

## 4. Do / don't (review checklist)

### Do

- Treat every "Data Soup" surprise as a **first-class data point**, not an
  exception to swallow.
- Cap each strategy: byte budget, regex compile time, sample rows.
- Emit the demotion reason in the **same audit row** as the eventual finding,
  so a reviewer can re-run with the same `session_id` and reproduce.
- When in doubt, reduce **coverage**, never **truthfulness** of the audit log.

### Don't

- Don't catch a parser error and continue with `regex` *without* logging the
  demotion. That is the failure mode this manifesto exists to prevent.
- Don't add a fourth level "below raw string" without an ADR. Heuristics that
  fire on entropy alone produce noise that taints the executive report.
- Don't reuse a strategy label across dialects when the implementation differs
  (see audit traceability rules in
  [`DEFENSIVE_SCANNING_MANIFESTO.md`](DEFENSIVE_SCANNING_MANIFESTO.md)).

---

## 5. Where this is (and will be) enforced

| Layer | File | Enforcement |
| ----- | ---- | ----------- |
| SQL sampling SQL composition | [`connectors/sql_sampling.py`](../../../connectors/sql_sampling.py) | Strategy label per plan; no implicit `ORDER BY`; dialect-aware. |
| Audit log shape | [`core/scan_audit_log.py`](../../../core/scan_audit_log.py) | Provider summary + per-connector strategy summary. |
| Executive report methodology | [`report/executive_report.py`](../../../report/executive_report.py) | Section 3 — last demotion reason quoted. |
| Plan that drives Slices 2–3 | [`PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md`](../../plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md) | Adds RCA block + doctrinal comments referencing this file. |

---

## 6. Related manifestos and rules

- [`DEFENSIVE_SCANNING_MANIFESTO.md`](DEFENSIVE_SCANNING_MANIFESTO.md) — why each
  step has a hard cap.
- [`INTERNAL_DIAGNOSTIC_AESTHETICS.md`](INTERNAL_DIAGNOSTIC_AESTHETICS.md) — how
  the demotion log should *read* in `--verbose`.
- [`ACTIONABLE_GOVERNANCE_AND_TRUST.md`](ACTIONABLE_GOVERNANCE_AND_TRUST.md) —
  why the executive report must surface fallback evidence.

The scanner does not stop. The diagnostic does not get skipped. That is the
whole rule.

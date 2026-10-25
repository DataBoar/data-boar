# Defensive scanning manifesto (Data Boar doctrine)

> **Seeds:** [NASA Software Engineering Lab](https://nasa.github.io/) ·
> [Cloudflare Engineering blog](https://blog.cloudflare.com/) ·
> [Steve Gibson / Security Now](https://www.grc.com/securitynow.htm)
>
> *"Test what you fly. Failing in production is not an acceptable outcome."*

This is a **doctrinal manifesto**. It states the non-negotiable rules Data Boar
must follow when it touches a customer database — the same way a pilot treats a
running turbine: with respect, instrumented redundancy, and a checklist.

---

## 1. The contract with the customer database

Data Boar is a **guest**. The customer keeps liability for the database; we
must keep liability for our impact on it. The contract has four clauses:

1. **No unbounded scans.** Every read has a hard sample cap and a wall-clock
   budget.
2. **No exclusive locks.** Where the dialect supports it, sampling reads use
   the lowest isolation that satisfies "compliance-style read" — see §3 on
   `WITH (NOLOCK)`.
3. **No surprise side effects.** No `DDL`, no temp objects on the customer
   instance, no schema mutation under `--verbose` or `--debug`.
4. **No anonymous footprint.** Every emitted statement is tagged so a DBA can
   grep activity views and identify Data Boar without paging the operator.

The seeds for this posture:

- **NASA SEL** — *test what you fly*. The same scan code paths that run in the
  customer environment are exercised in `tests/` and in the lab `completão`.
- **Cloudflare Engineering** — protocol rigor and **public** post-mortems with
  numeric evidence. When something fails in the lab, we publish the RCA with
  numbers, not vibes.
- **Steve Gibson** — non-invasive, verifiable code. SpinRite earned trust by
  being explicit about what it would *not* do; Data Boar inherits that posture.

---

## 2. Sampling caps and statement timeouts (relief valves)

The defaults are **bounded**. Operators can tune via env or YAML, but the
runtime clamps to a hard maximum. Treat these as **relief valves**, not knobs.

| Control | Default | Hard ceiling | Code |
| ------- | ------- | ------------ | ---- |
| `DATA_BOAR_SQL_SAMPLE_LIMIT` | YAML config | `10_000` rows / column | [`connectors/sql_sampling.py`](../../../connectors/sql_sampling.py) `_HARD_MAX_SAMPLE` |
| `DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS` | none in driver | `60_000` ms (60 s) | same file, `resolve_statement_timeout_ms_for_sampling` |
| PostgreSQL `TABLESAMPLE SYSTEM (p)` | 1.0 % | 0.01–100.0 % | `_pg_tablesample_system_percent` |
| SQL Server `TABLESAMPLE SYSTEM (p)` | 10.0 % | 0.01–100.0 % | `_mssql_tablesample_system_percent` |

These caps are **enforced** in code (`max(1, min(...))`), not asked nicely in
the docs. Invalid env values fall back to the documented base — never to
"unbounded".

---

## 3. Dialect-specific posture (do not blur dialects)

| Dialect | Rule | Reason |
| ------- | ---- | ------ |
| **Oracle** | `ROWNUM` is applied on the *outer* query; the inner query filters `IS NOT NULL` first. | Avoids feeding the row limit with null-only rows; classic Oracle subquery shape. |
| **Snowflake** | `SAMPLE (n ROWS)` on a non-null-filtered inline view. | Warehouse / cost-aware reads. |
| **SQL Server** | `SELECT TOP (n) … FROM … WITH (NOLOCK)` | Compliance-style **read-only sampling**: blocking on long writers is unacceptable; dirty / non-repeatable reads are accepted **only** because the output is sampling-grade and never feeds transactional decisions. |
| **PostgreSQL** | `LIMIT` baseline; `TABLESAMPLE SYSTEM` plus `LIMIT` only when row-count metadata says the table is large. | Avoids sequential bias on very large heaps. |
| **MySQL / DuckDB / Cockroach** | `LIMIT` only. | Dialect simplicity; no implicit `ORDER BY`. |

**`WITH (NOLOCK)` is a contract, not a hack.** It documents that Data Boar
will never block a writer, even if that means we read a tuple that is about to
be rolled back. We accept that asymmetry because the alternative — pinning a
shared lock during a long scan — would violate clause 2 of §1.

---

## 4. Statement attribution (DBA-grep contract)

Every emitted sampling statement begins with the line comment:

```sql
-- Data Boar Compliance Scan
SELECT TOP (n) ... FROM ... WITH (NOLOCK)
```

A DBA tailing `pg_stat_activity` / DMVs can identify Data Boar without
reverse-engineering the query plan. This comment is **not** decorative; it is
how a DBA decides whether to kill our session vs page the operator.

The leading comment is enforced in
[`connectors/sql_sampling.py`](../../../connectors/sql_sampling.py)
(`_COMPLIANCE_SCAN_LEADING`) — do **not** remove it in refactors.

---

## 5. No `ORDER BY` on auto-sampling

`ORDER BY` on a non-indexed column forces a full-table sort. That is the
opposite of "compliance-style read". The composition layer **must not** inject
`ORDER BY` into auto-sampling SQL; dialect caps (`TOP` / `LIMIT` / `ROWNUM` /
`SAMPLE`) and dictionary row hints carry the bound.

If a connector ever needs deterministic ordering, that requires an ADR and an
explicit `--ordered-sample` opt-in, not a quiet behavior change.

---

## 6. Do / don't (PR review checklist)

### Do

- Cap **every** read in code. If the cap is "configurable", clamp it.
- Tag every statement with `-- Data Boar Compliance Scan`.
- Document new dialects in this file *before* shipping the connector.
- Treat `WITH (NOLOCK)` and `TABLESAMPLE` as protocol decisions, not micro-
  optimizations.

### Don't

- Don't add a "fast path" that bypasses the sampling manager. There is one
  composition layer; benchmark inside it.
- Don't accept "the customer asked us to remove the leading comment". Make
  this section the answer in the PR thread.
- Don't run `OPTION (RECOMPILE)` or `WITH (READUNCOMMITTED)` as defaults — the
  former wastes plan cache, the latter is a SQL Server alias for `NOLOCK` and
  belongs as one explicit code path, not two.
- Don't escalate from "compliance scan" to "audit-grade scan" silently. That
  needs a new SKU and an ADR.

---

## 7. Where this is enforced

- **Composition:** [`connectors/sql_sampling.py`](../../../connectors/sql_sampling.py)
- **Audit emission:** [`core/scan_audit_log.py`](../../../core/scan_audit_log.py)
- **Tests:** `tests/test_sql_sampling.py`, `tests/test_scan_audit_log.py`,
  `tests/test_scan_evidence.py`.
- **Operator docs:** [`docs/USAGE.md`](../../USAGE.md) §SQL sampling,
  [`docs/TESTING.md`](../../TESTING.md).
- **Plan that drives Slices 2–3:**
  [`PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md`](../../plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md).

The scanner is a guest in someone else's house. It says *thank you*, leaves the
lights as it found them, and signs the visitor's book.

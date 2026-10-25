# Actionable governance and trust (Data Boar doctrine)

> **Seeds:** [Tailscale narrative discipline](https://tailscale.com/blog) ·
> [Charity Majors / Honeycomb](https://charity.wtf/) ·
> [Cloudflare post-mortems](https://blog.cloudflare.com/)
>
> *"The system must explain itself. The report does not deliver findings — it
> delivers the path to the cure."*

This is a **doctrinal manifesto** about the customer deliverable: the
executive report, the action plan generator (APG), and the surrounding
narrative. The bar is **observability + actionability**: a stakeholder must be
able to read the artefact and know what to *do* next.

---

## 1. The deliverable contract

A Data Boar engagement leaves three artefacts on the table:

1. **Executive Markdown** — `data-boar-report` output, stakeholder-grade
   narrative, generated from a fixed `session_id`.
2. **Scan manifest YAML** — `scan_manifest_*.yaml`, machine-readable evidence
   that backs every claim in the Markdown.
3. **Reproducible CLI invocation** — the exact `data-boar-report` command and
   the SQLite session that powers it.

These three together form the "trust triangle". Removing any one of them
turns the deliverable into a slide deck — which is **not** what the customer
is paying for.

The seeds for this posture:

- **Tailscale** — when something is going wrong, the product writes a
  *short, honest, actionable* page that says what happened and what to do.
  No corporate dampening.
- **Charity Majors / Honeycomb** — *the system must explain itself.* If the
  operator has to read source to know what happened, observability has
  failed.
- **Cloudflare post-mortems** — numeric evidence, with timestamps, with the
  "what we changed" section clearly visible.

---

## 2. The Action Plan Generator (APG) — the "path to the cure"

The executive Markdown's section **4 — Plano de ação (APG)** is **not** a
sorted list of findings. It is the customer's *path to the cure*.

Required structure (already enforced by
[`report/executive_report.py`](../../../report/executive_report.py)):

| Subsection | Purpose | Voice |
| ---------- | ------- | ----- |
| `### 4.1 Prioridades imediatas (Top 3)` | Three highest-leverage actions. | Imperative, single sentence each. |
| `### 4.2 Inventário por tipo de dado (achado → risco → recomendação técnica)` | Full per-pattern inventory. | Three columns, no narrative bridges. |

**Doctrine:**

- Each `Top 3` entry must be **doable by the customer**, not by us. If the
  fix requires Data Boar to ship a new feature, that goes in Section 5
  (roadmap notes), not Section 4.
- Each inventory row must cite a **pattern**, a **risk class**, and a
  **technical remediation** — no vague "review and remediate".
- No raw cell samples. No table/column tuples that would leak the customer's
  actual data into the deliverable. Counts and patterns only — see
  [`docs/REPORTS_AND_COMPLIANCE_OUTPUTS.md`](../../REPORTS_AND_COMPLIANCE_OUTPUTS.md).

The APG exists because *findings without a remediation path are anxiety
delivery, not security*. We do not ship anxiety.

---

## 3. The methodology of safety (Section 3)

The Markdown's section **3 — Metodologia e segurança** is where we prove we
were a good guest in the customer's database. It cites:

- The sampling caps actually applied (per dialect).
- The statement timeout in milliseconds.
- The dialect posture (`WITH (NOLOCK)` for SQL Server,
  `TABLESAMPLE SYSTEM` for PostgreSQL, etc.).
- The leading SQL comment for DBA traceability.
- The **last fallback demotion** when one occurred during the session
  (cross-reference [`THE_ART_OF_THE_FALLBACK.md`](THE_ART_OF_THE_FALLBACK.md)).

This section is the same reason a pilot signs the maintenance log: it makes
the contract from
[`DEFENSIVE_SCANNING_MANIFESTO.md`](DEFENSIVE_SCANNING_MANIFESTO.md) auditable
*after* the fact, not just *during* the scan.

**Slice 3 of [PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md](../../plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md)**
extends this section with explicit prose: "we treated this database the way a
pilot treats a running turbine".

---

## 4. The system explains itself (Honeycomb posture)

The deliverables answer three "self-explanation" questions without the
operator on the phone:

| Question | Where the answer lives |
| -------- | ---------------------- |
| *What did Data Boar do, and on what scope?* | Markdown § 2 + scan manifest `audit_trail`. |
| *Did Data Boar respect the database while doing it?* | Markdown § 3 + manifest `safety_tags`. |
| *What should the customer do, in what order?* | Markdown § 4 (APG) + § 5 (roadmap notes). |

If a stakeholder cannot answer one of those by reading the artefact, that is
a doctrinal bug — file it as a `PLAN_*.md` row, not a "we'll explain on the
call" workaround.

---

## 5. Do / don't (review checklist)

### Do

- Treat the executive report as a **product surface** — every PR that
  changes its sections gets `tests/test_executive_report*.py` updated.
- Land the APG before the findings table when the audience is non-technical.
- Quote the last fallback demotion and the actual sampling cap, not generic
  "best-effort sampling".
- Pair every claim in the Markdown with a manifest field a reviewer can
  grep.

### Don't

- Don't write "vulnerability density score" or any composite metric without
  a deterministic derivation in code. See the *no invented numbers* rule in
  [`INTERNAL_DIAGNOSTIC_AESTHETICS.md`](INTERNAL_DIAGNOSTIC_AESTHETICS.md) §4.
- Don't replace the APG with a "risk heatmap only" view. Heatmaps are
  decorative without an action plan attached.
- Don't gate Section 3 (methodology) on "if the operator opted in to verbose
  audit". Section 3 is **always** present; what changes is the depth of the
  manifest.

---

## 6. Where this is enforced

| Layer | File |
| ----- | ---- |
| Executive Markdown sections | [`report/executive_report.py`](../../../report/executive_report.py) |
| Scan manifest schema | [`report/scan_evidence.py`](../../../report/scan_evidence.py) · [`schemas/`](../../../schemas/) |
| Recommendation engine (APG inputs) | [`report/recommendation_engine.py`](../../../report/recommendation_engine.py) |
| Tests | `tests/test_executive_report*.py` · `tests/test_scan_evidence.py` |
| Operator narrative | [`docs/REPORTS_AND_COMPLIANCE_OUTPUTS.md`](../../REPORTS_AND_COMPLIANCE_OUTPUTS.md) · [`docs/plans/BENCHMARK_EVOLUTION.md`](../../plans/BENCHMARK_EVOLUTION.md) §1 |

---

## 7. Related

- [`DEFENSIVE_SCANNING_MANIFESTO.md`](DEFENSIVE_SCANNING_MANIFESTO.md) — what we
  promised the database.
- [`THE_ART_OF_THE_FALLBACK.md`](THE_ART_OF_THE_FALLBACK.md) — what we promised
  about resilience.
- [`INTERNAL_DIAGNOSTIC_AESTHETICS.md`](INTERNAL_DIAGNOSTIC_AESTHETICS.md) — how
  the underlying audit looks.
- [`ENGINEERING_BENCH_DISCIPLINE.md`](ENGINEERING_BENCH_DISCIPLINE.md) — the
  bench that produces these artefacts repeatably.

The customer keeps the report after the engagement ends. It must still be
useful in six months, with no operator on call. That is the bar.

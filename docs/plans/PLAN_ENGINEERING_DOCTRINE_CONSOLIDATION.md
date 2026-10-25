**Status:** Slices 1–3 complete on `main` (Slice 1 manifestos, Slice 2 RCA block, Slice 3 single-pass Pro fallback) — Slice 4 governance + benchmark refresh in flight

# Plan — Engineering doctrine consolidation (Data Boar DNA)

**Status:** Active
**Date:** 2026-04-27
**Authors:** Fabio Leitao
**Priority:** H0
**Depends on:** ADR-0046, ADR-0047

> *"Hope is not a strategy, but a well-built tool is."*

This plan consolidates the **Data Boar engineering doctrine** so that craftsmanship,
defensive scanning posture, fallback resilience, internal diagnostic aesthetics,
and actionable governance are documented **before** they are refactored into
code. It is a SRE-first, doc-first effort: each Slice is small, auditable, and
non-destructive to the customer database (zero impact on locks, sessions, or
transactional state).

The doctrine is sourced from the **Council of Mentors** (existing internal seeds
plus the new external seeds the operator added). Inspirations are **inputs, not
mandates** — see [docs/ops/inspirations/README.md](../ops/inspirations/README.md).

---

## 0. Council of Mentors (seeds for this plan)

Internal seeds already present in
[`docs/ops/inspirations/`](../ops/inspirations/) — improved, **never** rewritten
into a single voice:

- **Steve Gibson / Security Now** — verifiable, non-invasive code (SpinRite-style).
- **Adam Savage** — bench discipline and first-order retrievability.
- **Veronica Explains** — empathetic CLI didactics.
- **Aviões e Músicas (Lito Sousa)** — checklist culture for safety-critical systems.

External seeds (new) to inject DNA from:

- **Usagi Electric** — reverse engineering and "down to the silicon" resilience
  on dirty inputs.
- **The 8-Bit Guy** — efficient operation and restoration in resource-scarce
  environments.
- **Cloudflare Engineering** — protocol rigor and transparent post-mortems.
- **NASA Software Engineering Lab** — *test what you fly*; failing in production
  is not an acceptable outcome.
- **Mark Russinovich (Sysinternals)** — gold standard for diagnostic utilities;
  visibility into the database "kernel".
- **Julia Evans (b0rk)** — visual narrative; making SQL/networking intuitive
  through clear, layered explanation.
- **Charity Majors (Honeycomb)** — observability; the system must *explain
  itself* without external intervention.

---

## 1. RCA-style problem statement

**Symptom.** Cursor agents and contributors occasionally read the
`docs/ops/inspirations/` table and the `engineering craft` long table and walk
away with a tone reference, but **not** with a normative posture they can apply
to a code review or a connector PR. The result is uneven enforcement of:

- Defensive scanning (timeouts, `WITH (NOLOCK)`, sampling caps, leading
  comments) across new connectors.
- Fallback hierarchy (Parser SQL → Regex → Raw strings) when an unfamiliar
  "Data Soup" format hits the scanner.
- Diagnostic narrative in `--verbose` and `completão` outputs (sometimes
  Sysinternals-grade, sometimes terse).
- "Path to cure" framing in the executive report — versus a list of findings.

**Root cause.** The doctrine is implicit, scattered across rules, ADRs, and
inspirations rows. There is no single, normative manifesto block per theme that
a reviewer can cite in a PR comment.

**Constraint (non-negotiable).** Anything we change in code from this plan must
preserve the **defensive scanning** posture documented in
[`connectors/sql_sampling.py`](../../connectors/sql_sampling.py) (sampling caps,
`WITH (NOLOCK)`, statement timeouts, leading `-- Data Boar Compliance Scan`
comment) — see also
[`core/scan_audit_log.py`](../../core/scan_audit_log.py) and
[`report/executive_report.py`](../../report/executive_report.py). **Zero new
locks. Zero behavior changes in this plan's Slice 1.**

---

## 2. Execution Slices (small, auditable, SRE-first)

### Slice 1 — Doctrine manifestos (doc-only, this PR)

Add five normative manifesto files under `docs/ops/inspirations/`. Each file is
**short** (1–2 screens), **cites the seed mentor(s)**, gives **explicit do /
don't** rules, and links to the in-repo artifacts (rules, ADRs, code) where the
doctrine is already enforced or will be.

| File | Seeds | Scope |
| ---- | ----- | ----- |
| `THE_ART_OF_THE_FALLBACK.md` | Usagi Electric · The 8-Bit Guy | Fallback hierarchy: Parser SQL → Regex → Raw strings; never silently fail; always emit a diagnostic of *why* we fell back. |
| `DEFENSIVE_SCANNING_MANIFESTO.md` | NASA · Cloudflare · Steve Gibson | Sampling caps, statement timeouts, `WITH (NOLOCK)` posture, leading SQL comments, "gentleman in the customer DB" rule. |
| `ENGINEERING_BENCH_DISCIPLINE.md` | Adam Savage · Julia Evans · Aviões e Músicas | Bench ergonomics: `check-all`, `completão`, narrated logs; checklist culture for safety-critical scans. |
| `INTERNAL_DIAGNOSTIC_AESTHETICS.md` | Mark Russinovich (Sysinternals) | What `--verbose`, `completão -Privileged`, and audit JSON should *feel* like — a low-level diagnostic class, not a wall of noise. |
| `ACTIONABLE_GOVERNANCE_AND_TRUST.md` | Tailscale narrative · Charity Majors (Honeycomb) | The executive report delivers the *path to the cure* (APG), not just findings; observability so the system explains itself. |

**Done when (Slice 1):** the five files exist, the inspirations hub
([`INSPIRATIONS_HUB.md`](../ops/inspirations/INSPIRATIONS_HUB.md) +
[`README.md`](../ops/inspirations/README.md)) lists them under a new
**Doctrine** block, `PLANS_TODO.md` has a row pointing here, and `lint-only`
(`uv run pre-commit run --all-files`) is green.

### Slice 2 — Mission-critical rigor in `completão` (RCA + auditability)

Apply MythBusters-style rigor to the lab orchestrator:

1. When `scripts/benchmark-ab.ps1` A/B benchmark fails or regresses, emit a
   **technical, Sysinternals-style RCA block** (which step, exit code, narrowed
   hypothesis), not "completão failed".
2. Mathematically prove (in the report) that Data Boar respected SRE limits:
   sampling caps, statement timeouts, no `ORDER BY` injected on auto-sampling,
   leading SQL comment present.

**Touches:** `scripts/lab-completao-orchestrate.ps1`,
`scripts/benchmark-ab.ps1`, `report/executive_report.py` methodology section,
and tests under `tests/test_scan_audit_log.py`.

**Constraint:** no new live connector reads at report-regen time; APG path
(see `docs/plans/BENCHMARK_EVOLUTION.md` §1) stays SQLite-only.

### Slice 3 — Doctrinal comments in code (refactor, behavior-preserving)

Add **doctrine-grade** code comments referencing the manifestos created in
Slice 1, only on the files that already implement the doctrine:

```python
# NASA-style checklist: ensure connection safety before scan
# (Ref: docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md)
```

Plus a new **Methodology of Safety** section in the executive Markdown produced
by the **`data-boar-report`** CLI (**Python:** `cli/reporter.py` / console script
in `pyproject.toml` — **not** the Rust crate). The Rust optional pre-filter lives
only in **`rust/boar_fast_filter/`** (`boar_fast_filter`). The Markdown section
explains how we treat the customer database with the same respect a pilot gives
a running turbine.

**Constraint:** `refactor:` only — no behavior change. Tests:
`tests/test_executive_report*.py`, `tests/test_scan_audit_log.py`,
`tests/test_sql_sampling.py`.

### Slice 4 — Benchmark evolution + integrity (close the loop)

Update [`docs/plans/BENCHMARK_EVOLUTION.md`](BENCHMARK_EVOLUTION.md) with a
narrative comparing **v1.7.3** to **HEAD**, citing where we gained resilience
(*Art of the Fallback*) and coverage. Run `.\scripts\check-all.ps1` until 100%
green; only then mark Slice 4 done.

---

## 3. Out of scope (explicitly deferred)

- Renaming the `connectors/` module hierarchy.
- Touching `core/detector.py` ML/DL gates in the same PR as the doctrine work.
- New CLI flags. The doctrine is documentation + comments + RCA blocks. New
  flags require their own `PLAN_*.md` per
  [`.cursor/rules/docs-plans.mdc`](../../.cursor/rules/docs-plans.mdc).

---

## 4. Sequential to-dos

| Step | Slice | Description | Status |
| ---- | ----- | ----------- | ------ |
| 1 | 1 | Author this plan | ✅ Done |
| 2 | 1 | Add `THE_ART_OF_THE_FALLBACK.md` | ✅ Done |
| 3 | 1 | Add `DEFENSIVE_SCANNING_MANIFESTO.md` | ✅ Done |
| 4 | 1 | Add `ENGINEERING_BENCH_DISCIPLINE.md` | ✅ Done |
| 5 | 1 | Add `INTERNAL_DIAGNOSTIC_AESTHETICS.md` | ✅ Done |
| 6 | 1 | Add `ACTIONABLE_GOVERNANCE_AND_TRUST.md` | ✅ Done |
| 7 | 1 | Wire new files into the inspirations hub | ✅ Done |
| 8 | 1 | Add `PLANS_TODO.md` row + refresh `plans-stats` / `plans_hub_sync` | ✅ Done |
| 9 | 2 | RCA block in `data-boar-report` / `completão` failure path | ✅ Done (`cli/reporter.py` Sysinternals-style RCA on stderr; `tests/test_cli_reporter_rca.py` pins shape) |
| 10 | 2 | Methodology proof in `data-boar-report` | ✅ Done (manifest Section 3 already cites resolved sample caps + statement timeouts + leading SQL comment; RCA block names every step that consumes those invariants) |
| 11 | 3 | Doctrinal comments referencing manifestos (refactor only) | ✅ Done (`pro/worker_logic.py` single-pass + `pro/engine.py` chunk-copy skip; tests/test_basic_python_scan_single_pass_parity.py pins parity) |
| 12 | 4 | Refresh `BENCHMARK_EVOLUTION.md` with v1.7.3 → HEAD narrative + 0.574x debt baseline | 🔄 In progress (this commit window) |

---

## 5. References

- [`docs/ops/inspirations/INSPIRATIONS_HUB.md`](../ops/inspirations/INSPIRATIONS_HUB.md)
- [`docs/ops/inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md`](../ops/inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md)
- [`docs/plans/BENCHMARK_EVOLUTION.md`](BENCHMARK_EVOLUTION.md)
- [`connectors/sql_sampling.py`](../../connectors/sql_sampling.py) — defensive sampling SQL.
- [`core/scan_audit_log.py`](../../core/scan_audit_log.py) — audit log build.
- [`report/executive_report.py`](../../report/executive_report.py) — APG output.
- AGENTS.md — *Quick index* and *Risk posture* bullets.

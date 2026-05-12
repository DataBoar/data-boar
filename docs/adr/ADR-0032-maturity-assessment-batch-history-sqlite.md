# ADR 0032 — Maturity self-assessment: per-batch history on the dashboard HTML

- **Status:** Accepted
- **Date (UTC):** 2026-04-20
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

- The GRC maturity POC stores answers in SQLite (`maturity_assessment_answers`) with a client-generated **`batch_id`** per submission ([PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md)).
- Operators need to see **more than one** submission without querying SQLite by hand: a **bounded, newest-first** list on `GET /{locale}/assessment` complements the existing post-submit summary and CSV/Markdown export.
- **RBAC / per-tenant isolation** is **not** implemented ([GitHub #86](https://github.com/FabioLeitao/data-boar/issues/86), [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md)). Today, anyone who can open the assessment page sees **all** batches stored in the same DB file—the same trust model as the rest of the dashboard when `api.require_api_key` is off.

## Decision

- Add **`LocalDBManager.maturity_assessment_batch_summaries`** — SQL aggregation `GROUP BY batch_id`, `ORDER BY min(created_at) DESC`, capped **limit** (default 50, max 500) to keep HTML predictable.
- Pass **`assessment_batch_history`** into the assessment Jinja template; render a **card + table** only when the list is non-empty (i18n keys under `assessment.history_*`).
- Link each row to the existing summary URL (`saved=1&batch=…`) and CSV export; highlight the row when it matches the current **`batch`** query parameter.
- **Do not** add a separate REST JSON API for history in this slice—the HTML page is the POC surface; JSON can follow if product asks.

## Consequences

- **Pros:** Low coupling (one query + template); reuses existing export and summary behaviour; covered by `tests/test_database.py` and `tests/test_api_assessment_poc.py`.
- **Cons / future work:** Listing is **global to the DB** until identity + RBAC exist; [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) tier/JWT alignment remains a separate slice. When **#86 Phase 2** lands, **filter** `maturity_assessment_batch_summaries` (or equivalent) by authenticated **subject/tenant** instead of changing the aggregation shape.

### Manual QA (POC)

1. Enable `api.maturity_self_assessment_poc_enabled` and point `api.maturity_assessment_pack_path` at a pack; use **Pro+** tier (or open tier in lab).
2. Submit twice; open `GET /{locale}/assessment` — **Recent submissions** shows two rows, newest first; **Summary** opens the correct batch.
3. With an empty DB, confirm the history **section is absent** (no empty table noise).

## References

- [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md)
- [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) — Phase 0 route matrix; target **`authenticated`** for assessment routes.
- [docs/USAGE.md](../USAGE.md) — operator-facing table row for the assessment page.

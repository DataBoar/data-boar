# Corporate-Entity-C evolution review — 2026-03-18 (tracking in-repo)

**Source (local / operator):** PDF `docs/feedbacks, reviews, comments and criticism/analise\\\_evolucao\\\_data\\\_boar\\\_2026-03-18.pdf` (folder may be gitignored; keep the PDF in your workspace for audit trail).

**Verdict (Corporate-Entity-C):** **9.1 / 10** — strong, consistent evolution (detection, connectors, tests, compliance docs; releases 1.6.0 / 1.6.1 cadence in the report snapshot).

\---

## Already aligned in-repo (before this follow-up)

|Corporate-Entity-C theme|Repo status|
|-|-|
|Content-type / magic-byte detection|Done (report: “Resolvido”).|
|Compliance documentation (e.g. ISO/IEC 27701)|Done.|
|Release governance + versioning|Done (`docs/VERSIONING.md`, `docs/releases/`, tags).|
|API host default loopback (Wabix P0/P1)|Done — see PLANS\_TODO “Secure default host binding”.|
|Security triage **routine** (Dependabot / Scout)|**Tracked:** Priority band A, `scripts/maintenance-check.ps1`, `SECURITY.md`, `docs/ops/BRANCH\\\_AND\\\_DOCKER\\\_CLEANUP.md` — formalize cadence in ops calendar (still human).|
|Doc snapshot per version|**Partial:** each release has `docs/releases/X.Y.Z.md`; optional future “frozen doc bundle” remains backlog (W-DOC below).|

\---

## Executive recommendations → mapped work (token-aware order)

|ID|Corporate-Entity-C recommendation|Mapping|Priority vs token-aware rule|
|-|-|-|-|
|**W-KPI**|Painel de KPIs de release e segurança operacional|**Backlog:** DORA-lite / GitHub Actions insights (lead time, CI fail rate); no code in app. Link: `PLAN\\\_READINESS\\\_AND\\\_OPERATIONS.md`, future dashboard or wiki.|Low AI / manual-friendly; after critical security band.|
|**W-CONTRACT**|Bateria de testes de contrato (relatórios + APIs críticas)|**Done (baseline):** report/heatmap artifact regressions in `tests/test\\\_report\\\_trends.py` + OpenAPI contract response documentation in `tests/test\\\_routes\\\_responses.py`.|Low/moderate slice; already covered by existing tests.|
|**W-DECOUPLE**|Desacoplar regras centrais (detector / gerador)|**Ongoing:** SonarQube cognitive-complexity gates; incremental extraction (e.g. `core/fuzzy\\\_column\\\_match.py` pattern). No big-bang refactor.|High effort; small extractions when touching files.|
|**W-DOC**|Disciplina de release + snapshot de documentação|**Done (baseline):** release notes per version; **optional:** export doc set per tag — backlog under W-KPI ops.|Doc-only follow-up.|

\---

## Implemented from FN / aggregated plan in this cycle

* **Plan § aggregated wording (incomplete sample):** Excel **Cross-ref data – ident. risk** now starts with a **sample/coverage note** row; **Recommendations** row `AGGREGATED\\\_IDENTIFICATION` mentions sampling and manual confirmation (`report/generator.py`).
* **Plan table:** [PLAN\_ADDITIONAL\_DETECTION\_TECHNIQUES\_AND\_FN\_REDUCTION.md](PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md) item **8** marked done; item **9** (MEDIUM / `PII\\\_AMBIGUOUS` in aggregation) **verified** — `DEFAULT\\\_PATTERN\\\_CATEGORY\\\_MAP` includes `PII\\\_AMBIGUOUS` → `other` in `core/aggregated\\\_identification.py`.
* **Plan §4 (format / length hints from connectors) initial slice:** `sensitivity\\\_detection.connector\\\_format\\\_id\\\_hint` + detector `FORMAT\\\_LENGTH\\\_HINT\\\_ID`, wired through `DataScanner.scan\\\_column(..., connector\\\_data\\\_type=...)` for SQL/Snowflake/Dataverse/Power BI and the SQLite/filesystem typed path; verified via `tests/test\\\_format\\\_length\\\_hint.py`.

\---

## Staging: fuzzy column match

Use **`deploy/config.staging.example.yaml`** as a merge overlay:

* `sensitivity\\\_detection.fuzzy\\\_column\\\_match: true` (requires **`rapidfuzz`** via `uv sync --group dev` or `pip install ".\\\[detection-fuzzy]"`; tune `fuzzy\\\_column\\\_match\\\_min\\\_ratio` if noise is high).
* `sensitivity\\\_detection.connector\\\_format\\\_id\\\_hint: true` (Plan §4: uses declared `CHAR`/`VARCHAR(N)` + conservative ID-like name heuristics; if it gets noisy on generic `\\\*\\\_id`, set it back to `false`).

\---

## Next suggested (token-aware)

1. **W-KPI** — add 1-2 concrete release/security KPIs (lead time, CI fail rate, rollback frequency) to the ops playbook so we can monitor evolution.
2. **W-DECOUPLE** — small extractions to reduce core detector/report coupling when touching high-complexity modules.
3. **–1 / –1b** — maintenance when critical (Dependabot / Docker Scout).

**Synced with:** [PLANS\_TODO.md](PLANS_TODO.md) (Corporate-Entity-C subsection + FN reduction rows 8–9).


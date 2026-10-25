# Operator today mode — 2026-04-02 (normal rhythm, token-aware, release gate)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md)

**Purpose:** Keep momentum from the MAX session while returning to standard cadence: small coherent slices, explicit gates, no release ambiguity.

---

## Block 0 — Reality check (10-20 min)

1. Confirm current truth:
   - Working version in repo: `1.6.8` (`pyproject.toml`, `core/about.py`).
   - Last published release/tag: confirm on GitHub Releases and Docker Hub.
1. Confirm branch/worktree state:
   - `git status -sb`
   - `git fetch origin`
   - `gh pr list --state open`

---

## Block A — Documentation quality gate (15-25 min)

Run and keep output references:

```powershell
uv run pytest tests/test_docs_pt_br_locale.py -q
uv run pytest tests/test_markdown_lint.py::test_markdown_lint_no_violations -q
```

If red, fix locale drift (pt-PT traces, awkward translation) before any publish action.

---

## Block B — External review cycle (WRB + Gemini) (30-60 min)

### WRB (Corporate-Entity-C)

1. Use: `docs/ops/Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md`.
1. Keep the three time lenses explicit:
   - cumulative history;
   - since last Corporate-Entity-C report;
   - since last public release/tag.
1. Ask for explicit split by severity and by effort type (security, integrity/evidence, feature, docs/governance, ops/observability, refactor).

### Gemini

1. Build safe bundle:

```bash
uv run python scripts/export_public_gemini_bundle.py --output docs/private/gemini_bundles/public_bundle_2026-04-02.txt --compliance-yaml --verify
```

2. Use runbook prompt in `docs/ops/GEMINI_PUBLIC_BUNDLE_REVIEW.md`.
3. Triage outputs in `docs/plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md` before promoting into `PLANS_TODO.md`.

---

## Block C — Release decision gate (20-40 min)

Only publish `v1.6.8` when all are true:

- release note exists in `docs/releases/1.6.8.md`;
- quality gate is green (`check-all` or agreed subset for docs-only);
- open PR state is clear (no unresolved conflict with the release slice);
- working vs published version text is synchronized in docs.

If any gate fails, do not tag/publish; move pending items to carryover with a date.

---

## Block D — Quantified progress snapshot (15-25 min)

Generate progress windows:

```powershell
git log --since="2026-04-02 00:00" --pretty=format:"%h|%ad|%s" --date=short
git log --since="3 days ago" --pretty=format:"%h|%ad|%s" --date=short
git log --since="7 days ago" --pretty=format:"%h|%ad|%s" --date=short
```

Summarize by fronts:

- Product/detector/API/reporting
- Security/integrity/hardening
- Docs/compliance/decision-maker narrative
- Ops/lab-op/workflow automation
- Plans/roadmap governance

---

## Stop condition

Day is complete when:

- locale + markdown guards are green;
- WRB and Gemini requests are prepared/sent with source-of-truth framing;
- release decision is explicit (`publish now` or `defer with gate`);
- progress snapshot exists for today, 3 days, and 7 days.

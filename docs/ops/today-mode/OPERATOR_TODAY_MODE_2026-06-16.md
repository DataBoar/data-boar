# Operator today-mode — 2026-06-16 (safe Dependabot queue drain, no regressions)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-06-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-16.pt_BR.md)

**Note:** Drafted to drain the **Dependabot PR backlog safely**. The product gate work (#891/#890/#888/#889, deps #896/#899, claims #894, rust dev-dep #892) is merged. Seven Dependabot PRs remain in the queue; three of them (Python) were opened **before** the recent dependency merges, so their base is stale — blind-merging would conflict or downgrade. The safe ritual is **apply locally + validate + close the bot PR as "applied locally"**, per `.cursor/skills/dependabot-recommendations/SKILL.md`.

**`main` anchor:** `f870f156` — **#903** (handle-web exit reconcile) merged. Open Dependabot PRs: **#867 #868 #869** (actions), **#870 #871 #348** (Python minor/patch + build), **#872** (redis major). Remaining alert: one low-severity `torch` (no upstream fix).

---

## Block 0 — Morning reality (10–15 min)

1. **`origin/main`:** `git fetch` · `git status -sb` · confirm `ci.yml` green on `main` before deep work.
2. **Open PRs:** `gh pr list --state open` — all 7 are Dependabot.
3. **Private stack:** if `docs/private/` changed overnight, `./scripts/private-git-sync.ps1 -Push` (or the `.sh` path on Linux).

**Continuous queue:** [CARRYOVER.md](CARRYOVER.md)

---

## Safe drain ritual (no-regression contract)

For every batch:

1. **Apply locally** (do not merge the bot branch) — edit YAML / `pyproject.toml`, then `uv lock` (or `uv lock --upgrade-package <name>`), then refresh `requirements.txt` with `uv export --frozen --no-emit-project -o requirements.txt` (the `--no-emit-project` form locked in by #891).
2. **Validate:** `./scripts/check-all.sh` (Ruff + format + markdown + full pytest). For deps specifically, also reproduce the CI audit: `uv sync --extra shares && uv pip install pip-audit && uv run pip-audit` (matches the `Dependency audit` gate).
3. **Regression guard** only when it protects a contract (security floor, behavior). Skip for trivial patches.
4. **One PR per batch**, signed commit, no rebase/force. After merge, **close the matching bot PR** with a "applied locally in #<PR>" comment; let the branch be deleted.

---

## Risk classification (the 7 PRs)

| PR | Change | Type | Risk | Batch |
| -- | ------ | ---- | ---- | ----- |
| **#867** | `actions/checkout` 6.0.2→6.0.3 (10 workflows) | action patch | Low | **A** |
| **#869** | `astral-sh/setup-uv` 8.1.0→8.2.0 (3 workflows) | action minor | Low | **A** |
| **#868** | `gitleaks/gitleaks-action` 2.3.9→**3.0.0** | action major (Node 20→24, *no input/output/behavior change*) | Low, **time-boxed** | **A** |
| **#348** | `hatchling` >=1.24.0→>=1.29.0 | build backend | Low | **B** |
| **#870** | `uv-minor-patch` group (20 pkgs) | Python minor/patch | Medium (**stale base**) | **B** |
| **#871** | `rpds-py` 0.30.0→2026.5.1 (CalVer) | transitive (via referencing/jsonschema) | **High — breaking** | **B (pin `<2026`)** |
| **#872** | `redis` 7.4.0→**8.0.0** | direct-optional major (`nosql` extra; breaking only in type hints, RESP3 default) | Medium | **C** |

**Stale-base note:** `main` already has `pypdf 6.13.2`, `starlette 1.3.1`, `python-multipart 0.0.32` (from #896/#899). The #870 group still targets older versions of those — apply via `uv lock --upgrade` so the resolver keeps the higher floors; do **not** downgrade.

**#868 urgency:** GitHub flips runners to Node 24 on **2026-06-02** (already past) and removes Node 20 on **2026-09-16**. v3 is a pure runtime bump — safe and needed.

**#871 rpds-py is breaking (verified):** `2026.5.1` is a **legitimate** release (real CalVer pivot on PyPI, not a typosquat), **but it breaks `check-all`** — the bot PR's own CI is red on Lint + Test 3.12/3.13/3.14 (4 reds). `rpds-py` is purely transitive (via `referencing`/`jsonschema`); nothing here needs the pivot. **Fix:** add a constraint `rpds-py<2026` in Batch B so the resolver keeps the working `0.x`. Do not let `uv lock --upgrade` pull `2026.5.1`.

**#872 redis:** used by `connectors/redis_connector.py` (lazy import, `redis>=5.0` already permits 8.0). The 8.0 breaking changes are type-hint-only; runtime unchanged. Still isolate it and run the connector tier/timeout tests.

---

## Suggested order

| Step | Batch | PRs | Validation |
| ---- | ----- | --- | ---------- |
| 1 | **A — Actions** | #867, #869, #868 | `quick-test.sh --path tests/test_github_workflows.py` + `workflow-security-lint` (zizmor). #868 has a Sep/2026 deadline — do not sit on it. |
| 2 | **C — redis major** | #872 | `check-all.sh` + connector tier/timeout tests; isolated |
| 3 | **B — Python minor/patch + build** | #870, #348 | `check-all.sh` + reproduce `pip-audit` gate. **Pin `rpds-py<2026`** (close #871 as "won't take pivot — breaking") |

Order A → C → B is deliberate: A is low-risk and time-boxed; C is isolated and testable; B last because it needs the `rpds-py<2026` constraint to stay green. Each step = one signed PR; close matching bot PR(s) after merge.

---

## End of day (2026-06-16)

- `eod-sync` + `private-stack-sync` if the private stack or social hub changed.
- Tomorrow's checklist path: `OPERATOR_TODAY_MODE_2026-06-17.md` (create at next `eod-sync` if missing).

---

## Quick references

- Dependabot ritual: `.cursor/skills/dependabot-recommendations/SKILL.md`
- Session keywords: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `eod-sync`, `deps`)
- Workflow SHA-pin guard: `tests/test_github_workflows.py`; zizmor: `scripts/workflow-security-lint.sh`

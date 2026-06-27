# Quality workflow: recommendations and extra layers

This document suggests **additional layers** (tools, habits, and workflow) to keep the app working safely, readable, and to reduce toil, rework, and refactoring. Use it as a checklist; adopt incrementally. What you already have is in [TESTING.md](TESTING.md), [SECURITY.md](../SECURITY.md), and the Cursor rule/skill (`.cursor/rules/quality-sonarqube-codeql.mdc`, `.cursor/skills/quality-sonarqube-codeql/SKILL.md`).

**Already in place:** Ruff runs in CI (`uv run ruff check .`); `pyproject.toml` has `extend-exclude` for legacy dirs (`db`, `scanners`, `utils`, `logging_custom`). Run `uv run ruff check .` before PR. Optional: `uv run pre-commit install` so Ruff runs on commit (see `.pre-commit-config.yaml`).

## What you already have (baseline)

- **Tests:** Full pytest suite with `-W error`; SonarQube-style tests (S3981, S3776, S4423, S5706, S1192, etc.), security tests (SQL injection, path traversal, safe_load), markdown lint (including `.cursor/`).
- **CI:** Tests + `pip-audit` on every push/PR; optional SonarQube when `SONAR_TOKEN` is set; CodeQL in a separate workflow.
- **Cursor:** Rule and skill so the agent avoids SonarQube/CodeQL violations and runs quality tests after editing Python/markdown.
- **Docs:** CONTRIBUTING (release checklist, audit, min versions), SECURITY.md, TESTING.md, deploy hardening.

---

## Recommended layers (prioritised)

### 1. Run Ruff in CI (high value, low effort)

**Why:** Ruff catches style issues, unused imports, and many bug-prone patterns before they reach main. The PR template says "No new linter/format issues" but Ruff is not run in CI, so it's easy to forget.

## What to do (Ruff in CI):

- Add a **lint** job (or step) in `.github/workflows/ci.yml` that runs:
- `uv run ruff check .` (and optionally `uv run ruff format --check .`).
- Keep Ruff config in `pyproject.toml` (you already have `[tool.ruff.lint.per-file-ignores]`); add a `[tool.ruff]` section with `target-version`, `line-length`, and select rule sets if you want consistency.
- Update CONTRIBUTING and the quality rule/skill: "Before PR, run `uv run ruff check .` (and fix or adjust config)."

**Prevents:** Drift in style, unused code, many simple bugs; reduces review toil and post-merge fixes.

---

### 2. Pre-commit hooks (optional but strong)

**Why:** Catches issues **before** push so CI fails less often and you avoid "run after your own tail" on style/lint.

## What to do (pre-commit):

- Add [pre-commit](https://pre-commit.com/) (e.g. in dev dependency group) and a `.pre-commit-config.yaml` with:
- `ruff` (check + format),
- `markdownlint` or a hook that runs `scripts/fix_markdown_sonar.py` / `pytest tests/test_markdown_lint.py`,
- optionally a "fast" pytest subset (e.g. `test_markdown_lint`, `test_sonarqube_python`, `test_security`) if fast enough.
- Document in CONTRIBUTING: "Install hooks with `pre-commit install`; they run on commit."

**Prevents:** Pushing commits that will fail CI; keeps local and CI in sync.

---

### 3. Bandit (security linter) — dev + CI (medium+)

**Why:** Complements CodeQL, Semgrep, and SonarQube with Python-specific checks: `try/except/pass`, naive SQL string heuristics, `subprocess`, `assert` outside tests, hardcoded “password-like” strings, etc.

## What we do (Bandit):

- **`bandit`** is in the **`uv` dev** group; **`[tool.bandit]`** in **`pyproject.toml`** sets **`exclude_dirs`** and **`skips`** (e.g. **B608** where SQL uses vetted identifiers — aligned with Semgrep exclusions in [`.github/workflows/semgrep.yml`](../.github/workflows/semgrep.yml)).
- **CI:** Job **Bandit (medium+)** in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): `uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q` (fails on **medium** and **high** only until **low** is triaged).
- **Triage:** `uv run bandit -c pyproject.toml -r … -i` for **low**; fix, **`# nosec Bxxx`** with a short reason, or extend config — see [SECURITY.md](../SECURITY.md) and **`[tool.bandit]`** in **`pyproject.toml`**.
- **Agent habit:** [`.cursor/skills/quality-sonarqube-codeql/SKILL.md`](../.cursor/skills/quality-sonarqube-codeql/SKILL.md) — run Bandit after security-sensitive Python edits when relevant.

**Prevents:** Common security anti-patterns that tests might not cover.

---

### 4. Semgrep (CI enabled)

**Why:** Pattern-based SAST; custom and community rules for security and bug patterns. Overlaps with CodeQL and SonarQube but can catch project-specific patterns (e.g. project-specific config invariants).

## What we do (Semgrep):

- **GitHub Actions:** [`.github/workflows/semgrep.yml`](../.github/workflows/semgrep.yml) runs on push/PR to `main`/`master` using the official **`semgrep/semgrep`** container, ruleset **`p/python`**, **`--metrics=off`**, and one **excluded rule** documented in workflow comments (false positive on vetted `sqlalchemy.text` identifier paths).
- **Local (optional):** `uvx semgrep scan --config p/python --metrics=off` with the same **`--exclude-rule`** as the workflow (see **§ check-all unified mirror** below). Custom rules can live under `.semgrep/` later.

**Prevents:** Extra Python anti-patterns; complements CodeQL. **Slack:** **`Slack CI failure notify`** (`workflow_call`, lists **`Semgrep`** next to **`CI`**, etc.) ships on **`origin`** as **`.github/workflows/slack-ci-failure-notify.yml`**; a **private snapshot** for pause drills lives under **`docs/private/raw_pastes/cursor-incident/slack-ci-failure-notify.yml.old`** ([OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1.1). Pause again only deliberately (same doc).

---

### 4b. Zizmor (workflow static analysis)

**Why:** GitHub Actions workflows are code — misconfigured `permissions`, unpinned actions, or dangerous `pull_request_target` patterns are supply-chain and abuse risks. **Zizmor** scans `.github/workflows/` for those classes of issues.

## What we do (Zizmor):

- **CI:** [`.github/workflows/zizmor.yml`](../.github/workflows/zizmor.yml) runs on push/PR via **`zizmorcore/zizmor-action`** (SHA-pinned). **Advisory** by default unless **`ZIZMOR_ENFORCE`** / repo **`ENFORCE_ZIZMOR`** is set — see [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) and **`scripts/workflow-security-lint.sh`**.
- **Local:** `uvx zizmor .github/workflows/` (same path as **`workflow-security-lint.sh`**). **`check-all`** runs Zizmor in the **default** security tier and **fails** on findings (shift-left mirror of a strict posture before merge).

**Prevents:** Workflow misconfigurations that Bandit/Semgrep do not see.

---

### 4c. `check-all` as unified CI mirror (tiered)

**Why:** Contributors on the **Linux primary** dev workstation and agents should run **one** local ritual that matches **what CI will run**, without re-typing job commands from five workflow files.

## Tiers (`./scripts/check-all.sh` / `.\scripts\check-all.ps1`)

| Tier | When | What (after existing gatekeeper, Rust, plans-stats, hubs, Pester, pre-commit, pytest) |
| ---- | ---- | ---------------------------------------------------------------------------------------- |
| **Default (offline-capable)** | Every pre-PR / agent slice | **Bandit** — `uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q` (same paths as QUALITY doc + CI product scope). **Zizmor** — `uvx zizmor .github/workflows/`. |
| **Opt-in `--enforced` / `-Enforced`** | Before security-sensitive PRs; when Semgrep CI is the worry | **+ Semgrep** — `uvx semgrep scan --config p/python --metrics=off` with the same **`--exclude-rule`** as [`.github/workflows/semgrep.yml`](../.github/workflows/semgrep.yml), **`--error .`**. Requires network for `uvx`. |

**Fail-collect:** The security tier runs **all** scans in the tier, then reports **every** failure (no fail-fast within Bandit / Zizmor / Semgrep). Earlier gates (PII gatekeeper, Rust, pre-commit) still abort immediately — see **`scripts/check-all-security-scans.sh`** / **`.ps1`**.

**Not in default `check-all` (separate CI jobs):** CodeQL, Sonar, pip-audit, SBOM image build — run those via CI or dedicated scripts; do not bloat the daily loop.

### Future waves (same doc — not implemented in #1044)

| Wave | Intent | Status |
| ---- | ------ | ------ |
| **Wave 2** | Optional **pre-commit** hooks for Bandit / Zizmor (subset, fast) | Deferred — track in this section |
| **Wave 3** | Cursor rule: **run `check-all --enforced` before PR** when the slice touches connectors, workflows, or auth | Deferred — pointer in **§10** below |

---

### ROI — shift-left economics

Running **`check-all`** locally (default tier) trades **~2–5 minutes** on the dev PC for **avoiding a full CI round-trip** (queue + matrix + Semgrep container), which is typically **15–40+ minutes** wall-clock when a Bandit or workflow finding fails late.

| Finding class | Without local mirror | With `check-all` default tier |
| ------------- | ------------------- | ----------------------------- |
| Bandit on connectors | Fails in CI **Bandit** job after lint+test already ran | Surfaces in one local pass |
| Workflow permission drift | Fails in **Zizmor** workflow (or stays advisory until enforced) | Surfaces before push |
| Semgrep SQLAlchemy FP path | Only when **`--enforced`** or CI Semgrep | Operator/agent opt-in — matches container command |

**Token-aware habit:** Use **`./scripts/check-all.sh --skip-pre-commit`** only when iterating on tests; run **full** `check-all` before opening the PR. Use **`--enforced`** when the diff touches **security surfaces** listed in Wave 3 — not on every docs-only slice.

---

### 5. Type checking with mypy (gradual — dev only for now)

**Why:** Types make refactors safer and reduce "it worked until we changed X" regressions.

## What we have (mypy):

- **`mypy`** and **`types-PyYAML`** are in the **`uv` dev** group. **`[tool.mypy]`** in **`pyproject.toml`** starts **soft**: `disallow_untyped_defs = false`, `check_untyped_defs = false`, `warn_return_any = false`, `ignore_missing_imports = true`, `warn_unused_ignores = false` — **not** “strict mode”.
- **Local:** `uv run mypy api core` (mypy still follows imports into **`config`**, **`connectors`**, etc., so expect **many errors** until you triage module-by-module). **CI:** not wired yet — add a job only when the report is close to clean or use `continue-on-error` deliberately.

**Prevents:** Type-related bugs once the codebase is brought in line; until then, mypy is an **optional local signal**, not a merge gate.

**Tighten over time:** `disallow_untyped_defs = true` (or per-package overrides), `warn_return_any = true`, add stubs (`types-*`) or `[[tool.mypy.overrides]]` for third-party gaps.

---

### 6. MD029 and the fix script (reduce rework)

**Why:** `scripts/fix_markdown_sonar.py` applies MD029 (ordered list style 1/1/1), which converts all list numbers to `1.`. That can break **semantic** numbering (e.g. "Step 1, 2, 3" becomes "1, 1, 1") and forces manual re-editing in many docs.

**Accepted decision (record):** [ADR 0001](adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md) — keep MD029 in the script; restore **1. 2. 3.** by hand for real step lists; revisit smarter heuristics only if churn hurts.

## What to do (MD029):

- **Current practice:** (c) documented in CONTRIBUTING, **markdown-lint** rule, and ADR 0001. Alternatives (a) skip MD029 for some contexts or (b) stop applying MD029 globally remain **future** options if we outgrow manual restore.

**Prevents:** Repeated rework and confusion in docs after every markdown fix run.

---

### 7. Architecture / decision records (reduce wrong refactors)

**Why:** When "why" is written down, refactors are less likely to reintroduce the same mistakes or toil.

## What we have (ADRs):

- **Index:** [docs/adr/README.md](adr/README.md) ([pt-BR](adr/README.pt_BR.md)) — numbering convention, English-only ADR bodies (like plan files), baseline **[ADR 0000](adr/ADR-0000-project-origin-and-adr-baseline.md)** (origin + pre-ADR history), then **[ADR 0001](adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md)** (MD029 + `fix_markdown_sonar.py`), **[ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)** (information architecture: external-tier docs do not Markdown-link into `plans/`), **[ADR 0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md)** (CI: SHA-pinned Actions + pinned **uv** CLI; explicit non-guarantees), etc.
- **Still optional / incremental:** Keep a short **architecture** overview in TECH_GUIDE or a future `docs/architecture.md` for components and data flow; add new **`docs/adr/000N-....md`** files for security- or process-heavy choices. Link from SECURITY.md or CONTRIBUTING when a decision affects contributors directly.

**Prevents:** Refactoring that accidentally weakens security or duplicates past mistakes.

---

### 8. SBOM and supply chain (optional)

**Why:** pip-audit already addresses known vulnerabilities; a formal **Software Bill of Materials** supports **software supply-chain** transparency and **incident response** (mapping what shipped). It is **not** a substitute for **organizational** risk management (**ISO 31000** framing: [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md#iso-31000-framing)).

**CI / GitHub Actions (enforced in-repo):** Third-party Actions are pinned to **full commit SHAs**; **`astral-sh/setup-uv`** uses a **fixed uv semver** (not `latest`); **`tests/test_github_workflows.py`** guards **`ci.yml`**. **Decision + scope limits** (including what pinning **does not** guarantee): **[ADR 0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md)**. Operational backlog context: [WORKFLOW_DEFERRED_FOLLOWUPS.md](ops/WORKFLOW_DEFERRED_FOLLOWUPS.md).

## What to do (SBOM):

- **Implemented:** GitHub Actions workflow [**SBOM**](../.github/workflows/sbom.yml) — **CycloneDX JSON** from `uv export` + `cyclonedx-py` (`sbom-python.cdx.json`), **Syft** on the built image (`sbom-docker-image.cdx.json`). See [SECURITY.md](../SECURITY.md), [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md), [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). Local: [`scripts/generate-sbom.ps1`](../scripts/generate-sbom.ps1).

**Prevents:** Blind spots in dependency and image inventory and slower response to supply-chain or IR questions.

---

### 9. PR checklist and branch protection

**Why:** Ensures nothing merges without tests and audit; reduces "fix in main" and rework.

## What to do (branch protection):

- In GitHub: **Branch protection** on `main` (and `master` if used) requiring status checks to pass before merge. **Recommended required checks** once stable: **CI** jobs **Test** (matrix), **Lint (pre-commit)** (includes Ruff + plans-stats + markdown + pt-BR + commercial guard), **Dependency audit**, **Bandit (medium+)**, and the **Semgrep** workflow; add **CodeQL** if you want the Security tab to block merge.
- **Readiness:** Turn protection on after the branch that carries **Semgrep** (and any other new workflows) is **merged** and at least one **green** run exists for each required check name (GitHub shows exact check IDs in branch protection UI).
- In the **PR template**, make the checklist explicit: tests pass, **`uv run pre-commit run --all-files`** clean (or hooks installed), docs updated, security-sensitive changes considered. Reference CONTRIBUTING and TESTING.md.
- Deferred ideas (auto-merge, Environments, CODEOWNERS): [docs/ops/WORKFLOW_DEFERRED_FOLLOWUPS.md](ops/WORKFLOW_DEFERRED_FOLLOWUPS.md).

**Prevents:** Merging broken or insecure code and follow-up fix commits.

---

### 10. Cursor rules and skills (keep extending)

**Why:** Rules and skills guide the agent so fewer violations are introduced in the first place; tests remain the enforcement.

## What to do (rules and skills):

- When you add a **new** quality or security check (e.g. Ruff in CI, Bandit, a new Sonar rule): update the **quality rule** and **skill** with the new command and what to avoid. Keep TESTING.md and this doc in sync.
- Consider a short **rule** that fires when editing config or connector code: "Use parameterized queries; no secrets in logs; run security tests after change."
- **`check-all` mirror (#1044):** Default local gate = **`./scripts/check-all.sh`** / **`.\scripts\check-all.ps1`** (Bandit + Zizmor after pre-commit/pytest). Use **`--enforced`** / **`-Enforced`** for Semgrep parity before security-sensitive PRs — see **§4c** above. **Wave 3 (future):** codify "run `--enforced` before PR" in **`.cursor/rules/quality-sonarqube-codeql.mdc`** when the slice touches connectors, workflows, or auth.

**Prevents:** Regressions and bad habits from creeping in during daily edits.

---

## Summary table

| Layer                   | Purpose                                    | Effort | Prevents                                                     |
| ------------------      | -------------------------------            | ------ | ---------------------------------                            |
| Lint (pre-commit) in CI | Same hooks as `.pre-commit-config.yaml`    | Low    | Drift vs local hooks, failed lint job                        |
| Pre-commit (local)      | Catch on `git commit`                      | Low    | Failed CI, rework                                            |
| Bandit                  | Python security patterns (CI **medium+**)  | Low    | Anti-patterns tests may miss; **low** triage in plan Phase 3 |
| Zizmor                  | GitHub Actions workflow hygiene            | Low    | Permission/pinning drift before CI                           |
| `check-all` mirror      | Local tiered CI parity (Bandit+Zizmor+opt Semgrep) | Low | Late CI failures, rework loops                       |
| Semgrep                 | Custom + community SAST                    | Medium | Extra vulnerability/bug patterns                             |
| mypy                    | Type safety                                | Medium | Refactor bugs, wrong types                                   |
| MD029 / fix script      | Avoid doc rework                           | Low    | Repeated manual numbering fixes                              |
| ADRs / architecture     | Record "why"                               | Low    | Wrong refactors, repeated mistakes                           |
| SBOM                    | Supply chain + incident-response inventory | Low    | Missing deps/image components when responding to issues      |
| CI Action / uv pins     | Reduce tag-moving & installer drift in CI  | Low    | Silent compromised action or floating uv without review        |
| Branch protection       | Block bad merges                           | Low    | Merging broken or insecure code                              |
| Extend rules/skills     | Guide agent on new checks                  | Low    | New violations as you add tools                              |

---

## What you might not be paying attention to yet

1. **Lint vs local** – CI runs **`pre-commit run --all-files`**; install **`uv run pre-commit install`** so **`git commit`** matches. **`check-all`** adds **Bandit + Zizmor** (default) and optional **`--enforced`** Semgrep — see **§4c**.
1. **MD029 and semantic lists** – The fix script can overwrite intentional 1/2/3 numbering; see [ADR 0001](adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md).
1. **Branch protection** – Enable when required check names are stable (include **Semgrep** if merge-blocking). See [WORKFLOW_DEFERRED_FOLLOWUPS.md](ops/WORKFLOW_DEFERRED_FOLLOWUPS.md).
1. **Types** – mypy is gradual dev-only until triage (§5).
1. **SBOM** – CycloneDX then Syft; [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md).
1. **CI supply chain** – Pinned Actions + uv; [ADR 0005](adr/ADR-0005-ci-github-actions-supply-chain-pins.md).

Adopt what fits your team and timeline; strong baseline: **pre-commit parity in CI**, **branch protection**, **MD029/fix-script**, **Bandit** + **Semgrep**. **mypy** stays optional until clean.

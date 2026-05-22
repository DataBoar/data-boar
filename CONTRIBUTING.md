# Contributing to Data Boar

**Português (Brasil):** [CONTRIBUTING.pt_BR.md](CONTRIBUTING.pt_BR.md)

Thank you for considering contributing. This document covers local setup, workflow, and best practices so you can run the app, tests, and open changes safely.

**Team workflow (maintainer + contributor, Cursor + Git):** see **[docs/COLLABORATION_TEAM.md](docs/COLLABORATION_TEAM.md)** ([pt-BR](docs/COLLABORATION_TEAM.pt_BR.md)) and **`.cursor/rules/collaboration-maintainer-contributor.mdc`**.

## Repository and install identity (Data Boar)

- **Product and brand:** **Data Boar** — use this name in prose, issues, and PR titles.
- **Upstream repository:** **[github.com/FabioLeitao/data-boar](https://github.com/FabioLeitao/data-boar)** — fork or clone from there (replace `YOUR_FORK` if you use a fork).
- **PyPI distribution name:** `pyproject.toml` declares **`name = "data-boar"`**. When published to the Python Package Index, installs will use:

  ```bash
  pip install data-boar
  ```

  Until a release is published under that name, use a **git clone** with **`uv sync`** or **`pip install -e .`**. The tree still contains the historical **`lgpd_crawler`** Python package for imports and continuity — that is implementation layout, not the product name. Rename context: **[ADR 0014](docs/adr/ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)**.

### Publishing to PyPI (maintainers)

Build uses **[hatchling](https://github.com/pypa/hatch)** via **`pyproject.toml`** (`[build-system]` + `[tool.hatch.build]`). From the repo root (Windows):

```powershell
.\scripts\pypi-publish.ps1 -DryRun   # build + validate upload path only
$env:UV_PUBLISH_TOKEN = "<PyPI API token>"   # never commit this
.\scripts\pypi-publish.ps1
```

Or: **`uv build`** then **`uv publish dist/*`** with **`UV_PUBLISH_TOKEN`** set. PyPI installs expose two **first-class** console entry points (same package, same quality bar — regressions in either block the merge gate):

- **`data-boar`** → **`main:main`** (CLI, one-shot scan, `--web` API server).
- **`data-boar-report`** → **`cli.reporter:main`** (executive Markdown from the local SQLite session — no live SQL connector; see [docs/USAGE.md](docs/USAGE.md) section 5, [pt-BR](docs/USAGE.pt_BR.md)).

## Quick start (development)

1. **Clone and enter the repo**

   ```bash
   git clone https://github.com/FabioLeitao/data-boar.git
   cd data-boar
   ```

1. **Use Python 3.12+**

   The project targets Python 3.12 and 3.13. See [SECURITY.md](SECURITY.md) for supported versions.

1. **Install dependencies with uv (recommended)**

   ```bash
   uv sync
   ```

   Or with pip inside a virtualenv: `pip install -e .`

   **PowerShell (`pwsh`) — manual venv activation:** when `.\.venv\Scripts\Activate.ps1` exists, run it from the repo root. Do **not** invoke the extensionless `activate` shim inside `.venv\Scripts\` by full path — PowerShell only runs **`Activate.ps1`** as a script (running `…\Scripts\activate` without `.ps1` errors with *not recognized*). If that `.ps1` is missing after **`uv sync`**, rely on **`uv run …`** or recreate the env (remove `.venv` and **`uv sync`** again). Prefer **`uv run …`** day-to-day.

1. **Install pre-commit hooks (recommended, once per clone)**

   ```bash
   uv run pre-commit install
   ```

   This runs the same checks as the **CI** **Lint (pre-commit)** job on every `git commit` (Ruff, **plans-stats** and **plans-hub** freshness, markdown lint, pt-BR locale, commercial guard). Run **`uv run pre-commit run --all-files`** before a PR if you skip hooks.

1. **Run the full local gate (recommended before a PR)** — one command:

   - **Windows:** `.\scripts\check-all.ps1` from the repo root.
   - **Linux / macOS:** `./scripts/check-all.sh` (make executable: `chmod +x scripts/check-all.sh`). Requires **`uv`** on `PATH`; the gate runs **`uv run python scripts/gatekeeper_audit.py`** for staged PII seeds (no **`pwsh`** dependency — **`#560`**).
   - **Paired shortcuts:** `./scripts/lint-only.sh`, `./scripts/quick-test.sh`, `./scripts/pre-commit-and-tests.sh` mirror the **`.ps1`** scripts — see **[docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md](docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md)** ([pt-BR](docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)).

1. **Run tests** (or use the full gate above)

   ```bash
   uv run pytest -v -W error
   ```

   All tests must pass with no errors or warnings. See [docs/TESTING.md](docs/TESTING.md) for what each test module covers and how to run subsets.

1. **Run the app**

   ```bash
   uv run python main.py --config config.yaml
   uv run python main.py --config config.yaml --web --port 8088
   ```

## Workflow

- **Bugs and features:** Open an issue using the [Bug report](.github/ISSUE_TEMPLATE/bug_report.md) or [Feature request](.github/ISSUE_TEMPLATE/feature_request.md) templates.
- **Security:** Do not post exploit details publicly. Use the [Security issue](.github/ISSUE_TEMPLATE/security.md) template (high-level only) or the process in [SECURITY.md](SECURITY.md).
- **Planning orientation:** [docs/plans/PLANS_HUB.md](docs/plans/PLANS_HUB.md) lists every `PLAN_*.md` (open + completed) with short summaries—use it to see scope and intent before diving into [docs/plans/PLANS_TODO.md](docs/plans/PLANS_TODO.md). If you add or archive a plan file, run `python scripts/plans_hub_sync.py --write` and commit the updated hub (pre-commit enforces `--check`).
- **Pull requests:** Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md). Prefer **`.\scripts\check-all.ps1`** before push (full gate: plans dashboard, pre-commit, pytest with warnings as errors)—see [docs/ops/README.md](docs/ops/README.md) § *Before you open a PR*. At minimum: tests pass (`uv run pytest -v -W error`; see [docs/TESTING.md](docs/TESTING.md)), lint passes (`uv run ruff check .` / pre-commit), and docs/README are updated when behaviour or setup changes. **Private layout template (tracked):** copy from **`docs/private.example/`** into gitignored **`docs/private/`** per [docs/PRIVATE_OPERATOR_NOTES.md](docs/PRIVATE_OPERATOR_NOTES.md).

### Cursor session keywords vs application CLI

Maintainers may type **English session tokens** in Cursor chat (`deps`, `feature`, `docs`, …) to scope the assistant’s work. Those tokens are **not** flags for **`main.py`**. The Data Boar CLI is documented in **[docs/USAGE.md](docs/USAGE.md)**. Canonical token table: **`.cursor/rules/session-mode-keywords.mdc`**; summary: **[AGENTS.md](AGENTS.md)**.

### Ansible playbooks (Debian/Ubuntu)

Every play that installs packages on Debian/Ubuntu must set `environment: "{{ labop_debian_unattended_apt_environment }}"` (or merge with play-specific extras) so **`apt-listbugs`** does not abort unattended `apt` installs. Shared defaults live in **`group_vars/all.yml`** inside each Ansible tree (`ops/automation/ansible/`, `deploy/ansible/`). CI enforces this with **`tests/test_ansible_playbooks_unattended_apt.py`**. Operator context: **[ops/automation/ansible/README.md](ops/automation/ansible/README.md)** (Troubleshooting).

### Public repo hygiene (LAN, credentials)

- **Root `config.yaml`:** Listed in `.gitignore`—it often holds **filesystem paths**, DB hosts, and passwords. **Do not** `git add -f config.yaml`. Copy from `deploy/config.example.yaml` and keep secrets local. If the file was ever committed by mistake, run `git rm --cached config.yaml` so it stops tracking; **Git history** may still contain old blobs—use `git filter-repo` / BFG and **rotate** any exposed credentials if the repo was public.
- **Homelab / operator notes:** Avoid putting **real hostnames**, **RFC1918 IPs**, **Linux usernames**, or **`$HOME` paths** in tracked Markdown; use placeholders in docs and keep specifics in the **gitignored** `docs/private/` tree (recommended: **`docs/private/homelab/`**) or an external wiki. **Do not** add Markdown links from public docs to paths under `docs/private/`. Policy and layout: [docs/PRIVATE_OPERATOR_NOTES.md](docs/PRIVATE_OPERATOR_NOTES.md). Playbook (generic only): [docs/ops/HOMELAB_VALIDATION.md](docs/ops/HOMELAB_VALIDATION.md) §9.
- **`docs(private-layout):` commits:** Use for **`docs/PRIVATE_OPERATOR_NOTES.md`**, **`docs/private.example/`** (templates/policy). **Never** put real inventory there—**`docs/private/`** only (see [AGENTS.md](AGENTS.md) scope table).
- **Password manager (e.g. Bitwarden):** Storing DB passwords, API keys, and homelab tokens in **Bitwarden** (free tier is fine for solo use) is a good **operator vault**; at runtime still prefer **`pass_from_env`** / `*_from_env` so `config.yaml` stays lean. See [docs/ops/OPERATOR_SECRETS_BITWARDEN.md](docs/ops/OPERATOR_SECRETS_BITWARDEN.md).

### Public repo: third-party identifiers and Git history (LGPD/GDPR alignment)

- **Talent pool / ATS / LinkedIn:** Real names, slugs, and profile URLs belong in **gitignored** paths under `docs/private/commercial/` (for example `talent_pool.json`). Tracked `scripts/talent.ps1` must keep only the `example` placeholder and merge the private JSON at runtime—**do not** reintroduce inline candidate maps or real aliases in public scripts, skills, or examples.
- **Commit messages and PR bodies:** They are **permanent** on the default branch and in notifications. Do not use them for stories about **third parties**, **talent-pool operations**, **legal/whistleblowing** context, or other sensitive narratives. Prefer neutral, technical Conventional Commit subjects and PR text; keep sensitive context in `docs/private/` or in maintainer-agreed private channels.
- **Guards:** CI runs `tests/test_pii_guard.py`, `tests/test_talent_ps1_tracked_no_inline_pool.py`, and `tests/test_talent_public_script_placeholders.py` on **tracked** files. They do **not** rewrite existing history. To audit or remediate **old** commits, see [docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md](docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md) ([pt-BR](docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)) — Parts I–III; legacy filenames under `docs/ops/` redirect to this guide.

### PR state and agent advice (sync before citing PR numbers)

AI assistants and humans should **not** assume a PR is still open or that local `main` matches GitHub **without a fresh check** — chat context can reference an **already merged** PR (e.g. #80) while the next one (#81) is already merged.

- **Minimum:** `git fetch origin` and, on `main`, `git pull origin main` (or at least `git status -sb`) before advising “merge PR #N” or “what’s next” after a merge.
- **GitHub CLI:** `gh pr view <n> --json state,mergedAt,url` or `gh pr list --head <your-branch>`.
- **Automation:** `.\scripts\commit-or-pr.ps1` includes fetch/rebase patterns for PR flows; prefer it over ad-hoc git when possible.
- **After `gh pr create`:** Run `gh pr view --json number,state,url` (or `gh pr list --head <branch>`) **before** sharing the URL so the number matches the **new** PR, not a previous one.

Cursor encodes this in **`.cursor/rules/git-pr-sync-before-advice.mdc`**. See also **[AGENTS.md](AGENTS.md)**. Brief GitHub lag after merge is possible; re-query `gh` if unsure.

### Reducing merge conflicts

- **Commit locally as you go** on a feature branch (meaningful checkpoints or coherent batches—see [docs/ops/COMMIT_AND_PR.md](docs/ops/COMMIT_AND_PR.md) ([pt-BR](docs/ops/COMMIT_AND_PR.pt_BR.md)), **AGENTS.md**, `.cursor/rules/execution-priority-and-pr-batching.mdc`). Large **uncommitted** trees make conflicts and review harder at PR/release time.
- **Merge or rebase `main` into your branch before opening a PR.** Run `git fetch origin main` then `git merge origin/main` (or `git rebase origin/main`) and fix any conflicts locally. That way the PR stays mergeable and reviewers see a clean diff. Repeat **during** long branches, not only at the end.
- **`report/generator.py`:** Sheet-writing logic lives in `_write_excel_sheets` and helpers (`_build_report_info`, `_build_executive_summary_rows`, etc.). When adding or changing Excel sheets, update those helpers rather than inlining logic in `generate_report`. That keeps the same structure as `main` and avoids the merge conflicts we had when main had inlined code and the branch had the refactor.

## Code and docs

- **Style:** The repo uses [EditorConfig](.editorconfig) (indent, charset, line endings). The **CI** **Lint** job runs **`uv run pre-commit run --all-files`** (Ruff + format + plans-stats + plans-hub + markdown + pt-BR + commercial guard). Locally: **`uv run pre-commit install`** then commit as usual, or run **`uv run pre-commit run --all-files`** before PR. If **ruff-format** fails, run **`uv run ruff format .`** and re-stage. See **`.pre-commit-config.yaml`**.
- **Docs:** Keep [README.md](README.md) and [docs/USAGE.md](docs/USAGE.md) in sync with behaviour; update [README.pt_BR.md](README.pt_BR.md) and [docs/USAGE.pt_BR.md](docs/USAGE.pt_BR.md) for Portuguese. All **new** user-facing documentation must exist in **English (canonical)** and **Brazilian Portuguese**; **plan files** and **numbered ADRs** under [docs/adr/](docs/adr/) may be English-only (see [docs/adr/README.md](docs/adr/README.md)). When you change docs to reflect application updates, **sync the other language** (EN first, then pt-BR). Use a language switcher at the top of each doc and cross-links that offer both languages (see [docs/README.md](docs/README.md) — Documentation policy). **After editing any .md file:** run `uv run python scripts/fix_markdown_sonar.py` and `uv run pytest tests/test_markdown_lint.py -v -W error` so SonarQube/markdownlint rules (e.g. MD060 table style) pass. The fix script applies MD029 (ordered list style 1/1/1); if a doc uses **semantic step numbers** (1. 2. 3.), restore them by hand after running the script so the list still reads correctly — rationale: [ADR 0001](docs/adr/ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md).
- **Secrets:** Never commit credentials or real PII. Use `.env` or `config.local.yaml` (both are in `.gitignore`) and redact in issues/PRs.

## CI and dependency hygiene

- **CI:** GitHub Actions run tests and **dependency audit** (`uv run pip-audit`) on every push/PR to `main` (or `master`). PRs must resolve any audit failures (fix or upgrade vulnerable dependencies) before merge. When SonarQube/SonarCloud is enabled (see [docs/TESTING.md](docs/TESTING.md)), address reported issues so the quality gate stays green.
- **Dependencies:** The source of truth for libraries is **`pyproject.toml`** (uv toolchain). The **`uv.lock`** file pins the exact resolved dependency tree so installs are reproducible and users are protected from “it worked yesterday” breakage when a dependency updates. Declare all runtime and dev dependencies in **`pyproject.toml`** (prefer **minimum versions `>=`**; pin `==` only when needed). When you add or change deps, run `uv lock`, then `uv export --no-emit-package pyproject.toml -o requirements.txt`, and commit **pyproject.toml**, **uv.lock**, and **requirements.txt**. Do not edit `uv.lock` or `requirements.txt` by hand for version changes. CI runs `uv sync` (which uses `uv.lock`) and then `pip-audit`, so the locked environment is what is tested and audited. **`tests/test_dependency_artifacts_sync.py`** fails if `uv.lock` is stale versus **`pyproject.toml`** (`uv lock --check`) or if **`requirements.txt`** is not exactly the output of **`uv export`** from that lock—catching accidental single-file bumps (for example Dependabot PRs that only touch **`requirements.txt`**).
- **Dependabot / automation:** Dependabot opens weekly PRs for pip and GitHub Actions. When applying a dependency update (e.g. from a Dependabot PR), update **`pyproject.toml`** first (bump the minimum version), then run `uv lock` and `uv export --no-emit-package pyproject.toml -o requirements.txt`, and commit all three files. Merge dependency PRs only after CI (tests and audit) pass. Dependabot helps signal when to refresh dependencies; acting on those PRs (or before a stable release) keeps the lockfile updated, compatible, and safe. For **security** Dependabot PRs, we use the optional SLA in [SECURITY.md](SECURITY.md) (Security response).

### Editing GitHub Actions workflows (supply chain)

If you change **`.github/workflows/*.yml`** (new jobs, new third-party `uses:`, or `setup-uv`):

1. Follow **[ADR 0005](docs/adr/ADR-0005-ci-github-actions-supply-chain-pins.md)** — pin third-party actions to a **full 40-character commit SHA** (keep the human tag in a YAML **comment** on the same line); pin the **uv** CLI with an explicit **`version:`** semver in **`ci.yml`** — **not** `"latest"`.
1. Run **`uv run pytest tests/test_github_workflows.py -v`** (entire module: SHA pins, Slack webhook step pattern, Semgrep/Gitleaks/SBOM shape, **`ci.yml`** lint = **`pre-commit run --all-files`**, Slack CI failure notify presence + **§4.1.1** pause contract) before you push.

## Release history and changelog

Release history is **git commit/PR history** plus **versioned release notes in `docs/releases/`** (e.g. one file per version). A separate CHANGELOG file in the repo is **not required**; use `docs/releases/` and tags for “where we are” and progress.

## Release checklist (Security)

Before tagging a **stable release**, maintainers should:

- **Lockfile and audit:** Run `uv lock` to refresh the lockfile from current `pyproject.toml`, then `uv sync` and `uv run pip-audit`. Fix or upgrade any high/critical findings, then run `uv export --no-emit-package pyproject.toml -o requirements.txt` and commit **uv.lock** and **requirements.txt** so the release is reproducible, compatible, and safe. This protects users from accidental breakage while keeping the release on audited dependencies.
- **Docs:** Ensure [SECURITY.md](SECURITY.md) and [docs/SECURITY.md](docs/SECURITY.md) reflect current behaviour (validation, headers, API key, logging policy).
- **Secrets and logging:** Confirm no API keys or passwords in logs; config file and env handling restrict access to trusted users (see [SECURITY.md](SECURITY.md)). Ensure **config file permissions** restrict read/write to trusted users and that **config.yaml** (and any file with secrets) is **not committed** (see .gitignore). When adding or changing log statements, do not log raw config, request bodies, or credentials; persist or print failure/exception text via `core.validation.sanitize_log_text` or `core.validation.clean_error` (not raw `str(e)`), so SQL/HTTP client bodies cannot leak into SQLite or logs (regression: `test_redact_*`, `test_sanitize_log_text_*`, `test_clean_error_*`, `test_save_failure_persists_*` in `tests/test_security.py` / `tests/test_database.py`).

## Deployment and production

- Use a dedicated config file (e.g. via `CONFIG_PATH`) and never commit it. Run `uv run pip-audit` before deploying.
- For public or multi-tenant use, put the API behind a reverse proxy (HTTPS, rate limiting, auth) as described in the README.

## See also

- **[docs/TESTING.md](docs/TESTING.md)** ([pt-BR](docs/TESTING.pt_BR.md)) — Test modules, CI, SonarQube.
- **[docs/TOPOLOGY.md](docs/TOPOLOGY.md)** ([pt-BR](docs/TOPOLOGY.pt_BR.md)) — Application topology (modules, classes, data flow).
- **[docs/ops/COMMIT_AND_PR.md](docs/ops/COMMIT_AND_PR.md)** ([pt-BR](docs/ops/COMMIT_AND_PR.pt_BR.md)) — Commit and PR automation.
- **[docs/COMPLIANCE_FRAMEWORKS.md](docs/COMPLIANCE_FRAMEWORKS.md)** ([pt-BR](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md)) — Compliance labels and extensibility.
- **[docs/COPYRIGHT_AND_TRADEMARK.md](docs/COPYRIGHT_AND_TRADEMARK.md)** ([pt-BR](docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md)) — Copyright and trademark (making it official, registries). [NOTICE](NOTICE) for project notice.
- Full doc index: [docs/README.md](docs/README.md) ([pt-BR](docs/README.pt_BR.md)).

If you have questions, open a discussion or an issue. Thanks for contributing.

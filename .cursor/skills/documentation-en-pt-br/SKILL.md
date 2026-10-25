---
name: documentation-en-pt-br
description: Apply when creating or updating user-facing documentation. Ensures new docs exist in English and Brazilian Portuguese (except plan files), code is source of truth, EN is canonical, index and language switchers are updated. Docs must be navigable (no dead ends) and must always link EN ↔ pt-BR when both exist.
---

# Documentation: EN + pt-BR and source of truth

Use this skill when **creating or editing** user-facing documentation (docs/, README, SECURITY, CONTRIBUTING, deploy, testing, observability, etc.) so that docs stay in sync, both languages are covered, and operators can navigate and learn how to use the app and what it is capable of doing.

## Before you type Portuguese (non-negotiable)

Read **`.cursor/rules/docs-locale-pt-br-contract.mdc`** (always on). Every line of **`*.pt_BR.md`** and any Portuguese paragraph in tracked ops docs must read **Brazilian (pt-BR)**, not European (pt-PT), unless the operator explicitly scoped a different regional register. There is no built-in “locale sub-agent” — this skill + that rule + **`tests/test_docs_pt_br_locale.py`** are the stack; for a human-style second pass, spawn a **Task** whose sole job is “diff pt-BR mirror vs EN for locale markers only.”

## Source of truth (order)

1. **Code and application behaviour** – Config, API, CLI, and capabilities are the deepest source of truth. Docs must describe what the app actually does.
1. **English (EN)** – The canonical written source. Update EN first when behaviour or options change; EN must accurately reflect the code.
1. **Brazilian Portuguese (pt-BR)** – Translation of the EN doc; same structure and coverage. Sync pt-BR after updating EN. Use **Brazil** vocabulary and spelling, **not** European Portuguese (pt-PT): e.g. **arquivo** not *ficheiro*, **compartilhar** not *partilhar*, **seção** not *secção*, **padrão** for IT “default” not *defeito*. See **`.cursor/rules/docs-policy.mdc`**.

## Planning links (audience segregation)

- **External / integrator docs** (USAGE, COMPLIANCE_*, GLOSSARY, deploy guides, releases, etc.) must **not** use markdown links into `docs/plans/` or `.cursor/plans/`. Prefer **USAGE**, **TECH_GUIDE**, **releases/**, or **[docs/README.md](../../docs/README.md)** *Internal and reference* (and plain-text `` `docs/plans/` `` where needed).
- **Ops runbooks** (`docs/ops/`) may still link to plans. **docs/README.md** / **README.pt_BR.md** intentionally list plan rows.
- After editing docs, run **`uv run pytest tests/test_docs_external_no_plan_links.py -q`** when you touch external-tier Markdown.
- **Rule:** **`.cursor/rules/audience-segmentation-docs.mdc`**.

## Navigability (no dead ends)

Documentation must be **navigable to and from** other documents:

- **Avoid dead ends:** Every doc should link out to related docs (usage, deploy, testing, troubleshooting, compliance, etc.) where a topic is mentioned, so readers do not get stuck on a page with no way to discover more.
- **Goal:** Make it easy for **operators** to learn how to use the app, what it is capable of doing, and how to get it working properly. Use the **docs/README.md** index and in-doc cross-links so readers can move between topics and languages.

## EN ↔ pt-BR links (required when both exist)

Whenever a doc has a **pt-BR** version (as it should for all user-facing docs except plan files), **both directions** are required:

- **EN doc:** At the top, add `**Português (Brasil):** [Filename.pt_BR.md](Filename.pt_BR.md)` (or path-relative).
- **pt-BR doc:** At the top, add `**English:** [Filename.md](Filename.md)` (or path-relative).

When you cross-link to **another** doc that has both languages, provide both links (e.g. `[DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))` from an EN doc, and the inverse from a pt-BR doc). So EN always links to pt-BR and pt-BR always links to EN; no reader should hit a dead end in one language only.

## When adding a new documentation file

**Exception:** Plan files (`docs/plans/PLAN_*.md`, `docs/plans/PLANS_TODO.md`, `docs/plans/completed/`, `.cursor/plans/`) may be English-only.

For all other new docs (guides, reference, deploy, testing, observability, etc.):

1. **Create the English file first** under `docs/` (or root if it is README, SECURITY, etc.). Start with `# Title` (MD041); add language switcher at top: `**Português (Brasil):** [Filename.pt_BR.md](Filename.pt_BR.md)`.
1. **Add the doc to docs/README.md** in the appropriate table (Usage, Deploy, Internal, etc.). Include both EN and pt-BR links in the row once pt-BR exists.
1. **Create the pt-BR file** with the same structure and sections. Top line: `**English:** [Filename.md](Filename.md)`. Keep coverage and structure aligned with EN.
1. **Run markdown fix and lint:** `uv run python scripts/fix_markdown_sonar.py` then `uv run pytest tests/test_markdown_lint.py -v -W error`. Restore semantic list numbering (1. 2. 3.) by hand if the fix script changed step lists. Fix MD024 (unique headings), MD022/MD032/MD041/MD026 as needed (see markdown-lint rule and quality skill).
1. **pt-BR locale guard:** `uv run pytest tests/test_docs_pt_br_locale.py -v` so pt-BR files do not pick up **European Portuguese** habits (*ficheiro*, *partilhar*, *secção*, *utilizador*, *tem de*, etc.). See **`.cursor/rules/docs-pt-br-locale.mdc`**.

## When updating existing documentation

1. Change **code or behaviour** first if the doc is reflecting a feature change.
1. Update the **English** doc so it matches the application.
1. **Sync the pt-BR** file: same sections, same meaning; update links and examples as needed.
1. Run the markdown fix script and lint test; fix any new violations.
1. Run **`uv run pytest tests/test_docs_pt_br_locale.py -v`** on updated **`*.pt_BR.md`** files.

## Plan files (location and completion)

- **Open plans** live in `docs/plans/` (`PLANS_TODO.md` and `PLAN_*.md`). **Completed plans** live in `docs/plans/completed/`.
- **Plans hub:** After you **add** or **move/archive** a `PLAN_*.md`, run **`python scripts/plans_hub_sync.py --write`** and commit **`docs/plans/PLANS_HUB.md`**. Optional in-plan hints: `<!-- plans-hub-summary: ... -->` and `<!-- plans-hub-related: ... -->`. **pt-BR** intro: **`PLANS_HUB.pt_BR.md`**. Tests: **`tests/test_plans_hub_sync.py`**.
- When you **complete** a plan: mark to-dos done in the plan and in `PLANS_TODO.md`, then **move** the plan file to `docs/plans/completed/`, update `PLANS_TODO.md`, run **`plans_hub_sync.py --write`**, and **retarget or remove** links in **product-facing** docs (prefer USAGE / TECH_GUIDE / releases; avoid new `docs/plans/` hyperlinks from external-tier files per **audience-segmentation-docs**). **Update the pitch** (README and README.pt_BR): remove the item from the Roadmap sentence and reflect the new capability so the pitch stays in sync (see pitch–roadmap rule below).
- **Rule:** `.cursor/rules/docs-plans.mdc` – full workflow for plan location and completion.

## Pitch and roadmap (keep in sync with plans)

The README "For decision-makers" section (the **pitch**) must stay in sync with what we have accomplished and what we are working on:

- **When you create a new plan:** Add the new roadmap goal to the **Roadmap** sentence in README and README.pt_BR (e.g. in "Why it holds up") so the pitch mentions what we are working toward.
- **When you complete a plan:** Remove that item from the Roadmap sentence and, if useful, add or strengthen wording in "What we surface" or "Why it holds up" to describe the **new capability** and why prospects should consider the product. Update both EN and pt-BR.
- **When you remove, cancel, or substitute a plan:** Update the pitch so the Roadmap no longer mentions the dropped goal (or replace with the substitute). Reduce "future development" wording so the pitch does not promise work that is no longer planned. Sync README.pt_BR.
- **Rule:** `.cursor/rules/pitch-roadmap-sync.mdc` – full guidance for pitch and roadmap sync.

## Documentation and code naming

- **Documentation .md** (docs/, root): Use **UPPERCASE subject** names (e.g. `SENSITIVITY_DETECTION.md`, `SENSITIVITY_DETECTION.pt_BR.md`). Do not capitalize the `.md` extension or the language hint (e.g. `.pt_BR.md`).
- **Code, config, rules, skills:** Keep **lowercase** (e.g. `config.yaml`, `regex_overrides.example.yaml`, `markdown-lint.mdc`).
- **Rule:** `.cursor/rules/doc-and-code-naming.mdc` – full convention for doc vs code/config naming.

## Alignment with project

- **Rule:** `.cursor/rules/docs-policy.mdc` – same policy (EN + pt-BR, switcher, index); apply when editing docs.
- **Index:** `docs/README.md` – Documentation policy and tables for all topics and languages.
- **Markdown quality:** `.cursor/rules/markdown-lint.mdc` and `.cursor/skills/quality-sonarqube-codeql/SKILL.md` – MD022, MD026, MD032, MD041, MD024, MD060 so new and updated docs pass the lint test.

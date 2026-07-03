# Cursor rules — phase 2 situationalization (Tier A complete)

**Português (Brasil):** [CURSOR_RULES_PHASE2_SITUATIONALIZATION.pt_BR.md](CURSOR_RULES_PHASE2_SITUATIONALIZATION.pt_BR.md)

## Purpose

This runbook records **why** the Data Boar repo moved a batch of **heavy** Cursor rules from **`alwaysApply: true`** to **`alwaysApply: false`** with **narrow `globs`**, **session tokens**, and explicit **`@rule.mdc` latches**; **what** was intentionally **not** moved in phase 2; and **how to repeat** the ritual safely on a future slice so work stays **token-aware** and reversible.

It complements (does not replace) **[`OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md)** ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)), **[`CURSOR_AGENT_POLICY_HUB.md`](CURSOR_AGENT_POLICY_HUB.md)** ([pt-BR](CURSOR_AGENT_POLICY_HUB.pt_BR.md)), and **[`AGENTS.md`](../../AGENTS.md)**.

## Vocabulary (how we use “Tier” here)

| Tier | Meaning in this repo (phase 2 program) |
| ---- | -------------------------------------- |
| **A** | **Done:** rules that *were* always-on noise and are now **situational** with documented **token → rule** latches and hub wiring. |
| **B** | **Backlog — evaluate next:** always-on rules that *might* become situational **after** a deliberate cost/benefit pass (risk of missed guidance). |
| **C** | **Meta / hygiene:** inventories, tests, snapshots, consolidation-only doc work—not a rule flip by itself. |

This is a **maintainer** vocabulary for planning; it is not a Cursor product tier.

## Tier A — rules situationalized in phase 2 (inventory)

These rules now load from **`globs`** and/or explicit **`@…`** / session tokens instead of every chat:

| Rule file | Role (short) | Typical latch |
| --------- | ------------ | ------------- |
| **`lab-completao-workflow.mdc`** | Lab completão orchestration, SSH, evidence | **`completao`**, `scripts/lab-completao*`, `docs/ops/LAB_COMPLETAO*` |
| **`lab-lessons-learned-archive.mdc`** | Public lab lessons dated snapshots + hub + plan bridges | **`lab-lessons`**, `docs/ops/LAB_LESSONS*`, `docs/ops/lab_lessons_learned/**`, `docs/ops/SPRINT_*POSTMORTEM*` |
| **`dossier-update-on-evidence.mdc`** | Private legal / labour evidence | **`legal-dossier-update`**, `docs/private/legal_dossier/**`, `raw_pastes/**` |
| **`homelab-ssh-via-terminal.mdc`** | LAN / SSH / same-PC-as-operator | **`homelab`**, `docs/ops/HOMELAB*`, `scripts/lab-op*`, etc. |
| **`docs-private-workspace-context.mdc`** | Stacked private Git + `docs/private/` cadence | **`private-stack-sync`**, private ritual paths |
| **`everything-es-cli.mdc`** | Voidtools Everything / `es-find.ps1` | **`es-find`**, `EVERYTHING_ES_*`, `scripts/es-find.ps1` |
| **`release-publish-sequencing.mdc`** | Tag → Release → Docker Hub order | **`release-ritual`**, `VERSIONING.md`, `docs/releases/**`, Hub scripts |
| **`plans-status-pl-sync.mdc`** | Plan header / `PLANS_TODO` / body table sync | **`docs`** / **`feature`** / **`houseclean`** / **`backlog`**, `docs/plans/**` |
| **`plans-archive-on-completion.mdc`** | `git mv` finished `PLAN_*.md` to `completed/` | Plan paths, `plans_hub_sync`, `plans-stats`, **`@plans-archive-on-completion.mdc`** |
| **`sonarqube_mcp_instructions.mdc`** | SonarQube MCP tool etiquette | **`sonar-mcp`**, Sonar home-lab / properties globs |
| **`study-cadence-reminders.mdc`** | Study cadence recap / optional nudges | **`study-check`**, portfolio / sprints / operator-manual globs |

### Always-on pairing (not situationalized in phase 2)

- **`docker-local-smoke-cleanup.mdc`** — stays **always-on** so smoke, prune, and disk hygiene stay **high-frequency** beside situational **`release-publish-sequencing.mdc`** (see [Why keep docker-local-smoke-cleanup always-on?](#why-keep-docker-local-smoke-cleanup-always-on)).
- **`windows-pcloud-drive-search-discipline.mdc`** — stays **always-on** for **`P:\`** / unbounded tree discipline while **`everything-es-cli.mdc`** is situational.
- **`agent-docs-private-read-access.mdc`** — stays **always-on** so assistants **never self-block** on `docs/private/`.

Authoritative history bullets: **[`CHANGELOG.md`](../../CHANGELOG.md)** (*Unreleased* / phase 2 entries).

## Sacred always-on baseline (do not situationalize casually)

Treat these as **defaults** unless the operator explicitly reopens policy:

- **`agent-docs-private-read-access.mdc`** — never self-block on `docs/private/`.
- **`docs-locale-pt-br-contract.mdc`** — Portuguese assistant output stays **pt-BR**, not pt-PT.
- **`docker-local-smoke-cleanup.mdc`** — short, cross-cutting Docker smoke / prune / disk hygiene.
- **`windows-pcloud-drive-search-discipline.mdc`** — `P:` and unbounded tree discipline (paired with situational **`everything-es-cli.mdc`**).
- **`session-mode-keywords.mdc`** — canonical English token table for the whole repo.

## Why we did phase 2 (goals)

1. **Context budget:** Long always-on rules compete for the same prompt “attention” as code and user text. Situational rules attach when files or tokens signal real need.
2. **Signal vs noise:** Lab completão, dossier law, Sonar MCP, and release choreography are **powerful but rare** compared to a quick doc typo fix. They should not dominate every thread.
3. **Explicit operator control:** English session tokens (**`homelab`**, **`release-ritual`**, **`sonar-mcp`**, …) and **`@rule.mdc`** give **reproducible** hooks for **fresh chats** with no transcript memory.
4. **Reversible batches:** Each wave is one coherent **`git commit`**; rollback is **`git revert`** or `git show <parent>:path`.

## Trade-offs (pros and cons)

| Pros | Cons / risks |
| ---- | ------------- |
| Lower baseline noise; more room for task-relevant context | Assistants may **omit** a situational rule if the operator never opens a matching file and forgets **`@`** / token |
| Faster “simple task” chats | **`globs`** can drift when files move—rules need occasional audit |
| Clear map from intent → token → rule (cold-start ladder) | More **documentation surface** to keep in sync (this runbook, ladder, hubs) |
| Easier reasoning about “what is binding now” | Wrong narrow **`globs`** can **over**-attach on accidental file opens |

Mitigation: keep **[`session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc)** **`alwaysApply: true`** as the **canonical token table**, and run the [Reproducible ritual](#reproducible-ritual-concrete-steps) so hubs and tests move together.

## Why locale rules were not part of phase 2 “flip”

**Goal of phase 2 here:** reduce **domain workflow** bulk, not to make **language compliance** conditional.

- **`docs-locale-pt-br-contract.mdc`** stays **`alwaysApply: true`** so **every** assistant answer that uses Portuguese stays **pt-BR by default** (not pt-PT). That is a **cross-cutting** constraint, not a “sometimes” workflow.
- **`docs-pt-br-locale.mdc`** is already **`alwaysApply: false`** with editor-focused **`globs`**—it is a **lint-time / edit-time** helper, not the same class as lab completão.
- **Tests enforce the stack:** **`tests/test_docs_pt_br_locale.py`** will fail on European Portuguese markers in **`*.pt_BR.md`**. Making the contract situational would invite **avoidable** locale regressions and **more** rework (tokens + tests) for little context savings.

So: **locale = strong forced contextual behaviour** in the sense of **non-negotiable prose discipline**, not “load this only when editing pt-BR files.”

## Why keep docker-local-smoke-cleanup always-on?

1. **Short rule, high frequency:** Any Docker build, smoke, or prune on the dev PC benefits from the same hygiene (image tags, container count, disk). The cost in tokens is **small** relative to missing guidance and repeating huge smoke cruft.
2. **Release sequencing is already situational:** **`release-publish-sequencing.mdc`** binds on **`release-ritual`** / release **`globs`**. The **always-on** rule covers the **cross-cutting** “clean up after yourself” layer that also applies **outside** a full publish (local experiments, CI debugging).
3. **Failure mode:** If situationalized, assistants often **skip** prune/smoke cleanup in threads where only `main.py` is open—exactly when disk and tag hygiene still matter.

## Tier B — situationalized (issue #1154, 2026-07)

**Meta:** reduce baseline noise; **not** a magic target of ~13 always-on rules. Rollback: `git revert` the Tier B commit.

| Rule file | Latch (token / `@` / globs) |
| --------- | --------------------------- |
| **`agent-autonomous-merge-and-lab-ops.mdc`** | **`completao`**, **`homelab`**, `scripts/pr-merge-when-green*`, `scripts/lab-op*` |
| **`ats-locale-aware-recommendations.mdc`** | **`talent-ats`**, `docs/ops/LINKEDIN_ATS_PLAYBOOK*` |
| **`audience-segmentation-docs.mdc`** | **`docs`**, **`feature`**, `docs/**` |
| **`clean-slate-pii-self-audit.mdc`** | **`pii-fresh-audit`**, `docs/ops/PII_*` |
| **`collaboration-maintainer-contributor.mdc`** | `CONTRIBUTING.md`, `docs/COLLABORATION_TEAM*` |
| **`cursor-browser-social-sso-hygiene.mdc`** | browser MCP / social tokens; **`@cursor-browser-social-sso-hygiene.mdc`** |
| **`cursor-markdown-preview-guardrail.mdc`** | `docs/ops/CURSOR_MARKDOWN_PREVIEW*` |
| **`git-pr-sync-before-advice.mdc`** | `docs/ops/COMMIT_AND_PR*`, `scripts/commit-or-pr*` |
| **`operator-browser-warm-session.mdc`** | browser/social tasks; **`@operator-browser-warm-session.mdc`** |
| **`operator-career-private-layout.mdc`** | **`operator-sli-check`**, `docs/ops/LINKEDIN_ATS*` |
| **`operator-evidence-backup-no-rhetorical-asks.mdc`** | **`private-stack-sync`**, `scripts/private-git-sync*` |
| **`pre-commit-ruff.mdc`** | `**/*.py`, `.pre-commit-config.yaml` |
| **`repo-scripts-wrapper-ritual.mdc`** | `scripts/**`, `docs/ops/TOKEN_AWARE_SCRIPTS*` |
| **`agent-session-ritual-sync-main-and-private-stack.mdc`** | **`carryover-sweep`**, **`eod-sync`**, **`private-stack-sync`**, `docs/ops/today-mode/**` |

### Merged (redundancy — not new always-on)

- **`operator-chat-language.mdc`** → **`operator-chat-language-pt-br.mdc`** (situational; **`docs-locale-pt-br-contract.mdc`** stays always-on).
- **`persona-rigor.mdc`** → **`linguistic-rigor-and-performance.mdc`** (situational).

### Workstation protection — reframed, still always-on

- **`primary-linux-workstation-protected-no-destructive-repo-ops.mdc`** and **`primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** — **main dev box** vs **secondary** (Linux / L-series) naming; **same destructive-repo rigor** on whichever machine holds the canonical clone.

### Borderline — left always-on (judgment)

- **`check-all-gate.mdc`**, **`execution-priority-and-pr-batching.mdc`**, **`operator-investigation-before-blocking.mdc`**, **`operator-mandate-vs-external-limits.mdc`**

## Tier B — evaluation backlog (superseded by wave above)

_The table below is **historical** pre-#1154; use the [Tier B situationalized](#tier-b--situationalized-issue-1154-2026-07) inventory for current state._

| Rule (examples) | Why it might be Tier B later | Why wait / caution |
| --------------- | ---------------------------- | ------------------- |
| **`operator-direct-execution.mdc`** | Long; mostly relevant when operator says “ship it” | Risk of over-asking confirmations in urgent flows |
| **`operator-investigation-before-blocking.mdc`** | Recovery narrative | Easy to under-apply when user is stuck |
| **`git-pr-sync-before-advice.mdc`** | Merge advice only | Missed `git fetch` guidance hurts trust |
| **`execution-priority-and-pr-batching.mdc`** | PMO-heavy | Still useful in many “what next” threads |
| **`check-all-gate.mdc`**, **`repo-scripts-wrapper-ritual.mdc`** | Script discipline | Core guardrails for CI hygiene |
| **`cursor-browser-social-sso-hygiene.mdc`** | Large; only when browser/MCP | SSO flows are easy to get wrong if rule absent |
| **`agent-autonomous-merge-and-lab-ops.mdc`** | LAB-OP / merge automation | High impact if missed |
| **`cursor-markdown-preview-guardrail.mdc`** | Editor UX | Small but prevents preview confusion |

**Tier B workflow:** For each rule, answer: (1) What fraction of chats need it? (2) Can **`globs`** express that reliably? (3) Is there a **token** or **`@`** latch already? (4) What test or ladder row proves the latch?

## Tier C — meta and hygiene

- **Inventory automation (idea):** A test or script that asserts the list of **`alwaysApply: true`** rules matches an allowlist in docs (optional; maintenance cost).
- **Snapshots:** Private zips under **`docs/private/ops/cursor-config-snapshots/`** (if used) for before/after rule frontmatter.
- **Hub phase “B”:** **[`CURSOR_AGENT_POLICY_HUB.md`](CURSOR_AGENT_POLICY_HUB.md)** is the **clickable** map—keep it aligned with **`AGENTS.md`** when adding any new latch row.

## Reproducible ritual (concrete steps)

Use this checklist **in order** when situationalizing the **next** rule or batch. It is written so a future session spends **fewer tokens** rediscovering steps and avoids **forgotten** EN/pt-BR pairs.

1. **Select the candidate** — Prefer **large**, **domain-specific** rules that rarely apply to generic edits. Confirm it is not in the [Sacred always-on baseline](#sacred-always-on-baseline-do-not-situationalize-casually).
2. **Read the full rule** — Note sections that must stay **binding** when attached; identify cross-links to skills and runbooks.
3. **Design `globs`** — List paths that honestly predict “this thread needs this rule” (use ripgrep / file layout). Avoid `**/*` (defeats situationalization).
4. **Edit frontmatter** — Set **`alwaysApply: false`**; paste **`globs`**; add a short **“When this rule attaches”** blurb if missing.
5. **Session tokens** — If a **fresh chat** would need the rule without those files open, add or extend an English token in **[`session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc)** (and the YAML **`description`** line if present). **Never** invent Portuguese spellings for tokens in committed docs.
6. **Cold-start ladder (EN + pt-BR)** — Add or extend a **task router** row and a **Token → rule latch** subsection in **[`OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md)** and **[`.pt_BR.md`](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)**. Use **pt-BR** vocabulary in the mirror (**arquivo**, not *ficheiro*).
7. **`AGENTS.md`** — Quick index row(s) and session taxonomy line if a **new** token was added.
8. **Policy hub (EN + pt-BR)** — Matching rows in **[`CURSOR_AGENT_POLICY_HUB.md`](CURSOR_AGENT_POLICY_HUB.md)** and **[`.pt_BR.md`](CURSOR_AGENT_POLICY_HUB.pt_BR.md)**.
9. **Session shorthands (EN + pt-BR)** — Bullets in **[`OPERATOR_SESSION_SHORTHANDS.md`](OPERATOR_SESSION_SHORTHANDS.md)** and **[`.pt_BR.md`](OPERATOR_SESSION_SHORTHANDS.pt_BR.md)** when operators need one-hop reminders.
10. **Other cross-links** — e.g. **`VERSIONING.md`**, skills, or companion rules that mention the old always-on assumption.
11. **`CHANGELOG.md`** — **`Unreleased`** bullet: what flipped, what stayed always-on, **rollback** hint (`git revert` / `git show <parent>:path`).
12. **Validate** — At minimum: `uv run pytest tests/test_docs_pt_br_locale.py tests/test_markdown_lint.py tests/test_pii_guard.py -q` — for larger doc edits, run **`.\scripts\check-all.ps1`** (or **`./scripts/check-all.sh`**) before merge.
13. **Commit once** — Single coherent commit per batch so rollback is trivial; then push.

**Why reproducible?** Phase 2 touched **many files per rule** (rule + keywords + ladder EN/pt-BR + hubs + shorthands + changelog). A fixed checklist prevents **partial** wiring that passes locally but confuses the next **token-aware** session.

## Related

- **[`OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md)** ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)) — Task router + latches.
- **[`CURSOR_AGENT_POLICY_HUB.md`](CURSOR_AGENT_POLICY_HUB.md)** ([pt-BR](CURSOR_AGENT_POLICY_HUB.pt_BR.md)) — Theme → first doc map.
- **[`TOKEN_AWARE_SCRIPTS_HUB.md`](TOKEN_AWARE_SCRIPTS_HUB.md)** ([pt-BR](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)) — Scripts ↔ tokens ↔ skills.
- **[`AGENTS.md`](../../AGENTS.md)** — Long-form assistant contract.
- **Skill:** [`.cursor/skills/token-aware-automation/SKILL.md`](../../.cursor/skills/token-aware-automation/SKILL.md).

# Shorthands and wrappers hub

**Português (Brasil):** [SHORTHANDS_HUB.pt_BR.md](SHORTHANDS_HUB.pt_BR.md)

> **For agents:** prefer an existing shorthand or wrapper before assembling a long ad-hoc command.
> Platform: **W** = Windows `.ps1`, **L** = Linux/bash, **A** = both when a documented twin exists.
> This page **indexes** files that exist. It does **not** create empty `.sh` twins to close a table.

Canonical detail stays in the source docs.

## Lab-op shorthands

Source: [`LAB_OP_SHORTHANDS.md`](../ops/LAB_OP_SHORTHANDS.md) ([pt-BR](../ops/LAB_OP_SHORTHANDS.pt_BR.md)). Wrapper: `scripts/lab-op.ps1`.

| Shorthand | Expansion | Platform | Source |
| --------- | --------- | -------- | ------ |
| `report` | `homelab-host-report.sh` via `lab-op.ps1 -Action report` | W (entry) / L (on-host script) | LAB_OP_SHORTHANDS |
| `report-all` | Report on every host in the private manifest | W | LAB_OP_SHORTHANDS |
| `sync-collect` | Optional `git pull` per clone, then report | W | LAB_OP_SHORTHANDS |

## Session shorthands (chat tokens)

Canonical table (do not fork): [`.cursor/rules/session-mode-keywords.mdc`](../../.cursor/rules/session-mode-keywords.mdc). Operator notes: [`OPERATOR_SESSION_SHORTHANDS.md`](../ops/OPERATOR_SESSION_SHORTHANDS.md).

Tokens listed in `AGENTS.md` session taxonomy (English-only; type exactly): `deps`, `feature`, `homelab`, `external-eval`, `completao`, `lab-lessons`, `docs`, `houseclean`, `backlog`, `pmo-view`, `study-check`, `sidequest`, `glossary-check`, `feedback-inbox`, `today-mode`, `carryover-sweep`, `morning-readiness`, `eod-sync`, `block-close`, `private-stack-sync`, `safe-commit`, `pii-fresh-audit`, `pii-remediation-ritual`, `legal-dossier-update`, `es-find`, `x-pace-check`, `x-posted`, `social-today-check`, `sonar-mcp`, `release-ritual`, plus brevity `short` / `token-aware`.

Scope text stays in the `.mdc` — this hub does not restate commercial or private workflows.

## Windows fast CLI wrappers

Source: [`WINDOWS_FAST_CLI_WRAPPERS.md`](../ops/WINDOWS_FAST_CLI_WRAPPERS.md). Linux analogues are **not** empty twins of these scripts.

| Wrapper | Linux analogue (tools, not a repo `.sh`) | Source |
| ------- | ---------------------------------------- | ------ |
| `scripts/es-find.ps1` (`es.exe`) | `find` / `fd` / `locate` / `plocate` | WINDOWS_FAST_CLI_WRAPPERS · EVERYTHING_ES |
| `scripts/repo-grep.ps1` | `rg` | WINDOWS_FAST_CLI_WRAPPERS |
| `scripts/repo-tail.ps1` | `tail` | WINDOWS_FAST_CLI_WRAPPERS |
| `scripts/repo-view.ps1` | `bat` / `batcat` / `head` | WINDOWS_FAST_CLI_WRAPPERS |
| `scripts/video-frame-samples.ps1` | `ffmpeg` / `ffprobe` | WINDOWS_FAST_CLI_WRAPPERS |
| `scripts/image-inspect.ps1` | `uv run python scripts/image_inspect.py` | WINDOWS_FAST_CLI_WRAPPERS |

Dev gates that **are** paired: [`SCRIPTS_CROSS_PLATFORM_PAIRING.md`](../ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md) (`check-all`, `lint-only`, `quick-test`, …).

## Gaps (PS1 without `.sh` — audit only)

Run (do not invent empty `.sh` twins to close a table):

- `uv run python scripts/check_cross_platform_gaps.py --missing-only`
- wrappers: `scripts/check-cross-platform-gaps.ps1` / `scripts/check-cross-platform-gaps.sh`

Pairing is for behaviour-aligned **dev gates**. Most operator `.ps1` files stay Windows-first on purpose (`SCRIPTS_CROSS_PLATFORM_PAIRING.md` already says not everything is paired).

A committed dump of every `scripts/*.ps1` name is **not** in this hub: some filenames match PII seeds, and copying them into a new Markdown file fails the gatekeeper. Pytest `tests/test_check_cross_platform_gaps.py` locks the classifier. The auditor prints the P3 total when you run it.

## Related maps

- [INDEX.md](INDEX.md)
- [`TOKEN_AWARE_SCRIPTS_HUB.md`](../ops/TOKEN_AWARE_SCRIPTS_HUB.md)
- [`OPS_HUB.md`](OPS_HUB.md)

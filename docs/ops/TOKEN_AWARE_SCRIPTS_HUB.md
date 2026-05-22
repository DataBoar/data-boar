# Token-aware scripts hub (map + coverage)

**Português (Brasil):** [TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)

**Purpose:** One index of **repo automation** under **`scripts/`** (mostly **`.ps1`** on Windows; **paired `.sh`** for Linux/macOS gates — see **[`SCRIPTS_CROSS_PLATFORM_PAIRING.md`](SCRIPTS_CROSS_PLATFORM_PAIRING.md)**) and how each area connects to **skills**, **rules**, **session keywords**, and **ops runbooks** — so we reuse prior work instead of re-discovering scripts each session.

**Not a duplicate of:** **`.cursor/skills/token-aware-automation/SKILL.md`** (daily commands) or **`.cursor/rules/session-mode-keywords.mdc`** (chat tokens). This file answers: *“what else exists, and where is it documented?”*

**Assistant ritual:** **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** (`alwaysApply: true`) — skim this hub before reinventing long shell; use agreed **`scripts/*.ps1`** paths; if a wrapper fails, **notify the operator** (install/mount/PATH) instead of silently “forgetting” the automation.

**Fresh chat / low context:** read **[OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md)** ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)) first — ordered ladder + task router so you open this hub *after* you know which script family matters.

---

## 1. Golden path (every session)

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `check-all.ps1` | Full gate (Windows) | **`token-aware-automation`** SKILL, **`.cursor/rules/check-all-gate.mdc`**, `CONTRIBUTING.md`, **[`SCRIPTS_CROSS_PLATFORM_PAIRING.md`](SCRIPTS_CROSS_PLATFORM_PAIRING.md)** |
| `check-all.sh` | Full gate (Linux / macOS; bash) — same steps as **`check-all.ps1`**; PII seeds via **`uv run python scripts/gatekeeper_audit.py`** (**`pwsh`** not required — issue **`#560`**) | Same as **`check-all.ps1`** |
| `lint-only.ps1` | Docs/style only | Same + pairing doc |
| `lint-only.sh` | Same (Linux / macOS) | Same |
| `quick-test.ps1` | Narrow pytest | Same + pairing doc |
| `quick-test.sh` | Same (Linux / macOS) | Same |
| `pre-commit-and-tests.ps1` | Pre-commit + full pytest (thin; no gatekeeper) | **`check-all.ps1`** delegates here |
| `pre-commit-and-tests.sh` | Same (Linux / macOS) | Pairing doc |
| `preview-commit.ps1`, `commit-or-pr.ps1`, `create-pr.ps1` | Commit / PR | Same + **`docs/ops/COMMIT_AND_PR.md`** |
| `pr-merge-when-green.ps1` | Merge when CI green | **`.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc`**, **`autonomous-merge-and-lab`** SKILL |
| `safe-workspace-snapshot.ps1` | Pre-commit snapshot | Session **`safe-commit`** |
| `smoke-maturity-assessment-poc.ps1` | Fast pytest subset (maturity POC gate 1) | [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md), [SMOKE_MATURITY_ASSESSMENT_POC.md](SMOKE_MATURITY_ASSESSMENT_POC.md) |

### 1b. GitHub Actions YAML contract (pytest — not under `scripts/`)

| Artifact | How to run | Wired to |
| -------- | ---------- | -------- |
| **[`tests/test_github_workflows.py`](../../tests/test_github_workflows.py)** | **`.\scripts\quick-test.ps1 -Path tests/test_github_workflows.py`** (or full **`check-all`**) · **`./scripts/quick-test.sh --path tests/test_github_workflows.py`** | **[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)** runs **`uv run pytest`** on the **full** suite (this module always included); **[ADR 0005](../adr/ADR-0005-ci-github-actions-supply-chain-pins.md)**; **[`OPERATOR_NOTIFICATION_CHANNELS.md`](OPERATOR_NOTIFICATION_CHANNELS.md)** §4.1 / §4.1.1; **[`TESTING.md`](../TESTING.md)** |

**Use after:** edits to **`.github/workflows/*.yml`** (Slack, `ci.yml` pins / lint job, Semgrep, Gitleaks, SBOM, Dependabot sync, zizmor) — fast feedback without running the entire product test matrix.

### 1a. Windows fast CLI (content / tail / preview)

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `repo-grep.ps1` | Content search: **`rg`**, optional **`baregrep`** (`-PreferBareGrep`; also **`Downloads`**) | **`docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md`**, **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** |
| `repo-tail.ps1` | Last **N** lines: Git **`tail.exe`**, else **`Get-Content -Tail`** | Same |
| `repo-view.ps1` | Capped preview: **`bat`** / **`batcat`**, else **`Get-Content`** | Same |
| `video-frame-samples.ps1` | Sparse **PNG** frames from video (**`ffmpeg`** / **`ffprobe`**; operator **timestamps**) | **`docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md`**, **`.cursor/skills/video-frames-for-agent/SKILL.md`**, **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** |

### 1c. Still images + audio + video tags (operator inspect)

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `image-inspect.ps1` | **uv** wrapper: **`image_inspect.py`** — EXIF / mutagen / **ffprobe** + optional **Tesseract** (same stack as **`rich_media_sample`**) | **`docs/ops/IMAGE_EXIF_OCR_FOR_AGENT.md`**, **`.cursor/skills/image-inspect-for-agent/SKILL.md`** |
| `image_inspect.py` | One-file CLI over **`build_rich_media_text_sample`** | Same |
| `icloud-photos-fetch-range.ps1` | Stage iCloud / Apple Photos files into **`docs/private/icloud_temp/`** (then inspect) | Private **`ICLOUD_PHOTOS_SYNC_GUIDE.md`** when present; **`session-collect`** |

---

## 2. PII / public tree / primary dev workstation

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `pii-fresh-clone-audit.ps1` | Fresh clone + guards (Windows) | **`pii-fresh-clone-audit`** SKILL, **`docs/ops/PII_FRESH_CLONE_AUDIT.md`**, session **`pii-fresh-audit`**, **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`** |
| `new-b2-verify.ps1` | Username path segment audit (`C:\Users\...`) | **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** |
| `run-pii-local-seeds-pickaxe.ps1` | Pickaxe over local seeds (Windows) | **`docs/private.example/scripts/README.md`**, PII guide |
| `run-pii-history-rewrite.ps1` | History rewrite (dangerous) | PII guide Part II — **not** for routine primary Windows dev PC; **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`** |
| `es-find.ps1` | Filename search (**`es.exe`**, optional **`-FallbackPowerShell`**) | **`everything-es-search`** SKILL, **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**, session **`es-find`** |
| `social-x-pace-remind.ps1` | X editorial due rows vs gitignored `SOCIAL_HUB.md`; optional Slack POST | Session **`x-pace-check`**, **`x-posted`**; **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`** §6; private **`OPERATOR_X_PACE_AND_VALIDATION.pt_BR.md`** |
| `social_x_thread_lengths.py` | Validates fenced blocks under `## Thread pronta` in `2026*_x_*.md` (default max 279) | Private **`SOCIAL_HUB.md`**, **`X_PLATFORM_LIMITS_AND_PREMIUM.pt_BR.md`**; `uv run python scripts/social_x_thread_lengths.py` |

---

## 3. Homelab, lab-op, energy, network

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `lab-op.ps1` | SSH report / sync-collect | **`docs/ops/LAB_OP_SHORTHANDS.md`**, **`lab-op-systems-context.mdc`** |
| `lab-op-sync-and-collect.ps1` | Multi-host batch | **`autonomous-merge-and-lab`** SKILL, private manifest |
| `lab-completao-inventory-preflight.ps1` | Staleness check on private **`LAB_SOFTWARE_INVENTORY.md`** / **`OPERATOR_SYSTEM_MAP.md`**; optional **`lab-op-sync-and-collect.ps1`** | **`LAB_COMPLETAO_RUNBOOK.md`** (*Inventory freshness*); invoked by **`lab-completao-orchestrate.ps1`** by default |
| `lab-completao-orchestrate.ps1` | Lab “completão” (preflight + optional **`lab-op-git-ensure-ref`** when **`completaoTargetRef`** / **`-LabGitRef`** + optional **data contract** YAML when **`completaoDataContractsPath`** + optional **read-only** **`docker`/`podman` `image inspect`** preflight when **`completaoImageRefs`** + SSH smoke per host + optional HTTP; writes **`completao_*_orchestrate_events.jsonl`**, **`lab_result.json`** with **`audit_trail`** + **`exit_code_semantic`**, optional **`GRC_EXECUTIVE_REPORT.json`** via **`scripts/generate_grc_report.py`**, **`exit`** **0**/**1** on the success path per **`DATA_BOAR_COMPLETAO_EXIT_v1`**) | **`LAB_COMPLETAO_RUNBOOK.md`** (*Structured orchestration events*, *Data contract preflight*, *Telemetry-first exit codes*), **[ADR 0041](../adr/ADR-0041-lab-completao-data-contract-preflight.md)**, manifest **`completaoTargetRef`**, **`completaoHealthUrl`**, **`completaoDataContractsPath`**, **`completaoImageRefs`**, **`completaoImageProbeSshHost`**, **`-SkipImagePreflight`**, optional **`completaoEngineMode`:** **`container`** / **`completaoSkipEngineImport`** |
| `lab-completao-orchestrate-hybrid-v173.ps1` | Optional high-density path (scp ephemeral config + **`docker`/`podman` run**); **skips run** when image missing on node; **`completao_hybrid_*_events.jsonl`** | **`LAB_COMPLETAO_RUNBOOK.md`** (*Structured orchestration events*); invoked from **`lab-completao-orchestrate.ps1 -HybridLabOpHighDensity173`** |
| `run-benchmark.ps1` + `benchmark_sqlite_diff.py` | Optional A/B harness: two timed **`lab-completao-orchestrate.ps1`** runs (**`-LabGitRef`**, e.g. **`v1.7.3`** vs **`origin/main`**), optional **`-SqlitePath`** copies, optional **`data-boar-report`** after round 2, writes **`bench/COMPARISON.log`**; Python helper diffs two SQLite files when both **`bench/v1.7.3/results.db`** and **`bench/v1.7.4/results.db`** exist | **`LAB_COMPLETAO_RUNBOOK.md`** (*Target git ref*); **`bench/`** is gitignored |
| `benchmark-ab.ps1` | **Git** A/B on the dev clone: guard dirty tree (**`-AutoStash`** / **`-AllowDirty`**), **`git checkout`** legacy tag then **`lab-completao-orchestrate.ps1`**, restore branch/HEAD, second completão pass, copy/move logs (and optional SQLite / **`data-boar-report`**) under **`benchmark_runs/`**, append **`benchmark_runs/times.txt`** with **`Measure-Command`** totals | **`LAB_COMPLETAO_RUNBOOK.md`** (*Target git ref*, *Primary Windows dev PC* blast radius: normal checkout only); **`benchmark_runs/`** is gitignored |
| `lab_completao_data_contract_check.py` | Validates required DB columns from a YAML contract (SQLAlchemy URL via env var only); fails fast before host smoke; process exits **`DATA_BOAR_COMPLETAO_EXIT_v1`** (**0** ok, **1** infra/DB reachability, **2** schema/YAML shape, **3** reserved) | **`LAB_COMPLETAO_RUNBOOK.md`** (*Data contract preflight*, *Telemetry-first exit codes*), **`docs/private.example/homelab/completao_data_contracts.example.yaml`**; **`uv run python scripts/lab_completao_data_contract_check.py --contracts <path>`** |
| `completao-chat-starter.ps1` | Print minimal Cursor chat lines (**`completao`** + **`tier:…`**, plus **`semver:`** / **`tag:`** for **`release-master`**) + suggested command; **`release-master -ReleaseSemver X.Y.Z`** for future tags | **`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`**, **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT*.md`**, **`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`** (full blocks A–E when prose changes) |
| `maestro-deep-rc-monitor-collect.ps1` | One-shot lab session: **`scripts/maestro/Maestro.ps1 -Deep`**, optional **`Get-LabStatus`** loop (defaults **15** x **20s**), **`Maestro.ps1 -Collect`**; **`-SkipMonitor`**, **`-SkipCollect`**, **`-ClearHostEachLoop`**; **`Ref`** passed through to Maestro; exit code = max non-zero child (Docker preflight in Maestro still needs a local engine when the tarball build path runs) | **`scripts/maestro/Maestro.ps1`**, private **`docs/private/homelab/data/inventory.json`**, **`LAB_COMPLETAO_RUNBOOK.md`**, **`tests/config/benchmark-rc.yaml`**, **`tests/test_maestro_scripts.py`** |
| `lab-op-git-ensure-ref.ps1` | Check or reset LAB clones to a tag / **`origin/main`** / branch tip | **`LAB_COMPLETAO_RUNBOOK.md`**; invoked by **`lab-completao-orchestrate.ps1`** when a target ref is set |
| `lab-op-pre-big-bang.ps1` | Pre-Big-Bang gate: tag-aware inventory warmup, **`lab-op-git-ensure-ref`**, operator firewall/fail2ban checklist, optional read-only probes | **`LAB_COMPLETAO_RUNBOOK.md`** (*Pre-Big-Bang gate*) |
| `collect-homelab-report-remote.ps1`, `run-homelab-host-report-all.ps1` | Remote reports | **`HOMELAB_VALIDATION.md`**, private manifest |
| `lab-allow-data-boar-inbound.ps1`, `lab-allow-data-boar-inbound.sh` | Lab firewall allow for TCP 8088 (Windows / Linux) | **`DATA_BOAR_LAB_SECURITY_TOOLING.md`** |
| `lab-env-load.ps1` | Dot-source env for probes | **`lab-op-systems-context.mdc`** §3 |
| `growatt.ps1`, `enel.ps1`, `energy-report.ps1` | Solar / grid / correlation | **`homelab-lab-op-data`** SKILL, **`LAB-ROUTER-01-scan`**, **`solar-snap`**, **`enel-check`**, **`energy-report`** keywords |
| `growatt-session-collect.ps1`, `enel-session-collect.ps1` | Session window refresh | **`session-aware-collect`** SKILL, **`session-collect`** keyword |
| `LAB-ROUTER-01.ps1`, `snmp-LAB-ROUTER-01-lab-probe*.ps1`, `LAB-ROUTER-01-api-*.ps1` | UniFi / LAB-ROUTER-01 | **`homelab-lab-op-data`** SKILL, **`LAB-ROUTER-01-scan`** |
| `windows-dev-report.ps1` | Dev PC inventory | **`docs/ops/`** homelab matrix docs |

### GRC executive JSON (Python CLIs)

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `generate_grc_report.py` | Build ``data_boar_grc_executive_report_v1`` JSON (lab hook; optional raw scan + ``lab_result.json``) | **`LAB_COMPLETAO_RUNBOOK.md`**, **[`REPORTS_AND_COMPLIANCE_OUTPUTS.md`](../REPORTS_AND_COMPLIANCE_OUTPUTS.md)**, **[`GRC_EXECUTIVE_REPORT_SCHEMA.md`](../GRC_EXECUTIVE_REPORT_SCHEMA.md)** |
| `export_reports.py` | XLSX remediation table + executive PDF from the same v1 JSON | **`report/grc_export_multiformat.py`**, schema + example under **`schemas/`** |

### Product console entrypoints (PyPI `[project.scripts]`)

| Command | Role | Wired to |
| ------- | ---- | -------- |
| `data-boar` | Main CLI / API entry (`main.py`) | **[`USAGE.md`](../USAGE.md)** |
| `data-boar-report` | Executive Markdown from **local SQLite** session (`cli.reporter`); no live SQL connector | **[`USAGE.md`](../USAGE.md)** (section 5, *Executive desk summary*) · [pt-BR](../USAGE.pt_BR.md) |

---

## 4. Talent / ATS (mostly `docs/private/commercial/`)

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `talent.ps1` | Pool CLI (scan, import, review, …) | **`candidate-ats-evaluation`** SKILL, **`TALENT_SHORTHAND_HUB.pt_BR.md`** (private) |
| `candidate-dossier-scaffold.ps1` | Dossier files | Session **`talent-dossier`** |
| `ats.ps1`, `ats-candidate-import.ps1`, `ats-hub-export.ps1`, `ats-profile.ps1` | ATS pipeline helpers | Same skill; align with **`talent.ps1`** when choosing entry point |
| `normalize_pool_sync_snapshot.ps1` | Snapshot table text hygiene | Session **`talent-pool-sync`** |
| `generate_pool_sync_snapshot.py` | Generate pool snapshot markdown | Called from orchestration / pool workflow (see private hub) |
| `generate_talent_playbooks_v2.py` | LinkedIn playbooks v2 MD + pandoc exports | Private **`linkedin_peer_review/individual/v2/`** + **`ats_sli_hub/exports/v2/`** — see **`docs/private.example/commercial/ats_sli_hub/exports/README.md`** |

*Session keywords:* **`talent-dossier`**, **`talent-ats`**, **`talent-pool-sync`**, **`talent-map`**, **`talent-brief`**, **`talent-status`** — see **`session-mode-keywords.mdc`**.

---

## 5. Git / hygiene / release

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `git-progress-recap.ps1`, `progress-snapshot.ps1` | Progress / recap | Operator ritual; pair with **`eod-sync`** / **`git-pr-sync-before-advice.mdc`** |
| `git-cleanup-merged-gone-branches.ps1` | Branch cleanup | **`docs/ops/BRANCH_AND_DOCKER_CLEANUP.md`**, **`houseclean`** mode |
| `pr-hygiene-remind.ps1` | PR reminder | **`houseclean`**, open PR discipline |
| `recovery-doc-bundle-sanity.ps1` | Doc bundle recovery | **`check-all-gate.mdc`**, **`DOC_BUNDLE_RECOVERY_PLAYBOOK.md`** |
| `new-adr.ps1` | ADR scaffold | **`AGENTS.md`** ADR habit, **`docs/adr/README.md`** |
| `pre-commit-and-tests.ps1` | Thin wrapper | Prefer **`check-all.ps1`** unless you need the subset |
| `gatekeeper-audit.ps1` | PII seeds vs **staged paths only** (`git diff --cached --name-only` + `git grep -F -f`); drops public-identity seeds (**FabioLeitao**, **`C:\Users\fabio`**, **`/home/leitao`**) before grep; first gate in **`check-all.ps1`** | **`PII_LOCAL_SEEDS.txt`** (private), **`PII_REMEDIATION_RITUAL.md`** |
| `gatekeeper_audit.py` | Python port (**`uv run python`**) — same gate for **`check-all.sh`**, **`pre-commit`**, and collaborators without **`pwsh`** | Same seeds file; **`#560`** |
| `private-git-sync.ps1` | Nested private repo (`-Push`: **`lab-*`** + optional **VC bare `notes-sync.git` on `Z:`** (default) **then `Y:`** + `P:` tree mirror when mounted) | **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`**, **`PRIVATE_STACK_SYNC_RITUAL.md`**, session **`private-stack-sync`**, **`PRIVATE_OPERATOR_NOTES.md`**, **ADR 0040**, **`operator-evidence-backup-no-rhetorical-asks.mdc`** |
| `license-smoke.ps1`, `version-readiness-smoke.ps1`, `release-integrity-check.ps1` | Release checks | **`docs/releases/`**, **`VERSIONING.md`** |
| `generate-sbom.ps1` | SBOM | **`WORKFLOW_DEFERRED_FOLLOWUPS.md`**, security docs |
| `gitlab-mirror-health-check.ps1` | Mirror health | **`GITLAB_GITHUB_MIRROR.md`** |
| `docker-lab-build.ps1`, `docker-hub-pull.ps1`, `docker-prune-local.ps1`, `docker-scout-critical-gate.ps1` | Docker lab / Hub / Scout | **`docker-smoke-container-hygiene`** SKILL, **`token-aware-automation`** SKILL |

---

## 6. Operator day / session / iCloud

| Script | Role | Wired to |
| ------ | ---- | -------- |
| `operator-day-ritual.ps1` | Morning / EOD | Sessions **`carryover-sweep`**, **`eod-sync`** |
| `session-collect.ps1` | Cookie / session window | **`session-aware-collect`** SKILL, **`session-collect`** keyword |
| `icloud-photos-fetch-range.ps1` | iCloud range fetch | **`session-collect`** row (iCloud) |

---

## 7. Niche / advanced (use when the task matches)

| Script | Role | Note |
| ------ | ---- | ---- |
| `external-review-pack.ps1` | Pack for external review | Pair with **`feedback-inbox`**, **`GEMINI_PUBLIC_BUNDLE_REVIEW.md`** |
| `auto-mode-session-pack.ps1` | Session pack | Operator workflow experiments |
| `lab-node-01-ansible-baseline.ps1` | Ansible baseline | Lab host provisioning (private details stay private) |
| `lab-node-01-ansible-labop-podman-apply.sh` | Podman Ansible (sudoers-fixed args) | Invoked via `sudo -n` + narrow `LABOP_ANSIBLE_PODMAN`; see **LAB_OP_PRIVILEGED_COLLECTION.md** |
| `unifi-ssh-deep-audit.ps1` | Deep UniFi SSH | High signal; LAN-specific — **private** notes only |
| `linkedin-review-batch.ps1` | LinkedIn batch | Talent / social; keep outputs private |
| `gh-ensure-default.ps1` | GitHub default branch | One-off setup |

---

## 8. Operator-private economics (not “product” automation)

Scripts such as **`household-finance.ps1`**, **`claro.ps1`**, **`aguas.ps1`**, **`leste.ps1`** are for **operator-only** workflows; they do not need Cursor skills. Keep usage and outputs in **`docs/private/`** / vault — not in PRs or tracked evidence.

---

## 9. Coverage gaps (good next steps — without exploding tokens)

| Gap | Suggestion |
| --- | ---------- |
| **`new-b2-verify.ps1`** not in **`token-aware-automation`** table | Add one row pointing to **`PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** (optional; avoids duplicating this hub). |
| **`operator-day-ritual.ps1`** only via keywords | Enough; link from this hub only. |
| **ATS split** (`ats*.ps1` vs `talent.ps1`) | Document preferred entry in **`candidate-ats-evaluation`** SKILL next time ATS changes. |
| **Release trio** (`license-smoke`, `version-readiness-smoke`, `release-integrity-check`) | Optional mini-table in **`docs/releases/`** README — not a new session keyword. |
| **`talent-pool-sync`** keyword historically cited **`talent-pool-sync-snapshot.ps1`** | Repo uses **`scripts/generate_pool_sync_snapshot.py`** + **`scripts/normalize_pool_sync_snapshot.ps1`**; keyword row updated to match (**`session-mode-keywords.mdc`**). |

**Policy:** **`OPERATOR_WORKFLOW_PACE_AND_FOCUS.md`** §3 — avoid adding many new chat tokens; prefer **`backlog` + named item** or this **hub** for discovery.

---

## Related

- **`.cursor/skills/token-aware-automation/SKILL.md`**
- **`docs/plans/TOKEN_AWARE_USAGE.md`**
- **`docs/ops/OPERATOR_SESSION_SHORTHANDS.md`**

# Operator “today mode” — 2026-03-26 (morning)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md)

**Purpose:** One-screen focus for **the day after** the long **2026-03-25** session: land the open tree, **green CI**, **correct version story**, **Corporate-Entity-C** mail.

---

## Progress already made (2026-03-25 — sleep summary)

| Area                | Outcome                                                                                                                                                                            |
| ----                | -------                                                                                                                                                                            |
| **CI / pre-commit** | Lint job runs **`uv run pre-commit run --all-files`**; **`.pre-commit-config.yaml`** includes **`plans-stats-check`**; local **`pre-commit install`** recommended in CONTRIBUTING. |
| **Docs / ADR**      | **0000–0003** in `docs/adr/`; **WORKFLOW_DEFERRED_FOLLOWUPS** (EN + pt-BR); **ACADEMIC_USE_AND_THESIS** (EN + pt-BR) indexed in `docs/README`.                                     |
| **Quality**         | **quality-sonarqube** rule + skill aligned; **check-all-gate** notes pre-commit scope.                                                                                             |
| **Corporate-Entity-C**          | Guideline fixed so reviewers **derive tag vs pyproject**; **WRB_DELTA_SNAPSHOT_2026-03-26** ready to paste.                                                                        |
| **Version**         | **No 1.6.8.** Repo string **1.6.7**; **tag** still **v1.6.6** until you publish — next step is **tag + release**, not another bump.                                                |

---

## Today (2026-03-26) — suggested order

1. **`git status`** — review scope; split commits if needed (e.g. `ci:` vs `docs:`).
1. **`.\scripts\check-all.ps1`** — full green before push (or `check-all -SkipPreCommit` only if you already ran pre-commit).
1. **Commit + PR** (or direct push if policy allows) — merge to `main`.
1. **Tag `v1.6.7`** on the release commit and **GitHub Release** + **Docker** per internal checklist — *this completes* what `docs/releases/1.6.7.md` already describes.
1. **Morning: Corporate-Entity-C** — send WRB using guideline + [WRB_DELTA_SNAPSHOT_2026-03-26.md](../WRB_DELTA_SNAPSHOT_2026-03-26.md) paste block.

---

## Update (verified **2026-03-31** — GitHub + Docker Hub)

**`v1.6.7` is published:** git tag **`v1.6.7`**, GitHub Release **Latest** (published **2026-03-26**), Docker Hub **`fabioleitao/data_boar:1.6.7`** and **`:latest`** (pushed **2026-03-26**). The “tag still **v1.6.6**” line in the table above was **pre-publish**; do not treat tag / GitHub Release / Hub as pending.

**Still operator-owned:** Corporate-Entity-C WRB send, Slack notification proof, optional branch protection.

---

## Optional

- Branch protection: enable **required checks** after this merge proves green (Semgrep + CI).
- SBOM (CycloneDX): follow [ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) in a later PR.

---

## Chat shorthand

Tell the agent: **`today-mode 2026-03-26`** or open this file.

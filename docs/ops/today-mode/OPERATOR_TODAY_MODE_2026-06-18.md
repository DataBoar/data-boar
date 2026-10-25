# Operator today-mode — 2026-06-18 (Maestro e2e "for real" → handoff to Cursor)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-06-18.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-18.pt_BR.md)

**Note:** Same agreed plan with the operator + the read-only auditor (Claude Code) + Cursor, each on its own rhythm. The three fronts persist — **A (Vault, isolated warm-up) → B (Maestro smoke → completão) → C (release gate #406, fed by B)** — but **today's headline is B**: yesterday (17th) Claude spent the day on **Maestro micro-fixes** (several, as expected); today he gets a shot at a **real end-to-end round**, after which the **handoff to Cursor** should follow. Full operational detail (lab hostnames, Vault/iPhone specifics) lives in the **private map**, not in this tracked file.

**`main` anchor:** `139f754c` — last CI-green PR merge was **#939** (`102cd74f`, README forensic-grade tagline). Yesterday's docs-chore sweep landed: **#921** (glossary: provenance / SAST chain / DMBOK), **#923** (`mariadb` pip-audit ignore + follow-up #926), **#920** (glossary TAMPERED/TINTED), **#924/#925** (ADR-0070 + primers reorg), **#927** (re-signed INVENTORY.sig), **#928** (TESTING table), **#930** (man5 keys), **#933/#934/#936** (pt-BR mirrors, 1.7.3 highlights, QUICKSTART), **#938** (audience-guide), **#939** (README tagline), plus Dependabot **#911** (codeql-action).

**Private map (full detail):** `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** / **`./scripts/operator-day-ritual.sh -Mode Morning`** (or `.ps1`). Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · confirm `ci.yml` green on `main` (`139f754c`).
2. **Open PRs:** `gh pr list --state open` — **three** Dependabot (#915, #914, #912); **not** part of the three fronts, **held** until the Maestro handoff (don't perturb the bench env).
3. **Private stack:** if `docs/private/` changed overnight, `./scripts/private-git-sync.sh -Push` (or `.ps1`).

**Continuous queue:** [CARRYOVER.md](CARRYOVER.md)

---

## Priority — the three fronts (B is today's headline)

### B — Maestro: real end-to-end round, then handoff to Cursor (headline)

- Yesterday: Claude (read-only auditor) ran **Maestro micro-fixes** — several landed; the bench harness is the closest it has been to a true run.
- **Today's target:** one **real e2e round** ("pra valer") — first true completão pass after the recent repo + Maestro adjustments, notably the new **Capo handler** for **JWT enforcement validation** (commercial defense). Completão has **not** been run for real yet.
- Roles: the auditor **interprets/directs** the analysis (completão is **read-only** for Claude); **Cursor executes the `pwsh`** when the handoff lands.
- **Handoff to Cursor:** once the e2e round is healthy, Claude hands off the multi-host completão under Maestro to Cursor. Cursor should be ready to: run `lab-completao-orchestrate.ps1 -Privileged`, read logs under `docs/private/homelab/reports/`, and feed front C.
- Capture Lessons Learned (timeouts, latency, FP/FN vs synthetic truth, confidence on real paths) for the official archive (`lab-lessons`).

### A — Vault sync (isolated warm-up, off the gate)

- Self-hosted **CouchDB** on a lab host with ample free disk (the P2P LiveSync path is dead).
- **Prereq:** `podman logout docker.io` before bringing the container up.
- CouchDB up → Self-hosted LiveSync plugin on the laptop client and the phone → also closes the standing **vault → phone** task.
- Independent of the gate — good as a warm-up while the Maestro round runs. Specifics (hostnames, paths, phone) → **private map**.

### C — Release gate #406 (fed by B)

Honest framing: **ready to attempt**, knowing the gate is **fail-closed** and exists to tell us what is missing. Known blockers to confirm before/during:

- **G1 (only known content blocker):** `py7zr` + `nfs-utils` on the Void lab host.
- `boar_fast_filter` compiled on all four lab hosts.
- `$HOME=root` bug in the ensure scripts.
- **Golden rule:** the **first gate run is WITHOUT a license** — fail-closed **must fail** (= test #1). Never require `dev.lic` first; the license only enters on the **second** round. Three-axis matrix (enforcement / per-tier permissions / FP-FN).
- Only after the gate passes: bump `1.7.4-rc → 1.7.4`, CHANGELOG, Docker Hub, GitHub Release.

**Sequence:** A (quick, isolated) → B (e2e round → handoff) → C (gate, fed by B).

---

## Carryover — secondary (not the three fronts)

- [ ] **Dependabot queue (`deps` slice, HELD until Maestro handoff):** **#915** (`hatchling >=1.30.1`), **#914** (`uv-minor-patch` group ×12), **#912** (`SonarSource/sonarqube-scan-action` 8.1→8.2 — **blocked**: `gh` token needs `workflow` scope, or merge via web UI). Apply locally + validate per `.cursor/skills/dependabot-recommendations/SKILL.md` — **do not blind-merge** (the `rpds-py` CalVer breakage on 2026-06-16 is the cautionary tale; `rpds-py<2026` cap + `dependabot.yml` ignore now guard it). Not blocking the gate, and intentionally **deferred** so the bench env stays stable.
- [ ] **`mariadb` PYSEC-2026-217 ignore review (#926):** revisit the `pip-audit` ignore added in #923 once a fixed `mariadb` release ships.
- [ ] **#685 follow-up:** when `docs/primers/FORENSICS_AND_EVIDENCE_PRIMER.md` ships, add its link to the new README "forensic-grade" tagline (deferred per #693 AC).
- [ ] Rolling items: [CARRYOVER.md](CARRYOVER.md) (LAB-OP #756 lab-host disk, Maestro DB matrix evidence, etc.).

---

## End of day (2026-06-18)

- `eod-sync` + `private-stack-sync` if the private stack changed.
- Record Maestro/gate Lessons Learned (`lab-lessons`) if a completão round closed — **especially** if the first real e2e round ran today.
- Tomorrow's checklist path: `OPERATOR_TODAY_MODE_2026-06-19.md` (create at next `eod-sync` if missing).

---

## Quick references

- Private map (full detail): `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`
- Session keywords: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `carryover-sweep`, `eod-sync`, `completao`, `lab-lessons`, `deps`)
- Completão runbook: `docs/ops/LAB_COMPLETAO_RUNBOOK.md` · workflow rule: `.cursor/rules/lab-completao-workflow.mdc`
- Release gate: issue **#406**; release order: `.cursor/rules/release-publish-sequencing.mdc`
- Dependabot ritual: `.cursor/skills/dependabot-recommendations/SKILL.md`

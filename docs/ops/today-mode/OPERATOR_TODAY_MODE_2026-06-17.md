# Operator today-mode — 2026-06-17 (three fronts: Vault → Maestro → release gate)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-06-17.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-17.pt_BR.md)

**Note:** Agreed plan with the operator + the read-only auditor (Claude Code) + Cursor, each on its own rhythm and sidequests. Three fronts, two of them chained: **A (Vault, isolated warm-up) → B (Maestro smoke → completão) → C (release gate #406, fed by B)**. Full operational detail (lab hostnames, Vault/iPhone specifics) lives in the **private map**, not in this tracked file.

**`main` anchor:** `69549bd9` — **#917** (SSHSIG attestation + `allowed_signers` trust anchor, ADR-0056) merged. Yesterday also landed **#913** (#910 issuer encrypted-key passphrase) and **#909** (ADR-0069 cap `rpds-py<2026`).

**Private map (full detail):** `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** / **`./scripts/operator-day-ritual.sh -Mode Morning`** (or `.ps1`). Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · confirm `ci.yml` green on `main` (`69549bd9`).
2. **Open PRs:** `gh pr list --state open` — four Dependabot (see carryover below); **not** part of the three fronts.
3. **Private stack:** if `docs/private/` changed overnight, `./scripts/private-git-sync.sh -Push` (or `.ps1`).

**Continuous queue:** [CARRYOVER.md](CARRYOVER.md)

---

## Priority — the three fronts (agreed)

### A — Vault sync (isolated warm-up, off the gate)

- The abandoned P2P LiveSync path is dead; pivot to **self-hosted CouchDB** on a lab host with ample free disk.
- **Prereq:** `podman logout docker.io` before bringing the container up.
- CouchDB up → Self-hosted LiveSync plugin on the laptop client and the phone → this also closes the standing **vault → phone** task.
- Independent of the gate — good as a morning warm-up, with the read-only auditor.
- Operational specifics (hostnames, paths, phone) → **private map**.

### B — Maestro benchmarking (smoke → real run → completão handoff)

- Ramp: **micro-bench smoke** (fast sanity, per host, increasingly complete/complex scenarios) → **one real run** (operator interprets/directs the analysis — completão is **read-only** for the auditor; Cursor executes the `pwsh`) → **handoff** to multi-host completão under Maestro.
- **First real completão after** the recent repo + Maestro adjustments — notably the new **Capo handler** for **JWT enforcement validation** (commercial defense). Completão has **not** been run for real yet; this is the first true pass.
- Capture Lessons Learned (timeouts, latency, FP/FN vs synthetic truth, confidence on real paths) for the official archive.

### C — Release gate #406 ("finally?")

Honest framing: **ready to attempt**, knowing the gate is **fail-closed** and exists to tell us what is missing. Known blockers to confirm before/during:

- **G1 (only known content blocker):** `py7zr` + `nfs-utils` on the Void lab host.
- `boar_fast_filter` compiled on all four lab hosts.
- `$HOME=root` bug in the ensure scripts.
- **Golden rule:** the **first gate run is WITHOUT a license** — fail-closed **must fail** (= test #1). Never require `dev.lic` first; the license only enters on the **second** round. Three-axis matrix (enforcement / per-tier permissions / FP-FN).
- Only after the gate passes: bump `1.7.4-rc → 1.7.4`, CHANGELOG, Docker Hub, GitHub Release.

**Sequence:** A (quick, isolated) → B (smoke → completão) → C (gate, fed by B).

---

## Carryover — secondary (not the three fronts)

- [ ] **Dependabot queue (`deps` slice):** **#915** (`hatchling >=1.30.1`), **#914** (`uv-minor-patch` group ×12), **#912** (`SonarSource/sonarqube-scan-action` 8.1.0→8.2.0), **#911** (`github/codeql-action` 4.36.0→4.36.2). Apply locally + validate per `.cursor/skills/dependabot-recommendations/SKILL.md` — **do not blind-merge** (the `rpds-py` CalVer breakage on 2026-06-16 is the cautionary tale; the `rpds-py<2026` cap + `dependabot.yml` ignore now guard it). Not blocking the gate.
- [ ] Rolling items: [CARRYOVER.md](CARRYOVER.md) (LAB-OP #756 lab-host disk, Maestro DB matrix evidence, etc.).

---

## End of day (2026-06-17)

- `eod-sync` + `private-stack-sync` if the private stack changed.
- Record Maestro/gate Lessons Learned (`lab-lessons`) if a completão round closed.
- Tomorrow's checklist path: `OPERATOR_TODAY_MODE_2026-06-18.md` (create at next `eod-sync` if missing).

---

## Quick references

- Private map (full detail): `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`
- Session keywords: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `carryover-sweep`, `eod-sync`, `completao`, `lab-lessons`, `deps`)
- Completão runbook: `docs/ops/LAB_COMPLETAO_RUNBOOK.md` · workflow rule: `.cursor/rules/lab-completao-workflow.mdc`
- Release gate: issue **#406**; release order: `.cursor/rules/release-publish-sequencing.mdc`
- Dependabot ritual: `.cursor/skills/dependabot-recommendations/SKILL.md`

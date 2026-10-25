# Pipeline Vitals — 2026-04-27

> **Audience:** SRE agents (Cursor Web automation), maintainer.
> **Style:** Julia-Evans-flavoured. Plain language, concrete evidence, no
> hand-waving. If a number is here, it came from a `gh` or `git` command in
> the same session that produced this file.
> **Trigger:** Slack `[OPERATIONAL PROTOCOL: PIPELINE HEALTH-CHECK & DIAGNOSTIC]`
> at `1777310177.655909`.

## :traffic_light: Status: YELLOW

CI is green everywhere. The pipeline is **not** stuck. The pipeline is
*productive in the wrong way*: parallel SRE agents are doing real, well-tested
work that **overlaps on the same files**, and merges are stalled because
nothing wants to be the one that triggers the rebase chain.

## :turtle: Bottleneck — work duplication, not throughput

In the last 90 minutes (16:10 → 17:13 UTC) **11 draft PRs** were opened by
SRE agents. Every single one is `MERGEABLE` and every single one shows
`SUCCESS` on all 9 status checks.

```text
#242 17:13 docs(ops): SRE Dependency Guardian verdict ledger
#241 17:04 docs(ops): SRE PR Risk Assessor audit + reviewer assignment
#240 17:02 fix(security): protocol-relative open-redirect in WebAuthn
#239 16:49 feat(workflow,docs): dependabot-resync helper + Guardian audit
#238 16:31 fix(security): drop bogus T-SQL OPTION (MAX_EXECUTION_TIME)
#237 16:30 docs(inspirations): bilingual pt-BR doctrine manifestos
#236 16:27 feat(report)+refactor(detector): Slices 2-4 doctrine cycle
#235 16:25 perf(detector): Slice 2 single-pass fused regex
#234 16:20 docs(ops): SRE security audit of open PRs
#233 16:13 fix(ci): SLACK_WEBHOOK_URL guard out of job-level if:
#232 16:10 feat(ops,report,detector,plans): doctrine Slices 2-4
```

All green. None merged. Velocity = 0 PRs/hour.

## :octagonal_sign: Specific blockers (the actual collisions)

I diffed the file lists with `gh pr view --json files`. Two clusters will
conflict the moment one of them merges.

### Cluster A — “Doctrine Slices 2-4” triple-overlap

| File | #232 | #235 | #236 |
| ---- | :--: | :--: | :--: |
| `cli/reporter.py` | x |   | x |
| `pro/engine.py` |   | x | x |
| `pro/worker_logic.py` |   | x | x |
| `docs/plans/BENCHMARK_EVOLUTION.md` | x |   | x |
| `docs/plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md` | x |   | x |

Three different agents worked the same slice from three different angles.
Whoever merges first wins; the other two need a manual rebase or get closed
as superseded.

### Cluster B — `docs/ops/sre_audits/README.md` quadruple-touch

PRs **#234, #239, #241, #242** all create the same `README.md` for a folder
that **does not yet exist on `main`**. Same race, four contestants.

> Sidebar — “No-Racing rule” / `ci-fail-*` lock files / 30-min TTL
> referenced in the operator prompt: I `grep`-ed the repo and there are
> **no `ci-fail-*` files**, **no `.cursor-locks/` directory**, and no code
> path that creates or honours such a lock. The rule exists in operator
> prompts but is **not yet implemented**. That gap *is* the bottleneck.

### Cluster C — Dependabot backlog

5 PRs (#221, #222, #223, #224, #226) open since 2026-04-24/26, all
`MERGEABLE`. Not in the same race as the SRE drafts; just patiently waiting
for `chore(deps):` triage.

## :pill: Remedy applied here

This PR ships **two read-only artifacts** under `docs/ops/sre_audits/` with
**collision-free filenames** (different from `README.md` and from every
`*_2026-04-27*` file already in flight):

1. `PIPELINE_VITALS_2026-04-27.md` — this file.
2. `AGENT_WORK_CLAIMS.md` — a tiny ledger so the *next* SRE agent can read,
   in 30 seconds, what scope is already claimed before it starts editing
   `cli/reporter.py` for the fourth time.

No source code changed. No database touched (defensive architecture
respected per `DEFENSIVE_SCANNING_MANIFESTO.md`). Zero regression risk.

If a future agent wants to harden this into a real lock file with TTL, the
ledger format already names the date and the file scope, so a
`scripts/agent-claim.ps1` helper can read+enforce it.

## :gear: Immediate next step (for the maintainer or the next agent)

1. **Pick one PR per cluster to land first.** My recommendation, smallest
   blast radius first:
   - Cluster A: merge **#235** (it has its own evidence file at
     `tests/benchmarks/official_benchmark_200k.json` and zero overlap with
     the docs-only side of #232/#236), then rebase #232 and #236 on top.
   - Cluster B: merge **#234** first (smallest diff: 254/0, 2 files), then
     the other three rebase against the now-existing `README.md`.
2. **Triage Dependabot** with the helper introduced by #239 (once #239
   lands) or fall back to manual `gh pr merge` per
   `.cursor/skills/dependabot-recommendations/SKILL.md`.
3. **Add the ledger as the new pre-flight step** for the SRE protocol prompt
   in Slack: instruct agents to *read* `AGENT_WORK_CLAIMS.md` first.

## How I worked this out (so the next agent can verify)

```bash
git fetch origin
gh pr list --state open --limit 50 --json number,title,isDraft,mergeable,createdAt,headRefName
# then per PR:
gh pr view <N> --json files,additions,deletions,statusCheckRollup
# cross-tabulate file paths to spot overlaps.
```

That is it. No magic, no log archeology — just `gh` + a small Python
one-liner to count check states. Reproducible by anyone with `gh` and read
access to the repo.

## References

- `docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md` — respected (no DB
  reads, no scans).
- `docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md` — the ledger *is* the
  fallback for the missing real lock primitive.
- `.cursor/rules/git-pr-sync-before-advice.mdc` — `git fetch` was run before
  forming any merge advice above.

# Engineering bench discipline (Data Boar doctrine)

> **Seeds:** [Adam Savage / Tested.com](https://www.tested.com/) ·
> [Julia Evans (b0rk)](https://jvns.ca/) ·
> [Aviões e Músicas (Lito Sousa)](https://www.youtube.com/@avioesemusicas)
>
> *"First-order retrievability. Checklist culture. The complex made intuitive."*

This is a **doctrinal manifesto** about how the Data Boar workshop is laid out
— the bench, the scripts, the logs — so that the next person (or the next
agent) can sit down and ship safely.

---

## 1. Why bench ergonomics matter

When the operator opens Cursor in the morning, three things should be true
within minutes:

1. The right tool for the job is **at hand** — not buried under three folders.
2. There is a **checklist** for any safety-critical action (release, lab
   completão, destructive ops on the canonical clone).
3. The output is **narrated**, not just emitted: a human can read the log and
   reconstruct what happened, in what order, and why.

The seeds:

- **Adam Savage** — *first-order retrievability*: the tool you use most lives
  closest to your hand. Workshops collapse when this principle slips.
- **Julia Evans** — *make the complex intuitive*. SQL plans, Linux
  permissions, networking — when explained as small zines with diagrams, they
  stop being arcane.
- **Aviões e Músicas** — checklist culture transplanted from aviation. Every
  long-haul flight starts with a flow even the captain has run a thousand
  times. Same for releases and lab smokes.

---

## 2. The bench (where Data Boar tools live)

Data Boar's "bench" is the `scripts/` folder plus the documented runbooks. The
**first-order retrievability** principle is enforced via two hubs:

| Need | First-hand tool |
| ---- | --------------- |
| Full local gate | `.\scripts\check-all.ps1` (or `./scripts/check-all.sh`) |
| Lint only (docs/templates) | `.\scripts\lint-only.ps1` |
| Targeted tests | `.\scripts\quick-test.ps1 -Path tests/test_foo.py` |
| Commit + describe + PR | `.\scripts\commit-or-pr.ps1` |
| Docker lab build | `.\scripts\docker-lab-build.ps1` |
| Lab orchestration smoke | `.\scripts\lab-completao-orchestrate.ps1 -Privileged` |
| Benchmark A/B | `.\scripts\benchmark-ab.ps1` |
| Filename search (Windows) | `.\scripts\es-find.ps1` |

Indexes:

- [`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`](../TOKEN_AWARE_SCRIPTS_HUB.md) — full
  table.
- [`.cursor/rules/check-all-gate.mdc`](../../../.cursor/rules/check-all-gate.mdc)
  — daily command table.
- [`.cursor/rules/repo-scripts-wrapper-ritual.mdc`](../../../.cursor/rules/repo-scripts-wrapper-ritual.mdc)
  — *use the wrapper before reinventing the shell sequence*.

**Doctrine:** if you find yourself writing a shell incantation longer than
three lines, **stop** and check whether a wrapper already encodes the flow.
Reinventing it costs tokens, hides bugs, and reduces auditability.

---

## 3. Checklist culture (Aviões e Músicas)

Pilots run checklists not because they forgot how to fly, but because the
**workload spike** at landing is when human memory fails. Software has the
same shape: the moment of cutting a release, merging a multi-day branch,
running a privileged orchestration step.

The repo-side equivalents — these are not optional:

- **Pre-merge checklist:** `git fetch` → `git status -sb` →
  `.\scripts\check-all.ps1` → review diff → merge.
- **Pre-release checklist:**
  [`.cursor/rules/release-publish-sequencing.mdc`](../../../.cursor/rules/release-publish-sequencing.mdc)
  — tag *before* `-beta` lands on `main`, smoke Docker, paste Hub copy.
- **Pre-completão checklist:**
  [`docs/ops/LAB_COMPLETAO_RUNBOOK.md`](../LAB_COMPLETAO_RUNBOOK.md) — manifest
  freshness, `sudo -n`, blast radius, primary-workstation protection.

A checklist that has been silently skipped is the same as no checklist. Tests
and rules enforce these flows so the checklist runs even when the operator is
tired.

---

## 4. Narrated logs (Julia Evans, b0rk style)

Long log dumps are not narration. **Narration** is when a stranger can read the
log a year later and reconstruct the story. Data Boar logs aim for this bar:

- **Each step says what it is doing and why** (one short sentence above the
  command).
- **Each step prints what changed**, not just exit code.
- **Errors include the next step** ("retry with `-Verbose`", "see
  [`docs/ops/TROUBLESHOOTING.md`](../TROUBLESHOOTING.md)").
- **Time stamps** when the slice spans more than a few seconds.
- **Density without noise** — colors and symbols are signal, not decoration.

Counter-example (don't):

```text
INFO: starting
INFO: starting
INFO: done
ERROR: 1
```

Better (do):

```text
[1/4] benchmark legacy   v1.7.3   ...
       wall_time=18.7s   exit=0
[2/4] benchmark current  HEAD     ...
       wall_time=14.2s   exit=0
       Δ=-24% (significant only if cluster repeats — see BENCHMARK_EVOLUTION.md §3)
[3/4] manifest written   benchmark_runs/2026-04-27/times.txt
[4/4] artifact archive   benchmark_runs/2026-04-27/
```

Same information; the second one **explains itself**. This bar applies to
`completão`, `data-boar-report`, and CLI output. See also the diagnostic
posture in
[`INTERNAL_DIAGNOSTIC_AESTHETICS.md`](INTERNAL_DIAGNOSTIC_AESTHETICS.md).

---

## 5. Do / don't (review checklist)

### Do

- Add or update a wrapper when an ad-hoc sequence shows up twice.
- Treat `check-all` as the safety gate. Green or fix. Don't ship "almost
  green".
- Write log lines as if a stranger will read them in six months — because
  they will.

### Don't

- Don't paste 30-line shell sequences into chat as if they were a script.
  Promote them to `scripts/` so they are testable.
- Don't make wrappers chatty. Verbose mode is opt-in
  ([`INTERNAL_DIAGNOSTIC_AESTHETICS.md`](INTERNAL_DIAGNOSTIC_AESTHETICS.md));
  default mode is short and dense.
- Don't mix unrelated subjects in one PR. The bench stays clean by enforcing
  one slice per branch
  ([`.cursor/rules/execution-priority-and-pr-batching.mdc`](../../../.cursor/rules/execution-priority-and-pr-batching.mdc)).

---

## 6. Where this is reinforced

- [`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`](../TOKEN_AWARE_SCRIPTS_HUB.md) — bench layout.
- [`docs/ops/COMMIT_AND_PR.md`](../COMMIT_AND_PR.md) — PR checklist.
- [`docs/ops/LAB_COMPLETAO_RUNBOOK.md`](../LAB_COMPLETAO_RUNBOOK.md) — flight checklist.
- [`docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md`](INTERNAL_DIAGNOSTIC_AESTHETICS.md) — log voice.
- [`PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md`](../../plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md) — Slices 2–3 wire this manifesto into code comments and the executive report.

The bench stays usable when **everyone** treats it like the next person's
problem. That is the discipline.

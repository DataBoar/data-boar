# LAB Lessons Learned — session snapshot 2026-04-27

**Archive note:** Immutable snapshot for the SRE-protocol session that clarified
how the **2026-04-25** A/B benchmark figure must be read in manifests and
executive copy. The frozen 2026-04-25 snapshot at
[`LAB_LESSONS_LEARNED_2026_04_25.md`](LAB_LESSONS_LEARNED_2026_04_25.md) stays
unchanged, per the archive contract; this file is the **erratum / reading
guide**, not a rewrite.

Date: 2026-04-27 (UTC session)

## Trigger (operator handoff)

Slack handoff from the operator to the agent automation:

> O benchmark A/B de 200k confirmou que o perfil Pro é **0.574x mais lento**
> que o OpenCore. Considere isso no refinamento dos manifestos.

## What changed in this snapshot

- **No new measurement.** The artifact
  [`tests/benchmarks/official_benchmark_200k.json`](../../../tests/benchmarks/official_benchmark_200k.json)
  is unchanged from 2026-04-25 (`opencore_seconds=0.252242`,
  `pro_seconds=0.439419`, `speedup_vs_opencore=0.574`,
  `opencore_hits=100000`, `pro_hits=100000`).
- **Reading guide added** to the hub
  ([`../LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md)) and to the
  post-mortem
  ([`../SPRINT_GREAT_LEAP_POSTMORTEM.md`](../SPRINT_GREAT_LEAP_POSTMORTEM.md) /
  [pt-BR](../SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md)) so manifests do not flip
  the sign by accident.
- **Regression guard added** at
  [`tests/test_official_benchmark_200k_evidence.py`](../../../tests/test_official_benchmark_200k_evidence.py)
  pinning direction (Pro slower), JSON arithmetic
  (`opencore_seconds / pro_seconds ≈ recorded speedup`), and findings parity
  (`opencore_hits == pro_hits`).

## Direction vs ratio (do not double-invert)

| Statement                                            | What it means in this profile                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------- |
| `speedup_vs_opencore = 0.574` (JSON)                 | Pro is **0.574x as fast as** OpenCore (ratio = `t_open / t_pro`).   |
| "0.574x mais lento" (operator chat phrasing)         | Same direction (Pro slower); same numeric anchor as the JSON.       |
| Pro wall-clock                                       | Roughly `1 / 0.574 ≈ 1.74x` the OpenCore wall-clock here.            |

If a future profile (larger chunks, heavier downstream stage) flips this
direction, regenerate the JSON via
[`tests/benchmarks/run_official_bench.py`](../../../tests/benchmarks/run_official_bench.py)
**and** update the hub / post-mortem prose in the same commit so they stop
disagreeing.

## Defensive posture (DEFENSIVE_SCANNING_MANIFESTO spirit)

- The added test only **reads** a JSON artifact — no SQLite connection,
  no scan, no DB lock — and is therefore safe to run inside
  [`scripts/check-all.sh`](../../../scripts/check-all.sh) /
  [`scripts/check-all.ps1`](../../../scripts/check-all.ps1) on any host,
  including ones running active scans.

## Resilience posture (THE_ART_OF_THE_FALLBACK spirit)

- The guard does **not** force a regeneration; if the artifact disappears it
  raises an explicit message pointing at the harness, so the operator can
  decide whether to rerun or restore from `git`.
- Findings parity (`100,000 == 100,000`) is asserted before performance
  ratios, because a defensive scanner must protect detection coverage **even
  if the Pro path becomes faster** in a future profile.

## Follow-ups → plans (tracked)

| Topic                           | Bridge                                                                                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Pro+ benchmark / executive copy | [`../SPRINT_GREAT_LEAP_POSTMORTEM.md`](../SPRINT_GREAT_LEAP_POSTMORTEM.md) verified-vs-aspirational table; production-like profile before uplift narrative. |
| Regression coverage             | [`tests/test_official_benchmark_200k_evidence.py`](../../../tests/test_official_benchmark_200k_evidence.py) pins direction + parity until a new artifact lands. |

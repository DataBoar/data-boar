# ADR 0083 — Rust regex stage: accept form B (findings superset)

- **Date (UTC):** 2026-07-31
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-07-31 — Proposed (born Proposed per ADR-0045 / Phase 1 T1; records operator form-B decision on bus [#1413](https://github.com/DataBoar/data-boar/issues/1413); promote to Accepted when operator accepts)
- 2026-07-31 — Clarified engine = cached `regex::Regex` loop (not `RegexSet`); mother [#1414](https://github.com/DataBoar/data-boar/issues/1414); GIL release via `py.detach` + thread-scaling acceptance

## Context

The CLI / detector path will accelerate the **regex matching stage** in Rust
using a **loop of `regex::Regex` values compiled and cached per detector
instance** in `boar_fast_filter` — **not** `RegexSet` (spike measured **5.7×
slower** than the loop; see [ADR 0078](ADR-0078-multi-pattern-regex-benchmark-gate-regexset-before-vectorscan.md)
amendment and [PLAN_RUST_REGEX_STAGE.md](../plans/PLAN_RUST_REGEX_STAGE.md) §2.0).
The stage uses the **same** pattern list as the live `SensitivityDetector`
(built-ins + YAML overrides / plugins). This is **not** a prefilter that skips
rows before ML.

### Primary justification — GIL release and thread scaling

Speed per operation is secondary. The **main** reason for this work is that the
current `filter_batch` path **does not release the GIL** (PyO3 signature holds
Python tokens through the call). Under a **build with the GIL**, releasing the
GIL around the match loop enables real multi-thread scale; Python cannot.

Measured 2026-07-31 (probe; build **with GIL**):

| Threads | Python wall | Python scale vs 1t | Rust wall (GIL released) | Rust scale vs 1t |
| --- | --- | --- | --- | --- |
| 1 | 1700.4 ms | 1.00× | 806.2 ms | 1.00× |
| 8 | 2174.2 ms | **0.78×** (worse) | 247.5 ms | **3.26×** |

End-to-end advantage of Rust with threads vs Python in that setup: **~6.9×**.
Without GIL release, a future regression that **re-acquires** the GIL would keep
finding-parity tests green while destroying the scaling story — so acceptance
**must** include a thread-scaling test on a GIL build.

**PyO3 API:** the exposed match method must release the GIL with **`py.detach`**
(in PyO3 **0.29**, `allow_threads` was renamed to `detach`).

**Compile cost (cache is a requirement, not an optimization):** compiling **284**
patterns measured **108.9 ms** in Rust vs **12.4 ms** in Python. Recompiling per
batch would erase match-path gains — cache **once per detector instance** (reload
on config change only).

### ReDoS / accept form B

Python’s `re` engine uses backtracking. The Rust crate `regex` uses a finite
automaton with **guaranteed linear time** — ReDoS does not apply there.

Measured 2026-07-31 on `(a+)+$` against 40× `a` + `!`:

| Engine | Result |
| --- | --- |
| Rust `regex` | no match in ~82 µs |
| Python `re` | hung (>5 s, aborted) |

Today’s ReDoS guard (**#829**) in `_load_regex_overrides` **skips** nested-quantifier
patterns on the Python path (warn + drop). That reason does **not** apply to the
Rust engine: the same pattern can run safely there.

Two accept forms were evaluated:

| Form | Invariant | Coverage |
| --- | --- | --- |
| **A · strict parity** | `findings(Rust) == findings(Python)` | Nested-quantifier patterns stay discarded on both engines |
| **B · expanded coverage** | `findings(Rust) ⊇ findings(Python)` — never `⊂` | Patterns discarded by #829 may run **only** on Rust |

Product posture ([COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) —
*Deterministic detection vs generative LLM hype*): findings must stay
**repeatable**. Under B, the same YAML on two machines (extension present vs
absent) may differ — that must be **reconcilable via the scan manifest**, not
look like non-determinism.

Open-core posture: Community must never produce a **wrong** finding. It may
**refuse** to execute a pattern its engine cannot run safely, and **warn**.
Form B does **not** add a free-tier limitation — #829 already exists; B only
removes a limitation on the paid/accelerated path. Difference is **language
mechanics** (backtracking vs linear automaton), not policy fragility.

## Decision

1. **Accept form B:** `findings(Rust) ⊇ findings(Python)`. **Never** `⊂`.
   No finding Python would produce may disappear when Rust acceleration is on.
2. **Extra findings must be explainable:** each surplus hit is attributable to a
   specific pattern that Python discarded (#829) or to a **documented** mechanical
   difference. Bare “Rust found more” **fails acceptance**.
3. **#1412 is a merge prerequisite of #1414** (Rust regex-stage mother; call-site
   work remains [#1411](https://github.com/DataBoar/data-boar/issues/1411)): the
   scan manifest (and `GET /status` / evidence surfaces) must record at least:
   engine + version; count accelerated; count in Python fallback with **per-pattern
   reason**; **which patterns ran only on Rust**; whether the extension was absent
   and why. Repeatability is **conditioned on the recorded engine**.
4. **Community / no-extension path:** identical to today’s Python behaviour
   (including #829 refuse + warn). Never invent wrong detections on free.
5. **Class A/B Rust-compatibility checks** extend existing `_load_regex_overrides`
   next to the ReDoS guard — same warning channel; no parallel validation stack.
6. **Zero hardcoded customer patterns in `lib.rs`** for the new stage — Rust is
   the engine; YAML / detector instance is the catalogue (open domain:
   privacy, SISCOMEX, SUSEP, agro, farma, DLP, …).
7. **Engine shape:** loop of cached `regex::Regex` per detector instance — **not**
   `RegexSet`. Match path releases the GIL via **`py.detach`**. Acceptance includes
   a **thread-scaling** test on a **GIL** build (parity alone is insufficient).
8. **Compile once per instance:** pattern compile cost (≈109 ms / 284 patterns in
   Rust) makes per-batch recompile unacceptable.

## Consequences

- **Positive:** Paid / accelerated path can safely cover patterns that today
  vanish after a stderr warning; bias stays toward human review over silent FN.
- **Positive:** Manifest makes cross-machine differences auditable (DPO evidence).
- **Positive:** GIL release unlocks multi-thread scale that Python cannot match
  under the GIL (~3.26× at 8 threads vs ~0.78× for Python in the probe).
- **Negative:** Cross-host reports for the same YAML may differ when only one host
  has `boar_fast_filter` — operators must compare manifests, not assume byte-identical
  Excel across engines.
- **Watch:** Differential CI must assert the **superset** invariant and require
  attribution for extras; never weaken #829 on the Python path to “fake” parity.
- **Watch:** Thread-scaling gate must fail if a change reintroduces GIL retention
  while leaving finding parity green.

## References

- Plan: [PLAN_RUST_REGEX_STAGE.md](../plans/PLAN_RUST_REGEX_STAGE.md)
- Mother (spec): [#1414](https://github.com/DataBoar/data-boar/issues/1414)
- Bus: [#1413](https://github.com/DataBoar/data-boar/issues/1413)
- Correlatas: [#1411](https://github.com/DataBoar/data-boar/issues/1411) (call site), [#1412](https://github.com/DataBoar/data-boar/issues/1412) (manifest — merge prerequisite)
- Related: [ADR 0078](ADR-0078-multi-pattern-regex-benchmark-gate-regexset-before-vectorscan.md) (RegexSet spike failed; cached Regex loop next), ReDoS guard #829, `tests/test_redos_guard.py`
- Product claim: [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) (*Deterministic detection vs generative LLM hype*)

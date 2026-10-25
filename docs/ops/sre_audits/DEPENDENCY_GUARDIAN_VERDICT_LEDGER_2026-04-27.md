# Dependency Guardian — verdict ledger (2026-04-27)

> **Slack-triggered SRE Dependency Guardian V3 pass.** This is the *decision*
> ledger for the five Dependabot PRs open against `main` on 2026-04-27. It
> complements (does not duplicate) the **dependabot-resync helper** shipped on
> [`#239`](https://github.com/FabioLeitao/data-boar/pull/239); that PR ships the
> *mechanical* fix for the systemic CI red, this one books the *per-package
> verdict* with full caller maps so future passes have a dated reference.
>
> Form is inspired by the LMDE bug-fix ledger style — concrete evidence, one
> RCA per row, no rhetoric.

---

## TL;DR (one screen)

| PR    | Package                       | From      | To        | Severity | Callers (production-critical) | CI       | Verdict                                      |
| :---- | :---------------------------- | :-------- | :-------- | :------- | :---------------------------- | :------- | :------------------------------------------- |
| #226  | `pyo3` (Cargo)                | 0.23.5    | 0.24.1    | Medium   | 1 (`rust/boar_fast_filter/src/lib.rs`) | green    | **MERGE** — high confidence, non-breaking    |
| #224  | `cryptography`                | 46.0.7    | 47.0.0    | Medium   | 1 (`core/licensing/verify.py`) | red\*    | **MANUAL REVIEW** — Ed25519 critical path    |
| #222  | `chardet`                     | 5.2.0     | 7.4.3     | Low      | 0 direct (transitive only)    | red\*    | **MANUAL REVIEW** — major-major jump         |
| #223  | `tzdata`                      | 2025.3    | 2026.2    | Low      | 0 (data-only)                 | red\*    | **RESYNC + MERGE** — zero impact path        |
| #221  | `pip-minor-patch` group (×35) | mixed     | mixed     | Low–Med  | mixed (none touch DB drivers) | red\*    | **RESYNC, then split-and-merge per package** |

\* Red CI on #221 / #222 / #223 / #224 is the **same systemic finding**: the
Dependabot pip flow does not run `uv lock` + `uv export`, so
`tests/test_dependency_artifacts_sync.py` (the project's
single-source-of-truth guard between `pyproject.toml`, `uv.lock`, and
`requirements.txt`) goes red on every pip bump. Fix vehicle =
**[`scripts/dependabot-resync.{sh,ps1}`](../../../scripts/) on PR #239**.

---

## 0 — Confidence rule applied

Per the V3 protocol, **HIGH confidence** = (a) verified non-breaking changelog
*for the call paths we use*, (b) green CI, (c) zero touch on the DB connector
families called out by `DEFENSIVE_SCANNING_MANIFESTO.md` §3 (the **NOLOCK**
clause and friends).

Only **#226** (pyo3, Cargo) clears all three gates today. The other four are
**Manual Review** — not because the bumps are inherently dangerous, but
because the *baseline* (CI red on the systemic guard) erases the signal that
would let us call HIGH confidence. Fixing the baseline (PR #239 helper) is a
cheaper unlock than re-pinning per package.

This is the **audit-and-block** posture from
[ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-chain-pins.md) and the
SBOM/lockfile clauses in
[`SUPPLY_CHAIN_AND_TRUST_SIGNALS.md`](../inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md):
no rage-merge of a security bump on top of a misaligned lockfile.

---

## 1 — Per-PR verdict

### 1.1 — PR #226 · `pyo3 0.23.5 → 0.24.1` (Cargo) · **MERGE**

* **Manifest:** `rust/boar_fast_filter/Cargo.toml`, `Cargo.lock`.
* **Callers:**
  * `rust/boar_fast_filter/src/lib.rs:1-2` — `pyo3::exceptions::PyRuntimeError`,
    `pyo3::prelude::*`. Production-critical (the fast-filter extension module
    is on the hot path of the detector).
* **Changelog audit (0.23 → 0.24):** the upstream `RUSTSEC` advisory the bump
  closes is `PyString::from_object` UB on non-`str` inputs. We do **not** call
  that API — `lib.rs` uses `PyRuntimeError` and the prelude only. Defense-in-
  depth.
* **Breaking surface vs our usage:** none observed. The `extension-module`
  feature is unchanged; `PyO3 0.24` keeps the `prelude` and `exceptions`
  re-exports we rely on.
* **CI:** **all green** (Test 3.12, Test 3.13, Lint, Bandit, Semgrep,
  CodeQL, SonarQube, Dependency audit, SBOM, Analyze).
* **DB connector blast radius:** **zero** (Cargo path; no Python DB driver
  touched; cannot influence `WITH (NOLOCK)` or sampling).
* **Verdict:** **MERGE.** This is the cheapest win in the queue and the only
  one that actually clears the V3 HIGH-confidence bar today.

### 1.2 — PR #224 · `cryptography 46.0.7 → 47.0.0` · **MANUAL REVIEW**

* **Manifest:** `requirements.txt` only. Dependabot did not regen `uv.lock` /
  `pyproject.toml`, so the dependency-artifacts guard fails — see §2.
* **Callers (Python):**
  * **`core/licensing/verify.py`** — Ed25519 PEM load + EdDSA JWT verify via
    `pyjwt[crypto]`. **Production-critical** — gates every paid-tier feature.
  * `scripts/issue_dev_license_jwt.py` — Tooling/CLI (issuer for dev
    licenses). Same primitives, lower blast radius.
  * `tests/test_licensing.py`, `tests/test_api_assessment_poc.py` — Tests.
* **Changelog audit (46 → 47):** major-version jump on a security-critical
  library. The 47.x line is dropping legacy bindings on the OpenSSL side and
  tightening Ed25519 paths. Our usage is `serialization.load_pem_public_key`
  + `default_backend()` + EdDSA via PyJWT — **all three** are surfaces 47.x
  intentionally re-touches.
* **DB connector blast radius:** **none direct.** `cryptography` is a
  transitive dep of `oracledb`/`snowflake-connector-python`/`mssql` driver
  TLS certificate chains, but our DB code does not import `cryptography` directly, so the
  `WITH (NOLOCK)` and sampling logic remain untouched.
* **Verdict:** **MANUAL REVIEW.** Ed25519 license verification is exactly the
  contract NASA SEL §1 calls "test what you fly". Required before merge:
  1. Apply `dependabot-resync.sh` on the PR branch (PR #239).
  2. Re-run `tests/test_licensing.py` *and* `tests/test_api_assessment_poc.py`
     locally with the bumped wheel — both currently exercise PEM load + JWT
     decode.
  3. If green, merge. If red, **revert and STOP** — do not bypass.

### 1.3 — PR #222 · `chardet 5.2.0 → 7.4.3` · **MANUAL REVIEW**

* **Manifest:** `requirements.txt`.
* **Callers (Python, direct):** **none in tracked code** (`rg "(from|import)\s+chardet" --type py` → 0 matches at HEAD). Used transitively by `requests` /
  `beautifulsoup4` and inside the encoding fallback ladder described in
  [`THE_ART_OF_THE_FALLBACK.md`](../inspirations/THE_ART_OF_THE_FALLBACK.md)
  §2 (UTF-8 → declared codec → chardet sniffing → degraded "compliance text").
* **Changelog audit (5.x → 7.x):** two major releases. Detection thresholds
  changed; the legacy `chardet.detect()` API stayed but the confidence
  scoring on borderline Latin-1/CP1252 inputs is sharper (= different verdict
  on the same byte stream). Our fallback ladder *publishes* the detected
  encoding, so a different verdict is observable in operator reports.
* **DB connector blast radius:** **none.** Encoding sniffing runs on text
  payloads (CSV, TXT, exported logs), not on driver-bound result sets.
* **Verdict:** **MANUAL REVIEW.** Run a quick sample-vs-baseline pass on the
  fixture set under `tests/data/` (or a local cifras corpus per `AGENTS.md`)
  before merging — the operator-facing output of the fallback ladder is part
  of our trust signal, not a silent internal detail.

### 1.4 — PR #223 · `tzdata 2025.3 → 2026.2` · **RESYNC + MERGE**

* **Manifest:** `requirements.txt`.
* **Callers:** **none direct** (`rg "(from|import)\s+(zoneinfo|tzdata)" --type py` → 0 matches). Pure data package; consumed via `zoneinfo` only when the
  host OS lacks a tz database.
* **Changelog:** new IANA tz drops (Brazil, Mexico, Egypt). No code changes.
* **DB connector blast radius:** **zero.** Sampling and connector code do
  not consult `tzdata`; report timestamps use `datetime.now(timezone.utc)`.
* **Verdict:** **RESYNC + MERGE** — the only thing red is the systemic CI
  guard. Run `dependabot-resync.sh --commit` on the branch and merge.

### 1.5 — PR #221 · `pip-minor-patch` group (×35) · **RESYNC, then split-and-merge per package**

* **Manifest:** `requirements.txt` only (35 packages bumped).
* **Caller policy:** Group bumps lose per-package signal. Per
  `DEFENSIVE_SCANNING_MANIFESTO.md` §1.3 (no surprise side effects), we will
  not merge a 35-package group as one commit.
* **CI:** Lint + Test red on the dependency-artifacts guard (same systemic
  finding as §2). Bandit and CodeQL pass.
* **Verdict:** After resync turns CI green, split per-package: any bump that
  touches a DB driver, an HTTP/TLS lib (`urllib3`, `httpx`, `requests`), or
  the encoding/JSON stack gets its **own** PR with a 1-line caller note.
  Trivial bumps (typing-only, dev-tooling) can stay grouped.

---

## 2 — Systemic finding (Medium, unchanged from PR #234 audit)

**Symptom:** every Dependabot pip PR breaks
`tests/test_dependency_artifacts_sync.py`.

**Root cause (RCA):** Dependabot pip ecosystem only edits `requirements.txt`.
The repo enforces a **single source of truth** between `pyproject.toml`,
`uv.lock`, and `requirements.txt`. Without `uv lock` + `uv export`, the
guard sees drift and fails — even when the bump itself is harmless.

**Why this is a security finding (not just CI noise):** a maintainer under
time pressure (e.g. a real CVE) who admin-merges past the red CI lands an
inconsistent lockfile *and* a misaligned SBOM. That is exactly the
"fail-open" failure mode flagged in
[`SUPPLY_CHAIN_AND_TRUST_SIGNALS.md`](../inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md)
and is the inverse of the contract our doctrine signs with the customer
database — same principle, different surface (registry side instead of
driver side).

**Mitigation already in flight:** PR #239 ships
`scripts/dependabot-resync.{sh,ps1}`. It runs `uv lock` + `uv export` with
the exact flags the guard expects, and *fails loud* (per
[`THE_ART_OF_THE_FALLBACK.md`](../inspirations/THE_ART_OF_THE_FALLBACK.md)
§4 — diagnostic-on-fall) if either step regresses.

**Suggested follow-up (P1, deferred):** a `pull_request_target` workflow
that runs `dependabot-resync.sh --check` on every Dependabot pip PR and
posts the regen diff as a PR comment. Needs `pull-requests: write` plus a
strict `actor == 'dependabot[bot]'` check. Tracked in PR #239 prose.

---

## 3 — DB connector safety statement (mandatory protocol gate)

Per the Slack trigger ("ZERO impact on database locks; Defensive
Architecture; no regressions"):

* **Oracle / Snowflake / SQL Server connector code is untouched** by all
  five PRs (#221, #222, #223, #224, #226). None of them edit
  `connectors/`, `core/sampling*`, or any module that emits
  `WITH (NOLOCK)` / `SAMPLE` / equivalent dialect hints.
* **Sampling and isolation-level code paths are unchanged** — verified by
  inspecting the diffs (`requirements.txt` only on the four pip PRs;
  `Cargo.{toml,lock}` only on #226).
* **No DDL or temp-object risk** introduced by any bump.

This audit therefore satisfies `DEFENSIVE_SCANNING_MANIFESTO.md` §1
clauses 1–4 for every PR in scope.

---

## 4 — Recommended merge order (handed back to the maintainer)

1. **#226** (pyo3) — merge as-is, CI green, zero risk.
2. **#239** (dependabot-resync helper) — merge so the resync flow becomes
   one command and the systemic CI red stops being a regression risk.
3. **#223** (tzdata) — `dependabot-resync.sh --commit && git push` →
   merge.
4. **#221** (pip group) — resync, split per package, merge piece by piece.
5. **#222** (chardet) — resync + sample-vs-baseline encoding pass, then
   merge.
6. **#224** (cryptography) — resync + license-verify regression run, then
   merge. **STOP and flag if any licensing test goes red.**

---

## 5 — Doctrine references

* [`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`](../inspirations/DEFENSIVE_SCANNING_MANIFESTO.md)
  — "guest in the customer DB" contract, used as the §3 acceptance gate.
* [`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`](../inspirations/THE_ART_OF_THE_FALLBACK.md)
  — applied to `chardet` (§1.3) and to the helper's failure mode (§2).
* [`docs/ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md`](../inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md)
  — fail-open registry pattern; framing the systemic CI finding as a
  trust-signal issue, not noise.
* [`.cursor/skills/dependabot-recommendations/SKILL.md`](../../../.cursor/skills/dependabot-recommendations/SKILL.md)
  — operator workflow that PR #239 mechanizes.
* [ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-chain-pins.md) — the
  audit-and-block posture this ledger respects.

---

## 6 — Provenance

* Trigger: Slack automation **2026-04-27** (private channel, V3 prompt).
* PR sources of truth: `gh pr view {221,222,223,224,226} --json statusCheckRollup,files`
  taken on 2026-04-27.
* Caller maps: `rg` against the workspace at commit `91b0f29` (`main` HEAD
  at audit time).
* No commit pushed to any audited Dependabot branch (audit-and-block).

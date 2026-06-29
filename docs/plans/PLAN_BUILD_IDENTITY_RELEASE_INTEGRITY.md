# Plan: Build identity, runtime version display, and release integrity

**Status:** In progress — Phase E core landed (#856): SQLite integrity anchor (`core/integrity_anchor.py`), startup re-verify in any mode, TINTED/`-alpha` trust surfaces, `integrity_events`, open-mode worker clamp. Signed manifest (Phase C.4) and `--reverify-integrity` flag remain pending.
**Date:** 2026-03-23
**Authors:** Fabio Leitao
**Priority:** H2
**GitHub:** [#856](https://github.com/FabioLeitao/data-boar/issues/856) (Phase E core landed; Phase C.4 signed manifest + `--reverify-integrity` pending)
**Depends on:** ADR-0034

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)
**Related:** [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) (remote “latest” vs current; upgrade paths)

## Executive summary

**Recommendation:** Treat this as a **formal multi-phase plan**, not a single side quest. It spans **operator UX** (clear `INFO` lines and dashboard labels), **engineering hygiene** (PEP 440 / semver, git dirty state), optional **integrity signals** (manifests, CI-built artifacts), and **release automation** (bump → test → publish → Docker Hub → GitHub Release).

**Reality check on “tamper detection”:** A **local hash manifest** stored next to source proves whether **checked-out files** match a **recorded snapshot**. It does **not** by itself prove “no fraud” against an attacker with **write access** to both code and manifest. Stronger claims need **signatures** (e.g. CI-generated signed `build-info.json`, **Sigstore/Cosign** on container images, or **reproducible builds** compared to published digests). The plan below separates **honest UX** (Phase A) from **stronger assurance** (Phase C/D).

---

## Goals

1. **Single runtime story:** Every CLI run and web/dashboard view exposes a concise **build identity**: release number, optional **pre-release** tag (`alpha` / `beta` / `rc`), and whether the tree is **dirty** or **ahead of tag** (development).
1. **Logging:** At least one **INFO** (or equivalent) line on startup (CLI and uvicorn) with `version`, `build_kind`, and optional `vcs_revision` / `dirty`.
1. **Dashboard / API:** Same fields in dashboard footer (already has `about`) and optionally **`GET /about`** JSON for automation.
1. **Optional integrity:** A **manifest** of hashes for “behaviour-critical” modules, compared to **release-time** values (from CI artifact or embedded at image build). Clear **threat model** documented.
1. **SQLite anchor (Phase E):** On first run after deploy, **validate** manifest → **persist** release id + hashes/signatures in SQLite; **survive** `--reset-data` / wipe of scan data so audit still knows the **original** chancelada baseline; **re-verify** on startup; if mismatch → treat as **adulterated** / **not CI-validated** and downgrade **trust level** (force **`-alpha`**-style labelling in reports, logs, `/status`, health).
1. **Release train:** Scripted or workflow-driven **bump → all greens → tag → GitHub Release → Docker Hub** with tests guarding critical steps; documentation for operators.

---

## Non-goals (initially)

- Replacing **legal** attestation of findings (reports already carry version in “Report info”; this plan improves **clarity** of what ran).
- **Offline** cryptographic verification without a trust anchor (that is Phase C+).

---

## Current state

- **Version:** `importlib.metadata.version("data-boar")` in [core/about.py](../../core/about.py), aligned with `pyproject.toml`; fallback string if metadata missing.
- **UI/API:** [api/routes.py](../../api/routes.py) passes `about` to templates; Excel/report footer uses `get_about_info()`.
- **Startup:** [main.py](../../main.py) does not yet emit a standard **INFO** build line before audit/web.
- **Existing plan:** [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) covers **remote** latest version and upgrade UX—**complement** with local **build identity** first so operators see **what is running** before checking **whether an update exists**.
- **Licensing tamper-evidence** ([`core/licensing/integrity.py`](../../core/licensing/integrity.py), [`docs/RELEASE_INTEGRITY.md`](../RELEASE_INTEGRITY.md)): optional **`DATA_BOAR_EXPECTED_BUILD_DIGEST`** (must match the single line in embedded [`core/licensing/_build_digest.txt`](../../core/licensing/_build_digest.txt)) and optional manifest via **`DATA_BOAR_RELEASE_MANIFEST_PATH`** / **`licensing.manifest_path`**. Checked-out Git trees ship **`dev`** in that file; **release pipelines** overwrite the embedded line **or** deliver a matching built artefact—the **`dev`** placeholder is **not**, by itself, a production integrity anchor. **`PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY`** baseline: Phase **E.11** done (**CLI** **`--export-audit-trail`** JSON with placeholders for future anchor rows). **SQLite integrity anchor**, **startup re-verify**, and tamper-driven **trust level** (**E.1–E.9**) remain **pending** (tracked as Phase 2–3 / future issues—**not** part of tamper-documentation-only slices).

---

## Phase A — Runtime build identity (high value, low risk)

| #   | To-do                                                                                                                                                                                                                                                                                                          | Notes                                                                  |                                                        |                                                                                                                                                                    |
| -   | -----                                                                                                                                                                                                                                                                                                          | -----                                                                  |                                                        |                                                                                                                                                                    |
| A.1 | Add **`get_build_identity()`** (or extend `get_about_info()`) returning at least: `version` (PEP 440), `release` (same as version if no local dev), `build_kind` (`release` \                                                                                                                                  | `dev` \                                                                | `unknown`), `vcs_describe` (optional), `dirty` (bool). | Prefer **stdlib**: subprocess `git describe --dirty --always` when `.git` exists; else env **`DATA_BOAR_GIT_REF`** / **`SOURCE_DATE_EPOCH`** for container builds. |
| A.2 | **Display rules:** If **exact tag** matches `pyproject` version and **not dirty** → show `release=1.6.5` (or `version=1.6.5`). If **dirty** or **commits after tag** → append `*` or suffix `+dev` / `1.6.7a0` style per [PEP 440](https://packaging.python.org/en/latest/specifications/version-specifiers/). | Document convention in [VERSIONING.md](../VERSIONING.md) (EN + pt-BR). |                                                        |                                                                                                                                                                    |
| A.3 | **CLI:** One **INFO** line at start of `main()` (and after config load if useful): e.g. `INFO data_boar build version=1.6.5 release … dirty=False`. Use **logging** module if not already wired; else `print(..., file=sys.stderr)` with a single stable prefix.                                               | Tests: snapshot or regex on capsys.                                    |                                                        |                                                                                                                                                                    |
| A.4 | **Web:** Ensure dashboard template shows **`build`** string next to existing `about.version` (footer). Optional: same in `/about` JSON.                                                                                                                                                                        | Template + `tests/test_routes_responses.py` or similar.                |                                                        |                                                                                                                                                                    |
| A.5 | **Docker:** Pass **`LABEL org.opencontainers.image.version`** and **`revision`** at build time (existing Dockerfile/CI); read in app via env **`DATA_BOAR_IMAGE_DIGEST`** optional.                                                                                                                            | Align with [deploy/DEPLOY.md](../deploy/DEPLOY.md).                    |                                                        |                                                                                                                                                                    |

**Deliverable:** Operators always see **what build** is running; no hash file yet.

---

## Phase B — Pre-release labels (alpha / beta / RC)

| #   | To-do                                                                                                                                                                                                                                | Notes                                                                                  |
| -   | -----                                                                                                                                                                                                                                | -----                                                                                  |
| B.1 | **Convention:** `alpha` = working tree not matching release tag or explicit env **`DATA_BOAR_PRERELEASE=alpha`**. `beta` = optional CI flag after **smoke** job passes on candidate commit. `rc` = release candidate before tagging. | Map to PEP 440: `1.6.5a1`, `1.6.5b1`, `1.6.5rc1`—avoid ad-hoc strings that don’t sort. |
| B.2 | **Automation:** CI workflow sets **`DATA_BOAR_PRERELEASE`** or builds **wheel/sdist** with correct version via **`uv`/`hatch`** bump—single source of truth remains **`pyproject.toml`**.                                            | Link to [docs/ops/COMMIT_AND_PR.md](../ops/COMMIT_AND_PR.md) and release checklist.    |

---

## Phase C — Integrity manifest (optional, threat model explicit)

| #   | To-do                                                                                                                                                                                                                                            | Notes                                                                                                         |
| -   | -----                                                                                                                                                                                                                                            | -----                                                                                                         |
| C.1 | **Manifest file** (e.g. `build/manifest.sha256` or JSON list): paths relative to repo root + **SHA-256** of **allowlisted** `*.py` (core, api, engine, detector, main). **Exclude** tests, docs, `docs/`, `.github/`, config samples by default. | Generated by **`scripts/generate-code-manifest.py`** run in **CI on tag** and attached to **Release assets**. |
| C.2 | **Runtime check (optional flag):** `--verify-manifest` or config `build.verify_manifest_path` compares on-disk hashes to manifest. **Mismatch** → WARN or FAIL per policy.                                                                       | Tests with temp tree.                                                                                         |
| C.3 | **Limitation doc:** If attacker can modify **both** `core/detector.py` and `manifest.json`, verification is **void** unless manifest is **signed** and verified with a **public key** shipped in the binary/image (next phase).                  | Security doc section.                                                                                         |
| C.4 | **Signed manifest (stretch):** CI signs manifest with **GitHub OIDC** / Sigstore; app verifies optional.                                                                                                                                         | Align with container signing in [PLAN_SELF_UPGRADE §9](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md).               |

---

## Phase E — SQLite integrity anchor, audit trail, and tamper-aware trust level

> **Status (2026-06-11, #856):** E.1–E.9 **implemented** in
> [`core/integrity_anchor.py`](../../core/integrity_anchor.py) (anchor +
> `integrity_events` tables in the scan SQLite file, preserved by
> `wipe_all_data()`), wired into `main.py` startup, `/health`, `/status`,
> `get_about_info()` (`-alpha` forcing), `enterprise_surface_posture`
> (`integrity_tampered` → `elevated`), and the report Info sheet
> (`Build trust` / `Integrity state` rows). E.10 threat model documented in
> [`docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md`](../ops/INTEGRITY_CHECK_ALPHA_LOGIC.md).
> Plus a **new** behaviour-critical gate: open-mode worker clamp
> (`OPEN_MODE_WORKER_CAP = 2` in `core/engine.py`, inside the hashed
> allowlist). Pending: `--reverify-integrity` flag, Merkle-root compression,
> HMAC of the anchor row, signed manifest (Phase C.4).
> Tests: [`tests/test_integrity_anchor.py`](../../tests/test_integrity_anchor.py).

*Operator idea (2026-03): deploy may ship a **hash/signature manifest**; the app should **persist** the outcome in **SQLite** so it is not “one-shot”, survives selective wipes, and drives **what we tell the user** about reliability.*

### E.0 Problem statement

- **Scan/session data** may be wiped with **`--reset-data`** (or future wipe APIs), but operators still need an **immutable (within the DB file)** record of **which release was first validated** and **what hashes/signatures matched** at that moment.
- If **on-disk code** later **diverges** from those stored expectations (tamper, manual edit, partial upgrade), the product should **not** present itself as a **gold** release: at minimum label as **development / low trust** (**`-alpha`** semantics), or **`-beta`** only when a defined bar is met (e.g. smoke passed but not full release train).

### E.1 First-run “preparatory” flow

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                               | Notes                                                                                           |
| -   | -----                                                                                                                                                                                                                                                                                                                                                                                               | -----                                                                                           |
| E.1 | **Detect** whether integrity anchor was already computed: e.g. row in new table **`build_integrity_anchor`** (or `integrity_metadata`) with `anchor_version=1`.                                                                                                                                                                                                                                     | If table missing → migration creates it.                                                        |
| E.2 | If **not** yet done: load manifest path from **env** / **config** / **default next to image** (e.g. `DATA_BOAR_MANIFEST_PATH`); compute **SHA-256** (and verify **signature** if present) for allowlisted paths; store: **`release_label`**, **`manifest_content_hash`**, **per-file hashes** (or Merkle root to save space), **`validated_at`**, **`signature_ok`** bool, **`validator_version`**. | Idempotent: second run skips full re-hash unless **`--reverify-integrity`** or mismatch policy. |
| E.3 | **Import into SQLite** as the **system anchor** — separate from **scan sessions**. Use a **small, fixed schema** (few columns + optional JSON blob for detail).                                                                                                                                                                                                                                     | Document in [SECURITY.md](../SECURITY.md) / TECH_GUIDE.                                         |

### E.2 Interaction with `--reset-data` / wipe

| #   | To-do                                                                                                                                                                                                                                                                                        | Notes                                                                             |
| -   | -----                                                                                                                                                                                                                                                                                        | -----                                                                             |
| E.4 | **Wipe semantics:** `--reset-data` (and any `wipe_all_data` path) **clears** session/finding/report artifacts as today but **does not delete** `build_integrity_anchor` (or a dedicated **`audit_trail`** slice) unless a **separate** dangerous flag **`--reset-integrity-anchor`** exists. | Prevents losing “original release + first validation” after operator wipes scans. |
| E.5 | **Optional:** second table **`integrity_events`** append-only (validation, re-verify, tamper detected) for **forensics** without bloating main session log.                                                                                                                                  |                                                                                   |

### E.3 Startup sanity check (lightweight)

| #   | To-do                                                                                                                                          | Notes                                                     |
| -   | -----                                                                                                                                          | -----                                                     |
| E.6 | On each **process start** (CLI + web): quick check — recompute hashes **or** Merkle root for the same allowlist; compare to **stored** values. | If **DB missing** row → treat as **unknown** / run E.1.   |
| E.7 | **Mismatch** → set runtime flag **`trust_level=adulterated`** (or `integrity_state=tampered`); **do not** silently stay on “release”.          | Propagate to `get_build_identity()` / `get_about_info()`. |

### E.4 Trust level → user-visible strings (reports, logs, API)

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                                  | Notes                                                                                 |
| -   | -----                                                                                                                                                                                                                                                                                                                                                                                                  | -----                                                                                 |
| E.8 | **Mapping (configurable):** `release_and_manifest_match` + CI profile → **`build_kind=release`** (or **`beta`** if only smoke/HMLG). `mismatch` / `unsigned` / `never_validated` → **force `-alpha`** (or explicit string **“development / not CI-validated”**) in **Report info** sheet, **dashboard** footer, **`GET /about`**, **`GET /status`**, **health** endpoint if any, and **startup logs**. | Align with Phase B: **`-beta`** only when policy says “smoke OK but not full QA/UAT”. |
| E.9 | **Excel / PDF:** Minimum one extra field: **`Build trust`** or **`Integrity state`** so auditors see **adulterated** vs **validated**.                                                                                                                                                                                                                                                                 |                                                                                       |

### E.5 Threat model (honest)

| #    | To-do                                                                                                                                                                                                                                                                                                                                              | Notes |
| -    | -----                                                                                                                                                                                                                                                                                                                                              | ----- |
| E.10 | Document: attacker with **write access to SQLite file** can **delete or edit** the anchor table — then the app may **re-run** first validation or show **unknown**. **Mitigation:** file permissions, read-only mount for DB in high-assurance deploys, optional **HMAC of anchor row** with key in env (does not stop root, reduces casual edit). |       |

### E.6 CLI export of audit trail (baseline **implemented**)

| #    | To-do                                                                                                                                                                                                                                                                                                                                                                                                                                | Notes                                                                                                           |
| -    | -----                                                                                                                                                                                                                                                                                                                                                                                                                                | -----                                                                                                           |
| E.11 | **`--export-audit-trail [PATH]`** on **`main.py`**: writes JSON (default **stdout** if omitted or **`-`**). Current payload: `schema_version`, `exported_at`, **`application`** (from `get_about_info()`), **`paths`**, **`runtime_trust`** (license/integrity trust snapshot), **`data_wipe_log`** (full table), **`scan_sessions_summary`**, **`maturity_assessment_integrity`** (same counts as **`GET /status`** when maturity POC rows exist — separate from Phase E build anchor), placeholders **`integrity_anchor`** / **`integrity_events`** for Phase E persistence. | Does **not** open a scan or call wipe. Incompatible with **`--web`** / **`--reset-data`**.                      |
| E.12 | **Future:** extend export with **integrity_events** rows, **per-run version checks**, and optional **redacted execution log** pointers when those tables exist.                                                                                                                                                                                                                                                                      | Same JSON schema version bump or nested `extensions`.                                                           |
| E.13 | Runtime trust **operator surfacing**: emit explicit `INFO` lines to **stdout + stderr** so unexpected states are impossible to miss (`THERE IS SOMETHING DIFFERENT AND UNEXPECTED IN THIS RUNTIME`).                                                                                                                                                                                                                                 | Implemented baseline in CLI; keep message aligned with report/API wording when Phase E trust fields land there. |

### E.7 Governance: wipes vs audit trail (defence narrative)

- **`data_wipe_log`** is **append-only**: `wipe_all_data()` **never deletes** prior wipe rows — only **adds** a row for the new wipe (existing behaviour; documented in `LocalDBManager.wipe_all_data`).
- **Future** `integrity_anchor` / `integrity_events` tables must follow the same rule: **`--reset-data` clears scan artefacts, not the audit spine** — unless **`--reset-integrity-anchor`** (dangerous, explicit).
- **Export** lets operators and counsel produce a **timestamped JSON** showing **which wipes occurred**, **app version at export time**, and (once shipped) **integrity state** — supporting both **your** evidence that findings were produced by a **known build** and **detection** that someone ran a **non-release** or **tampered** tree.

### E.8 Dependencies (Phase E vs C)

- Requires **Phase C.1** manifest format (or a **subset** embedded in Docker image). Phase E can **ship after** C.1 is defined; UI strings from **Phase A** should read **`trust_level`** when present.

---

## Phase D — Release automation (“one button”)

| #   | To-do                                                                                                                                                                                                                                                                   | Notes                                                                                                                                        |
| -   | -----                                                                                                                                                                                                                                                                   | -----                                                                                                                                        |
| D.1 | **`scripts/release/`** (or extend existing): orchestrate **version bump** (patch/minor per arg), **`uv run pytest`**, **`ruff`**, build **sdist/wheel**, **Docker buildx**, **`gh release create`**, **Docker Hub push**—each step **skippable** via flags for dry-run. | Reuse [docs/ops/COMMIT_AND_PR.md](../ops/COMMIT_AND_PR.md) conventions; never embed secrets—use **`gh`**, **`docker login`** via CI secrets. |
| D.2 | **GitHub Actions:** `workflow_dispatch` inputs: `bump`, `dry_run`. Calls composite steps or script.                                                                                                                                                                     | Idempotent; protect workflow with **environment** approval if needed.                                                                        |
| D.3 | **Tests:** Unit tests for **version bump** helper; integration test with **mock** `gh`/`docker` (or `dry_run` only).                                                                                                                                                    |                                                                                                                                              |
| D.4 | **Documentation:** New **`docs/ops/RELEASE_TRAIN.md`** (EN + pt-BR) with **operator checklist** and **rollback** notes.                                                                                                                                                 |                                                                                                                                              |

---

## Testing matrix (minimum)

- Unit: `get_build_identity()` with mocked git / env / no `.git`.
- Integration: CLI startup line contains version; dashboard HTML contains build string.
- Manifest: golden file + tampered file → expected WARN/FAIL.
- **Phase E:** first-run populates anchor; `--reset-data` leaves anchor; tampered file → `trust_level` + **Report info** field; migration tests; **`--export-audit-trail`** JSON snapshot tests.
- Release script: dry-run does not call network.

---

## Compliance and trust narrative

- **Reports:** Excel “Report info” already records **version**; extending with **`build_kind`** / **`vcs`** (optional column or footer) supports audit questions (“was this a dev build?”).
- **Legal / leadership:** Short pointer in [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) and [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) under **Evidence**—*build identity and roadmap for signed release artifacts*.
- **Pitch (private):** When updating `docs/private/pitch/slides.yaml`, add one bullet: **reproducible versioning + integrity roadmap** for enterprises—optional; not required for Phase A.

---

## Future: session_id format (UUID v7) — evidence precision, not fraud proof

**Context:** Today `core.session.new_session_id()` uses UUID4-derived hex (truncated) plus an explicit UTC timestamp suffix — already human-readable and log-friendly.

**Idea (when prioritised):** Adopt **RFC 9562 UUID version 7** for `session_id` strings so identifiers are **time-ordered** and embed **millisecond-resolution** time in the standard UUID structure (modern practice, better sortability vs ad hoc suffixes). This signals attention to **evidence and correlation precision**; it is **not** a substitute for tamper detection (**hashes, signed manifests, SQLite anchor** in Phase E). Evaluate alongside minimum Python version and migration/compatibility for existing SQLite rows and API clients.

**Doc pointers:** `core/session.py` module docstring, `docs/TOPOLOGY.md` (session bullet).

---

## Order of execution (recommended)

1. **Phase A** (runtime identity + logging + dashboard) — unblock operators immediately.
1. **Phase B** if you need **alpha/beta/rc** semantics in customer-facing builds.
1. **Phase C.1** (manifest format + generator) — prerequisite for meaningful **Phase E**.
1. **Phase E** (SQLite anchor + wipe semantics + startup re-verify + trust strings) — **high value** for compliance narrative; pairs with C.
1. **Phase D** when manual release steps become painful (often parallel to late A/E).
1. **Phase C.2–C.4** (optional flags, signed manifest) when threat model requires it.

---

## Relation to “side quest” vs “plan”

- **Side quest:** Only Phase A (one PR, small).
- **Full program:** Phases A–E + D + **PLAN_SELF_UPGRADE** for a complete **version + upgrade + integrity + audit anchor** story—**worth a dedicated milestone** in [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) (e.g. **M-BUILD-ID**).

---

*Last updated: Phase **E.11** (`--export-audit-trail`) implemented. SQLite anchor + startup re-verify + trust downgrade (**E.1–E.9**) pending. Licensing-layer digest/manifest baseline documented (`docs/RELEASE_INTEGRITY.md`; issue `#545`).*

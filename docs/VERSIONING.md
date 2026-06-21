# Version convention and bump checklist

**Português (Brasil):** [VERSIONING.pt_BR.md](VERSIONING.pt_BR.md)

This project uses a **major.minor.build** version scheme, with optional **pre-release suffixes** while work is still being prepared:

- **major** – first number (e.g. breaking changes or major release)
- **minor** – second number (e.g. new features, backward-compatible)
- **build** – third number (e.g. fixes, docs, no behaviour change)
- **suffix** (optional) – pre-release stage marker in lowercase: `-beta` or `-rc`

Examples:

- `1.3.2` means major 1, minor 3, build 2 (final publishable number).
- `1.3.3-beta` means pre-release work in progress for the next build.
- `1.3.3-rc` means release candidate (feature/code/docs/tests wired, final publish checks pending).

---

## Bump rules

| Bump type | Rule                                                    | Example             |
| ---       | ---                                                     | ---                 |
| **Major** | Increment first number; set minor and build to **0**    | `1.3.2` → **2.0.0** |
| **Minor** | Keep major; increment second number; set build to **0** | `1.3.2` → **1.4.0** |
| **Build** | Keep major and minor; increment build only              | `1.3.2` → **1.3.3** |

---

## Build octet maturity + release-line roadmap (ADR-0073)

**Canonical decision:** [ADR-0073](adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md). Pairs with [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (commit gate ≠ release gate).

Originally an **internal** Gibson DNS-beacon discipline; after the unauthorized `1.7.4` promotion (#970) the **public** number exposes maturity too.

### Third-segment octet bands (when using numeric build maturity)

| Build range | Meaning | Examples |
| --- | --- | --- |
| **0–127** | beta band | experimental / working slices |
| **128–199** | rc band | release-candidate maturity |
| **200–255** | release band | **`.200` = GA**, **`.201` = fix-1**, **`.202` = fix-2**, … |

Suffixes (`-beta`, `-rc`, `-rc-N`) remain valid on `main` while the **release gate** (GitHub #406) is open. A green **commit gate** (`check-all`) never authorizes removing them — see ADR-0072.

### Current 1.7.4 line (post-#970)

| Label | Status |
| --- | --- |
| **`1.7.4` / build `.200` (GA)** | **VOID** — never released; promoted without gate (#970, PR #840) |
| **`main` working tree** | **`1.7.4-rc-2`** in `pyproject.toml` until gate **#406** closes |
| **Real stable after gate** | starts at **`1.7.4.201`** (fix-1 post-burned GA) — not `1.7.4` |

Ladder (historic + target): `1.7.4-beta` → `1.7.4-rc` → **`1.7.4-rc-2`** (today) → **`1.7.4.201`** (post-gate).

### Release-line roadmap (intent — not naive semver increment)

| Line | Scope |
| --- | --- |
| **`1.7.4.x`** | Open-core maturity + commercial JWT protection (**fix line** after gate) |
| **`1.8.x`** | Augmented corporate capacities (re-ID, sidecars, plugins/Clojure — **new architecture**, not a 1.7 minor) |
| **`1.7.5`** | **Does not exist** — agents must not invent it (#772). Next dev milestone: **`1.8.0-beta`**. |
| **`1.9.x`** | Horizon (compliance-domain expansion — triage per #772) |

DNS-beacon / heartbeat / kill-switch lifecycle (#717) stays on the **1.8.x** roadmap (`docs/plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md`, maintainer index in `docs/README.md`); out of scope for this section.

---

## Pre-release flow (`-beta` / `-rc`) before final publish

Use lowercase suffixes consistently:

| Stage                 | Recommended use                                                                                                                   | Example      |
| ---                   | ---                                                                                                                               | ---          |
| **`-beta`**           | Relevant code/behavior changes started and tracked, but not yet considered release-candidate ready.                               | `1.7.1-beta` |
| **`-rc`**             | Candidate ready for final validation/publish choreography (tests green, docs synced, release notes ready, merge/release pending). | `1.7.1-rc`   |
| **final (no suffix)** | Public release number (Git tag + GitHub Release + Docker Hub publish).                                                            | `1.7.1`      |

### Practical policy

- If a slice changes meaningful behavior (API, detection logic, report output, runtime operation, security posture), prefer moving the working version to `X.Y.Z-beta`.
- When the release package is materially ready (code + tests + docs/release notes in shape), promote to `X.Y.Z-rc`.
- Only remove suffix and publish `X.Y.Z` when doing the real release sequence (merge + tag + GitHub Release + Docker publish).
- For bigger scope (or when explicitly requested), publish as a **minor bump**: `X.(Y+1).0` (no suffix at final publish).

---

## Working vs published version (avoid confusion)

- **Working version:** what `pyproject.toml` currently states on your branch (may be `-beta`/`-rc` or unsent work).
- **Published version:** latest Git tag + GitHub Release + Docker Hub tag available to external users.
- Do not assume they are equal; always call both explicitly in release notes and review requests.

### Assistant / automation (ordering guardrail)

**Cursor / agents:** follow **`.cursor/rules/release-publish-sequencing.mdc`** (**situational** — session **`release-ritual`** or **`@release-publish-sequencing.mdc`** when globs miss; **`docker-local-smoke-cleanup.mdc`** stays **always-on** for smoke/prune) — create Git tag **`vX.Y.Z`**, GitHub Release, and Docker Hub publish steps **before** moving `main` to the next **`-beta`** (or next dev) bump. Session keyword **`release-ritual`** means **`read_file`** that rule (or **`@`**) and this file before editing semver or release docs.

---

## Where the version appears (bump checklist)

When you bump the version, update **all** of the following so the number is consistent everywhere:

### 1. Source of truth (required)

| Location             | What to change                                                                                                                                                                                                                                                                                                                |
| ---                  | ---                                                                                                                                                                                                                                                                                                                           |
| **`pyproject.toml`** | Update the `version = "X.Y.Z"` line. This is the **single source of truth** for the installed package. The running application (About page, Report info sheet, heatmap footer, API `/about/json`) reads the version from the installed package metadata, so updating `pyproject.toml` and reinstalling is enough for runtime. |

### 2. Fallback when metadata is missing

| Location            | What to change                                                                                                                                                                    |
| ---                 | ---                                                                                                                                                                               |
| **`core/about.py`** | Update the fallback string in `get_about_info()` when `importlib.metadata.version(...)` fails (e.g. running from source without install). Example: `ver = "1.3.0"` → new version. |

### 3. Man pages

| Location               | What to change                                                                                                  |
| ---                    | ---                                                                                                             |
| **`docs/data_boar.1`** | In the `.TH` line (e.g. `"Data Boar 1.5.4"`), set the version to the new one.                                   |
| **`docs/data_boar.5`** | Same: update the version in the `.TH` line. (Legacy: `lgpd_crawler` is a compatibility symlink to these pages.) |

### 4. Deploy and Docker

| Location                    | What to change                                                                                                                                                    |
| ---                         | ---                                                                                                                                                               |
| **`docs/deploy/DEPLOY.md`** | Update any **example** version tags in the Docker tag/push commands (e.g. `1.3.0` in the examples) to the new version so copy-paste commands use the correct tag. |

### 5. Documentation (EN and PT-BR)

| Location                       | What to change                                                                                                                                   |
| ---                            | ---                                                                                                                                              |
| **`README.md`**                | If the text mentions the current version number (e.g. in a release or image tag example), update it.                                             |
| **`README.pt_BR.md`**          | Same as README.md for any explicit version mention.                                                                                              |
| **`docs/USAGE.md`**            | Update any explicit version reference if present.                                                                                                |
| **`docs/USAGE.pt_BR.md`**      | Same as USAGE.md.                                                                                                                                |
| **`docs/plans/PLANS_TODO.md`** | If there is a “current version” or “app version” note in a plan’s “Current state” or publish step, update it when you release.                   |
| **Other docs**                 | Search the repo for the old version string (e.g. `1.3.0`) and update any remaining references in SECURITY.md, CONTRIBUTING.md, or release notes. |

### 6. Distribution, Docker Hub, and customer-facing copy

Keep **published** semver story consistent for anyone pulling images or reading marketing text (not only `pyproject.toml`):

| Location | What to change |
| --- | --- |
| **`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`** | **Short** + **Full** blocks for the Docker Hub UI: **Current release**, **Supported tags** semver, **copyright/maintainer** lines, and CLI examples (`python main.py`). **Manual paste** into Hub **after each stable image push** — the website does not pull from Git; drift (e.g. years-old **Tags** listing **1.6.5**) means someone skipped this step. Skip Hub copy refresh for **`-beta`** / **`-rc`**-only pushes unless you intentionally advertise them. |
| **`docs/ops/today-mode/PUBLISHED_SYNC.md`** (+ **`.pt_BR.md`**) | Table row: **GitHub Latest**, **Docker Hub** tags, and “next” patch — must match what customers can actually install. |
| **`docs/TECH_GUIDE.md`** (+ **`.pt_BR.md`**) | Example Hub tag in the Docker subsection (if it pins a semver). |
| **Operator social / milestones** (e.g. **`docs/private/social_drafts/`**, gitignored) | If a post cites “current release”, “latest on Docker Hub”, or a version number, align with **`README.md`** **Current release** line and **`PUBLISHED_SYNC`** — never celebrate a version that is not yet on GitHub + Hub unless you label it as **upcoming**. |

### 7. UI and reports (no edit needed if 1–2 are done)

These show the version **dynamically** from package metadata (via `core/about.py`), so they do **not** need manual edits when you bump:

- **About page** (`api/templates/about.html`) – uses `{{ about.version }}`
- **Dashboard / Reports pages** – use `{{ about.version }}`
- **Excel report “Report info” sheet** – `report/generator.py` uses `about["version"]`
- **Heatmap PNG footer** – same `about` dict
- **API `/about/json`** – same `about` dict

After updating `pyproject.toml` (and optionally `core/about.py`), reinstall the package (e.g. `uv sync` or `pip install -e .`) so the new version is in metadata; then the UI and reports will show it automatically.

---

## Quick reference

- **Format:** `major.minor.build`
- **Pre-release suffixes:** lowercase `-beta`, `-rc` (working states only)
- **Bump major:** `X.Y.Z` → `(X+1).0.0`
- **Bump minor:** `X.Y.Z` → `X.(Y+1).0`
- **Bump build:** `X.Y.Z` → `X.Y.(Z+1)`
- **Promote flow:** `X.Y.Z-beta` → `X.Y.Z-rc` → `X.Y.Z` (final publish)
- **Checklist:** pyproject.toml → core/about.py → docs/data_boar.1, data_boar.5 → docs/deploy/DEPLOY.md → README (EN/PT-BR), USAGE (EN/PT-BR), PLANS_TODO → **DOCKER_HUB_REPOSITORY_DESCRIPTION** + **PUBLISHED_SYNC** → TECH_GUIDE Docker example → optional social drafts → search repo for old version string.

**Português (Brasil):** [VERSIONING.pt_BR.md](VERSIONING.pt_BR.md)

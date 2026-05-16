# Python runtime upgrade playbook (3.12 → 3.13 → 3.14, Docker, CI)

**Location:** This is a **planned / ops meta** document (upgrade path and matrix), kept under **`docs/plans/`** with other readiness and sequencing guides—not only day-to-day HOWTOs under **`docs/`**.

**Português (Brasil):** [PYTHON_UPGRADE_PLAYBOOK.pt_BR.md](PYTHON_UPGRADE_PLAYBOOK.pt_BR.md)

**Purpose:** Stay **safe on 3.12** while **preparing** for newer CPython lines without breaking **wheels** numpy/pandas/scipy, SQL drivers, ORM, **Docker** multi-stage paths, or **CI**.

---

## 1. Current contract (what must stay true)

| Layer           | Source of truth                                                   | Today                                                                                  |
| -----           | ----------------                                                  | -----                                                                                  |
| Declared range  | `pyproject.toml` → `requires-python`                              | `>=3.12`                                                                               |
| Locked tree     | `uv.lock` + `uv sync`                                             | Resolved for 3.12/3.13 (CI test matrix on `main`)                                      |
| Published image | `Dockerfile` **`FROM`** + **`COPY .../python3.XY/site-packages`** | Must match **one** Python minor end-to-end                                             |
| CI signal       | `.github/workflows/ci.yml`                                        | **Test** job should cover every **supported** minor you claim in SECURITY/CONTRIBUTING |

**Catch:** Claiming **3.13** without CI on 3.13 hides regressions until Docker or local runs fail.

---

## 2. Why 3.13 before 3.14?

|                     | 3.13                                                     | 3.14                                                                                |
| ---                 | ---                                                      | ---                                                                                 |
| **Wheel ecosystem** | Mature **cp313** wheels for most scientific/DB stack     | **cp314** wheels still trailing; more **source builds** risk                        |
| **Friction**        | Lower: official `python:3.13-slim`, same pattern as 3.12 | Higher: watch PyPI for `cp314` on numpy/scipy/pandas/sklearn/psycopg2/oracledb/etc. |
| **Security / CVEs** | Newer interpreter + Debian base refresh in slim images   | Same idea, gated by dependency wheels                                               |

**Recommendation:** Treat **3.13** as the **next production target** for Docker + lockfile verification; treat **3.14** as **experimental** until `docker build` installs **only wheels** (or acceptable compile time) for your full `requirements.txt` / `uv.lock`.

---

## 3. Compatibility matrix to maintain

| Check                                         | 3.12            | 3.13                                       | 3.14 (prep)            |
| -----                                         | ----            | ----                                       | -----------            |
| `uv sync` + `uv run pytest -v -W error`       | CI              | CI (matrix)                                | Manual or optional job |
| `uv run ruff check` / format                  | CI              | Same as 3.12 job (keep one)                | N/A                    |
| `pip-audit` / Dependabot                      | CI              | Same                                       | N/A                    |
| **Docker** `docker build`                     | Default publish | Branch: change `FROM` + `python3.XY` paths | Branch only            |
| **Smoke:** container up, `/health`, idle scan | Homelab         | Same image tag family                      | Same                   |

**Dockerfile edits when minor changes:** Replace **every** `python3.12` in `find`/`COPY` with `python3.13` (or `3.14`).

---

## 4. Preparing for 3.14 (sooner–later)

1. **CI:** Keep **3.12 + 3.13** green; add an optional **`workflow_dispatch`** or **weekly** job on **3.14** that does `uv sync` + `pytest` (allow **failure** or **continue-on-error** until green).
1. **Lockfile:** Run `uv lock` under **3.14** in a throwaway env **only after** `uv` reports a solvable tree; commit lock updates in a **dedicated PR**.
1. **Wheel audit (manual):** Before bumping Docker `FROM`, run `pip install -r requirements.txt` in a **3.14** container and note any **“Building wheel for …”** that runs **>2–3 minutes** — that’s your regression risk.
1. **`requires-python`:** Raise to `>=3.13` or `>=3.14` **only** when you **drop** 3.12 support — a **major** comms + release decision.

---

## 5. Local A/B Docker (time build + smoke)

**Goal:** Compare **baseline** (`data_boar:py312`) vs **candidate** (`data_boar:py313`) without touching the default `latest` tag until satisfied.

```powershell
# From repo root — example for 3.13 candidate branch
docker build -t data_boar:ab-py312 -f Dockerfile .
# After editing Dockerfile to 3.13:
docker build --no-cache -t data_boar:ab-py313 -f Dockerfile .

docker images data_boar --format "{{.Tag}}\t{{.Size}}"
```

**Smoke (both):** same `config.yaml`, same volume, `docker run -p 8088:8088`, hit `/health`, optional `POST /scan` with `targets: []`.

**If candidate fails or build explodes:** keep **3.12** `FROM` for **published** Hub images; keep the **branch** for retry next quarter.

---

## 6. What you might not be seeing

- **Python upgrades ≠ automatic CVE cure:** Many findings are **Debian packages** (`apt`) or **PyPI** deps — refresh **base slim tag**, `apt-get upgrade` policy, and **Dependabot** anyway.
- **`pylock.toml` (if present):** A `uv export --format pylock.toml` can show `requires-python` from the **export environment**; **`uv.lock` + `pyproject.toml`** are authoritative — don’t let a stray export contradict support policy.
- **JFrog / private index:** If you mirror wheels, ensure **cp313** / **cp314** artifacts exist for pinned versions or resolution will fall back to PyPI or **sdist**.

---

## 7. Related docs

- [TESTING.md](../TESTING.md) · [DOCKER_SETUP.md](../DOCKER_SETUP.md) · [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md)
- [SECURITY.md](../SECURITY.md) — supported Python lines
- [TECH_GUIDE.md](../TECH_GUIDE.md) — local toolchains
- [PLAN_READINESS_AND_OPERATIONS.md](PLAN_READINESS_AND_OPERATIONS.md) · [PLANS_TODO.md](PLANS_TODO.md)

---

## Last updated: playbook relocated to `docs/plans/`; CI matrix 3.12+3.13 for tests.

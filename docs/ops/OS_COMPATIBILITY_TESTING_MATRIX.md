# OS compatibility testing matrix (homelab expansion)

**Purpose:** Guide **which Linux distributions** to test Data Boar on in the homelab, prioritized by **production relevance**, **Python 3.12+ availability**, and **package manager** differences. This helps expand **documented support** beyond the current **Debian/Ubuntu** baseline.

**Related:** [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) · [SECURITY.md](../../SECURITY.md) (Python 3.12+ requirement) · [TECH_GUIDE.md](../TECH_GUIDE.md) (install examples)

---

## 1. Current baseline (documented)

- **Primary:** **Ubuntu 24.04 LTS** / **Debian 13** (recommended in [TECH_GUIDE.md](../TECH_GUIDE.md)).
- **Python:** **3.12+** required ([SECURITY.md](../../SECURITY.md)); CI tests **3.12 and 3.13** on Ubuntu.
- **Package manager:** Examples use **`apt`**; **`uv`** (or `pip`) handles Python deps.

---

## 2. Priority tiers for testing

### Tier 1: Enterprise / production common (test first)

| Distro family                       | Why test                                                                                 | Python 3.12+ status                                                                                                           | Package manager                | Notes                                                                                                                                                                                                 |
| -------------                       | --------                                                                                 | -------------------                                                                                                           | ----------------               | -----                                                                                                                                                                                                 |
| **Red Hat Enterprise Linux (RHEL)** | **Enterprise** deployments often use RHEL; **AlmaLinux** / **Rocky** are RHEL-compatible | **RHEL 9+** has Python 3.12 in **AppStream**; **RHEL 8** may need explicit `python3.12` package install | **`dnf`** (or `yum` on RHEL 7) | **Proven install split (1.7.4.post3 retest):** **RHEL 8 + RHEL 9** need `dnf install -y python3.12` and `pipx install --python python3.12 data-boar` in the `pipx` path. **RHEL/Alma/Rocky/Oracle 10** is frictionless in the default `pipx install data-boar` path. **RHEL/CentOS 7** is EOL (dead repos + `requires-python>=3.12` unreachable): use Docker only. |
| **AlmaLinux** (RHEL-compatible)     | **Free** RHEL rebuild; common in homelabs and small orgs                                 | **AlmaLinux 9** has Python 3.12; **8.x** may need **EPEL** / **SCL**                                                          | **`dnf`**                      | Same package names as RHEL 9. Test **AlmaLinux 9** first; **8.x** if you need legacy coverage.                                                                                                        |
| **Rocky Linux**                     | Another **RHEL-compatible** rebuild                                                      | **Rocky 9** has Python 3.12; **8.x** similar to AlmaLinux                                                                     | **`dnf`**                      | Similar to AlmaLinux; pick one for initial testing unless you want both.                                                                                                                              |
| **Fedora**                          | **Upstream** for RHEL; **bleeding edge** packages; common on **developer** workstations  | **Fedora 40+** has Python 3.12+; **39** may have 3.11 (check before testing)                                                  | **`dnf`**                      | Often **first** to get new Python; good for **early** compatibility checks. Test **Fedora 40+** (or current stable).                                                                                  |

**Recommendation:** Start with **AlmaLinux 9** or **Fedora 40+** (whichever you can spin up faster). If both pass, you likely cover **RHEL 9** too.

---

### Tier 2: General-purpose / popular (test after Tier 1)

| Distro                  | Why test                                                                             | Python 3.12+ status                                                           | Package manager  | Notes                                                                                                                                                                                                                                       |
| ------                  | --------                                                                             | -------------------                                                           | ---------------- | -----                                                                                                                                                                                                                                       |
| **Arch Linux**          | **Rolling release**; popular with developers; catches **bleeding edge** issues early | **Arch** typically has **latest** Python (3.13+ often); **AUR** for extras    | **`pacman`**     | **System deps:** `pacman -S python python-pip gcc openssl libffi postgresql-libs unixodbc` (package names differ from Debian). **`uv`** installs same way. **Arch** can expose **new** dependency conflicts before they hit stable distros. |
| **Manjaro**             | **Arch-based** but **more stable** (delayed updates); easier for homelab             | **Manjaro** follows Arch with **delay**; check current ISO for Python version | **`pacman`**     | Similar to Arch; if **Arch** works, **Manjaro** likely does too (test one first).                                                                                                                                                           |
| **BigLinux**            | **Brazilian** Arch-based distro; **localization** relevance                          | Follows **Arch/Manjaro** package base; check Python version                   | **`pacman`**     | If you test **Arch** or **Manjaro**, **BigLinux** is likely similar; document if you find **localization** or **package** differences.                                                                                                      |
| **openSUSE Tumbleweed** | **Rolling** SUSE; **zypper** package manager; enterprise SUSE compatibility          | **Tumbleweed** has **latest** Python; **Leap** (LTS) may lag                  | **`zypper`**     | **System deps:** `zypper install python312 python312-devel gcc libopenssl-devel libffi-devel postgresql-devel unixODBC-devel`. Less common than RHEL/Debian but **enterprise** SUSE exists.                                                 |

**Recommendation:** **Arch** or **Manjaro** first (pick one); **openSUSE** if you have time for a **third** package manager.

---

### Tier 3: Source-based / niche (test if time allows)

| Distro           | Why test                                                                             | Python 3.12+ status                                                           | Package manager    | Notes                                                                                                                                                                                                                                                                   |
| ------           | --------                                                                             | -------------------                                                           | ----------------   | -----                                                                                                                                                                                                                                                                   |
| **Gentoo**       | **Source-based**; **USE flags**; catches **compile-time** issues; **advanced** users | **Gentoo** can compile **any** Python version; **ebuilds** for 3.12+ exist    | **`emerge`**       | **System deps:** `emerge -av dev-lang/python:3.12 dev-libs/openssl dev-libs/libffi dev-db/postgresql` (adjust USE flags). **`uv`** may work; **pip** fallback if wheels fail. **Gentoo** is **slow** to install; use for **final** compatibility pass, not first smoke. |
| **Void Linux**   | **musl** option; **xbps** package manager; **lightweight**                           | **Void** has Python 3.12+; **musl** vs **glibc** can affect **native wheels** | **`xbps-install`** | **Proven split (1.7.4.post3 retest):** **Void-glibc** passes in default `pipx install data-boar` (PyPI publishes `cp314` wheel). **Void-musl** currently fails in the same path because available wheelhouse is `cp312` while host Python is 3.14; needs a `cp314` wheelhouse (tracking [#1182](https://github.com/DataBoar/data-boar/issues/1182)) or Docker. |
| **Alpine Linux** | **musl** + **apk**; **Docker** base images; **minimal**                              | **Alpine** has Python 3.12+; **musl** + **small** libc can break some wheels  | **`apk add`**      | **System deps:** `apk add python3 py3-pip gcc musl-dev openssl-dev libffi-dev postgresql-dev unixodbc-dev`. **Onboarding gap (pipx):** in this musl path, `scikit-learn` may fall back to source build and fail with `metadata-generation-failed` without toolchain. Use wheelhouse (`--find-links`) when available, or pre-step `apk add build-base gfortran openblas-dev` before `pipx install data-boar` (until wheelhouse work in #929 and #1182). **Runtime parity note:** once install succeeds and smoke waits for scan completion, Alpine-musl matched Debian-glibc at 26 findings in the 1.7.4.post3 retest; the earlier 13-count was a harness timeout artifact, not a detector/parser gap. |

**Recommendation:** **Void** or **Alpine** (musl) is **higher** priority than **Gentoo** if you want **musl** coverage; **Gentoo** is **educational** but **time-consuming**.

---

### Tier 3.5: Proven `pipx` install outcomes (1.7.4.post3 retest)

| Path | Current status | Required action |
| ---- | -------------- | --------------- |
| **Debian / Fedora / RHEL10-family / Void-glibc** | Frictionless | `pipx install data-boar` |
| **RHEL 8 / RHEL 9** | Extra step required | `dnf install -y python3.12` then `pipx install --python python3.12 data-boar` |
| **Alpine musl / Void musl / no-AVX hosts** | Default path not frictionless | Use wheelhouse (`--find-links`) or distro build prerequisites; fall back to Docker when wheelhouse is unavailable |
| **RHEL 7 / CentOS 7** | Native `pipx` path not viable | Docker-only path (EOL repos + Python floor mismatch) |

---

### Tier 4: Solaris lineage (**illumos**) — historical OpenSolaris / exploratory

| What you have                             | Reality check                                                                                                                                                       |
| -------------                             | -------------                                                                                                                                                       |
| **“OpenSolaris”** (official ISO / legacy) | The **OpenSolaris** project was **discontinued** (~2010). Install media is **historical**; no current security support. **Do not** expose it to untrusted networks. |
| **Modern equivalent**                     | **illumos** distributions: **OpenIndiana**, **OmniOS**, **Tribblix**, etc. — these are the **active** descendants of the Solaris/ZFS ecosystem.                     |

| Distro / image                         | Why test                                                                | Python 3.12+ / tooling                                                                                                                               | Notes                                                                                                                                                                                            |
| --------------                         | --------                                                                | ----------------------                                                                                                                               | -----                                                                                                                                                                                            |
| **OpenIndiana** (or other **illumos**) | **ZFS**, **SMF**, **enterprise Solaris-style** curiosity; **not** Linux | **Python** may be available via **IPS** (`pkg`) or **pkgsrc**; **3.12+** availability varies by release — **verify** before planning a full §1 pass. | **No** `manylinux` wheels for illumos — expect **source builds** or **pip** failures on native deps (`cryptography`, `lxml`, DB drivers). **`uv`** is **not** validated on illumos in this repo. |
| **OmniOS** / **Tribblix**              | **Server-focused** illumos; some sites use for **storage / NAS** roles  | Same caveats as OpenIndiana; check each project’s **Python** packaging story.                                                                        | Useful if your **homelab** standardises on **ZFS + illumos**; still **lowest** priority for **Data Boar** CI or “supported OS” claims.                                                           |

**Fit for Data Boar:** **Exploratory only** — same tier as **Haiku** for “shipping support”: document **gaps**, do **not** expect `uv sync` + full connector matrix without **significant** porting or **Linux container** sidecars.

**IBM OS/2** (Warp, etc.): **Out of scope** — **nostalgia / preservation** VMs only; there is **no** credible path to **Python 3.12+** + this app’s dependencies on OS/2 for homelab validation.

**Recommendation:** If you install something Solaris-like, prefer a **current illumos** ISO (**OpenIndiana** etc.) in a **VM** on **Proxmox** or spare metal — **after** Tier 1–3 Linux coverage. Keep **OpenSolaris-era** bits **lab-only** and **air-gapped** if possible.

---

## 3. Testing checklist per distro

For **each** OS you add to the homelab:

- [ ] **Python 3.12+** available via **native** package manager (or **SCL** / **PPA** / **AUR** if documented).
- [ ] **System libraries** installed (SSL, FFI, PostgreSQL client, ODBC if needed) — see **package names** table above.
- [ ] **`uv`** installs and runs (or **`pip`** fallback if `uv` fails).
- [ ] **`uv sync`** completes (or `pip install -e .`).
- [ ] **`uv run pytest -v -W error`** passes (or equivalent).
- [ ] **`docker build -t data_boar:lab .`** works if you test **Docker** on that host.
- [ ] **§2 filesystem synthetic** scan completes.
- [ ] **Document** any **package name differences** or **missing** deps in a **GitHub issue** (tagged `documentation` / `compatibility`); **host-specific** notes only in **gitignored** **`docs/private/homelab/`** ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

---

## 4. Version strategy (same distro, different releases)

| Approach               | When to use                                                                                                                               |
| --------               | -----------                                                                                                                               |
| **Latest stable** only | **Fedora**, **Arch**, **Tumbleweed** (rolling) — test **current** ISO.                                                                    |
| **LTS + current**      | **Ubuntu** (22.04 + 24.04), **Debian** (12 + 13), **RHEL** (8 + 9) — test **both** if you want **enterprise** coverage.                   |
| **One representative** | **AlmaLinux 9** likely covers **RHEL 9**; **Manjaro** likely covers **Arch** base; test **one** per family unless you find **surprises**. |

**Recommendation:** Start with **one** distro per **family** (RHEL-compatible, Arch-based, Debian-based, musl). Add **versions** only if you find **Python 3.12** availability differs or **package names** change. **illumos** (Solaris lineage) is a **separate** family — **Tier 4** only; do not block Linux matrix work on it.

---

## 5. What to document (public vs private)

## Public (tracked docs):

- **Generic** package manager commands (e.g. `dnf install python3.12` for RHEL family) in **`TECH_GUIDE.md`** or a new **`INSTALL_<DISTRO>.md`**.
- **Known issues** in **`TROUBLESHOOTING.md`** or **GitHub issues** (e.g. RHEL9-family pipx with default `python3=3.9` requires `pipx install --python python3.12 data-boar`; Alpine/musl pipx pre-step `apk add build-base gfortran openblas-dev`).
- **CI matrix** expansion (if you add **GitHub Actions** runners for Fedora/Arch) — see **`.github/workflows/`**.

## Private (`docs/private/homelab/` — gitignored):

- **Exact** hostnames, **IPs**, **VM IDs**, **snapshot names**.
- **Personal** notes like “Fedora 40 on spare desktop, 4 GB RAM, slow but works.”

---

## 6. Recommended testing order (for your homelab)

1. **AlmaLinux 9** or **Fedora 40+** (RHEL family) — **Tier 1** enterprise relevance.
1. **Arch** or **Manjaro** (Arch family) — **Tier 2** rolling / developer popularity.
1. **Void** or **Alpine** (musl) — **Tier 3** if you want **musl** coverage (already in §9 as “second x86_64”).
1. **Gentoo** (if you have **time** and want **source-based** edge cases).
1. **illumos** (**OpenIndiana** or similar) — only **after** Linux tiers; **OpenSolaris**-era media is **legacy** (see **Tier 4**).

**Skip** for now: **BigLinux** (test after **Arch/Manjaro** if you want Brazilian localization validation), **openSUSE** (lower priority unless you target **SUSE** customers).

---

## 7. Integration with homelab playbook

- **VM on primary laptop** (§1.5): Use **Boxes** / **virt-manager** to spin up **AlmaLinux 9** or **Fedora** guest for **early** Tier 1 smoke.
- **Proxmox guest** (§9): When the **tower** is ready, create **multiple** VMs (one per distro family) and run **§1.1–1.2 + §2** on each. An **illumos** or legacy **OpenSolaris-class** VM is **optional** and **lowest** priority (see **Tier 4**).
- **Bare metal** (§9): If you have **spare** hardware, **AlmaLinux** or **Arch** on the **i3 desktop** counts as a **second x86_64** row.

**Record** host-specific results in **`docs/private/homelab/`**; update **public** docs only when you find **package name** differences worth documenting.

---

**Português (Brasil):** [OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md](OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md)

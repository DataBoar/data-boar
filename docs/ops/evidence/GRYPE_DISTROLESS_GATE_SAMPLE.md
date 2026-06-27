# Grype gate sample — distroless release image (#1028 PR-B)

**Purpose:** Release evidence excerpt after PR-A (distroless `cc-debian13:nonroot`) + PR-B (`.grype.yaml` + gate scripts).

**Policy:** `grype IMG --fail-on high --only-fixed --config .grype.yaml` — actionable High/Critical only; never weaken `--only-fixed`.

**Image scanned (operator lab, 2026-06-27):** `podman:localhost/data_boar:hardening-test` (same Dockerfile as release train).

**Tooling:** grype **0.115.0** (Anchore DB schema 6).

---

## Gate result (pass)

Command:

```bash
./scripts/grype-image-gate.sh podman:localhost/data_boar:hardening-test
```

Exit code: **0**

Excerpt (only findings with a vendor fix version — none at High+):

```
NAME    INSTALLED  FIXED IN  TYPE    VULNERABILITY   SEVERITY  EPSS         RISK
python  3.13.14    3.15.0a6  binary  CVE-2025-15367  Medium    0.3% (23rd)  0.2
python  3.13.14    3.15.0a6  binary  CVE-2025-15366  Medium    0.3% (23rd)  0.2
```

**Interpretation:** Medium Python CVEs reference fix in **3.15.0a6** (alpha — inactionable for production). No High/Critical with an installable fix on the **1.7.4** line.

---

## Full-scan context (won't-fix base — VEX in `.grype.yaml`)

Without `--only-fixed`, the same image still reports Critical/High on **libc6**, **mariadb** (libmariadb3), and **python** with empty or **won't fix** vendor state — documented in `.grype.yaml` per package class. Distroless runtime deb closure on this digest: **libc6**, **mariadb**, **zlib1g** (vs larger `python:3.13-slim` noise pre-PR-A).

**Re-scan:** After each bump of distroless or slim digests in `Dockerfile`, re-run this gate and refresh this excerpt if the actionable set changes.

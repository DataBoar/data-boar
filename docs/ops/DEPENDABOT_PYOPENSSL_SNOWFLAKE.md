# Dependabot: pyOpenSSL alerts blocked by Snowflake connector pin

**Last triage:** **2026-05-22** (wave **#656** / issue **#427**).

**Status (2026-05-22):** **Resolved on `main`.** **`snowflake-connector-python` 4.5.0** (optional **`bigdata`** extra) resolves with **`pyopenssl` 26.2.0** in **`uv.lock`**. GitHub Dependabot alerts **#9** / **#10** (CVE-2026-27448, CVE-2026-27459) should stay **closed** while the lockfile keeps **`pyopenssl>=26`**. Re-open triage if a future connector release reintroduces a **`pyopenssl<26`** cap or new advisories appear.

---

## Historical context (pre-4.5.0)

GitHub Dependabot showed **open** alerts **#9** and **#10** for **pyOpenSSL** (CVE-2026-27448 low, CVE-2026-27459 high). The fix is **pyOpenSSL ≥ 26.0.0**.

**Why we could not bump earlier:** **`pyopenssl`** is pulled in as a **transitive** dependency of **`snowflake-connector-python`** ([`bigdata` optional extra](../../pyproject.toml)). Published **`snowflake-connector-python`** versions **through 4.3.0** declared **`pyopenssl<26`**, so **`uv lock`** could not resolve **`pyopenssl>=26`** together with **`data-boar[bigdata]`** without an unsatisfiable graph.

**Upstream:** Snowflake tracked the cap (e.g. [snowflake-connector-python#2789](https://github.com/snowflakedb/snowflake-connector-python/issues/2789)). **4.5.0+** allows **pyOpenSSL 26+** in the resolved graph.

**Risk note (operator judgment):** The advisories concern **DTLS cookie callbacks** and **SNI callback exception handling**. Typical Data Boar use of the Snowflake connector does not custom-wire these OpenSSL callbacks; residual risk is lower than the raw CVSS suggests for many deployments.

## If alerts reopen

1. Confirm **`snowflake-connector-python`** metadata and **`uv lock`** output.
1. Bump **`snowflake-connector-python`** (or add an explicit **`pyopenssl>=26.0.0`** floor if the connector no longer caps it).
1. Run **`uv lock`**, **`uv export --no-emit-package pyproject.toml -o requirements.txt`**, **`.\scripts\check-all.ps1`**.
1. Merge; Dependabot should close when the lockfile no longer contains a vulnerable range.

**Optional GitHub UI:** If noise is high with **no fix yet**, maintainers may **dismiss** alerts with reason **`patch_unavailable`** and a comment linking this doc — **re-check** on the quarterly cadence below.

**Related:** [SECURITY.md](../SECURITY.md) (dependency workflow), [MAINTENANCE_FRONT_OF_WORK.md](../plans/MAINTENANCE_FRONT_OF_WORK.md) (S4 / A1). **`.\scripts\maintenance-check.ps1`** (after `gh auth login`) lists open Dependabot **alerts**.

**Cadence:** Re-check on each **Band A order –1** pass and at least **quarterly** — see **PLANS_TODO.md** *Every order –1 pass* and *Quarterly blocked-dependency checkpoint*.

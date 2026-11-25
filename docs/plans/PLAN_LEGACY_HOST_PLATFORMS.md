# PLAN: Legacy host platforms (Linux s390x, AIX, HP-UX, z/OS)

**Status:** In progress (classification documented; **nothing tested locally**; Linux s390x QEMU recipe pending)
**Date:** 2026-11-25
**Priority:** P3
**GitHub:** [#2183](https://github.com/DataBoar/data-boar/issues/2183)
**Relates to:** [#1666](https://github.com/DataBoar/data-boar/issues/1666) (indirect mainframe path), [#2179](https://github.com/DataBoar/data-boar/issues/2179) (BSD), [#1182](https://github.com/DataBoar/data-boar/issues/1182) (wheelhouse), [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md), [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md)

---
<!-- plans-hub-summary: Host vs target boundary for legacy platforms (Linux s390x, AIX, HP-UX, z/OS) in three evidence classes; nothing tested locally; s390x QEMU recipe pending; future wheel evidence via data-boar-site release + PEP 503 simple/ (same pattern as #1182). -->

## Context

AIX, HP-UX and the mainframe (IBM Z) are still present in banks, insurers and other regulated verticals with legacy databases and processing. The repo had no plan about **running Data Boar as a host** on these platforms. [#1666](https://github.com/DataBoar/data-boar/issues/1666) already defines the **indirect** path for the mainframe: it is not about running the Boar on the mainframe; the data reaches the Data Soup through a controlled, read-only export. This plan records the **host vs target** boundary for the legacy platforms.

## Three classes

Each platform falls into **one** class, with evidence:

1. **Host validatable in a VM:** Data Boar runs and is tested in a virtual machine, reproducibly.
2. **Host only with vendor hardware or license:** not validatable in open emulation; no support promise without evidence.
3. **Target only (Data Soup ingredient):** Data Boar does not run there; the data is exported (SFTP/FTPS/NFS/MQ, step 1 of #1666) to a supported host.

## Known state (third-party reports and metadata; **none tested locally**)

| Platform | Class | Basis (not verified locally) | Still to verify |
| --- | --- | --- | --- |
| **Linux s390x (IBM Z / LinuxONE)** | candidate for **1** | `qemu-system-s390x` is in the Debian/Ubuntu repositories and distributions publish official s390x images. TCG emulation is slow (no reliable measurement). Technical value: **big-endian** architecture, which can expose endianness assumptions in native wheels and in the Rust extension. | URL, size and hash of the images; s390x wheels for the stack (numpy, scipy, scikit-learn, cryptography); the validated QEMU recipe below. |
| **AIX (POWER)** | candidate for **2** | 2024 reports say QEMU `pseries` does **not** boot AIX 7.3; the media depends on IBM licensing. | Python 3.12+ and toolchain availability on AIX before any promise. |
| **HP-UX (PA-RISC / Itanium)** | candidate for **2 or 3** | QEMU emulates PA-RISC (`B160L`, `C3700`) with mixed reports for HP-UX 11.11 and reported failures on 11.23/11.31; no source for Itanium. Licensed media. | Whether any reproducible path exists; until then, no host claim. |
| **z/OS** | **3** (target) | As in #1666. Python on z/OS exists as a vendor product; running the Boar there is not a goal of this plan. | Nothing for the host side; ingestion follows #1666. |

## Linux s390x QEMU recipe (pending acceptance)

**Not done.** Acceptance for this step (issue [#2183](https://github.com/DataBoar/data-boar/issues/2183)): installation, Python environment, **`uv run python main.py --demo`** without tracebacks, the expected findings, and the list of **wheels that needed a local build** (package name, version, build command), all recorded here with dates. Until then, s390x stays **candidate for class 1, not verified**.

### Wheel and install evidence (after a successful QEMU pass)

When that QEMU run completes, **record in this plan** (and, if useful, a dated file under `docs/ops/evidence/`): guest image URL/digest; Python and `uv` versions; demo outcome; the **local-build wheel list**.

**Publish binaries** with the same channel discipline as the proven x86-64-v1 wheelhouse ([#1182](https://github.com/DataBoar/data-boar/issues/1182), [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md)):

1. **GitHub Release** on **`DataBoar/data-boar-site`** (versioned tag, `.whl` assets, **`SHA256SUMS`**).
2. **PEP 503 `simple/`** index at **`https://databoar.com.br/simple/`** (rebuilt in the site repo via `scripts/build-wheelhouse-index.py` — not duplicated here).
3. Operator install path documented like today’s wheelhouse pattern: [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) (*x86-64-v1 / wheelhouse install*) — `pip install` / `pipx` with `--extra-index-url https://databoar.com.br/simple/` or offline `--find-links` after `gh release download`.

**Today:** the live `simple/` index ships **x86_64 / arm64** (and related) cells from **`wheelhouse-x86-64-v1-2026-07-29`** — **no** s390x slice is published yet. Planning only; not a support claim.

## Class 3 platforms

For z/OS (and HP-UX if it ends in class 3), the path is the #1666 ingestion: export to a supported host. Data Boar is **not** declared supported as a host there.

## Out of scope

Connector implementation (#1666, #1362); any support claim without evidence; buying licensed media without an operator decision.

Evidence, not a legal or support conclusion.
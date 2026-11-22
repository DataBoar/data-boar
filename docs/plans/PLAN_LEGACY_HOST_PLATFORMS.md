# PLAN: Legacy host platforms (Linux s390x, AIX, HP-UX, z/OS)

**Status:** In progress (classification documented; nothing tested locally yet)
**Date:** 2026-11-20
**Priority:** P3
**GitHub:** [#2183](https://github.com/DataBoar/data-boar/issues/2183)
**Relates to:** [#1666](https://github.com/DataBoar/data-boar/issues/1666) (indirect mainframe path), [#2179](https://github.com/DataBoar/data-boar/issues/2179) (BSDs), [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md)

---
<!-- plans-hub-summary: Host vs target boundary for legacy platforms (Linux s390x, AIX, HP-UX, z/OS) in three evidence classes; nothing tested locally yet, s390x QEMU recipe pending. -->

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

## Linux s390x QEMU recipe (pending)

Not done. Acceptance for this step (from #2183): installation, Python environment, `uv run python main.py --demo` without tracebacks, the expected findings, and the list of wheels that needed a local build, all recorded here with versions and dates. Until then, s390x stays "candidate for class 1, not verified".

## Class 3 platforms

For z/OS (and HP-UX if it ends in class 3), the path is the #1666 ingestion: export to a supported host. Data Boar is **not** declared supported as a host there.

## Out of scope

Connector implementation (#1666, #1362); any support claim without evidence; buying licensed media without an operator decision.

Evidence, not a legal or support conclusion.

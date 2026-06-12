# License FAQ — Data Boar

**Português (Brasil):** [LICENSE_FAQ.pt_BR.md](LICENSE_FAQ.pt_BR.md)

This FAQ explains the Data Boar **open-core licensing model** in plain language. It supplements — and never overrides — the [`LICENSE`](../LICENSE) file, the [Terms of Use](../TERMS_OF_USE.md), and the commercial documents ([SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md), [LICENSING_SPEC.md](LICENSING_SPEC.md), [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md)).

> **Model status (2026-06):** Today the entire repository ships under the license in the `LICENSE` file (BSD 3-Clause). The **source-available commercial module** split described below is the **ratified target model**; the physical split (`databoar_license/`) and the "Data Boar Commercial License" text await a deliberate maintainer step with legal review. This FAQ documents the model so buyers and contributors are never surprised.

## 1. What license does Data Boar use?

A **dual structure in one public, auditable repository** (the Bitwarden / Elastic pattern):

- **Core — BSD 3-Clause (open source):** scanner engine, detectors, plugin interface, baseline CLI/API/dashboard, research and thesis material.
- **Commercial modules — source-available (target model):** corporate features (corporate connectors, custom RBAC, SIEM/RoPA push, deploy packs, partner/white-label architecture). The code is **visible** to everyone; **commercial production use requires a paid subscription**.

## 2. What can I use for free?

Everything in the **core**, for any purpose the BSD 3-Clause allows — including **internal use inside a commercial organisation** at no cost (see [Terms of Use §2](../TERMS_OF_USE.md)). Scanning systems you are authorised to scan, building reports for your own compliance program, modifying and extending the code: all free.

## 3. What requires a paid subscription?

- **Delivering scan results to third parties as a paid service** (consulting, audit, MSSP) — Pro or higher (see [Terms of Use §4](../TERMS_OF_USE.md)).
- **Commercial production use of commercial modules** (corporate connectors, custom RBAC, SIEM/RoPA push, deploy packs) — per the tier ladder in [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md).
- A subscription also buys **standard support, configuration assistance, and productized customization** — it is not just feature gates.

## 4. Will the core ever close?

**No — by definition.** The open-source core (scanner, detectors, plugin interface, baseline surfaces, research material) **never closes**. The commercial model funds the project precisely so the core can stay open and auditable.

## 5. Can I fork Data Boar?

Yes. The BSD 3-Clause core is forkable under its terms. Two boundaries:

- **Trademark and brand:** the name, mascot, narrative, and product experience are **not** licensed by the code license — forks must not imply endorsement or confuse origin (see the brand IP inventory in [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md)).
- **Commercial modules:** under the target model, source-available code remains visible for audit/dev/test, but commercial production use still requires a subscription, fork or not.

## 6. If the code is visible, what stops abuse?

**Layered defense, not code secrecy:**

1. **Signed Ed25519 JWT licenses** — fail-closed enforcement (`licensing.mode: enforced`).
2. **Machine fingerprint binding** (`dbmfp`, deployment packs) — issuance-enforced deploy counts.
3. **Release integrity** — build digest verification and tamper-evident integrity anchor (TINTED/`-alpha` marking).
4. **Trademark and contract** — legal layer for commercial misuse.

A determined actor can patch any of it locally; the point is that **tampered builds are evident**, unsupported, and commercially unusable at scale.

## 7. What are the tiers?

Community (free) → Pro → Pro+ → Enterprise, plus a custom **Partner** family. **Tier = capability, claim = quantity.** Full ladder, capability table, and worker/deployment claims: [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md).

## 8. Can I write and distribute plugins?

The **plugin interface is core (BSD-3)** — writing plugins against it is free. The **plugin/partner architecture** for commercial distribution (partner catalogs, white-label packaging) is an **Enterprise/Partner** capability. Independent open-source plugins remain yours under your own license.

## 9. Can I use Data Boar in academic work?

Yes — research, theses, coursework, and papers are core use cases (the project itself carries research material). Cite the project, respect the [Terms of Use](../TERMS_OF_USE.md) (only scan what you are authorised to scan), and note that scan results are probabilistic — not a legal compliance certification.

---

*Questions not covered here: open an issue or contact the maintainer. For acceptable-use boundaries (what you may never do with the tool, in any tier), read the [Terms of Use](../TERMS_OF_USE.md).*

# Academic use and thesis guidance (Data Boar)

**Português (Brasil):** [ACADEMIC_USE_AND_THESIS.pt_BR.md](ACADEMIC_USE_AND_THESIS.pt_BR.md)

This document helps **students, advisors, and examiners** use the **public** Data Boar documentation and codebase in **dissertations, theses, and research reports** without mixing product secrets, personal data, or operator-only commercial material. It is **guidance**, not legal advice; confirm requirements with your **graduate programme** and, if needed, **legal counsel**.

---

## 1. What Data Boar is (pointers)

- **Product overview and claims:** [README.md](../README.md) (decision-makers and compliance framing).
- **Technical operation:** [TECH_GUIDE.md](TECH_GUIDE.md) (install, CLI, API, connectors, config).
- **Compliance framing (not legal advice for your study):** [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md), [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md).
- **Historical baseline for the repo and ADRs:** [adr/ADR-0000-project-origin-and-adr-baseline.md](adr/ADR-0000-project-origin-and-adr-baseline.md).

---

## 2. License and attribution

- **Open-core license (public tree):** [LICENSE](../LICENSE) — **BSD 3-Clause** (permissive; retain copyright notice and license text on redistribution — see the license file for exact conditions).
- **Optional commercial enforcement** (runtime tokens) is specified in [LICENSING_SPEC.md](LICENSING_SPEC.md); **default** development and academic replication typically use **`open`** mode (no paid token required). See also [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) for the intended product boundary.
- **How to cite the software** in a thesis (adapt to your institution’s style):
- **Repository:** canonical Git URL (e.g. GitHub `FabioLeitao/data-boar` or successor), **commit hash** or **release tag**, and **date accessed**.
- **Version:** match [VERSIONING.md](VERSIONING.md) / `pyproject.toml` when you freeze a reproduction baseline.
- **License:** name **BSD 3-Clause** and point to the root **`LICENSE`** file (some programmes ask for a license appendix).

---

## 3. What you can normally use in academic work

- **Public source code** and **tracked documentation** under this repository for: methodology, architecture description, heuristic or pipeline comparison at **design** level, and reproducibility instructions.
- **Public diagrams or quotes** from docs, with citation (respect **copyright** on expressive text and **trademark** on branding — see [COPYRIGHT_AND_TRADEMARK.md](COPYRIGHT_AND_TRADEMARK.md)).
- **Synthetic or public datasets** for experiments; see [tests/README.md](../tests/README.md) for notes on optional public text samples (respect third-party **terms** and **copyright**).

---

## 4. What needs extra care (often mandatory)

- **Personal data (PII):** do **not** ship real production datasets in a thesis appendix. Prefer **synthetic** data, **public** corpora, or **strongly redacted** samples; follow **LGPD** / **GDPR** (and your ethics board) where applicable.
- **Operator and client confidentiality:** no **hostnames**, **LAN IPs**, **credentials**, or **client-identifying** scenarios from private engagements in public thesis text unless you have **written permission** and a **redaction** plan.
- **`docs/private/`** (and similar **gitignored** trees): **not** part of the public academic package — do not paste into **tracked** institutional repositories as if it were public product documentation.
- **Commercial-only material** (pricing studies, proposals, rate cards): keep **off** the public thesis deliverable; store under policy agreed with your institution (often **separate annex** with access control, or omit).

---

## 5. Reproducibility checklist (recommended for examiners)

1. State **Git commit** or **tag**, **Python** version (e.g. 3.12/3.13), and how dependencies were installed (**`uv sync`** / lockfile).
1. Provide a **sanitised** `config` excerpt based on [deploy/config.example.yaml](../deploy/config.example.yaml) — **no secrets**.
1. If you used Docker, cite **image tag** and **`Dockerfile`** / compose reference from [DOCKER_SETUP.md](DOCKER_SETUP.md).
1. Note **`licensing.mode: open`** (or equivalent) if readers must replicate without a commercial token.
1. List **tests** or **scripts** you ran (`pytest` targets, CLI flags) so others can verify claims **without** your private data.

---

## 6. Institution, authorship, and IP

- Many universities have rules on **software authorship**, **supervisor rights**, and **company IP** if you are employed while studying. Resolve **early** with your **programme office** or **technology transfer** unit.
- If you are both **maintainer** and **author**, clarify in the thesis **what is your scholarly contribution** (e.g. novel heuristic, evaluation design) versus **product documentation** written for operators.

---

## 7. Related documents

- **Portfolio, PUCRS supplements, PUC-Rio Digital extensions, study cadence:** Use the **Internal and reference** entry in [docs/README.md](README.md) to open `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (no direct `plans/` link from this page per repo policy). There, see **section 3.3** (**PUCRS extension supplements**), the **PUC-Rio Digital extension courses** subsection (benefit-aligned recommendations; confirm against your **private** contract in `docs/private/academic/`), and **section 3.0** (weekly study cadence).
- [CONTRIBUTING.md](../CONTRIBUTING.md) — contributor hygiene (no secrets in public repo).
- [SECURITY.md](../SECURITY.md) — supported versions and reporting vulnerabilities.
- [TESTING.md](TESTING.md) — what automated checks exist (useful for “validation” chapters).
- [docs/adr/README.md](adr/README.md) — recorded **why** decisions after ADRs were adopted.

---

## Disclaimer

This file does **not** constitute **legal advice**. Licensing, data protection, and thesis rules depend on **jurisdiction** and **institution**. Use this guide to brief advisors and counsel; do not treat it as a substitute for formal review.

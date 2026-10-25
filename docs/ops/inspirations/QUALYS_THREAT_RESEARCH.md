# Source note — Qualys Threat Research (blog / TRU)

**Português (Brasil):** [QUALYS_THREAT_RESEARCH.pt_BR.md](QUALYS_THREAT_RESEARCH.pt_BR.md)

Primary links:

- [Qualys blog — Vulnerabilities & Threat Research](https://blog.qualys.com/category/vulnerabilities-threat-research/)
- Example (coordinated disclosure, kernel / LSM): [CrackArmor: Critical AppArmor flaws enable local privilege escalation to root](https://blog.qualys.com/vulnerabilities-threat-research/2026/03/12/crackarmor-critical-apparmor-flaws-enable-local-privilege-escalation-to-root) (March 2026) — AppArmor confused-deputy class issues, patch urgency, container-relevant trust boundaries; upstream CVE assignment timing discussed in the post.

Why this source is useful:

- Long-form **threat research** with executive summary, impact, and technical depth — good reference for how to **frame** kernel and infrastructure risk for operators.
- Reinforces that **default** hardening layers (e.g. LSM profiles) still need **vendor patch cadence** and monitoring — analogous discipline for scanners, containers, and homelab hosts.

How we consume it:

- Use as **inspiration** for prioritizing Linux/kernel patching in environments where Data Boar or dependencies run (CI runners, homelab, customer advice in docs).
- Cross-check distribution advisories; do not treat any vendor blog as sole authority for our product threat model.

Watch-outs:

- Content is **vendor-aligned** (Qualys product mentions); extract the **technical and process** lessons, not sales copy.
- Exploit details may be withheld during disclosure; follow your distro’s security notices for actionable versions.

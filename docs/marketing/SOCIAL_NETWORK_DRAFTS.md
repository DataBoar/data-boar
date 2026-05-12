# Social network drafts (operator copy bank)

**Audience:** Maintainer or partner posting on LinkedIn, X, or similar. **Not** scheduled content in CI.

**Disclaimer:** Data Boar surfaces **signals and governance metadata**; it does **not** provide legal advice. When a post touches law or compliance, keep language inventory-oriented (“alerts”, “retention posture”, “operator-owned policy”) and link to product docs, not to plans.

**Pt-BR mirror:** [SOCIAL_NETWORK_DRAFTS.pt_BR.md](SOCIAL_NETWORK_DRAFTS.pt_BR.md)

**Source themes (public docs):** [MAP.md](../MAP.md), [THE_WHY.md](../philosophy/THE_WHY.md), [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md), ADRs [0038](../adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) / [0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md), [PORT_LOGISTICS_MULTINATIONAL_CREW.md](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.md).

---

## Short posts (single screen)

1. **MAP + vault**
   We published a **MAP** for Data Boar: what exists today, what is experimental, and where ADRs lock intent. If you are evaluating sensitive-data discovery, start there—then the **Architect’s Vault** in the README for philosophy and collision handling. #DataGovernance #SensitiveData

2. **Evidence vs theatre**
   Good compliance tooling is not a slide deck. It is **repeatable evidence**: what was scanned, what matched, what you kept or dropped, and who owns retention. Our public **THE_WHY** page states that plainly—no hero story required. #LGPD #DataProtection

3. **Jurisdiction is a hint, not a verdict**
   Multinational data often carries **more than one plausible legal frame**. The product’s job is to **surface tension and inventory signals**, not to auto-pick a statute. See ADR 0038 and the jurisdiction collision guide. #Compliance #CrossBorder

4. **Minors are not an afterthought**
   If your corpus can include people under 18, **minors detection is first-class** in the roadmap—not a bolt-on regex. That is a product ethics choice, not a marketing slogan. #ChildSafety #ResponsibleAI

5. **Bonded / customs-adjacent contexts**
   In sealed or customs-adjacent environments, **retention and artefacts are operator-owned**. The tool does not silently tag “legal basis” for you. ADR 0039 documents that posture for integrators. #SupplyColleague-Nn #Audit

6. **Port logistics + crew data**
   Generic **use-case storyboard**: multinational crew, shore passes, mixed languages, high sensitivity. Useful for **DPIA-style thinking** and scope conversations—no customer names, no drama. #Maritime #HRData

7. **Logs and secrets**
   Operational logs should not become a second leak surface. We document **redaction defaults** (ADR 0036) so operators know what the daemon is allowed to retain. #Security #DevOps

8. **Governance of the auditor**
   Buyers ask **who ran the scanner** and whether behaviour changes are **defensible**. ADR 0037 documents the 2026 baseline: scan attribution, tamper-oriented signals, export audit trail—without overselling “immutable every click.” #SOC2 #GRC

---

## Thread-style (LinkedIn / X — tighten per platform limit)

**A. The honest POC thread**
(1) We ship a **MAP**: honest about what is production-shaped vs lab.
(2) Sensitive-data discovery needs **collision handling** when jurisdiction hints disagree.
(3) Read **THE_WHY**: evidence beats theatre.
(4) Integrators: ADRs 0038–0039 for ambiguity alerts and bonded-context retention.
(5) CTA: clone the repo, read USAGE, run your own corpus in a sandbox.

**B. Multinational HR / logistics**
(1) Crew and contractor files are **high risk** and **multi-jurisdiction by default**.
(2) A scanner that “picks Brazil only” from a phone number is **overselling**.
(3) Prefer products that **inventory conflict** and let **policy owners** decide.
(4) Pointer: jurisdiction collision doc + port logistics use-case.

---

## Optional QA journal entry (internal one-liner)

When you ship a doc slice (MAP, ADR, use-case), paste into your **release or QA notes**:
*“Doc-only: added/updated [file]; external tier has no plan links (ADR 0004); locale/pt-BR checked for paired files.”*

That keeps social copy aligned with what actually shipped.

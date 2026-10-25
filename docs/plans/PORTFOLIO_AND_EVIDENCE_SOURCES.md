# Portfolio and evidence sources (thesis, pitch, CV narrative)

**Purpose:** Single place to list **where** to get (or add) evidence for thesis, compliance narrative, and pitch. Keeps sessions token-efficient: open this file + one source at a time. See [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) §3 for how this ties into plans.

**Policy:** Public URLs and repo paths only. No sensitive or private content here; private docs stay in `docs/private/` (git-ignored) and are referenced by filename.

---

## 0. Stakeholder pitch — keep in sync with README

**Canonical copy** for decision-makers lives in the root **[README.md](../../README.md)** and **[README.pt_BR.md](../../README.pt_BR.md)** (*For decision-makers / Para gestores*). When you refresh decks, CV blurbs, or thesis “product” paragraphs, start there.

**Roadmap tone (keep aligned):** The README **Roadmap** paragraph includes one **executive-readable** line (boards / audits: direction and evidence on visibility and compliance posture—without an engineering-only story). Deeper roadmap bullets below are for **plans and evidence**; they are **not** meant to be pasted verbatim into external decks—summarise in the same tone as the README.

## Differentiators to cite (hireability / commercial story):

- **Filesystem judgment:** Configurable plain-text depth plus **calmer ML triage** on entertainment-shaped and common OSS-doc content—**review band** vs **priority** violations—so legal and DPO time goes to real risk.
- **Roadmap — richer data soup:** Optional **image metadata and OCR**, **audio/video** tags, **subtitle** sidecars ([PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md), [USAGE.md](../../USAGE.md))—same **boar / soup** metaphor for media-heavy estates.
- **Roadmap — enterprise extensions:** **SAP** plus **HR / SST / ERP / CRM**-class systems (research-first integration patterns: [PLAN_SAP_CONNECTOR.md](PLAN_SAP_CONNECTOR.md), [PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md](PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md)).
- **Roadmap — operability:** **Scan-complete notifications** ([PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md)); **identity / subscription-ready** access for multi-operator deploys (**M-ACCESS**, [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)).

---

## 1. Docker images and Dockerfiles

| Image           | Docker Hub                                                                                   | GitHub / Dockerfile                                                                                                                                                             | Notes (fetched or from you)                                                                                                      |
| -----           | ----------                                                                                   | -------------------                                                                                                                                                             | ---------------------------                                                                                                      |
| **data_boar**   | [hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar)     | This repo: **[Dockerfile](https://github.com/FabioLeitao/data-boar/blob/main/Dockerfile)** (multi-stage, **python:3.13-slim**, builder + runtime). Tags e.g. `1.6.0`, `latest`. | Short description on Hub; full description with quick start and link to GitHub. Size ~186 MB (1.6.0).                            |
| **wildfly_t1r** | [hub.docker.com/r/fabioleitao/wildfly_t1r](https://hub.docker.com/r/fabioleitao/wildfly_t1r) | **[FabioLeitao/wf_t1r](https://github.com/FabioLeitao/wf_t1r)** — **[Dockerfile](https://github.com/FabioLeitao/wf_t1r/blob/main/Dockerfile)** at repo root (Eclipse Temurin + WildFly; see README for variants). | Archived on Hub. Tag e.g. `et-ojdk8-a_w26.1.1-final`. **Citable “Dockerfile I created”:** public link above.                  |
| **uptk**        | [hub.docker.com/r/fabioleitao/uptk](https://hub.docker.com/r/fabioleitao/uptk)               | **No public GitHub repo** for this image at last check; Dockerfile may live only on the server or under private notes.                                                            | Tag `0.1`, ~3.1 MB. **Citable path:** add a one-line pointer in **`docs/private/Dockerfiles_used.md`** (copy from **`docs/private.example/Dockerfiles_used.md`**) if you need “Dockerfile I built for Uptime Colleague-Ma” without publishing the repo. |

**Optional:** Copy **`docs/private.example/Dockerfiles_used.md`** → **`docs/private/Dockerfiles_used.md`** and list **wf_t1r** (public Dockerfile) plus **uptk** (where the file lives, if private) so thesis/CV can cite “Dockerfiles created and used” in one place.

---

## 2. GitHub repositories (public)

**Source of truth for the list below:** `gh repo list FabioLeitao --limit 200 --json name,description` (public, non-archived). **Refresh** this table when you add or rename repos.

| Repo | Description (from GitHub) | Use in narrative |
| ---- | ---- | ---- |
| **[ada-sample-guid](https://github.com/FabioLeitao/ada-sample-guid)** | Simple sample to learn ada | Ada learning; languages breadth. |
| **[auto_uploader](https://github.com/FabioLeitao/auto_uploader)** | Bash script para automação de transferência de arquivos | Automation / SRE; file transfer. |
| **[bash_busca_vm_proxmox](https://github.com/FabioLeitao/bash_busca_vm_proxmox)** | Busca de VM rodando no Proxmox para uso dentro do PRTG como Script SSH | Proxmox + PRTG; infra monitoring. |
| **[bash_cups_control](https://github.com/FabioLeitao/bash_cups_control)** | cups_control | CUPS / printing automation. |
| **[bash_jboss_monitor](https://github.com/FabioLeitao/bash_jboss_monitor)** | Bash jBoss 7.4 Monitor for PRTG | JBoss monitoring; PRTG sensors. |
| **[bash_localiza_danfe_por_id_de_upload](https://github.com/FabioLeitao/bash_localiza_danfe_por_id_de_upload)** | Bash script para automação de busca de arquivos DANFE em PDF enviadas no processo de Checkin Documental do TOSP para uma determinada DI. | Logistics / document automation (context-specific). |
| **[batch_reload_ap](https://github.com/FabioLeitao/batch_reload_ap)** | Scripts para automatizar reload de APs CISCO na LAN | Cisco Wi‑Fi; batch ops. |
| **[cifras](https://github.com/FabioLeitao/cifras)** | Cifras diversas para estudos de Guitarra e Violão | Optional PT text samples; personal corpus. |
| **[data-boar](https://github.com/FabioLeitao/data-boar)** | Dashboard com capacidade de sondagem, apreciação e mapeamento dos dados pessoais e/ou sensíveis | **Main product**; compliance/LGPD; Dockerfile in repo root. |
| **[go-healthcheck-and-reconnect-sgat](https://github.com/FabioLeitao/go-healthcheck-and-reconnect-sgat)** | Poc em GO para healthcheck do cosetting SGAD no TOSP | Go; healthcheck / reconnect patterns. |
| **[go-rest-api](https://github.com/FabioLeitao/go-rest-api)** | Curso de go, para criar uma API rest simples | Go; REST API learning. |
| **[java-corporate-entity-a-tosp](https://github.com/FabioLeitao/java-corporate-entity-a-tosp)** | Poc para integracao com SonarQube | SonarQube POC; cite employer context only if policy allows. |
| **[memory-rust](https://github.com/FabioLeitao/memory-rust)** | memory-rust | Rust experiment (see repo README). |
| **[odin_breakout_simple_game](https://github.com/FabioLeitao/odin_breakout_simple_game)** | Simple breakeout game | Odin; small game demo. |
| **[odin_cat_simple_game](https://github.com/FabioLeitao/odin_cat_simple_game)** | Seguindo curso de raylib com odin | Odin + raylib. |
| **[odin_hellorld](https://github.com/FabioLeitao/odin_hellorld)** | Simple testing in Odin | Odin learning. |
| **[poc-api-siscomex-rfb](https://github.com/FabioLeitao/poc-api-siscomex-rfb)** | POC de consumos das APIs Siscomex no portal da RFB | Siscomex / customs API integration POC. |
| **[powershell_nddprint_control](https://github.com/FabioLeitao/powershell_nddprint_control)** | nddprint_control | Windows print control automation. |
| **[python3-healthcheck-and-reconnect-sgad](https://github.com/FabioLeitao/python3-healthcheck-and-reconnect-sgad)** | python3-healthcheck-and-reconnect-sgad | SGAD healthcheck / reconnect (Python). |
| **[data-boar](https://github.com/FabioLeitao/data-boar)** | Dashboard com capacidade de sondagem, apreciação e mapeamento dos dados pessoais e/ou sensíveis | Repositório canónico (**Data Boar**). URL antiga `github.com/.../python3-lgpd-crawler` redireciona; não usar o nome antigo como identidade do produto. |
| **[python3-qrcodegenerator](https://github.com/FabioLeitao/python3-qrcodegenerator)** | Script to read from file with a list of strings to generate as QRCode images ready to print as labels | QR labels; small utility. |
| **[python3-sabor-express](https://github.com/FabioLeitao/python3-sabor-express)** | Projeto da aula de backend em Python3 | Python backend course project. |
| **[rust-healthcheck-and-reconnect-sgad](https://github.com/FabioLeitao/rust-healthcheck-and-reconnect-sgad)** | rust-healthcheck-and-reconnect-sgad | SGAD healthcheck / reconnect (Rust). |
| **[selenium-robots](https://github.com/FabioLeitao/selenium-robots)** | Selenium Applications for monitoring robots | Selenium; monitoring automation. |
| **[tmux-configs](https://github.com/FabioLeitao/tmux-configs)** | Personal tmux | Dotfiles; terminal productivity. |
| **[tosp-healthcheck](https://github.com/FabioLeitao/tosp-healthcheck)** | TOSP Healthcheck | Healthcheck service patterns. |
| **[wf_t1r](https://github.com/FabioLeitao/wf_t1r)** | Container Eclipse-Temurin com Wildfly Tunado para Testes | Java/infra; **Dockerfile** at repo root; Docker Hub `wildfly_t1r`. |

**Profile:** [github.com/FabioLeitao](https://github.com/FabioLeitao) — **27** public repositories (per `gh repo list`, non-archived); location Niterói; recent activity **data-boar**.

---

## 3. Certifications and community (for thesis/CV/pitch)

Add only what you are comfortable making reference to in docs; keep wording factual.

#### Public narrative hygiene (LinkedIn, CV, thesis)

- **Safe to cite in public profiles and talks:** institution names, program titles, years, workload (hours), public **edital** or catalog URLs, official **certificate validation** pages (when the issuer publishes a code), and high-level status (e.g. “awaiting convocation,” “in progress”).
- **Do not paste into GitHub, public issues/PRs, or open LinkedIn attachments:** CPF or national ID numbers, full **contract** scans, banking or payment lines, exam **registration** numbers, or unredacted PDFs that combine identity with competition data. Keep those only under **`docs/private/`** (see **`docs/private.example/`** layouts).
- **Dataprev (public competition):** Link to the **FGV concourse hub** and the **official Edital** PDF; describe placement and profile at **CV-level** abstraction. For personal screenshots or PDFs, use **`docs/private/`** and reference by filename in this file—not by pasting document contents here.
- **Dataprev classification “not showing” in this file:** If you shared a **classification screenshot or PDF** with the assistant, it is **not** reproduced here **by design** (PII / inscrição). The **same facts** you approve for public narrative (e.g. **6th** in the **Rio** vacancy, **not summoned**) are already in the **§3 table row** **DataPrev 2024**; keep **redacted** files only under **`docs/private/`** (e.g. `dataprev_status_2024_redacted.pdf`).
- **PUCRS / PUC-Rio:** Cite **course name**, **issuer school**, **hours**, and **validation** instructions the institution already publishes; do not quote **contract** clauses or ID fields in tracked docs.

| Item                                                                                                            | How to use                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----                                                                                                            | ----------                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **LPIC-1 (101)**                                                                                                | Certification; supports Linux/systems and infra narrative in thesis and bio.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **SRE Foundation (Quode)**                                                                                      | **SRE reliability baseline**; complements observability, incident, and production narrative next to CWL and Data Boar. **Workload:** **16 h**; conclusion **2022-12** per issued certificate. **Issuer:** [Quode](https://www.quode.com.br) (training partner; certificate title **SRE Foundation**). **Private PDF:** employer or personal copy only under `docs/private/` (e.g. `Quode_SRE_Foundation_2022.pdf`); do not commit Corporate-Entity-A OneDrive paths. |
| **SRE Practitioner (Quode)**                                                                                  | **Next step** after Foundation; strengthens SRE practice, error budgets, and ops narrative alongside Data Boar / production. **Workload:** **16 h**; conclusion **2023-03** per issued certificate (cohort **2003** on certificate filename). **Issuer:** [Quode](https://www.quode.com.br). **Private PDF:** only under `docs/private/` (e.g. `Quode_SRE_Practitioner_2023.pdf`); do not commit OneDrive paths. |
| **PUC-RS – IA e IoT**                                                                                           | Recent **extension** certificate (AI and IoT); supports ML/DL and “diverse data sources” narrative; PUC-RS adds academic weight for thesis and advisor outreach. **Course:** “Internet das Coisas, IA e a Revolução Conectada” (Escola de Negócios, **10 h/a**, Porto Alegre **2026-02-20**). Syllabus themes include IoT architecture, 5G/6G, **LGPD and data responsibility**, AI, smart cities. **Validation (public):** [PUCRS certificate validation](https://educon.pucrs.br/validarcertificado) using the code printed on the certificate. **Private PDF copy:** store under `docs/private/` only (e.g. `Certificado_IA_IOT_PUCRS.pdf`); do not commit. |
| **PUC-Rio (CCEC) – Compliance de Cibersegurança**                                                               | **Lato sensu–style** program (**480 h**, **EAD**, ingress **2026**). Aligns governance + cyber compliance narrative with CWL / Data Boar positioning. **Public catalog:** confirm current offering on [PUC-Rio Digital / CCEC](https://especializacao.ccec.puc-rio.br/). **Enrollment (active student):** the **Lyceum / Mais Campus** web app (`maiscampus.lyceum.com.br`, student login) shows **Ativo** for this program—use as **personal** proof of open enrollment; **do not** paste **RA**, **turma**, or portal URLs with session into Git. **Private:** contract/payment PDFs **and** optional redacted screenshot (name/RA/turma blurred or cropped) under `docs/private/` (e.g. `PUC_Rio_Lyceum_matricula_ativo_redacted.png`); **never** commit unredacted portal captures. |
| **Ubuntu tester / collaborator**                                                                                | Community contribution; supports quality, testing, and open-source narrative.                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Launchpad (Canonical/Ubuntu)**                                                                                | **[launchpad.net/~fabio-tleitao](https://launchpad.net/~fabio-tleitao)** (PresuntoRJ). Member since 2005-10-19; signed Ubuntu Code of Conduct. Teams: Ubuntu Brasil, Ubuntu Brazilian Security Team, Ubuntu Server Team, Launchpad Translators, Ubuntu on Rails. IRC: PresuntoRJ (Freenode #ubuntu, #ubuntu-br, etc.). **Location:** Niterói - RJ (Launchpad may still show Rio de Janeiro; that is stale). Languages EN, PT. Use for Ubuntu/community narrative and credibility.                                        |
| **RCDD BICSI** (former; renewal lapsed – expensive renewal, limited value in BR at the time; may renew someday) | Registered Communications Distribution Designer ([BICSI](https://www.bicsi.org/)). **File:** `docs/private/titulo-rcdd.jpeg`. Supports telecom/infra/cabling narrative; strong for CV and thesis background.                                                                                                                                                                                                                                                                                                             |
| **DataPrev 2024 – Analista de TI (Segurança Cibernética e Proteção de Dados)**                                  | Public competition **2024** (Edital **nº 1**, **5 Sep 2024**); **FGV** as executor. **6th** in classification for the **Rio de Janeiro** vacancy; **not yet summoned** (`NÃO CONVOCADO`) as of official candidate status consult. **Public links:** [FGV — Dataprev 2024](https://conhecimento.fgv.br/concursos/dataprev24); **situação dos concursados** on `dataprev.gov.br`. **Edital PDF:** public document—**do not** commit personal downloads to Git; cite URL or keep read-only copy outside the repo. **Private:** screenshots with CPF/inscrição only under `docs/private/` (e.g. `dataprev_status_2024_redacted.pdf`). |
| **Rio Brasil Terminal (Corporate-Entity-A Group) – Destaque do Semestre 2023.1 – TI**                                         | Employer **recognition** (“Highlight of the Semester”) for **Information Technology**, semester **2023.1**. Supports leadership / impact narrative alongside security ops. **Private:** keep scan or photo only under `docs/private/` (e.g. `RioBrasil_Terminal_destaque_2023_1_TI.pdf`); **do not** commit OneDrive paths or full personal-ID pages. |
| **Corporate-Entity-A LMS – Protect Yourself from Ransomware (with Quiz)**                                                     | Completed **2023-05-04**; security **awareness** / ransomware basics via employer LMS. **Private:** PDF copy under `docs/private/` only (e.g. `Corporate-Entity-A_LMS_Ransomware_2023.pdf`); original may stay on employer storage. |
| **Corporate-Entity-A LMS – Treinamento ISPS Code 18.3b**                                                                    | Completed **2025-05-23**; **~1 h** stated workload; **ISPS** (maritime / port facility security) alignment with terminal operations context. **Private:** PDF under `docs/private/` only (e.g. `Corporate-Entity-A_LMS_ISPS_Code_18_3b_2025.pdf`). |
| **Other communities / forums**                                                                                  | TrueNAS, FreeBSD (e.g. FUG-BR), Void Linux, Zorin Pro (paying user), etc. All count: they support infra, storage, BSD, minimal Linux, and ecosystem engagement. Add links or one-liners in §3 or here when you want them cited (no need to paste forum content).                                                                                                                                                                                                                                                         |
| *(Optional)* Other certs (e.g. LPIC-2, cloud, security)                                                         | Add a row here when you want them cited.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| *(Optional)* Talks, blog, articles                                                                              | Add URLs or one-liners here when you want them in the narrative.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

**Learning platforms (Udemy, Alura, etc.):** Certifications and courses from CV are listed in §3.2. We don’t have your full course/cert list from CV or LinkedIn here. For in-progress or paid-not-started, add or update `docs/private/Learning_and_certs.md` for prioritisation.

---

### 3.0 Study priority window (2026) — paid cyber + product proof first; AI / Anthropic alternating; CCA when eligible

**Intent:** **Cursor** (and whichever models the IDE uses) is the **delivery toolchain** for **this repo**—we do **not** assume the runtime product is “Claude-only.” **Stakeholder proof** stays **shipped Data Boar**, **compliance narrative**, **tests/docs/CI**, **releases**. **Already-paid cyber (CWL)** is the **main** structured cert lane to **finish**—it matches security, audit, and production-hardening story. **Anthropic Academy** (free) is a **useful alternating track** over the year (API, MCP, agent patterns—portable concepts even when the editor uses other providers). **CCA** remains a **later capstone** when Anthropic’s **experience bar** is met; partner perks affect **exam access/pricing**, not the free courses.

**CWL (primary paid lane):** §3.2 — start **BTF → C3SA**, then onward; **alternate** blocks with AI so neither track stalls.

**Suggested weekly cadence (operator-tunable):** **2** blocks **cyber (CWL)** + **1** block **IA** (Anthropic Academy ou outro); na semana seguinte **2** cyber + **1** **outro assunto** (ex.: tese, LGPD, doc de homelab, leitura de plano); **repetir** o ciclo até fechar marcos CWL. Se **faixa A** ou **release** pesarem, reduzir a 1+1 ou só manter o fio fino A.

**Anthropic Academy (secondary / alternating):** [Anthropic courses](https://docs.claude.com/en/docs/resources/courses) — [anthropic.skilljar.com](https://anthropic.skilljar.com/). Suggested sequence when you open that lane: **Claude 101** → **Building with the Claude API** → **Introduction to Model Context Protocol** (+ **Advanced** when relevant) → **Claude Code in Action** → **agent skills / subagents**.

**CCA exam (later):** [Claude Certified Architect — Anthropic Academy](https://anthropic.skilljar.com/claude-certified-architect-foundations-access-request); unofficial [guide](https://aitoolsclub.com/how-to-become-a-claude-certified-architect-complete-guide/). Schedule when prep + depth align—no fixed month.

**Optional third-party completion certs** (Cursor/AI on Coursera, Codecademy, etc.): CV polish only—not vendor proctored exams.

**Stakeholder line (short):** *Security and delivery evidence come first (paid cyber progress + shipped product + LGPD posture). AI ecosystem learning runs in parallel at a sustainable cadence; formal AI-vendor exams are a milestone when the bar is met—not the gate for credibility this quarter.*

| Phase                        | Focus                                          | Notes                                                                                                                                 |
| -----                        | -----                                          | -----                                                                                                                                 |
| **Primary (2026)**           | **CWL cyber track** + **release-backed proof** | Finish what you **already paid**; fixed blocks (1–2×/week). Same calendar: ship Data Boar slices.                                     |
| **Alternating**              | **Anthropic Academy** (or other AI courses)    | **Not** the top priority vs CWL; slot when energy/calendar allow—portable patterns (MCP, agents) still help this repo’s **workflow**. |
| **In parallel (thin)**       | **Priority band A** (–1, –1b)                  | Dependabot, Docker Scout, `check-all`—**M-TRUST**. [PLANS_TODO.md](PLANS_TODO.md).                                                    |
| **When eligible + prepared** | **CCA attempt**                                | Optional capstone; retake OK; notes in `docs/private/`.                                                                               |

**Tracked operator checklist:** [OPERATOR_MANUAL_ACTIONS.md](../ops/OPERATOR_MANUAL_ACTIONS.md) ([pt-BR](../ops/OPERATOR_MANUAL_ACTIONS.pt_BR.md)). **Sprint mirror:** [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) §3.1.

---

### 3.1 Certifications and learning – sequenced to-do (production + academic)

Use this when you (re)find **paid but incomplete** certs or want to pick **low-effort, high-gain** certs. Store your list in `docs/private/Learning_and_certs.md` (or similar); this section stays as the sequenced checklist.

| Order | To-do                                                                                | Why (production / academic)                                  |
| ----- | -----                                                                                | ----------------------------                                 |
| 1     | **List paid / incomplete certs** (platform, course name, link if any).               | So we don’t lose track; prioritise by effort vs gain.        |
| 2     | **Prioritise 1–2** as “low effort, high gain” for this cycle.                        | Focus beats scattering; one cert finished > three half-done. |
| 3     | **Complete the chosen cert(s)** and save proof in `docs/private/` (PDF/screenshot).  | Adds to §3 table and CV/thesis narrative.                    |
| 4     | **Update this file** (§3 table) and optional checklist in PLANS_TODO or TOKEN_AWARE. | Keeps portfolio and plans in sync.                           |

**Low-effort, high-gain (suggestions):** Prefer certs that support **both** production readiness and academic narrative: e.g. **LGPD / privacy / DPO awareness** (short courses, many on Udemy/Alura), **ISO 27001/27701 awareness**, **cloud fundamentals** (AWS/GCP/Azure free or low-cost), **security basics** (e.g. CompTIA Security+ prep, or platform-specific). Avoid long, expensive ones unless they’re already paid and near completion. When in doubt, finish one you’ve already paid for before buying new.

**Talent pool (trusted contributors):** Optional **role-archetype** mini-roadmaps (repo onboarding + career-aligned certs, including PUCRS supplements in section 3.3) live in **[`docs/TALENT_POOL_LEARNING_PATHS.md`](../TALENT_POOL_LEARNING_PATHS.md)** — **no** candidate names or LinkedIn data in that file; per-person notes stay under **`docs/private/`**.

---

### 3.2 CWL (CyberWarFare Labs) – paid courses in progress (from `docs/private/` images)

**Source:** Screenshots in `docs/private/`: IMG_6491–6499.jpg, signal-2026-03-18-035101.jpeg. Platform: **labs.cyberwarfare.live**. All listed below are marked "On Progress."

| Code        | Course                              | Why it helps (production / academic / certifiable confidence)                                                                                     |
| ----        | ------                              | -------------------------------------------------------------                                                                                     |
| **BTF**     | Blue Team Fundamentals              | Threat detection, incident response, security monitoring. **Foundation** for production readiness and defensive narrative; short, high leverage.  |
| **C3SA**    | Certified Cyber Security Analyst    | SOC analyst: detect threats, investigate incidents, analyze logs. Direct fit for **audit, logging, and certifiable confidence**; strong CV title. |
| **MCBTA**   | Multi-Cloud Blue Team Analyst       | Centralized logging, log analysis, threat detection on AWS/Azure/GCP. Supports **cloud-ready** app narrative and Data Prev / enterprise roles.    |
| **PTF**     | Purple Team Fundamentals            | Core of purple teaming (red + blue). Supports **balanced offensive/defensive** narrative for thesis and PUC-Rio Compliance de Cibersegurança.     |
| **MCRTA**   | Multi-Cloud Red Team Analyst        | Cloud red team, credentials enum/exploit, AWS/Azure/GCP. Complements MCBTA; good for **cloud security** depth and academic breadth.               |
| **CRTA**    | Red Team Analyst                    | Web/network exploitation, AD basics & attacks, pivoting. **Offensive** depth; informs defensive hardening of app and deploy pipeline.             |
| **CRT-ID**  | Red Team Infra Dev                  | OPSEC-safe infra, redirectors, payload servers, cloud/on-prem. Relevant to **secure deploy** (signing, repo, OPSEC) and production infra.         |
| **CRT-COI** | Red Team CredOps Infiltrator        | Windows creds (DPAPI, LSASS), credential dumping. **Defensive** value: understand cred handling for secure config/secrets in app.                 |
| **CPIA**    | Certified Process Injection Analyst | Process injection, persistence, evasion. Informs **app hardening** and "why signed/verified deploy" narrative.                                    |
| **CCSE**    | Cyber Security Engineer             | Broad: 50+ labs, OSINT to internal pentest. Strong **certifiable confidence** and CV; larger scope – do after 1–2 shorter certs.                  |

## How to use these for maximum value (your study, token-aware):

- **Studying is your task;** the agent does not do the learning. Use this section to decide **what** to do and **when**.
- **One cert at a time:** Finish one course fully (proof in `docs/private/`) before starting the next. "One done > three in progress" keeps narrative and CV clear.
- **Recommended order for goals (production + academic + certifiable confidence):**
  1. **BTF** → foundational blue team; fastest impact on "defensive readiness" and incident response.
  1. **C3SA** → SOC analyst; logs and detection; strong title for Data Prev / enterprise and thesis.
  1. **MCBTA** → multi-cloud blue; after BTF/C3SA for cloud and centralized logging narrative.
  1. **PTF** → purple team; bridges red+blue; good for thesis "balanced view" and PUC-Rio alignment.
  1. Then red/advanced as capacity allows: **MCRTA**, **CRTA**, **CRT-ID**, **CRT-COI**, **CPIA**; **CCSE** last or in parallel with one shorter one (broad, 50+ labs).
- **When to slot study in the sequence:** After **Dependabot/Scout** and **one feature slice** (e.g. Content type step 2 or Data source versions Phase 1), allocate **fixed study blocks** (e.g. 1–2 sessions per week). Do not mix deep study with same-day agent-heavy coding; keeps context and tokens manageable.
- **Evidence:** When you complete a CWL cert, save the certificate or completion screenshot to `docs/private/` (e.g. `CWL_BTF_certificate.pdf`) and add a row to §3 table (Certifications and community) so it feeds CV and thesis narrative.

---

### 3.3 Certifications and courses (from CV – LEITAO_Candidates_Resume_BR.pdf, p.2)

Source: **`docs/private/LEITAO_Candidates_Resume_BR.pdf`**, section "CERTIFICAÇÕES E CURSOS COMPLEMENTARES" (second page). Use for narrative, prioritisation, and §3.1 sequenced to-do.

| Platform / issuer       | Course / certification                                                                                                  | Year      |
| ------------------      | ----------------------                                                                                                  | ----      |
| PUCRS                   | Curso de Extensão IOT e IA - Revolução Conectada                                                                        | 2026      |
| IBM                     | Cybersecurity Fundamentals; On the Defense (MDL-407); On the Offense (MDL-405); Introduction to Cybersecurity (MDL-403) | 2024      |
| Certiprof               | Cyber Security Foundation Professional Certificate (CSFPC)                                                              | 2023      |
| IBM                     | Protect from Ransomware                                                                                                 | 2023      |
| Quode / DevOps Institute | SRE Foundation; SRE Practitioner                                                                                     | 2022–2023 |
| SOLAS                   | ISPS Code                                                                                                               | 2025      |
| Udemy                   | Ethical Hacking; Rust Completo; Python 3; Selenium WebDriver; Terraform with Ansible; Odin Bootcamp; Ansible SysAdmin   | 2023–2025 |
| Alura                   | Go (linguagem, OO, app web); Go e Gin API rest; AZ-900 Azure Fundamentals; SRE confiabilidade                           | 2023–2024 |
| LPI                     | LPIC-1 Exam 101                                                                                                         | 2008      |
| Microsoft               | Microsoft Certified Professional (70-271)                                                                               | 2000      |

#### PUCRS extension supplements (candidate list — confirm on official catalog)

**Before enrolling:** verify syllabus, workload, certificate validation (e.g. **educon.pucrs.br**), fees, and any prerequisites on the **official PUCRS** page for each offering. This block is **planning alignment only**, not a substitute for the institution’s rules.

| PUCRS course (name as listed)                      | Data Boar / delivery                                                                                                                                                                    | Lato sensu & thesis (compliance / cyber narrative)                                                    | CWL / technical cyber lane                                                                                | Suggested priority                                                                                     |
| ----                                               | ----                                                                                                                                                                                    | ----                                                                                                  | ----                                                                                                      | ----                                                                                                   |
| **Gestão do Conhecimento e Transformação Digital** | Strong fit: **knowledge** artifacts (reports, inventories), **digital transformation** story alongside the product; complements your completed **IA e IoT** PUCRS extension (§3 table). | High: bridges **governance**, **DPO-facing** evidence, and **organizational** context for the TCC.    | Low direct overlap; use as the **“other subject”** block in the weekly cadence (§3.0) when not doing CWL. | **1** — finish one paid lane (e.g. **BTF/C3SA**) slice first, then take this **one course at a time**. |
| **Compliance Criminal**                            | Medium: reinforces **Brazilian corporate criminal compliance** narrative; useful when pitching to **legal/compliance** buyers; little impact on code.                                   | High for **jurídico**-weighted thesis chapters (program integrity, accountability).                   | Some overlap with **defensive** mindset (risk, controls); does not replace CWL labs.                      | **2** — after or alongside thesis **background** drafting; avoid same month as heavy release.          |
| **Gestão de Mudança**                              | Medium: **rollout** of Data Boar in enterprises (adoption, resistance, comms); good for **professional services** and **implementation** storyline.                                     | Medium: TCC **discussion** on deploying technical controls in real orgs.                              | Low.                                                                                                      | **3**                                                                                                  |
| **A Escuta dos Excessos**                          | Medium: **ethics, proportionality, limits** of automated scanning — use carefully in **COMPLIANCE** wording; supports “**not exhaustive** / human review” positioning.                  | High if the thesis includes **fundamentos éticos** or **direitos fundamentais** vs surveillance tech. | Low.                                                                                                      | **3–4**                                                                                                |
| **Economia Circular**                              | Lower direct fit unless you frame **data lifecycle**, **retention**, or **ESG** reporting; optional for **sustainability** pitch.                                                       | Low unless advisor wants **ESG × dados** angle.                                                       | Low.                                                                                                      | **5** — only if thesis or employer explicitly values **circular economy** narrative.                   |

**How to slot without a new “plan file”:** Treat PUCRS extensions like §3.1 — **one completion at a time**; store enrolment and proof under **`docs/private/Learning_and_certs.md`**; after each certificate, add a row to the §3 **Certifications and community** table (issuer PUCRS, course title, year). Keep **CWL** as the **primary paid cyber** lane unless you deliberately pause it for a short PUCRS sprint; use the **alternating week’s “other” block** (§3.0) for PUCRS reading/assessment first.

#### PUC-Rio Digital extension courses (lato sensu benefit — verify contract)

**Catalog (public):** [PUC-Rio Digital — Cursos de extensão](https://especializacao.ccec.puc-rio.br/cursos-extensao) — short **Aperfeiçoamento** and **Cursos livres** (often up to ~30h). Titles and availability change; confirm syllabus, price, and schedule on the official page.

**Enrollment terms:** If your **especialização** includes a benefit (e.g. **up to two paid extension courses** and/or a **per-course value cap**), treat this table as **advisory only** until the **coordenação/secretaria** confirms **eligible offerings**, **deadlines**, and whether the cap is **per course** or **aggregate**. Store the **signed contract or PDF** only under **`docs/private/`** (see **`docs/private.example/academic/README.md`**); **do not** commit it to Git.

**Priority (aligned with Data Boar, professional narrative, and TCC):** Favour courses that add **governance / data / secure engineering** language without duplicating your existing deep Python–SRE stack.

| Priority | Offering (name on catalog) | Why |
| -------- | -------------------------- | --- |
| **1** | **Curso livre: Gestão e Governança de Dados** | Strong fit for **LGPD / ISO** narrative, inventory and **evidence** story, and **TCC** “fundamentação” — complements the product positioning. |
| **2a** | **Aperfeiçoamento: Qualidade de Software, Segurança e Sistemas Inteligentes** | Covers **quality, secure development, intelligent systems** — maps to hybrid detection, **CI/quality** habits, and defensible engineering claims. |
| **2b** *(alternative to 2a)* | **Curso livre: Desenvolvimento de Software Seguro** | Narrower **AppSec** focus if you prefer explicit secure-development framing over the broader aperfeiçoamento. |
| **3** | **Curso livre: Engenharia de Requisitos e Gestão Ágil de Produtos** | Use if the bottleneck is **product discovery, roadmap, and specs** rather than core cyber or data governance. |
| **Lower marginal gain (unless TCC explicitly needs the citation)** | **Machine Learning e Analytics** / **Curso livre: Machine Learning** | Useful for **formal curriculum alignment** with ML in the thesis; often **redundant** with existing hands-on depth — take only with a clear academic or credential goal. |

**Suggested two-course bundles (if both are contract-eligible and affordable):**

- **Default:** **Gestão e Governança de Dados** + **Qualidade de Software, Segurança e Sistemas Inteligentes**.
- **More AppSec-specific:** **Gestão e Governança de Dados** + **Desenvolvimento de Software Seguro**.

After completion, add a row to the §3 **Certifications and community** table (issuer **PUC-Rio Digital** / **CCEC**, course title, year) and keep receipts in **`docs/private/Learning_and_certs.md`**.

## For in-progress or paid-not-started, add or update `docs/private/Learning_and_certs.md`.

---

### 3.4 Education, monitoring, and technical background (for narrative / CV)

- **UFRJ (student):** Studied at UFRJ (taught by their professors). Worked at the **LCI Lab** during student years. **Monitored** students (helping the teacher and students who needed help with course content, classes, and IT lab).
- **UESA (Telecommunications):** While studying Telecommunications at UESA, **monitored and assisted** the Physics class.
- **Systems and platforms (early adoption and breadth):** Linux since kernel **0.96** (before Slackware), Novell NetWare 3 and later 4 (network servers), DOS 3.3 onward, Windows 3.1 onward, OS/2 Warp 3 and 4, OpenSolaris, AIX (RISC/6000 workstations), HP-UX, etc. Supports narrative of long-standing systems and infra experience across many OSes and eras.
- **Monitoring and custom sensors:** Hand-crafted custom sensors for **PRTG** (usually Bash), **Nagios** (usually Bash), and **Zabbix**. Fits SRE/observability narrative (CV already mentions PRTG, Zabbix, Uptime Colleague-Ma, etc.).
- **Security, backup, and infrastructure stack:** Deployed **Wazuh**; Symantec EPP and AV, **Backup Exec**; IBM Tivoli (including BladeCenter H cluster running **VMware**, 2010s). Avid **Proxmox** administrator; **Synology** solutions. **TrueNAS** admin (both BSD- and Linux-based). **UniFi** networking (dual WAN/load-balanced UniFi DM at home; also administered at office). **pfSense** at home and office: Suricata or Snort IDS/IPS, DNS/regional/proxy filtering and rules via pfSense packages. **Cisco ASA**, **Fortinet FortiGate**. **MISP** deployed for threat intelligence gathering (previous job). **Asterisk** SoftPBX deployment (VoIP and POTS lines). Supports security, hardening, threat intel, and compliance narrative (Data Boar, LGPD, cibersegurança).
- **Corporate-Entity-A (until departure):** **Tenable Nessus** and **CrowdStrike Falcon** for **monitoring, triage, response, mitigation**, and **documentation** of security alerts; **SLA** alignment with **Global IT (Manila)** requirements. Use in CV / “Formação e experiência” for **vulnerability management**, **EDR**, and **enterprise security operations** narrative (complements PUC-Rio Compliance / Data Boar positioning). **Rio Brasil Terminal (Corporate-Entity-A Group):** **Destaque do Semestre 2023.1 – TI** plus **LMS** completions (e.g. ransomware awareness **2023**, **ISPS Code 18.3b** **2025**) are listed in §3 with **private** PDF filenames—copy employer certs from OneDrive (or similar) into **`docs/private/`** if you want a single local evidence tree; **never** commit employer storage paths.
- **Languages (work and personal projects, including before GitHub and similar):** Pascal (Turbo, Borland, Delphi, Lazarus, FPC, etc.), C/C++, and some Visual Basic. **Scripting and current development:** Bash, Python, Expect; plenty of .bat, .cmd, VBS, and .ps1 (PowerShell) for Windows/systems automation; and the stack behind current work (e.g. Data Boar, Python, Go, Rust from CV). Supports narrative of long-standing programming practice, breadth of stacks, and evolution from desktop/legacy to modern tooling.

*No artifact to “fetch”; reference in bio and “Formação e experiência” when drafting thesis or pitch.*

---

### 3.5 Free / optional courses to consider (when capacity allows)

## Stanford – Transformers and Large Language Models (free, YouTube)
Official Stanford fall curriculum; full course on LLMs, 9 lectures. **Free on YouTube.** Relevant to: Data Boar's optional [dl] (sentence-transformers, embeddings), PUC-Rio's "IA" and "Gestão de Incidentes e Privacidade de Dados + IA" content, and academic/stricto sensu narrative. Consider when you have bandwidth; no cost, watch at your own pace.

| Aula | Topic                                      | YouTube                                     |
| ---- | -----                                      | -------                                     |
| 1    | Transformer                                | [Ub3GoFaUcds](https://youtu.be/Ub3GoFaUcds) |
| 2    | Modelos baseados em Transformer e técnicas | [yT84Y5zCnaA](https://youtu.be/yT84Y5zCnaA) |
| 3    | Transformers e Large Language Models       | [Q5baLehv5So](https://youtu.be/Q5baLehv5So) |
| 4    | Treinamento de LLMs                        | [VlA_jt_3Qc4](https://youtu.be/VlA_jt_3Qc4) |
| 5    | Ajuste fino de LLMs                        | [PmW_TMQ3l0I](https://youtu.be/PmW_TMQ3l0I) |
| 6    | Raciocínio em LLMs                         | [k5Fh-UgTuCo](https://youtu.be/k5Fh-UgTuCo) |
| 7    | LLMs agênticos                             | [h-7S6HNq0Vg](https://youtu.be/h-7S6HNq0Vg) |
| 8    | Avaliação de LLMs                          | [8fNP4N46RRo](https://youtu.be/8fNP4N46RRo) |
| 9    | Recapitulação e tendências atuais          | [Q86qzJ1K1Ss](https://youtu.be/Q86qzJ1K1Ss) |

**How to use:** Slot after CWL priority certs or in parallel with lato sensu if you want to deepen LLM/AI for thesis or future stricto sensu. No certificate to save unless you track completion yourself; can still cite "Stanford CS curriculum (Transformers & LLMs)" in CV or narrative if you complete the playlist.

## Harvard PLL – Machine Learning for Leaders (HKS Executive Education webinar)
Free, online, self-paced, ~1 hour. Harvard Kennedy School + SEAS; faculty Martin Wattenberg and Fernanda Viégas. Topics: machine learning basics for leaders and policy-makers, cybersecurity, public policy. [Course page](https://pll.harvard.edu/course/hks-executive-education-faculty-webinar-machine-learning-leaders). Fits Data Boar ML/DL narrative, PUC-Rio “IA”, and leadership/compliance angle.

## Harvard Online – CS50's Introduction to Cybersecurity
Introduction to cybersecurity (Harvard Online / CS50 series). [Course page](https://www.harvardonline.harvard.edu/course/cs50s-introduction-cybersecurity). Fits production readiness, certifiable confidence, and PUC-Rio Compliance de Cibersegurança / Data Prev narrative.

## Harvard PLL – Data Science: Visualization
Free*, online, 8 weeks, 1–2 h/week, self-paced (edX). ggplot2/R, visualization principles, communicating data-driven findings; part of Harvard’s Professional Certificate in Data Science. [Course page](https://pll.harvard.edu/course/data-science-visualization/2025-10). Fits Data Boar reports/heatmaps narrative and data-science credibility.

## Harvard PLL – Data Science: Productivity Tools
Free*, online, 8 weeks, 1–2 h/week, self-paced (edX). Unix/Linux, git, GitHub, RStudio, R Markdown; reproducible reports and project organization; part of Harvard's Professional Certificate in Data Science. [Course page](https://pll.harvard.edu/course/data-science-productivity-tools/2025-10). Fits production workflow and open-source (GitHub) narrative.

## Harvard PLL – Machine Learning and AI with Python
Free* (audit), online, 6 weeks, 4–5 h/week, self-paced (edX). Decision trees, random forests, ML models, Python libraries; data bias, overfitting/underfitting; SEAS. [Course page](https://pll.harvard.edu/course/machine-learning-and-ai-python). Fits Data Boar optional [dl] and ML sensitivity detection narrative; verified certificate $299 if desired.

## Harvard PLL – Data Science: Building Machine Learning Models
Free*, online, 8 weeks, 2–4 h/week, self-paced (edX). ML basics, cross-validation, popular algorithms, recommendation systems, regularization; part of Harvard's Professional Certificate in Data Science. [Course page](https://pll.harvard.edu/course/data-science-building-machine-learning-models/2025-10). Fits Data Boar ML/sensitivity detection and data-science credential narrative.

## Harvard PLL – Free courses catalog
Browse all free* courses (140+): filter by subject (Data Science, Computer Science, etc.), duration, school, difficulty. [Free courses](https://pll.harvard.edu/catalog/FRee). Use when you want to add more Harvard PLL options beyond the ones already listed above.

## Additional free resources:
- YouTube: [youtu.be/qHwIiwjrT1I](https://youtu.be/qHwIiwjrT1I) – add title/topic when you note it.
- **IBM SkillsBuild:** [activity/plan](https://skills.yourlearning.ibm.com/activity/PLAN-FA511CDFAF48) – add plan name/topic in `docs/private/Learning_and_certs.md` when you check it (fits with your existing IBM cybersecurity certs on CV).

---

## 4. Private docs (do not commit content)

Stored in **`docs/private/`** (git-ignored). Reference by **filename** only in plans.

### 4.1 PUC-Rio program (enrolled) – Compliance de Cibersegurança

Fetched from [PUC-Rio Digital – Compliance de Cibersegurança](https://especializacao.ccec.puc-rio.br/especializacao/compliance-de-ciberseguranca). Use for lato sensu thesis plan alignment (objectives, structure, TCC).

| Item                                | Detail                                                                                                                                                                                                                                                                                    |
| -----                               | ------                                                                                                                                                                                                                                                                                    |
| **Name**                            | Pós-Graduação em Compliance de Cibersegurança (Especialização Lato Sensu)                                                                                                                                                                                                                 |
| **Institution**                     | PUC-Rio (CCEC – Coordenação Central de Educação Continuada), formato PUC-Rio Digital                                                                                                                                                                                                      |
| **Duration**                        | 12 meses (ou 15 com Sprint de Aperfeiçoamento "Do Zero ao Código")                                                                                                                                                                                                                        |
| **Carga horária**                   | 480 horas                                                                                                                                                                                                                                                                                 |
| **Format**                          | 100% online; aulas gravadas + encontros ao vivo; certificação Lato Sensu PUC-Rio                                                                                                                                                                                                          |
| **Structure**                       | Sprints a cada 3 meses (3 disciplinas + 1 MVP por sprint). **Blocos:** (1) Segurança Ofensiva: Ameaças, Ataques e Crimes; (2) Segurança Defensiva: Gestão de Controles, Riscos e Continuidade de Negócio; (3) Gestão de Incidentes e Privacidade de Dados + IA; (4) Governança e Forense. |
| **LGPD / privacidade**              | Disciplina **"Gestão da Privacidade de Dados Pessoais (LGPD e RIPD)"** (30h) – princípios de privacidade, LGPD, GDPR, ferramentas de conformidade. Professores incluem Caitlin Mulholland (ex-CNPD, Diretora Dept. Direito PUC-Rio), Anderson da Silva.                                   |
| **Relevance to Data Boar / thesis** | Direct fit: compliance digital, privacidade de dados, governança de dados com cibersegurança, gestão de riscos. Thesis can frame Data Boar as artefato de apoio à conformidade e evidências (LGPD, ISO 27xxx) dentro deste programa.                                                      |

Optional: add official "Guia do Curso", ementa completa, or TCC norms to `docs/private/` when you have them.

**Open enrollment evidence (operator-only):** The **Lyceum / Mais Campus** student portal shows **Ativo** status after login. Keep any capture that includes **RA**, **turma**, or full name tied to ID fields **only** under `docs/private/` (redacted filename pattern in §3 table); do not commit portal screenshots to Git.

### 4.2 After the lato sensu at PUC-Rio – possible next steps

**Purpose:** Document the option to pursue **another course or track** after finishing the PUC-Rio Compliance de Cibersegurança (lato sensu). Makes sense as a natural continuation for production readiness, certifiable confidence, and academic career.

**Token-aware:** When deciding post-lato, open only this section (and the one plan or program link you are comparing). No need to open all academic plans in one session; pick one option at a time (low complexity / high gain).

| Option                                                               | What it is                                                                                                                                                                                                                                                                                                                              | Where it lives / what to add                                                                                                                                                                                                       |
| ------                                                               | ----------                                                                                                                                                                                                                                                                                                                              | ----------------------------                                                                                                                                                                                                       |
| **Stricto sensu (M.Sc. / PhD)**                                      | Research path building on Data Boar and the lato sensu thesis: research questions, methodology, experimental infrastructure, advisor outreach.                                                                                                                                                                                          | [PLAN_STRICTO_SENSU_RESEARCH_PATH.md](PLAN_STRICTO_SENSU_RESEARCH_PATH.md). Use lato sensu TCC and 1–2 papers as stepping stones; see plan §4 (early publications and advisor outreach).                                           |
| **Universidade do Intercâmbio (Harvard online + mestrado opcional)** | Escola/programa com cursos online de Harvard; possibilidade de mestrado opcional.                                                                                                                                                                                                                                                       | [Cursos online de Harvard](https://www.universidadedointercambio.com/cursos-online-de-harvard/). Add details (modalidade, duração, custo, requisitos do mestrado) to `docs/private/Post_lato_sensu_options.md` when you have them. |
| **Faculdade HUB – MBA em IA (+ Mestrado AGTU opcional)**             | MBA em Transformação de Negócios com IA Generativa (HUB, MEC); dupla titulação opcional com Mestrado em Negócios e IA (AGTU, Flórida). 12 meses, 100% online; sem TCC; inclui trilha de microcertificados Harvard/IBM/Babson, bootcamp presencial em SP (opcional). Pago (12x ou 18x); graduação completa exigida para o mestrado AGTU. | [MBA Inteligência Artificial – Faculdade HUB](https://pv.faculdadehub.com.br/mbaia0002/mba-inteligencia-artificial/). Add preço atual e condições to `docs/private/Post_lato_sensu_options.md` when you evaluate.                  |
| **Other course or program**                                          | A second specialization, MBA, or extension you are considering (e.g. another PUC-Rio program, or a different institution).                                                                                                                                                                                                              | When you have the link or name: add a row here and, if useful, a short note in `docs/private/` (e.g. `docs/private/Post_lato_sensu_options.md`) with URL, duration, and how it fits after Compliance de Cibersegurança.            |

**Suggested sequence (if it makes sense for you):** (1) Finish PUC-Rio lato sensu and TCC; (2) then choose one of: stricto sensu (M.Sc. track) per PLAN_STRICTO_SENSU, Universidade do Intercâmbio (Harvard online / mestrado opcional), Faculdade HUB (MBA em IA + mestrado AGTU opcional), or another course you have in mind; (3) CWL certs (BTF, C3SA, etc.) can run in parallel with the lato sensu as capacity allows, and will strengthen the narrative for whichever path you choose next.

---

- CV, TCC, LinkedIn: see [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) §3.
- **From Docker hub list of repositories.md** – authoritative list of Docker Hub repos (data_boar, wildfly_t1r, uptk).
- **Certificates:** **PUC-RS IA e IoT:** `Certificado_IA_IOT_PucRS_Fabio.pdf`. **RCDD:** `titulo-rcdd.jpeg`. Reference by filename in §3. |
- **PUC-Rio (recently enrolled):** Program fetched and summarised in §4.1 (Compliance de Cibersegurança). Optional: add TCC norms or enrollment confirmation (PDF/screenshot) to `docs/private/` (e.g. `PUC_Rio_program_requirements.pdf`). We’ll use it for the lato sensu thesis plan (objectives, structure, deadlines). |
- **Learning and certs (optional):** `Learning_and_certs.md` – list completed, in progress, and paid-not-started courses/certs (Udemy, Alura, etc.). Use for prioritisation and §3.1 sequenced to-do.
- Any new PDF/MD you add: add the filename to TOKEN_AWARE_USAGE §3 or to this section.

---

## 5. What to get next – recommendations

Use this when you can "try to get" something and want to prioritise. Ordered by **impact on the plans** and **realistic to obtain**.

| Priority | What to get                                            | Why it helps                                                                                                                     | Where to put it                                                                                                                                          |
| -------- | -----------                                            | ------------                                                                                                                     | -----------------                                                                                                                                        |
| **1**    | **Program / course requirements** (lato sensu)         | If you already have a program or course: official "estrutura do TCC", "critérios de avaliação", or "normas da ABNT" (1–3 pages). | `docs/private/` (e.g. `program_tcc_requirements.pdf`). Then we align thesis outline (PLAN_LATO_SENSU §1.2, §5.2) to it.                                  |
| **2**    | **1–2 redacted report excerpts** (Data Boar)           | One inventory sheet and one heatmap/summary (fake or anonymised data) as PDF or screenshots.                                     | `docs/private/` (e.g. `sample_report_inventory.pdf`, `sample_heatmap.png`). Thesis "case study" and "outputs" (PLAN_LATO_SENSU §4.2) can reference them. |
| **3**    | **Architecture diagram export**                        | TOPOLOGY.md is textual. One visual (Mermaid → PNG/SVG, or draw.io) "high-level components + scan pipeline" for the thesis.       | `docs/` (e.g. `topology-diagram.png`) or thesis folder. PLAN_LATO_SENSU §3.1 needs "1–2 architecture diagrams".                                          |
| **4**    | **Ubuntu / LPIC proof (optional)**                     | Link to your Ubuntu profile or "contributor" page; LPIC-1 (101) certificate scan or link if you want it cited.                   | Add URL or filename to §3 above; no need to commit certificate image.                                                                                    |
| **5**    | **Runbook or backup procedure** (from your experience) | Short "when app is down we check X; when we backup we do Y" (even bullet points).                                                | Paste into a note in `docs/private/` or send in chat; we turn it into the operator runbook and backup/restore text (PLAN_READINESS §4.3).                |
| **6**    | **Scenario one-liners** (case studies)                 | 1–3 sentences per scenario: e.g. "Empresa médio porte BR: 2 DBs PostgreSQL, 1 filesystem, foco LGPD Art. 37".                    | `docs/private/case_study_scenarios.md` or in chat. Feeds PLAN_LATO_SENSU §4.1–4.3.                                                                       |
| **7**    | **LGPD/ISO checklist** (if you have one)               | Any checklist or list of "evidence we need" from a course, employer, or DPO template (generic is fine).                          | `docs/private/` or paste; we map app features to each line (PLAN_COMPLIANCE_EVIDENCE_MAPPING).                                                           |
| **8**    | **Dockerfiles** (wf_t1r, uptk)                         | So we can say "Dockerfiles created and used" with a single reference.                                                            | `docs/private/Dockerfiles_used.md` (paste or paths) or ensure they're in the GitHub repos; add link in §1.                                               |

**Not required:** Real customer data, confidential configs, or anything that would expose PII. Anonymised, synthetic, or "inspired by" is enough for thesis and evidence mapping.

### What you said you'll grab – quick checklist

Use this to tick off as you find or add each item. Store files in `docs/private/` unless noted.

| Item                                                            | Where to put it                                                                                     | Status (you can tick) |
| ----                                                            | -----------------                                                                                   | --------------------- |
| **RCDD BICSI** (cert or proof)                                  | `docs/private/titulo-rcdd.jpeg`                                                                     | ✅ Added               |
| **PUC-RS IA e IoT** (cert PDF or PNG)                           | `docs/private/Certificado_IA_IOT_PucRS_Fabio.pdf`                                                   | ✅ Added               |
| Program / course requirements (lato sensu)                      | `docs/private/` e.g. `program_tcc_requirements.pdf`                                                 | ⬜                     |
| 1–2 redacted report excerpts (Data Boar)                        | `docs/private/` e.g. `sample_report_inventory.pdf`, `sample_heatmap.png`                            | ⬜                     |
| Architecture diagram (high-level + pipeline)                    | `docs/topology-diagram.png` or thesis folder                                                        | ⬜                     |
| Runbook or backup procedure (bullets)                           | `docs/private/` note or paste in chat                                                               | ⬜                     |
| Scenario one-liners (case studies)                              | `docs/private/case_study_scenarios.md` or chat                                                      | ⬜                     |
| LGPD/ISO checklist (if you have one)                            | `docs/private/` or paste                                                                            | ⬜                     |
| Dockerfiles note (wf_t1r, uptk)                                 | `docs/private/Dockerfiles_used.md` or links in GitHub                                               | ⬜                     |
| **Learning / certs list** (paid incomplete; Udemy, Alura, etc.) | `docs/private/Learning_and_certs.md` – then use §3.1 sequenced to-do to prioritise and complete 1–2 | ⬜                     |
| **DataPrev** (evidence of classification / 6th place)           | `docs/private/` e.g. `DataPrev_exame_classificacao.pdf` or screenshot – for CV and narrative        | ⬜                     |

*(Optional)* Ubuntu/LPIC proof: add URL or filename to §3; no file needed if you only cite the link.

---

## 6. What else you can add (optional)

- **Dockerfiles:** From wf_t1r or uptk (or a short note in `docs/private/Dockerfiles_used.md`) so “Dockerfiles I created and used” is citable.
- **GitHub:** If you create a repo for uptk or add more public repos, add one line per repo in §2.
- **Certifications:** LPIC-2, cloud (AWS/GCP/Azure), security (e.g. CEH, CompTIA), or others – add a row in §3.
- **Community:** Ubuntu membership level, other FOSS projects, conference talks – add a row or link in §3.
- **Blog / articles:** Links and one-line description in §3.

When you add something, update this file and, if it affects narrative or evidence, mention it in TOKEN_AWARE_USAGE §3 or in the relevant plan (lato sensu, stricto sensu, compliance evidence).

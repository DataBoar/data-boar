# Corporate-Entity-C review request guideline (code + docs + plans + language model)

**Nome curto (interno e ao encaminhar):** **WRB** — *Corporate-Entity-C Review Briefing*. Use em assunto ou mensagem, por exemplo: *“Pedido WRB — ciclo pós-2026-03-18”*, para identificar este tipo de pedido sem confundir com outros e-mails.

Use this template when asking Corporate-Entity-C for a new report after meaningful project changes.

**In-repo baseline paths (for reviewers — avoids “file not found” in reports):** [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md).

## Workflow when drafting a new WRB request (review + persist)

1. **Show for review:** surface the full message in the chat/UI so you can proofread before sending to Corporate-Entity-C.
2. **Persist in-repo:** save the same text in `docs/ops/Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md` (the “Prompt mestre completo” ````text`block) and mirror it in`docs/ops/Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md` when you use that package; **commit** so drafts are not lost to session history or clipboard issues.
3. **Validate (pt-BR + lint):** run `uv run pytest tests/test_markdown_lint.py::test_markdown_lint_no_violations tests/test_docs_pt_br_locale.py -q`. Portuguese prose must follow **Brazilian Portuguese** (`.cursor/rules/docs-pt-br-locale.mdc`, `docs-policy.mdc`, `operator-chat-language-pt-br.mdc`); English for paths, APIs, and established technical terms is fine.

*(PT-BR: ao criar um pedido, mostrar o texto na tela para revisão **e** gravar no repositório + commit + validar lint e locale pt-BR.)*

## Persistent operator tip (always include)

Always include a **concrete context reminder** in the request because external reviewers may
not fully preserve prior chat/report context.

Minimum reminder block:

- Last report date/version (for example: 2026-03-18, score 9.1/10).
- Source reference path for the prior report/tracking note.
- Explicit review window ("since last report until now").
- Key themes changed in this interval (code vs docs vs plans).
- **Release baseline vs current state** (see next section): last **GitHub Release tag** and **Docker Hub** image tag the project shipped to testers/partners/market, versus **today’s** repo/branch state (may include unshipped work).

## Release vs report vs cumulative (three different “since when”)

Ask Corporate-Entity-C to **not conflate** these baselines. They answer **different questions** and produce **different viewpoints**:

| Baseline                                                                          | Question it answers                                                                                                                                           |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cumulative / historical** (“todo acumulado”)                                    | Overall maturity and risk trajectory over the long run.                                                                                                       |
| **Last Corporate-Entity-C report** (e.g. PDF 2026-03-18)                                      | What changed **since their last recommendations** — what we **treated**, **planned**, or **left pending** in dialogue with them.                              |
| **Last public release** (GitHub `vX.Y.Z`, Docker Hub `:X.Y.Z` / `:latest` digest) | What changed **since we last delivered** to testers, partners, or the market — the last **identifiable** cut (often **not** the same date as the Corporate-Entity-C PDF). |

**Typical case:** last report ≈ mid-March 2026; latest shipped release in repo today is often `**v1.6.7`** (confirm from `README`, `docs/releases/1.6.7.md`, GitHub Releases, Docker Hub). `**main` may be ahead of the tag** — call that out explicitly.

## How they can discover the release baseline (artifacts in repo — no need to guess):

- `README.md` / `docs/releases/X.Y.Z.md` — shipped version narrative.
- GitHub **Releases** / tags (e.g. `v1.6.7`).
- Docker Hub tags + digest notes in `docs/deploy/` or release notes.

## What to ask them to produce:

1. **At last Corporate-Entity-C report:** infer **which release** the repo likely reflected (or state “unclear” and use tag history).
2. **Latest tagged release today** (GitHub + Docker Hub as applicable) vs **current `main` / default branch** (unshipped commits, open PR themes).
3. **Since last delivery to market/testers/partners** (delta from last tag → now): what landed in repo **after** that tag — distinct from “since last Corporate-Entity-C PDF” alone.
4. **Since last Corporate-Entity-C recommendations:** what we **addressed**, **partially addressed**, or **planned** vs **net-new gaps** in this review.
5. Keep **roadmap** and **optional annex** separate from these baselines so readers do not mix “shipped” vs “planned”.

## When to request a new Corporate-Entity-C report

Request **immediately** when one or more apply:

- Trust/integrity behavior changes (`runtime_trust`, tamper/adulterated/tinted semantics).
- SQLite evidence model changes (audit trail, integrity events, session seals/hashes).
- Licensing enforcement changes (tiers, feature gating, kill switch).
- Report validity changes (limited rows, draft/tinted outputs, trust marks in report info).

Request as a **planned checkpoint** when one or more apply:

- ~8+ files changed in one feature slice.
- ~250+ net LOC in critical modules/docs.
- 2+ plan files updated with new milestones or dependencies.
- New operator-facing behavior in CLI/API/reporting plus docs updates.

Fallback cadence:

- Every 2 sprints, or every 4-6 weeks.

Version-signal heuristic (to avoid timing confusion):

- If working version is `**X.Y.Z-beta`**, treat as “promising but still early”; request now only if you need external feedback before feature stabilization.
- If working version reaches `**X.Y.Z-rc`**, treat as a **clear checkpoint** where requesting Corporate-Entity-C review is usually worth considering before final publish.
- Keep report text explicit about **working version** vs **latest published tag/image** so reviewers do not conflate branch tip with market release.

## What to ask Corporate-Entity-C to focus on (beyond usual checks)

- Evidence chain-of-custody quality (runtime -> SQLite -> export -> report).
- Trust-state clarity for operator/client (INFO vs WARN/ERROR and ambiguity risk).
- Anti-misuse posture (tinted/draft mode, limited output strategy, forensic value).
- Monitoring/off-band design (webhook-first architecture, Zabbix/PRTG/Nagios/Splunk fit).
- Legal/commercial wording risk (tamper-evident vs tamper-proof claims).
- Prioritization sanity (best risk reduction per implementation step).
- Code-as-truth discipline: flag any doc/plan claim not grounded in current implementation/tests.
- Audience-fit quality: check if executive/legal text stays decision-ready while operator docs remain concrete how-to.
- Roadmap representativeness: verify whether current priorities are visible for SMB, mid-market, and enterprise buyers without overclaim.

## Time-scope framing (request multiple lenses)

Always ask Corporate-Entity-C to analyze in **at least these lenses** (they complement each other):

1. **Cumulative trajectory** — long-horizon maturity and risk (“visão acumulada”).
2. **Delta since last Corporate-Entity-C report** — what we did with their prior recommendations + new findings (“desde o último relatório deles”).
3. **Delta since last public release** — what changed **after** the last GitHub/Docker deliverable to testers/partners/market, including **unshipped** work on `main` if ahead of tag (“para onde já fomos desde a última entrega”).

This helps catch interval regressions, separates **market-facing delivery** from **review-cycle progress**, and avoids confusing **tagged release** with **current branch tip**.

### Ask for this explicit structure in their output

- **Interval progress (since last report):**
- What was shipped in code/docs/plans.
- What improved vs what regressed.
- New risks introduced unintentionally.
- **Cumulative progress (historical):**
- Maturity trend across reports.
- Security/quality trend (improving, flat, degrading).
- Recurrent weak spots still unresolved.
- **Since last tagged release (market/testers/partners):**
- Name the tag (e.g. `v1.6.7`) and date from repo/GitHub/Docker artifacts.
- Summarize commits/themes **after** that tag until current branch tip (even if not re-released).
- Note whether “current product” for a buyer is still **1.6.7** or already **ahead** on `main`.
- **Taxonomy of effort in the interval:**
- Security hardening
- Integrity/evidence
- Feature delivery
- Documentation/governance
- Ops/observability
- Refactoring/quality debt
- **Regression and drift checks:**
- Potential behavioral regressions.
- Code-doc-plan drift.
- Increased ambiguity in operator/legal narrative.
- **Prior recommendation verification:**
- Which recommendations from the previous report were fully addressed.
- Which were partially addressed or still pending.
- Whether fixes seem correct/effective (not just "implemented").
- A simple progress score per prior recommendation (e.g. 0-100% or Not started/Partial/Done/Validated).

## Report format requested from Corporate-Entity-C (3 views / chapters)

Ask Corporate-Entity-C to return a **single PDF** (or a small bundle) with at least these 3 sections:

1. **Executive / managerial view** (max 2 pages)
  - Audience: IT director, legal/compliance leadership, partner stakeholders.
  - Low-technical summary: progress, key risks, confidence level, business impact.
  - Top recommendations prioritized by urgency and expected risk reduction.
  - Avoid deep technical detail; focus on decisions and governance.
2. **Technical detailed view** (full analysis)
  - Delta since last report + cumulative trajectory.
  - Code/docs/plans consistency, regressions, new risks, trend lines.
  - Linguistic category model analysis (abstraction vs concreteness by artifact/audience).
  - Clear evidence and rationale for each recommendation.
3. **DevSecOps hardening view** (security-focused)
  - Vulnerabilities, hardening gaps, dependency/package update guidance.
  - Security posture trend and practical remediation sequence.
  - Prioritized action plan intended for sprint/task segmentation.
  - Should be explicit enough for direct use by engineering/devsecops workflows.

Prefer that all recommendations (especially chapter 3) are tagged by:

- Critical / Important / Improvement
- Quick win / medium effort / structural change
- Next sprint / next 2-4 sprints / backlog

## Optional annex: Corporate-Entity-C roadmap ideas (separate from “what we built” analysis)

This is **not** a review of existing work; it is **forward-looking** and should be clearly labeled in the PDF so it is not confused with findings grounded in the current codebase.

Ask Corporate-Entity-C (if they can) to add a **short optional section or appendix**, e.g. **“Corporate-Entity-C optional roadmap tips”**, containing:

- Ideas for **capability gaps** we may not have considered yet.
- Suggestions that help move Data Boar toward **production-ready** posture for target markets.
- Anything that could make us **less competitive** if left unaddressed (ops, compliance narrative, packaging, SLAs, partner onboarding, etc.).

Rules for this annex:

- Mark every item as **optional / speculative** and **not** derived from mandatory analysis of shipped code.
- Keep it **separate** from chapters 1–3 (or place it after chapter 3 with a distinct heading).
- Prefer **prioritized** bullets (impact vs effort) so we can triage into backlog without mixing with verified gaps.

## Linguistic category model check (mandatory section)

Ask Corporate-Entity-C to explicitly evaluate abstraction vs concreteness:

- Plans: abstract/structural level (intent, sequencing, trade-offs).
- Operator docs: concrete/procedural level (steps, commands, expected behavior).
- Compliance/pitch: controlled abstraction (value/risk/governance) without overclaim.

Ask them to flag where text is:

1. Too abstract (not verifiable),
2. Too concrete in the wrong artifact (implementation detail in executive/legal text),
3. Ambiguous about current state vs roadmap.

## Reusable request message (long form)

```text
Hi Corporate-Entity-C team,

We’re grateful for the depth of your 2026-03-18 and 2026-03-23 reviews — they’ve been a constructive compass for Data Boar (detection, tests, compliance narrative, release discipline). If earlier context was lost on your side, no problem: this message plus docs/ops/Corporate-Entity-C_IN_REPO_BASELINE.md and docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md are the single source of truth for what we captured from your work. We’re asking for a forward-looking pass on today’s tree, not re-litigating past threads.

We are sending this WRB request again; an earlier message may not have reached you. Please treat this message (and the linked in-repo briefing paths below) as the single source of truth — we do not assume you retain context from a prior thread. Our last report from you remains the 2026-03-18 delivery; tracking: docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md.

Please run a new review cycle with your usual overall progress/maturity/security view, plus focused analysis on trust/integrity/evidence hardening.

Please separate your review by artifact type:

1) CODE (already implemented)

* Runtime trust signaling in CLI and audit export baseline.
* Explicit unexpected-runtime warning surface.
* Related tests for baseline behavior.

2) DOCUMENTATION (roadmap/narrative)

* Compliance/legal and operator-facing wording updated for trust/evidence roadmap.
* Pitch/private narrative updated for enterprise audit value.
* Usage and planning docs synchronized with recent trust/integrity direction.

3) PLANS (not fully implemented yet)

* Escalation policy for compromised state messaging (WARN / non-blocking ERROR).
* Tinted/draft session/report behavior and optional limited-report mode.
* Session trust seal/hash and pre-report integrity verification.
* Off-band trust-event alerts and monitoring bridge patterns.
* Completeness of backlog and possible sequencing priority of the documented future tasks and actions and slices (docs/plans/PLANS_TODO.md and docs/plans/SPRINTS_AND_MILESTONES.md for overview, any other /docs/plans/*.md for further details if necessary and drill down analysis)

Besides your standard checks, please focus on:
A) Consistency between code, docs, and plans for integrity/evidence claims.
B) Chain-of-custody gaps that could still allow "valid-looking" manipulated outputs.
C) Operator/client signaling quality (clear severity and actionability).
D) MVP sequencing for maximum legal/technical risk reduction.
E) Wording risks: avoid overclaim; keep tamper-evident boundaries explicit.
F) Linguistic category model:

   - Is each artifact at the right abstraction level for its audience?
   - Where are we too abstract, too concrete, or ambiguous?
   - Suggest rewrites that improve traceability (claim -> evidence) and audience clarity.
   - Suggest rewrites to address proper translations in different locales (where code is the "source of truth", from that we get EN documentation and help reflecting actual capabilities or functionalities, and from EN we get pt_BR documentation).
   - Suggest rewrites for better adherence to pt_BR instead of drifting accidentally into pt_PT style, wording and phraseology.
   - Suggest Glossary entries.

G) Time-scope analysis (three lenses — do not merge):

   - Cumulative history (long horizon).
   - Since last Corporate-Entity-C report (recommendations addressed vs pending vs planned).
   - Since last GitHub/Docker tagged release (last market-facing delivery → now, including unshipped `main` if applicable).
   - State explicitly: latest **published Git tag** (verify in the repo; `main` may already show a **pre-release** suffix or a **next patch/minor** while the published tag still reflects the last delivery, but it looks like "since last release” means tag v1.6.8, unless confirmed by a newer tag indicating stable release at GitHub, not alpha, beta or release-candidate) vs current branch tip (git rev-parse --short HEAD shows ca41774 right now).
   - We don’t have your internal clone SHA; as a reference point on our public main, the tip at the end of 2026-03-18 was approximately 3a7b59d (see our git history for that date if you do not have the full context of the last report).
   - Highlight interval regressions, newly introduced risks, and trend direction.
   - Classify interval work by effort taxonomy (security/integrity/features/docs/ops/refactor/ci).

H) Prior recommendation verification:

   - Confirm whether previous recommendations were correctly addressed.
   - Mark each as Not started / Partial / Done / Validated and include a progress score.
   - Flag any "false sense of closure" where implementation exists but effect is weak.

Please return findings grouped as:

* Critical / Important / Improvement
* Short term (next PR) / Mid term (2-4 PRs)
* Code / Docs / Plans
* Keep a 3-part report format: executive (<=2 pages), technical detailed, and DevSecOps hardening.

I) Optional annex — "Corporate-Entity-C roadmap tips" (separate from analysis of what we already shipped):

   - Forward-looking ideas for capability gaps, production-readiness, and market competitiveness.
   - Clearly labeled as optional/speculative; not confused with evidence-based findings from chapters 1–3.
   - Prioritized for triage (impact vs effort).
   - Recommend what should be prioritized for high cognitive AI agent assistence in Cursor (via API, only after token refil, due to high cost of token, but high value reward, such as Premium, Opus 4.6, GPT 5.3 Codex, MAX Mode, etc.) vs normal pace using auto AI agent in cursor (token aware behavior)

Thanks.
```

## Prompt mestre completo (PT-BR) — copiar para e-mail ou colar em IA

**Pacote para envio:** matriz de conformidade (guideline × *long form*), texto pronto para colar e modelo WhatsApp em `[Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md)`.

Use este bloco como **pedido único, completo e em prosa**. Pode ser colado em e-mail, ticket ou como **prompt de IA** para um assistente que prepara o relatório: o texto abaixo articula intervalos temporais, capítulos, focos e formato de saída, em tom profissional e cordial.

**Antes de enviar:** ajuste apenas se necessário a data do último relatório Corporate-Entity-C, o caminho do PDF local e o nome do branch padrão; **não fixe** número de versão sem conferir `README.md`, `docs/releases/`, GitHub Releases e Docker Hub — ou peça explicitamente que o revisor **derive** a última tag do repo.

```text
Olá, equipe Corporate-Entity-C,

Esperamos que se encontrem bem. Viemos por este meio solicitar, com o máximo de apreço pelo trabalho que vocês já nos dedicaram, um novo relatório de revisão e recomendações sobre o projeto Data Boar (repositório no GitHub e imagens publicadas no Docker Hub, quando aplicável).

O texto abaixo funciona como um briefing único: pode orientar a própria análise de vocês ou servir de base para quem estruture o relatório (incluindo assistentes de IA), sempre com o rigor e a educação que o assunto merece. Nada aqui pretende ser uma ordem; são pedidos e sugestões de foco, que vocês podem adaptar conforme a metodologia de vocês.

Resumo (âncora rápida):

- Novo relatório de revisão e recomendações sobre o Data Boar.
- Briefing único; sugestões adaptáveis à metodologia de vocês (não instruções rígidas).

---

Contexto e fonte de verdade

Sabemos que conversas e e-mails não preservam todo o contexto. Por isso, seria muito valioso para nós que a análise se apoie, sempre que possível, nos artefatos do repositório — código, documentação, planos, notas de release, tags no GitHub, configuração de imagem e CI — e não apenas na memória do último contato. Como referência não exaustiva, mencionamos README, docs/releases, docs/plans/PLANS_TODO.md, tags e releases no GitHub, Dockerfile e documentação de deploy, pyproject.toml, SECURITY.md e os fluxos de trabalho de integração contínua. Se algo no repositório estiver mais atualizado do que este e-mail, pedimos que prevaleça o que estiver no repo.

Resumo (âncora rápida):

- Priorizar evidência no repositório (código, docs, releases, CI) em relação a este e-mail.
- Lista de caminhos acima é exemplificativa, não fechada.

---

Referência ao último relatório de vocês

Para não perder o fio da meada, lembramos o relatório anterior de vocês com data de referência em 18 de março de 2026, com nota global de 9,1 em dez na nossa anotação interna. O acompanhamento no repositório está em docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. O PDF correspondente, quando existir no ambiente do operador, costuma estar na pasta de feedbacks e revisões com nome semelhante a analise_evolucao_data_boar_2026-03-18.pdf.

Seria extremamente útil que, neste novo ciclo, vocês retomassem as recomendações daquele relatório e nos ajudassem a perceber o que já foi plenamente atendido, o que ficou em parte, ou o que ainda permanece em aberto — tema que desenvolvemos mais adiante neste pedido.

Se possível, pedimos também que indiquem logo na abertura do novo relatório qual foi o marco técnico de comparação que vocês adotaram (por exemplo PR principal e/ou commit-base), junto da data do último relatório, para facilitar a consciência de contexto e rastreabilidade da análise.

Resumo (âncora rápida):

- Último relatório Corporate-Entity-C: 2026-03-18; tracking em Corporate-Entity-C_ANALISE_2026-03-18.md.
- Pedido: retomar recomendações daquele ciclo e distinguir atendido / parcial / aberto.
- Na abertura do novo PDF: explicitar data de referência + PR/commit-base usado na comparação.

---

Três ângulos temporais que pedimos para não confundir

Três perguntas diferentes pedem três camadas de narrativa distintas no relatório de vocês. Pedimos gentilmente que não as misturem, porque cada uma responde a um público e a uma decisão de produto diferente.

Primeiro, a visão histórica acumulada: como vocês enxergam a maturidade do produto, a tendência de risco e a narrativa de longo prazo, como já costumam fazer.

Segundo, o que mudou desde o último relatório de vocês: o que já tratamos, o que planejamos explicitamente, o que deixamos pendente; e, sobretudo, se as recomendações anteriores foram corrigidas de forma eficaz ou apenas formalmente.

Terceiro, o que mudou desde a última release pública que identificarem no GitHub (tag de versão) e na imagem Docker correspondente, até o estado atual do branch principal. Se ainda houver commits no branch principal após a última tag, esse trabalho ainda não foi “entregue” como nova versão nomeada a testadores, parceiros ou mercado; pedimos que isso fique explícito, para que ninguém confunda o que o mercado instala com o que o repositório já contém hoje.

Resumo (âncora rápida):

- Camada 1 — acumulado histórico (maturidade e tendência).
- Camada 2 — desde o último relatório Corporate-Entity-C (tratamento das recomendações deles).
- Camada 3 — desde última tag GitHub/Docker até o tip do branch (inclui trabalho ainda não “retagueado”).

---

Código, documentação e planos

Pedimos que considerem, onde fizer sentido para vocês, uma leitura articulada em três famílias de artefatos. No código, interessa-nos qualidade, clareza, cobertura de testes, possíveis regressões, riscos de segurança e consistência de comportamento entre CLI, API e relatórios. No nosso roadmap recente, temos atenção a temas de confiança de runtime, trilha de auditoria exportável e integração com licenciamento e integridade, quando aplicável.

Na documentação, agradecemos qualquer observação sobre operação (USAGE, deploy, SECURITY), material de compliance e jurídico, e pitch ou material privado se for referenciado. Onde existir par inglês e português, a sincronização e a clareza para o operador são importantes; e, no texto jurídico ou de compliance, evitar overclaim em relação ao que o produto já garante de fato.

Nos planos, em docs/plans e em PLANS_TODO.md, interessa-nos a coerência entre roadmap, dependências entre iniciativas e distinção clara entre o que já está entregue e o que ainda é intenção futura, para que o leitor não confunda planejamento com produto disponível.

Resumo (âncora rápida):

- Código: qualidade, testes, segurança, consistência CLI/API/relatório; temas de confiança e auditoria quando relevante.
- Documentação: operação, compliance, i18n; sem overclaim.
- Planos: roadmap vs entregue; dependências entre iniciativas.

---

Modelo linguístico e níveis de abstração

Ficaríamos gratos se, no capítulo técnico, pudessem dedicar um espaço ao que chamamos de modelo linguistic category: ou seja, se o nível de abstração está adequado a cada tipo de documento e audiência. Em linhas gerais, os planos tendem a ser mais estruturais; a documentação operacional, mais concreta; o material de compliance e pitch, uma abstração controlada em valor e risco, sem prometer o que ainda não está implementado. Sempre que possível, apontar trechos abstratos demais para serem verificáveis, trechos concretos demais no lugar errado, ou ambiguidade entre estado atual e roadmap seria uma contribuição enorme.

Resumo (âncora rápida):

- Avaliar abstração por tipo de documento e audiência.
- Sinalizar trechos demasiado abstratos, demasiado concretos no lugar errado, ou ambíguos (atual vs roadmap).

---

Pontos de atenção que nos preocupam além do habitual

Além da maturidade geral, segurança e vulnerabilidades que vocês já costumam cobrir, pedimos atenção especial, se o tempo de vocês permitir, a: cadeia de confiança e evidência do runtime ao SQLite, exportação e relatório; clareza de severidade para operador e cliente; linguagem adequada entre tamper-evident e tamper-proof; encaixe futuro de observabilidade e alertas off-band; e drift entre código, documentação e planos, incluindo regressões que não apareçam como falhas de teste.

Resumo (âncora rápida):

- Além do “checklist” habitual: evidência ponta a ponta, severidade, wording jurídico defensável.
- Observabilidade/alertas (futuro) e drift código/docs/planos.

---

Retorno sobre as recomendações do relatório anterior

Para cada recomendação relevante do relatório de 18 de março de 2026 que vocês retomarem, seria muito útil receber um estado resumido (por exemplo não iniciado, parcial, concluído ou validado), uma nota de progresso em que façam sentido, e um comentário honesto se a correção parece efetiva ou apenas formal — incluindo o caso em que a sensação de “feito” não corresponde ao efeito real.

Resumo (âncora rápida):

- Por recomendação retomada: estado, nota de progresso, comentário “efetivo vs formal”.
- Chamar atenção para falso “feito” quando o problema persistir.

---

Formato do entregável que imaginamos

Se for viável para o fluxo de vocês, imaginamos um único PDF, ou um pacote mínimo equivalente, com três capítulos principais e um anexo opcional.

O primeiro capítulo seria uma visão gerencial ou executiva, idealmente nas primeiras duas páginas, dirigida a direção de TI, jurídico ou compliance e parceiros de negócio, com progresso, riscos-chave, impacto e prioridades de decisão, sem mergulho técnico profundo.

O segundo capítulo seria a visão técnica detalhada, integrando os três ângulos temporais que descrevemos, o tratamento de código, documentação e planos, o modelo linguístico, os pontos de atenção, a verificação das recomendações anteriores, tendências, regressões e qualidade de código e testes onde aplicável.

O terceiro capítulo seria dedicado a DevSecOps e hardening: vulnerabilidades, dependências, orientações de atualização de pacotes e uma sequência de remediação que possamos alinhar a sprints ou backlog de segurança.

Sempre que possível, agradeceríamos que as recomendações viessem acompanhadas de uma indicação de severidade, esforço aproximado e janela de tempo sugerida, e, quando fizer sentido, uma classificação do tipo de esforço (por exemplo segurança, integridade e evidência, funcionalidades, documentação e governança, operações e observabilidade, ou refatoração e dívida técnica).

Resumo (âncora rápida):

- Cap. 1 — executivo (≤2 páginas): TI, jurídico, parceiros.
- Cap. 2 — técnico: integra tudo o que pedimos acima.
- Cap. 3 — DevSecOps: vulnerabilidades, deps, priorização para sprint/backlog.
- Opcional: severidade, esforço, janela, taxonomia de tipo de trabalho.
- No início do PDF: registrar baseline de contexto (data do último relatório + PR/commit-base).

---

Anexo opcional de ideias de roadmap

Se a metodologia e o tempo de vocês permitirem, um anexo separado com ideias especulativas de lacunas de capacidade e caminhos para um produto production-ready e competitivo nos mercados que visamos seria bem-vindo. Pedimos que esse anexo fique claramente identificado como opcional e especulativo, separado dos achados que vocês fundamentam diretamente no código e na documentação atual.

Resumo (âncora rápida):

- Anexo separado, claramente opcional e especulativo.
- Ideias de lacunas e production-ready; não misturar com achados evidenciados no repo.

---

Encerramento

Agradecemos de antemão a paciência e o rigor de sempre. Qualquer ajuste deste briefing ao que for mais natural para o processo de vocês é bem-vindo. Permanecemos à disposição para esclarecimentos.

Com estima,
Fabio Leitao
Equipe Data Boar
```

---

## Versão resumida (PT-BR) — só quando o canal for curto

Use quando não couber o prompt mestre; o destinatário deve saber que o **briefing completo** está em `docs/ops/Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md` (seção “Prompt mestre completo”).

```text
Olá, Corporate-Entity-C. Pedimos gentilmente um novo relatório Data Boar; o briefing completo está em docs/ops/Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md (seção Prompt mestre). Referência do último relatório de vocês: 2026-03-18 (notas em docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md). Por favor, três camadas de tempo separadas: histórico acumulado; desde esse relatório com retorno sobre recomendações anteriores; desde a última release GitHub/Docker até hoje (main pode estar à frente do tag). PDF em três capítulos conforme o briefing, mais anexo opcional de ideias de roadmap. Muito obrigado.
```

## Optional short request (chat/IM)

```text
Can you run a new review with your normal maturity/security overview, but focus on trust/evidence hardening across code+docs+plans? Please assess chain-of-custody gaps, compromised-state signaling (INFO/WARN/ERROR), tinted/draft policy, session seals, and monitoring alerts. Also evaluate our linguistic category model (abstraction vs concreteness by audience) and suggest rewrites where text is too abstract, too concrete, or ambiguous.
```


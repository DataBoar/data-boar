# Plano: Interface de plugin de remediação pós-scan (Enterprise)

<!-- plans-hub-summary: Ponte Enterprise de remediação — #649 manifest + #606 hook + #1443 JSONL; v1.8.0 #1057 mapeia classes de política/anonimizador no contrato de plugin existente; Phase 2 FPE e Phase 3 verify ainda abertos -->
<!-- plans-hub-related: PLAN_PLUGIN_SDK.md, PLAN_PLUGIN_PARTNER_INTERFACE.md, PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md -->

**Status:** Ativo (ponte em `main`; o survey v1.8.0 [#1057](https://github.com/DataBoar/data-boar/issues/1057) enriquece este plano — não arquivar)
**Data:** 2026-05-19 (onda v1.8.0: 2026-08-27)
**Autores:** Fabio Leitao
**Prioridade:** H1
**Milestone:** v1.8.0

**GitHub:** [#601](https://github.com/DataBoar/data-boar/issues/601) · [#606](https://github.com/DataBoar/data-boar/issues/606) · [#649](https://github.com/DataBoar/data-boar/issues/649) · [#1057](https://github.com/DataBoar/data-boar/issues/1057) (enriquecimento v1.8.x: anonimizador / políticas)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

**Relacionado:** [USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md), [USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md), [PLAN_G_TIER.pt_BR.md](PLAN_G_TIER.pt_BR.md), [PLAN_PLUGIN_SDK.md](PLAN_PLUGIN_SDK.md) (guia do parceiro **#611**), [PLAN_PLUGIN_PARTNER_INTERFACE.md](PLAN_PLUGIN_PARTNER_INTERFACE.md) (L1/L2/L3 + esquemas L3 — **#695**), [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) (ações sugeridas — sem escrita automática)

---

## Problema

**Discovery** e **reporting** open-core já existem; **remediação** (tokenizar, mascarar, criptografar no lugar) é específica de parceiro. Sem **contrato de plugin estável**, cada integração bifurca o core e quebra a narrativa de auditoria.

---

## Objetivo

Definir hook **Enterprise** pós-scan que:

1. Recebe **mapa estruturado de findings** (localização + `pii_type` + id estável).
1. Invoca **plugin de terceiro** registrado (tokenização, masking, pseudonimização, criptografia de campo).
1. Suporta **re-scan de verificação** e campos de **audit trail** documentados nos use cases.

**Modelo de IP:** tokenizador/remediador permanece **terceiro**; Data Boar detém discovery, orquestração e export de evidência.

---

## Fases

| Fase | Entregável | Status |
| ---- | ---------- | ------ |
| **0 – Docs** | Use cases + este plano | 🔄 Em progresso (**#602–605**, **#601**) |
| **1 – Export do remediation manifest** | CLI `--export-remediation-manifest` + JSON schema v1 (ponte para plugins terceiros) | ✅ **#649** |
| **1b – Esqueleto do hook** | Registro mínimo de plugin + hook do host (`RemediationPlugin` / ADR-0059) | ✅ **#606** |
| **2 – Caminho de export** | JSONL de findings pelo host antes do plugin (`findings_{session_id}.jsonl`, taxonomia #649) | ✅ **#1443** (escrita no host); ⬜ FPE / samples tokenizados |
| **3 – Job de re-scan** | Verificação no escopo após plugin | ⬜ |

---

## Fora de escopo (fases 0–1)

- Entregar produto proprietário de HSM ou vault dentro do core.
- Substituir o jurídico em base legal para biometria ou pagamentos.

---

## Aceite (plano)

- [x] Docs de use case em `docs/use-cases/`
- [x] Export JSON do remediation manifest (`--session` + `--export-remediation-manifest`) — **#649**
- [x] ADR de interface — [ADR-0059](../adr/ADR-0059-remediation-plugin-architecture.md) (revisar nas fases 2–3)
- [x] Hook em código conforme **#606** (link do PR quando aberto)

---

## Onda v1.8.0 — enriquecimento de políticas / anonimizador ([#1057](https://github.com/DataBoar/data-boar/issues/1057))

**Motivo:** Survey competitivo (dossiê privado). **Docs-first** nesta fatia; código continua no plugin Enterprise já existente. O Data Boar **não** entrega anonimizador interno, HSM nem reescrita in-place no core.

**O que não se afirma (alinhado a [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) e [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)):** Relatórios de scan, valores de `norm_tag` e `report.recommendation_overrides` são **auxílios de inventário e mapeamento técnico** — não são parecer jurídico, não determinam que um campo precisa ser anonimizado sob LGPD/GDPR e **não** são chancela da ANPD (nem de outra autoridade). Plugins de parceiro que tokenizam ou mascaram dados o fazem sob **política e jurídico do cliente**; o host só exporta **metadados** (`pii_type`, `suggested_profile`, localizações).

### O que já existe (não inventar um segundo contrato)

| Superfície | Papel hoje | Relevância para política |
| ---------- | ---------- | ------------------------ |
| `--export-remediation-manifest` (**#649**) | Mapa JSON de localizações + `pii_type` + `suggested_profile` (`core/remediation_manifest.py`) | O plugin escolhe mascarar / tokenizar / criptografar **a partir desses hints** — sem amostras brutas |
| Hook `RemediationPlugin` (**#606** / ADR-0059) | Callback Enterprise no mesmo processo, após o relatório | IP do parceiro executa; host falha de forma controlada |
| JSONL de findings no host (**#1443**) | Mesma taxonomia do manifest, escrito antes do plugin | Só coordenadas de entrada |
| Excel / YAML `recommendation_overrides` | Texto no relatório a partir de `docs/compliance-samples/compliance-sample-*.yaml` | Sugere **direção** (restringir, mascarar, revisar) — **não** altera as fontes |
| [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md) | Narrativa opcional de **ações sugeridas** | Ortogonal: o APG **não** remedia automaticamente |

### Classes de política (linguagem do comprador → ações já documentadas no SDK)

SKUs competitivos de “anonimizador” costumam agrupar vários **tratamentos**. Mapeie-os nos casos de uso de [PLUGIN_SDK.md](../PLUGIN_SDK.md) — **o parceiro implementa**; o core permanece discovery + evidência.

| Classe de política | Pedido típico do comprador | Gancho no produto (sem motor novo) | Caminho de sample / override |
| ------------------ | -------------------------- | ---------------------------------- | ---------------------------- |
| **Mascarar / redigir** | Ocultar PAN, parte local do e-mail ou documento em cópias | SDK **Masking** (sobrescrever ou cópia em estágio) | Itens de `recommendation_overrides` nos samples PCI / LGPD |
| **Tokenizar / FPE** | Manter formato para validadores a jusante | SDK **FPE tokenization** via cofre do parceiro; Phase **2** ainda ⬜ para **amostras** tokenizadas no export do host | [USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md) |
| **Anonimizar irreversível** | Transformação unidirecional quando a política proíbe reversão | Só log de ação do parceiro; **não** há anonimizador por hash no core | O jurídico decide a base legal; não afirmar “dataset anonimizado” a partir de um scan |
| **Criptografia de campo** | Ciphertext em colunas nomeadas | SDK **Field encryption** | O `suggested_profile` do manifest (ex.: `TGCPF`, `TGPAN`) seleciona o perfil no cofre |
| **Notificar / ticket** | ITSM a partir das coordenadas do finding | SDK **Notification** | Conveniência operacional — não é notificação legal |

Os tokens `suggested_profile` já no código (`TGCPF`, `TGCNPJ`, `TGEMAIL`, `TGPAN`, …, `TGGENERIC`) são **hints para o plugin**, não uma afirmação de cobertura de todo `pattern_detected`.

### Metodologia dos compliance-samples (obrigatória para o texto de política)

Mesma disciplina dos packs de detecção — **não** criar um segundo dialeto YAML de anonimizador:

1. Manter `regex:` / termos ML nos arquivos `docs/compliance-samples/compliance-sample-*.yaml` existentes; `norm_tag` é **rótulo de framework**, não conclusão jurídica.
2. Mesclar `recommendation_overrides` no `report.recommendation_overrides` do operador para o Excel acompanhar a política interna (mascarar vs tokenizar vs “revisar com o DPO”).
3. Os cabeçalhos dos arquivos já exigem revisão jurídica antes de padrões em produção.
4. Um stub opcional posterior `compliance-sample-remediation_hints.yaml` traria **somente** bullets de override + avisos (sem detectores novos) — **não** nesta fatia de docs.
5. O host nunca escreve tabelas do cliente. Snippets e plugins são **opt-in** e aprovados pelo operador (barreiras em [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md)).

### Tabela de execução (docs-first → fatias posteriores)

| Passo | Entregável | Status |
| ----- | ---------- | ------ |
| P1 | Esta seção do plano + resumo no hub + linhas do survey em `PLANS_TODO` | ✅ Feito (PR de docs) |
| P2 | Pack opcional em `docs/compliance-samples/`: `recommendation_overrides` chaveados pelo `pattern` → id de ação do plugin + avisos no cabeçalho | ⬜ Pendente |
| P3 | [PLUGIN_SDK.md](../PLUGIN_SDK.md) (+ pt-BR): tabela curta do vocabulário `suggested_profile` (espelha `core/remediation_manifest.py`) | ⬜ Pendente |
| P4 | Phase 2 — **amostras** tokenizadas / FPE no caminho de export do host (ainda executadas pelo parceiro) | ⬜ Pendente (tabela de fases já existente) |
| P5 | Phase 3 — re-scan no escopo após o plugin | ⬜ Pendente (tabela de fases já existente) |

### Revisitar (planos irmãos / concluídos — só notas do survey)

- [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md): manter ações **sugeridas**; **não** embutir SQL automático neste plano de plugin.
- [PLAN_PLUGIN_PARTNER_INTERFACE.md](PLAN_PLUGIN_PARTNER_INTERFACE.md) / épico **[#865](https://github.com/DataBoar/data-boar/issues/865)**: isolamento L2/L3 continua o follow-up de fronteira de confiança — não substitui o mapeamento de políticas aqui.

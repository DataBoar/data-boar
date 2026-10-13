# Plano: viabilidade de augmentação Clojure/Lisp no Data Boar

**Status:** Emendado (2026-10-12 — runtime em bestiais irmãos, não sidecar no host; ver §0)
**Date:** 2026-05-09
**Authors:** Fabio Leitao
**Priority:** H3

**English:** [PLAN_CLOJURE_AUGMENTATION.md](PLAN_CLOJURE_AUGMENTATION.md)

<!-- plans-hub-summary: Avaliar se um sidecar em Clojure agrega valor mensurável para lógica de políticas e evidência temporal sem regredir a base Rust/Python. -->
<!-- plans-hub-related: PLAN_LATO_SENSU_THESIS.md, PLAN_STRICTO_SENSU_RESEARCH_PATH.md, PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md -->

**Horizonte sugerido:** `[H4][U3]` exploração de longo prazo após as fatias atuais de comercialização
**Escopo principal:** Viabilidade arquitetural e evidências, não migração imediata do produto

---

## 0. Emenda (2026-10-12 — issue #1839)

**Conclusão:** um **plugin sidecar** Clojure/Lisp continua válido, mas **não** dentro da árvore `data-boar` (`experimental/clojure_sidecar/`, JVM no caminho Community, adapter Python no core).

- O runtime fica em **repositórios separados** da org DataBoar (sage-remora, faithful-ferret), orquestrados pelo slot plugin/SDK — não como subproduto deste monorepo.
- O **host** mantém só o contrato L2 spawn/timeout/Safe-Hold (`PLAN_PLUGIN_PARTNER_INTERFACE` / epic #865); não é dono do motor Clojure.
- **Fases 0–2 abaixo (PoC no host):** **canceladas / não aplicam** — preservadas só como hipótese histórica.

Este plano **não** vai para `completed/` só para sumir do hub; status **Emendado**, não “concluído no core.”

---

## 1. Por que este plano existe

Este plano testa uma hipótese focada: um sidecar pequeno em Clojure/Lisp pode melhorar raciocínio de políticas e geração de evidências temporais para cenários de compliance mais complexos.

O plano **não** substitui o core atual em Rust/Python:

- Rust permanece como motor de performance.
- Python permanece como camada de orquestração e conectores.
- Clojure só entra como sidecar opcional se houver evidência objetiva de ganho líquido.

---

## 2. Hipótese de valor e gates de decisão

### 2.1 Valor potencial para o Data Boar

Áreas potenciais de valor:

1. **Expressividade de políticas:** composição de regras mais rica (por exemplo, correlações de compliance com múltiplas condições) com menos código imperativo.
2. **Raciocínio auditável:** explicabilidade de regra mais clara para operador e narrativas de compliance.
3. **Ponte acadêmica:** cria uma linha de pesquisa crível ligada a raciocínio formal e modelos de evidência.

### 2.2 Restrições duras

Qualquer experimento de sidecar precisa preservar:

- Sem regressão de runtime no caminho padrão do Data Boar.
- Sem dependência obrigatória de JVM no baseline Community.
- Sem enfraquecer segurança, observabilidade ou fluxo operacional.

### 2.3 Critérios de go/no-go

Só avançar além de PoC se tudo for verdadeiro:

- Overhead ponta a ponta permanece aceitável em cenário de benchmark limitado.
- Autoria e revisão de regras melhoram de forma mensurável contra implementação Python pura.
- Complexidade de integração permanece sustentável para execução com operador único.

---

## 3. Fase 0 - Brief de viabilidade (doc-first)

**Objetivo:** decidir se vale construir uma PoC.

| # | To-do | Status |
| - | ----- | ------ |
| 0.1 | Definir 2-3 casos de regra realistas onde a lógica Python atual está verbosa ou difícil de auditar. | ❌ Cancelada (§0 — trilha host) |
| 0.2 | Comparar stacks candidatas (`datascript`, `malli`, modelo de regra EDN leve) e listar trade-offs. | ❌ Cancelada (§0) |
| 0.3 | Escrever opções de integração (sidecar gRPC, processo local ou compilador de regras offline) com notas de blast radius. | ❌ Cancelada (§0) |
| 0.4 | Produzir memo de go/no-go (uma página) e classificar esta trilha como backlog de produto ou backlog acadêmico. | ❌ Cancelada (§0) |

---

## 4. Fase 1 - PoC mínima de sidecar (opcional)

**Objetivo:** testar um caminho concreto com cenário único e limitado.

| # | To-do | Status |
| - | ----- | ------ |
| 1.1 | Criar `experimental/clojure_sidecar/` com bootstrap mínimo e README de restrições. | ❌ Cancelada (§0) |
| 1.2 | Implementar um endpoint de avaliação de regra com contrato de entrada/saída determinístico. | ❌ Cancelada (§0) |
| 1.3 | Adicionar adapter Python atrás de feature flag opt-in (`off` por padrão). | ❌ Cancelada (§0) |
| 1.4 | Adicionar script de benchmark e capturar overhead de latência/memória versus baseline. | ❌ Cancelada (§0) |
| 1.5 | Registrar achados e recomendação (`continue`, `park` ou `discard`). | ❌ Cancelada (§0) |

---

## 5. Fase 2 - Gate de productização (somente se aprovada)

**Objetivo:** definir o necessário antes de qualquer alegação de produção.

| # | To-do | Status |
| - | ----- | ------ |
| 2.1 | Definir workflow operacional (instalação, health checks, fallback quando sidecar indisponível). | ❌ Cancelada (§0 — trilha host) |
| 2.2 | Definir modelo de segurança para comunicação do sidecar e validação de entrada. | ❌ Cancelada (§0) |
| 2.3 | Definir campos em relatório/Audit Trail mostrando quando lógica de sidecar esteve ativa. | ❌ Cancelada (§0) |
| 2.4 | Estimar custo de manutenção e confirmar aderência à prioridade do roadmap. | ❌ Cancelada (§0) |

---

## 6. Alinhamento acadêmico (lato/stricto sensu)

Este plano também apoia trilhas acadêmicas sem forçar escopo de produto no curto prazo:

- **Lato sensu:** usar viabilidade e raciocínio auditável como material de arquitetura aplicada.
- **Stricto sensu:** usar experimentos controlados para comparar abordagens de modelagem de regras e qualidade de evidências.

Referências relacionadas:

- [PLAN_LATO_SENSU_THESIS.md](PLAN_LATO_SENSU_THESIS.md)
- [PLAN_STRICTO_SENSU_RESEARCH_PATH.md](PLAN_STRICTO_SENSU_RESEARCH_PATH.md)
- [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md) (ponte N3)

---

## 7. Recomendação atual

**Após §0 (2026-10-12):** **não** retomar as fases 0–2 no host. Trabalho Clojure/Lisp sidecar fica em **repositórios bestiais irmãos** (slot plugin/SDK); o host mantém só spawn/timeout/Safe-Hold.

Para planejamento de produto, trate este arquivo como **referência emendada** — não como marco imediato em `main`. Reavaliar twins + contrato do host quando:

- Solicitação de cliente/parceiro exigir raciocínio de política mais rico.
- Ciclo de tese/pesquisa pedir ramificação experimental de regras formais.
- A interface de plugin parceiro (#865) definir um teste L2 concreto.

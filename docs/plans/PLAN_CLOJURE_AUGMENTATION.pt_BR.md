# Plano: viabilidade de augmentação Clojure/Lisp no Data Boar

**English:** [PLAN_CLOJURE_AUGMENTATION.md](PLAN_CLOJURE_AUGMENTATION.md)

<!-- plans-hub-summary: Avaliar se um sidecar em Clojure agrega valor mensurável para lógica de políticas e evidência temporal sem regredir a base Rust/Python. -->
<!-- plans-hub-related: PLAN_LATO_SENSU_THESIS.md, PLAN_STRICTO_SENSU_RESEARCH_PATH.md, PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md -->

**Status:** Proposto (não iniciado)
**Horizonte sugerido:** `[H4][U3]` exploração de longo prazo após as fatias atuais de comercialização
**Escopo principal:** Viabilidade arquitetural e evidências, não migração imediata do produto

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
| 0.1 | Definir 2-3 casos de regra realistas onde a lógica Python atual está verbosa ou difícil de auditar. | ⬜ Pending |
| 0.2 | Comparar stacks candidatas (`datascript`, `malli`, modelo de regra EDN leve) e listar trade-offs. | ⬜ Pending |
| 0.3 | Escrever opções de integração (sidecar gRPC, processo local ou compilador de regras offline) com notas de blast radius. | ⬜ Pending |
| 0.4 | Produzir memo de go/no-go (uma página) e classificar esta trilha como backlog de produto ou backlog acadêmico. | ⬜ Pending |

---

## 4. Fase 1 - PoC mínima de sidecar (opcional)

**Objetivo:** testar um caminho concreto com cenário único e limitado.

| # | To-do | Status |
| - | ----- | ------ |
| 1.1 | Criar `experimental/clojure_sidecar/` com bootstrap mínimo e README de restrições. | ⬜ Pending |
| 1.2 | Implementar um endpoint de avaliação de regra com contrato de entrada/saída determinístico. | ⬜ Pending |
| 1.3 | Adicionar adapter Python atrás de feature flag opt-in (`off` por padrão). | ⬜ Pending |
| 1.4 | Adicionar script de benchmark e capturar overhead de latência/memória versus baseline. | ⬜ Pending |
| 1.5 | Registrar achados e recomendação (`continue`, `park` ou `discard`). | ⬜ Pending |

---

## 5. Fase 2 - Gate de productização (somente se aprovada)

**Objetivo:** definir o necessário antes de qualquer alegação de produção.

| # | To-do | Status |
| - | ----- | ------ |
| 2.1 | Definir workflow operacional (instalação, health checks, fallback quando sidecar indisponível). | ⬜ Pending |
| 2.2 | Definir modelo de segurança para comunicação do sidecar e validação de entrada. | ⬜ Pending |
| 2.3 | Definir campos em relatório/Audit Trail mostrando quando lógica de sidecar esteve ativa. | ⬜ Pending |
| 2.4 | Estimar custo de manutenção e confirmar aderência à prioridade do roadmap. | ⬜ Pending |

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

Recomendação atual: manter esta trilha em **backlog de horizonte distante** até estabilizar fatias ativas de confiança/comercialização. Reavaliar quando um destes gatilhos ocorrer:

- Solicitação de cliente/parceiro exigindo raciocínio de política mais rico.
- Ciclo de tese/pesquisa pedindo uma ramificação experimental de regras formais.
- Lógica de política em Python ficar cara demais para manter.

# Grafana Cloud — reativação + primeiros passos seguros (runbook do operador)

**English:** [GRAFANA_CLOUD_REACTIVATION.md](GRAFANA_CLOUD_REACTIVATION.md)

**Objetivo:** manter um caminho curto e repetível para (a) **reativar** um stack Grafana Cloud suspenso por inatividade e (b) executar os primeiros passos **seguros** após a reativação, sem vazar segredos no Git.

**Âmbito:** operador. Este repositório **não** provisiona Grafana Cloud automaticamente e **não** guarda tokens do Grafana em arquivos rastreados.

## 1. O que “reativação” significa (e o modo de falha comum)

No free tier, o Grafana Cloud pode suspender stacks após longo período sem uso. Um erro comum no portal é informar que a instância **não pode ser reativada automaticamente** e que precisa de **suporte**.

**O que registrar (sem segredos):**

- Nome do stack (rótulo humano).
- Região (se aparecer).
- Formato da URL pública do stack (use placeholders em docs, ex.: `https://<org>.grafana.net/`).
- Screenshot da mensagem do portal (mantenha privado se contiver identificadores).

## 2. Passos de reativação (portal)

1. Faça login no portal do Grafana Cloud.
1. Abra seu stack e tente **Launch**.
1. Se o portal disser que não pode reativar automaticamente:
   - Use o caminho de **suporte** do portal (ou o e-mail mostrado) e peça reativação.
   - Envie só o necessário (nome do stack + mensagem + janela de tempo). Evite dados pessoais extras.
1. Aguarde confirmação e tente **Launch** de novo.

## 3. Pós-reativação: “primeira configuração segura”

### 3.1 Criar um token de Access Policy (privilégio mínimo)

1. No portal, vá em **Access policies**.
1. Crie policy + token com o mínimo de escopo:
   - **Read-only** se você quer só dashboards/consulta.
   - **Write** apenas para o pipeline que você realmente vai usar (métricas/logs/traces).
1. Guarde o token em um (ou ambos):
   - Secrets do GitHub (para CI/workflows), e/ou
   - gerenciador de senhas (Bitwarden) para recuperação do operador.

**Nunca** guarde o token em Markdown rastreado, `config.yaml`, screenshots versionados, ou em logs/exports de chat.

### 3.2 Decidir o que você quer primeiro (métricas vs logs vs traces)

A sequência recomendada no repo está no plano:

- `docs/plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md` ([pt-BR](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md))

**Padrão amigável ao operador:** começar por **métricas** (caminho Prometheus) e só depois adicionar logs/traces quando o lab tiver RAM.

## 4. Formas de integração (alto nível, sem segredos)

Escolha um ou dois, não tudo ao mesmo tempo:

- **Métricas**: Prometheus remote_write → endpoint de métricas do Grafana Cloud.
- **Logs**: Loki/Promtail → endpoint de logs do Grafana Cloud.
- **Traces**: collector OpenTelemetry (OTLP) → endpoint de traces do Grafana Cloud.

**Onde colocar endpoints/tokens reais:** `docs/private/` (gitignored) ou variáveis de ambiente no host do operador / secrets do CI.

## 5. Onde isso se encaixa na documentação do repo

- Índice ops: `docs/ops/README.md` ([pt-BR](README.pt_BR.md))
- Mapa do lab: `docs/ops/OPERATOR_LAB_DOCUMENT_MAP.md` ([pt-BR](OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md))
- Links de estudo: `docs/ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.md` ([pt-BR](inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md))


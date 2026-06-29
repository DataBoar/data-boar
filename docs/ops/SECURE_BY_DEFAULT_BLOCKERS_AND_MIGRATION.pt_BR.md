# Bloqueios para secure-by-default e migração segura (API key + transporte)

**English:** [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md)

## Objetivo

Explicar por que algumas mudanças de "secure-by-default" hoje são tratadas como **decisão de produto com risco de migração** (e não como patch simples), e como chegar nisso sem quebrar deploys reais.

## Resposta curta

O bloqueio quase nunca é impossibilidade técnica. É, principalmente, **risco de compatibilidade e rollout**:

- Forçar default de auth/transporte sem transição pode quebrar automações, probes, dashboards e scripts existentes.
- "Segurança ligada por padrão" é correta, mas sem estratégia de migração pode gerar indisponibilidade e lock-out.

## Mapa principal de bloqueios

| Tema                                 | Como pode quebrar app/deploy                                                                                | Regressão típica                                            |
| ---                                  | ---                                                                                                         | ---                                                         |
| **API key obrigatória por padrão**   | Ferramentas/rotinas existentes podem chamar rotas protegidas sem `X-API-Key`                                | 401 em scripts, jobs agendados, integrações                 |
| **Migração para `api_key_from_env`** | Nome/valor da variável mal configurado, ou confusão de precedência (`api_key` literal no YAML sobrepõe env) | app sobe, mas comportamento de auth não bate com o esperado |
| **HTTP -> HTTPS por padrão**         | Cert/key ausente ou inválido em ambientes antes em HTTP puro                                                | falha de startup ou dashboard inacessível                   |
| **Suposição de health/status**       | Alguns consumidores assumem que tudo funciona como `/health`                                                | ruído de monitoramento e falso negativo                     |

## Por que isso aparece como "decisão de produto" nos planos

No `PLANS_TODO` e no trilho Corporate-Entity-C, "secure-by-default" de API auth e transporte é tratado como mudança de produto porque pode ser **breaking-by-default** para instalações atuais se ativado de forma abrupta.

Por isso o repositório vem em hardening incremental:

- warnings claros em runtime inseguro,
- padrão `api_key_from_env` documentado,
- passos de migração explícitos,
- testes cobrindo modo seguro e modo de compatibilidade.

## Workarounds sem quebrar operação

1. **Rollout em modo duplo**
   - modo seguro disponível já;
   - modo de compatibilidade apenas por opt-in explícito + warning.
1. **Transição warning -> enforcement**
   - Fase A: warning + telemetria/auditoria;
   - Fase B: default seguro para instalações novas, flag de compat para legado;
   - Fase C: deprecar modo inseguro com prazo claro.
1. **Gestão segura de chave**
   - usar `api_key_from_env` (ver [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md));
   - evitar chave literal em YAML versionado.
1. **Clareza de status/health**
   - manter semântica de `/health` explícita;
   - documentar quais rotas exigem chave e como interpretar falhas.

## Checklist prático de migração

1. Inventariar consumidores de API/dashboard (scripts, cron, CI, probes, mobile checks).
1. Ativar trilha segura primeiro em staging (API key + HTTPS quando aplicável).
1. Atualizar consumidores com header de auth e expectativa de certificado.
1. Levar para produção com fallback explícito por janela curta.
1. Monitorar logs/status/audit de uso inseguro e reduzir até desligar.

## Contexto do operador (implantações iniciais)

Para **este produto**, a base instalada sob controle do mantenedor é hoje **efetivamente vazia**: **não há clientes externos conhecidos em produção** chamando API/dashboard. Isso **reduz o risco de rollout** ao ligar `require_api_key`, listeners HTTPS-first e sinais de audit mais ricos — mas **não dispensa** **caminhos de migração documentados**, **testes de regressão** (modo seguro + compatibilidade) e **segredos seguros** (`api_key_from_env`, sem chave literal em YAML rastreado). O primeiro ambiente de cliente real não deve ser o primeiro teste desses caminhos.

## Documentos relacionados

- [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md) ([EN](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)) — configuração concreta de chave de API + TLS para técnicos
- [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)
- [SECURITY.pt_BR.md](../SECURITY.pt_BR.md)
- [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/completed/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md)
- [Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md](../plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md)

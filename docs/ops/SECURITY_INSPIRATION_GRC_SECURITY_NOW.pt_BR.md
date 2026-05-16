# Revisão de inspiração em segurança: GRC / Security Now (como aprender, o que adotar, o que evitar)

**English:** [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.md)

## Objetivo

Registrar como usar o material do Security Now/GRC como **fonte de inspiração prática** sem copiar opiniões de forma cega, traduzindo aprendizados úteis em guardrails do Data Boar.

## Fontes (contínuo)

- [Arquivo do Security Now (GRC)](https://www.grc.com/securitynow.htm)
- [Link do episódio citado](https://www.youtube.com/watch?v=JebKuiHu5mg&t=2850s)

Este é um guia vivo. Atualizamos de forma incremental conforme extraímos lições de alto sinal.

## É uma boa fonte de inspiração para nós?

### Pontos fortes (por que sim)

- Comentário de segurança de longa duração, com muitos padrões reais de incidentes.
- Ênfase em higiene operacional e em "como isso quebra em produção."
- Foco frequente em falhas de configuração e de fronteira de confiança (muito relevante para secure-by-default).

### Limites (por que não copiar cegamente)

- Conteúdo de podcast é orientação, não norma formal por si só.
- Cobertura ampla e às vezes opinativa; o projeto precisa de adaptação com evidência.
- Parte das recomendações pode mirar endpoint pessoal mais que arquitetura de produto.

## O que vale tentar imitar

- Defaults defensivos com override inseguro explícito (e warnings claros).
- Mensagens de segurança legíveis para operador (sem falha silenciosa e sem "downgrade" oculto de confiança).
- Comunicação de risco concreta e orientada a comportamento.
- Repetição de princípios centrais: least privilege, fronteiras de confiança explícitas, evitar atalhos inseguros.

## O que evitar imitar

- Tratar dica de podcast como "política pronta" sem ajuste à arquitetura.
- Exagerar em uma fonte única e ignorar nosso próprio threat model/testes.
- Teatro de segurança: texto assustador sem controle real em runtime.

## Lições práticas para aplicar agora

1. Manter anti-patterns de "conveniência insegura" explicitamente proibidos em plano/docs (ex.: injeção de root trust pelo app).
1. Exigir modelo observável de estado de confiança (stdout/stderr/logs/status/dashboard/audit/report alinhados).
1. Manter rollout seguro para migração (warn -> modo duplo -> enforce).
1. Transformar lições em testes/guardrails, não só em prosa.
1. Rastrear temas de alto risco no backlog com prioridade crítica quando afetam integridade/confidencialidade.
1. Quando discussão externa destacar **rastreadores embutidos** em mídia rica (por exemplo URLs de telemetria em metadados de imagem/vídeo), registrar como **fatia de backlog** com detecção opt-in e relatório claro — ver [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](../plans/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) (Tier 3b).

## Guardrails candidatos para manter

- Transporte HTTPS-first com baseline cripto estrita (sem fallback legado).
- Trilha de auth secure-by-default com controle de compatibilidade.
- Comportamento de saída "tinted/untrusted" quando confiança estiver degradada.
- Lista explícita de anti-patterns nos docs/planos de segurança.
- Checks em CI/automação quando viável (lint/test/workflow guards).

## Método de trabalho para minerar histórico de show notes (token-aware)

1. Amostrar por tema, não varrer arquivo inteiro em um passo:
   - criptografia de transporte,
   - trust anchors/certificados,
   - hardening de endpoint,
   - supply chain e assinatura,
   - least privilege / abuse controls.
1. Para cada lição candidata, decidir:
   - **Adotar agora**, ou
   - **Backlog com motivo**, ou
   - **Rejeitar (não encaixa)**.
1. Ligar cada decisão a um artefato do repo (plano/doc/teste/script).

## Checklist de avaliação (para cada recomendação externa)

- O threat model é relevante para os deploys do Data Boar?
- Existe trilha de rollout sem quebra?
- Conseguimos validar com testes/logs/audit?
- Melhora clareza para operador, não só postura teórica?
- Custo de manutenção é aceitável no estágio atual do roadmap?

## Snapshot de decisão atual

- **Qualidade da fonte de inspiração:** útil e prática, com filtro criterioso.
- **Postura de adoção:** seletiva e apoiada em testes.
- **Uso imediato:** guardrails de transporte/auth secure-by-default, anti-patterns proibidos e visibilidade de trust-state.

## Documentos relacionados

- [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](../plans/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) (Tier 3b rastreadores embutidos / mídia rica)
- [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md)
- [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md)
- [SECURITY.pt_BR.md](../SECURITY.pt_BR.md)
- [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md)

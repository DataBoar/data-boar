# Observabilidade, SLO/SLI, DevSecOps e alinhamento SRE

**English:** [OBSERVABILITY_SRE.md](OBSERVABILITY_SRE.md)

Este documento descreve como o projeto **equilibra segurança e proteção com desempenho e confiabilidade**, e como se alinha às práticas de **observabilidade**, **SLO/SLI/SLA**, **DevSecOps** e **SRE**. Todas as recomendações são **aditivas** e **não quebram** o app; implemente-as de forma incremental e execute a suíte de testes completa após qualquer alteração de código.

---

## 1. Equilíbrio segurança/proteção com desempenho e confiabilidade

Hoje o app já equilibra essas preocupações da seguinte forma:

| Preocupação        | O que fazemos                                                                                                                                                  | Onde                                                                                                                  |
| -------------      | -----------------------------------------------------------------------------------------------------------------------------------------------------------    | --------------------------------------------------------------------------------------------------------------------  |
| **Segurança**      | API key (opcional), headers de segurança (CSP, X-Frame-Options, etc.), sem segredos em respostas, queries parametrizadas, validação session_id, YAML safe_load | [SECURITY.md](../SECURITY.md), [api/routes.py](../api/routes.py), [tests/test_security.py](../tests/test_security.py) |
| **Proteção**       | Rate limiting (429), timeouts configuráveis (por plano), scan.max_workers, pip-audit e higiene de dependências                                                 | [CONTRIBUTING.md](../CONTRIBUTING.md), [docs/USAGE.md](USAGE.md), config                                              |
| **Confiabilidade** | Endpoint de health para liveness/readiness, GET /status para estado do scan, SQLite e carga de config na inicialização, testes com `-W error`                  | [api/routes.py](../api/routes.py), [docs/deploy/DEPLOY.md](deploy/DEPLOY.md)                                          |
| **Desempenho**     | Cache da lista de sessões (TTL quando não há scan), rate_limit para não sobrecarregar alvos, paralelismo configurável                                          | [api/routes.py](../api/routes.py), config                                                                             |

**Trade-offs aceitos:** O health é um simples `{"status": "ok"}` (processo no ar); não verifica DB nem alcance da config. Para muitas implantações isso basta para liveness no Kubernetes/Docker; para readiness mais rígida você pode usar um reverse-proxy ou sidecar que checa GET /status ou um futuro endpoint de readiness. Não registramos latência de requisição nem expomos métricas por padrão, para evitar custo e vazamento acidental de dados sensíveis; veja abaixo a instrumentação opcional.

---

## 2. Observabilidade e SLO/SLI/SLA

### Estado atual

- **Liveness/readiness:** `GET /health` retorna 200 quando o processo está no ar. Usado por Docker, Compose e Kubernetes para healthchecks (veja [deploy/DEPLOY.md](deploy/DEPLOY.md)).
- **Estado do scan:** `GET /status` retorna `running`, `current_session_id`, `findings_count` (útil para dashboards ou runbooks).
- **Sem endpoint de métricas ainda:** Não há `/metrics` (Prometheus) nem export OpenTelemetry. Adicionar seria um recurso **aditivo** (nova rota, dependência opcional).
- **Logging:** Existe logging da aplicação, mas não é estruturado (ex.: sem request_id, duração) por padrão; veja [SECURITY.md](../SECURITY.md) para política (sem segredos em logs).

### SLI/SLO/SLA (como chegar lá)

Para dar suporte a **SLAs** você precisa de **SLOs** (metas), e para medir SLOs precisa de **SLIs** (indicadores). Abaixo um conjunto mínimo que o app pode suportar hoje ou com pequenas adições.

| SLI (o que medir)               | Como medir hoje                                                                  | Melhoria opcional                                                                                   |
| ---------------------------     | -------------------------------------------------------------------------------  | --------------------------------------------------------------------------------------------------- |
| **Disponibilidade** (API no ar) | Probes do LB/orquestrador em `GET /health`; contar 200 vs 5xx                    | Adicionar `/ready` que checa config + DB se precisar de readiness mais rígida                       |
| **Taxa de sucesso do scan**     | Logs ou DB: contar sessões com status completed vs failed; ou parse do relatório | Contador ou label em um futuro `/metrics` (ex.: `scan_completed_total`, `scan_failed_total`)        |
| **Latência da API** (ex.: p99)  | Reverse-proxy ou APM (ex.: Prometheus + middleware que registra duração)         | Middleware opcional que emite duração (ou exporta para Prometheus) sem logar corpo da requisição    |
| **Taxa de erro** (4xx/5xx)      | Access logs do reverse proxy ou logs da app                                      | Idem: métricas opcionais ou logs estruturados com status code                                       |

**Recomendação:** Por ora, use **GET /health** e seu **reverse proxy ou orquestrador** (Nginx, Traefik, Kubernetes Ingress) para medir disponibilidade e latência. Documente seu SLO alvo (ex.: “99,9% dos health checks retornam 200”) e alerte quando o probe falhar. Quando precisar de SLIs in-app (ex.: taxa de sucesso do scan, duração da requisição), adicione um endpoint **opcional** `/metrics` (formato Prometheus) e/ou logging estruturado com request_id e duração; mantenha ambos atrás de config para o comportamento padrão não mudar e sem expor segredos.

---

## 3. Alinhamento DevSecOps

DevSecOps significa **segurança como código**, **shift-left** e **automação**. O projeto já faz o seguinte:

| Prática                   | O que fazemos                                                                                                                                 |
| ------------------------  | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Shift-left**            | Testes (pytest), Ruff, testes estilo SonarQube, CodeQL, pip-audit no CI; regra e skill para o agente evitar violações antes do commit         |
| **Segurança no pipeline** | Auditoria de dependências (pip-audit), testes de segurança (SQL injection, path traversal, safe_load), API key e testes CSP                   |
| **Segredos**              | Sem segredos em logs (política em SECURITY.md); config e env para API key; checklist de release confirma ausência de segredos em logs         |
| **Supply Colleague-Nn**          | Dependabot, versões mínimas em pyproject.toml, auditoria antes do release                                                                     |

**Recomendação:** Mantenha a segurança integrada ao mesmo pipeline (testes + lint + auditoria). Ao adicionar novos recursos (ex.: webhooks, novos conectores), adicione testes e atualize [SECURITY.md](../SECURITY.md) e [docs/SECURITY.md](SECURITY.md) para o comportamento ficar documentado.

---

## 4. Alinhamento SRE

SRE foca em **confiabilidade**, **redução de toil**, **error budgets** e **operabilidade**.

| Prática             | O que fazemos                                                                                                                                                                                                                                     |
| ------------------  | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------                        |
| **Healthchecks**    | GET /health para liveness/readiness; usado nos exemplos Docker e K8s                                                                                                                                                                              |
| **Runbooks**        | [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md), [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md); docs de deploy descrevem limites e healthchecks |
| **Redução de toil** | CI (testes, lint, auditoria), scripts (fix_markdown_sonar, commit-or-pr), pre-commit opcional; regras de qualidade reduzem retrabalho                                                                                                             |
| **Operabilidade**   | Arquivo de config (muitos cenários sem mudar código), rate_limit e timeouts para evitar sobrecarga, binário/container único                                                                                                                       |

**Error budgets:** Se você definir um SLO (ex.: 99,9% de disponibilidade), o “error budget” é a fração permitida de falhas (ex.: 0,1%). Use a taxa de sucesso do health probe e, se adicionar, a taxa de sucesso do scan para ficar dentro do budget; priorize trabalho de confiabilidade quando o budget for consumido.

**Recomendação:** Documente seu SLO escolhido e como você o mede (ex.: “Health check 99,9% em 30 dias”). Adicione uma seção curta “Operations” ou “Runbooks” em [docs/deploy/DEPLOY.md](deploy/DEPLOY.md) ou mantenha ponteiros aqui para o operador saber onde procurar quando algo falhar.

### Governança do auditor

Enquadramento SRE: **quem vigia o vigilante** — o scanner precisa ser **defensável em auditoria**, não só os dados que ele inspeciona. O **[ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)** (inglês) registra a **linha de base 2026** (atribuição de sessão no SQLite, export audit trail, log de wipe, log de envio de notificação, logs no host com redação) e as **lacunas explícitas** (sem log imutável por download de relatório ou por cada POST de config por padrão). Use-o em narrativas honestas para **CISO / procurement** e no [MAP.pt_BR.md](MAP.pt_BR.md).

---

## 5. O que adicionar em seguida (apenas aditivo)

Sem quebrar o app ou introduzir regressões, você pode:

1. **Manter o comportamento atual:** Usar GET /health e GET /status mais o reverse proxy/orquestrador para disponibilidade e latência. Documentar o SLO e onde você mede.
1. **Opção /metrics (depois):** Adicionar rota (ex.: GET /metrics) que retorne formato texto Prometheus: ex. `http_requests_total`, `http_request_duration_seconds`, `scan_completed_total`, `scan_failed_total`. Proteger com flag de config (ex.: `api.metrics_enabled: false` por padrão) para ficar desligado a menos que habilitado. Não expor segredos nem PII.
1. **Logging estruturado opcional (depois):** Adicionar request_id e duração aos logs (ex.: middleware que loga method, path, status, duration_ms). Garantir que logs nunca contenham API keys, session_ids sensíveis ou credenciais de alvo; ver [SECURITY.md](../SECURITY.md).
1. **Readiness (opcional):** Se precisar que “ready” signifique “config carregada e DB acessível”, adicionar GET /ready que faça uma checagem mínima no DB (ex.: list_sessions limit 1) e retorne 200/503. Manter GET /health como liveness simples para orquestradores não precisarem mudar.

Execute a suíte completa (`uv run pytest -v -W error`) e o job de lint (`uv run ruff check .`) após qualquer alteração de código; atualize este doc e [TESTING.md](TESTING.md) ao adicionar novos endpoints ou comportamento.

---

## 6. Resumo

| Pergunta                                                         | Resposta                                                                                                                                                                                                                                                                 |
| -----------------------------------------------------------      | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Equilíbrio segurança/proteção com desempenho/confiabilidade?** | Sim: segurança (headers, API key, validação, auditoria) e confiabilidade (health, status, rate limit, timeouts) estão presentes; trade-offs (health simples, sem métricas por padrão) estão documentados.                                                                |
| **Instrumentação para observabilidade e SLOs?**                  | Health e status existem; SLIs podem ser medidos hoje via health probes e logs do proxy. /metrics e logging estruturado opcionais podem ser adicionados depois sem quebrar o app.                                                                                         |
| **DevSecOps e SRE?**                                             | DevSecOps: shift-left (testes, lint, auditoria, CodeQL), segurança no pipeline, sem segredos em logs. SRE: healthchecks, runbooks (docs de troubleshooting), redução de toil (CI, scripts), operabilidade (config, rate limit).                                          |
| **Sem quebrar ou regressões?**                                   | Este doc e os próximos passos sugeridos são aditivos e opcionais por config; qualquer código novo deve ser testado e documentado para o app manter a suíte verde e seguir SECURITY.md.                                                                                   |

Para detalhes de implantação (Docker, Kubernetes, healthchecks), veja [deploy/DEPLOY.md](deploy/DEPLOY.md). Para política de segurança e API key, veja [SECURITY.md](../SECURITY.md). Para **sprints**, marco **M-OBS** e guardrails de **orçamento de erros**, veja **SPRINTS_AND_MILESTONES** em **Interno e referência** em [README.pt_BR.md](README.pt_BR.md) (`docs/plans/` no checkout).

# Primer: Observabilidade (métricas, logs, traces) e o Data Boar

**English:** [OBSERVABILITY_PRIMER.md](OBSERVABILITY_PRIMER.md)

Primer conceitual sobre observabilidade no estilo **OpenTelemetry** e o que a árvore **pública** `data-boar` de fato emite. **Não** descreve topologias privadas de coletores em lab.

---

## 1. Pilares (vocabulário)

| Pilar | Pergunta | Neste repo |
| ----- | -------- | ---------- |
| **Métricas** | Taxas, erros, duração (RED) | Medidores OTel opt-in quando habilitado |
| **Logs** | Registros estruturados ou bridge | Bridge opt-in (`opentelemetry-instrumentation-logging` em `pyproject.toml`) |
| **Traces** | Spans de requisição/scan | Traces opt-in de `core/otel_setup.py` / instrumentação FastAPI |

Caminhos OTel de produto ficam **desligados por padrão** até `DATA_BOAR_OTEL_ENABLED` (`tests/test_otel_setup_1500.py`).

---

## 2. Pontos de integração versionados

| Área | Evidência |
| ---- | --------- |
| Gate de setup | `core/otel_setup.py` — `maybe_setup_otel(app=None)` no CLI; `api/routes.py` com `app` FastAPI no dashboard |
| Hook CLI | `main.py` chama `maybe_setup_otel(app=None)` cedo em comandos oneshot |
| Dependências | extras OTel em `pyproject.toml` |
| Testes | `tests/test_otel_setup_1500.py` |
| Trilha de auditoria (não OTel) | JSON `--export-audit-trail` do SQLite — evidência de sessão, não backend de observabilidade completo |

---

## 3. O que **não** está nesta árvore pública

- Stack Grafana/Prometheus/Loki **versionada** para operadores (stacks de lab ficam fora deste repo).
- Não há garantia de span em todo subcomando — cobertura segue código entregue, não roadmap.
- A palavra **tempo** em português (tempo) não é Grafana Tempo, salvo se você ligar OTLP a esse backend.

---

## 4. Onde ir depois

| Necessidade | Doc |
| ----------- | --- |
| Flags / comportamento | `core/otel_setup.py`, [USAGE.pt_BR.md](../USAGE.pt_BR.md) |
| Deploy IaC | [IAC_AND_DEVSECOPS_PRIMER.pt_BR.md](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md) |

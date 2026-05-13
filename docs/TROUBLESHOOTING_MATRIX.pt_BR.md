# Data Boar — Matriz de solução de problemas

**English:** [TROUBLESHOOTING_MATRIX.md](TROUBLESHOOTING_MATRIX.md)

> **Público:** Testadores de POC, colaboradores (membros da equipe), operadores.
> **Versão:** 2026-04-05 | **Relacionado:** `scripts/run_poc_error_scenarios.py`

Use esta matriz quando o Data Boar retorna um resultado inesperado, erro no dashboard ou o scanner não encontra dados que você espera que estejam lá.

---

## Como coletar e compartilhar achados

```bash
# 1. Iniciar o Data Boar
uv run python main.py --config deploy/config.example.yaml --web --port 8088

# 2. Executar o conjunto de cenários de erro
uv run python scripts/run_poc_error_scenarios.py --output reports/poc_error_metrics.json

# 3. Importar a collection do Postman
# tests/postman/Data_Boar_POC_ErrorScenarios.postman_collection.json

# 4. Compartilhar achados: abrir issue no GitHub com reports/poc_error_metrics.json
```

---

## Categoria A — Erros de API

### A-001: Connection refused

**Sintoma:** `CONNECTION_REFUSED` na saída do script ou `curl: (7) Failed to connect`.

**Causa:** Servidor não está rodando.

**Correção:**

```bash
uv run python main.py --config config.yaml --web --port 8088
# ou Docker:
docker run -p 8088:8088 -v /caminho/para/config.yaml:/data/config.yaml fabioleitao/data_boar:latest
```

**Validação:** `curl http://localhost:8088/health` retorna `{"status":"ok"}`.

---

### A-002: HTTP 401 / 403 em todos os endpoints

**Sintoma:** Toda requisição retorna 401 ou 403.

**Causa:** `api.require_api_key: true` mas a requisição não tem chave.

**Correção:** Adicione o header `X-API-Key: sua-chave` ou defina `api.require_api_key: false` no config.

---

### A-003: HTTP 422 Unprocessable Entity

**Sintoma:** POST para `/scan` retorna 422.

**Causa:** Payload sem campos obrigatórios ou com tipos errados.

**Campos obrigatórios por tipo de conector:**

| Tipo | Campos obrigatórios |
|---|---|
| `postgresql` | `host`, `port`, `database`, `user`, `password` |
| `mysql` | `host`, `port`, `database`, `user`, `password` |
| `sqlite` | `path` |
| `mongodb` | `host`, `port`, `database` |
| `filesystem` | `path` |
| `mssql` | `host`, `port`, `database`, `user`, `password` |

---

### A-004: HTTP 429 Too Many Requests

**Sintoma:** POST para `/scan` retorna 429.

**Causa:** Scan já em execução ou limite de taxa atingido.

**Correção:** Verificar `GET /status`, aguardar o scan atual terminar.

---

## Categoria B — Erros de banco de dados

### B-001: Timeout de conexão / connection refused no alvo DB

**Causa:** Host do DB inacessível a partir do contêiner/host do Data Boar.

**Atenção com Docker:**

```yaml
# ERRADO (dentro do contêiner, localhost = o próprio contêiner):
targets:
  - type: postgresql
    host: localhost

# CORRETO:
targets:
  - type: postgresql
    host: host.docker.internal  # Docker Desktop
    # ou IP real da LAN
```

**Diagnóstico:**

```bash
telnet db-host db-port
# ou: nc -zv db-host db-port
```

---

### B-002: Autenticação falhou

**Causa:** Usuário/senha errados ou GRANT ausente.

**Correção (PostgreSQL):**

```sql
GRANT CONNECT ON DATABASE seu_banco TO seu_usuario;
GRANT USAGE ON SCHEMA public TO seu_usuario;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO seu_usuario;
```

**Correção (MySQL):**

```sql
GRANT SELECT ON seu_banco.* TO 'seu_usuario'@'%';
FLUSH PRIVILEGES;
```

---

### B-003: Tipo de conector desconhecido

**Tipos suportados:** `postgresql`, `mysql`, `sqlite`, `mongodb`, `mssql`,
`redis`, `snowflake`, `filesystem`

**Correção:** Corrija o campo `type`.

---

## Categoria C — Erros de scan de arquivos

### C-001: Caminho não encontrado

**Causa:** O caminho não existe em runtime (especialmente no Docker sem volume montado).

**Correção:**

```bash
docker run -v /seus/dados:/scan/data ... # depois use path: /scan/data no config
```

---

### C-002: Arquivo não escaneado (extensão errada)

**Causa:** Extensão não está na lista `file_scan.extensions`.

**Correção:** Adicione a extensão ausente ao config:

```yaml
file_scan:
  extensions: [.txt, .csv, .pdf, .docx, .xlsx, .json, .xml, .db, .parquet, .zip, .tar.gz]
```

---

### C-003: Arquivo escaneado mas zero achados

**Checklist de diagnóstico:**

1. O formato do arquivo é suportado? Execute o corpus `7_extensions/`.
2. OCR está habilitado para imagens? `ocr.enabled: true`
3. O formato de PII é reconhecido? Execute o corpus `1_happy/` — CPF `123.456.789-09` deve ser encontrado.
4. Os dados estão dentro de um arquivo compactado? `file_scan.scan_archives: true`
5. O encoding é não-UTF-8? Verificar tratamento de latin-1, windows-1252.

---

## Categoria D — Erros de dashboard / UI

### D-001: Página em branco ou erro 500

**Correção:**

```bash
docker logs data_boar 2>&1 | tail -50
curl http://localhost:8088/health
```

---

### D-002: Heatmap vazio (404)

**Causa:** Nenhum scan concluído ou ID de sessão errado.

**Correção:** POST `/scan`, aguardar conclusão (`GET /status`), depois `GET /list` para obter o ID de sessão.

---

## Categoria E — Performance

### E-001: Scan muito lento

**Correção:**

```yaml
scan:
  sample_limit: 100
  file_sample_max_chars: 5000
  max_workers: 2
```

---

### E-002: API sem resposta sob carga

**Correção:**

```yaml
api:
  workers: 2
```

Também verificar: `docker stats data_boar`

---

## Template de coleta de métricas

Após `run_poc_error_scenarios.py`, compartilhe a saída JSON. Para achados manuais:

```json
{
  "scenario": "B1",
  "observed_http_code": 422,
  "observed_body": "...",
  "latency_ms": 340,
  "expected": "202 (scan inicia)",
  "finding": "Porta como string aceita sem erro",
  "recommendation": "Adicionar validador int para campo port",
  "severity": "MEDIUM",
  "reproduced_by": "tester-1",
  "date": "2026-04-06",
  "github_issue": "#XX"
}
```

Abra uma issue no GitHub em <https://github.com/FabioLeitao/data-boar/issues> com o JSON.

---

## Documentação relacionada

- `scripts/run_poc_error_scenarios.py` — executor automatizado
- `tests/postman/Data_Boar_POC_ErrorScenarios.postman_collection.json` — collection Postman
- `scripts/generate_synthetic_poc_corpus.py` — dados sintéticos
- `docs/TESTING_POC_GUIDE.md` — guia completo de validação
- `docs/USAGE.pt_BR.md` — referência de configuração

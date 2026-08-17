# Cloudflare GraphQL Analytics → OTLP / Grafana (#1599)

**English:** [CLOUDFLARE_GRAPHQL_OTLP_EXPORT.md](CLOUDFLARE_GRAPHQL_OTLP_EXPORT.md)

**Objetivo:** Agendar um exporter **server-side** que consulta a **GraphQL Analytics** da Cloudflare (`httpRequestsAdaptiveGroups`) e emite **métricas agregadas normalizadas** para um collector OTLP / Grafana do operador.

**Fora de escopo:** mudanças de DNS/Workers/Tunnel, Google Analytics, tokens Cloudflare no browser, ou afirmar que esses agregados são **traces distribuídos**.

**Sinais ortogonais:**

| Sinal | `service.name` / origem | Superfície |
| ----- | ----------------------- | ---------- |
| Agregados de **edge** Cloudflare (este doc) | `cloudflare-edge` | GraphQL → métricas OTLP |
| RUM **Faro** do DataBoar Site | browser / Faro | RUM frontend (dashboard separado) |
| OTel do produto Data Boar | `data-boar` (app) | `DATA_BOAR_OTEL_ENABLED` |

JSON do dashboard (somente edge): [`dashboards/cloudflare-edge-metrics.json`](dashboards/cloudflare-edge-metrics.json). **Não** misturar com painéis Faro RUM.

## Segurança e privacidade

- **Token de produção:** API token com escopo de **zona** e permissão **Analytics Read**. Defina `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ZONE_ID` via env / injeção de segredo — **nunca** commitar ou imprimir.
- **Não** dependa de token **all-zones** em export agendado de produção. `CLOUDFLARE_ALLOW_ALL_ZONES_FOR_LOCAL_TEST` só documenta a recusa (export sem zona **não** está implementado); use `--fixture` para local/CI.
- O exporter **não** pede IP, URL/path/query crua, referrer, User-Agent ou cookies como dimensões GraphQL.
- Labels limitados: allowlist de hostname / máximo de hosts, `http.status_class`, `cloudflare.cache_status` allowlisted.
- Credenciais Grafana / OTLP ficam no **host do collector** — nunca em HTML/JS do browser.

## Ambiente

| Variável | Papel |
| -------- | ----- |
| `CLOUDFLARE_API_TOKEN` | Analytics Read com escopo de zona (somente live) |
| `CLOUDFLARE_ZONE_ID` | Zone tag do filtro GraphQL |
| `CLOUDFLARE_GRAPHQL_URL` | Padrão `https://api.cloudflare.com/client/v4/graphql` |
| `CLOUDFLARE_HOSTNAME_ALLOWLIST` | Lista opcional (ex.: `databoar.com.br`) |
| `CLOUDFLARE_EXPORT_LOOKBACK_MINUTES` | Padrão `60` sem watermark |
| `CLOUDFLARE_EXPORT_OVERLAP_MINUTES` | Padrão `0` (evita double-count em counters OTLP) |
| `CLOUDFLARE_EXPORT_LAG_MINUTES` | Padrão `5` (atraso de frescor da Analytics) |
| `CLOUDFLARE_EXPORT_LIMIT` | `limit` GraphQL (padrão `1000`, teto `5000`) |
| `CLOUDFLARE_EXPORT_WATERMARK_PATH` | Padrão `~/.cache/data-boar/cloudflare_edge_watermark.txt` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | Collector (padrão loopback `:4317`) |

Extra opcional: `uv sync --extra otel`.

## Contrato da query

- **Dataset:** `httpRequestsAdaptiveGroups`.
- **Filtro:** janela meio-aberta `datetime_geq` / `datetime_lt` + `requestSource: "eyeball"`.
- **Dimensões:** `datetimeHour`, `clientRequestHTTPHost`, `cacheStatus`, `edgeResponseStatus` → classe de status no exporter.
- **Medidas:** `count`, `sum.visits`, `sum.edgeResponseBytes`.
- **Caveat de visits:** definição Cloudflare (referer host ≠ hostname ou direto); **não** é visitantes únicos.

## Execução

```bash
uv run python scripts/cloudflare_graphql_otel_export.py \
  --fixture tests/fixtures/cloudflare/http_requests_adaptive_groups.json \
  --dry-run --no-watermark
```

Windows: `.\scripts\cloudflare-graphql-otel-export.ps1`.

### Agendamento / rollback

Cron / systemd / Task Scheduler a cada 5–15 min. Watermark + overlap evitam buracos; lag evita buckets incompletos. Retries em HTTP 429 / 5xx.

**Desligar:** pare o agendador; revogue/rotacione o token; remova o dashboard se quiser. Nenhum caminho de produto depende deste job.

## Referências

- [Cloudflare GraphQL Analytics](https://developers.cloudflare.com/analytics/graphql-api/)
- [PLAN_CROSS_SURFACE_OBSERVABILITY.md](../plans/PLAN_CROSS_SURFACE_OBSERVABILITY.md)
- [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)
- [GRAFANA_CLOUD_REACTIVATION.pt_BR.md](GRAFANA_CLOUD_REACTIVATION.pt_BR.md)

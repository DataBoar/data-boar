# Grafana dashboard exports (operator)

Tracked JSON imports for Grafana. **No credentials** in these files.

| File | Signal | `service.name` / notes |
| ---- | ------ | ---------------------- |
| [cloudflare-edge-metrics.json](cloudflare-edge-metrics.json) | Cloudflare GraphQL edge aggregates (#1599) | `cloudflare-edge` — **not** Faro, **not** traces |
| [data-boar-site-faro-rum.json](data-boar-site-faro-rum.json) | DataBoar Site Faro RUM (#1604) | Browser RUM — **separate** UID/title; do not merge panels with edge |

Import via Grafana UI (**Dashboards → Import**) or API. Datasource UIDs (`grafanacloud-prom`, etc.) are placeholders — rebind to your stack after import.

Runbook: [CLOUDFLARE_GRAPHQL_OTLP_EXPORT.md](../CLOUDFLARE_GRAPHQL_OTLP_EXPORT.md).

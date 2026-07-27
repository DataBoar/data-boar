# Resolução de problemas: Conectividade e timeouts

**English:** [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md)

**Ver também:** [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md) (visão geral e dicas rápidas).

Este documento ajuda a diagnosticar e corrigir falhas **unreachable**, **timeout** e **permission_denied** ao varrer bancos de dados, APIs ou shares de arquivos (incluindo NFS/SMB). Aplica-se a implantações em host e em Docker; para rede e volumes específicos de Docker, veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md).

---

## 1. O que o relatório e o app mostram

- **Planilha Scan failures:** Colunas **Target**, **Reason**, **Details**, **Suggested next step**. **Reason** é um de: `unreachable`, `auth_failed`, `permission_denied`, `timeout`, `error`. **Suggested next step** é gerado a partir desse motivo; **Details** traz a mensagem bruta da exceção.
- **failure_hint (no código):** O app mapeia esses motivos para texto curto e acionável (ex.: para `timeout`: "Operation timed out. Check for high latency…"). Se a dica não bastar, use este doc.

---

## 2. Unreachable (alvo não respondeu)

**O que procurar:** Reason `unreachable`; Details com connection refused, no route to host ou falha de resolução de nome.

### 2.1 Checklist

1. **Alcance do host (ou container) de auditoria:** É possível pingar ou conectar na mesma máquina/container que roda o Data Boar? Em Docker, teste de dentro do container (`docker exec <container> ping <db-host>` ou `nc -zv <host> <port>`).
1. **DNS:** Se o config usa hostname, resolva no host/container: `getent hosts <hostname>` ou `nslookup <hostname>`. Se falhar, corrija DNS ou use o IP no config.
1. **Firewall:** Saída do host/container para a porta do alvo (ex.: 5432 PostgreSQL, 445 SMB, 443 HTTPS). Entrada no servidor alvo deve permitir o IP do host/container.
1. **VPN:** Se o alvo só é acessível por VPN, a VPN deve estar ativa no host (ou o container usar rede do host, se aplicável).
1. **Host/porta/caminho errado no config:** Erro de digitação em `host`, `port`, `base_url` ou `path`. Confira com o endereço real do alvo.

### 2.2 Passos para corrigir

Corrija DNS (use IP ou servidor DNS correto); abra firewall para a porta necessária; corrija `host`, `port` ou URL no config e reexecute a varredura. Em Docker, veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md).

---

## 3. Timeout

**O que procurar:** Reason `timeout`; Details com timeout de conexão/httpx.

### 3.1 Checklist

1. **Alvo lento ou sobrecarregado:** Alta latência ou carga no DB/API; tente em horário de menor uso.
1. **Timeout baixo no config:** Alvos REST/API aceitam `timeout` (segundos). Aumente (ex.: 60 ou 120) se o alvo for lento.
1. **Latência de rede:** Caminho entre regiões ou congestionado; aumente timeout ou rode o scanner mais perto do alvo.
1. **Banco de produção frágil com scan paralelo:** Pouca memória ou sem swap — `scan.max_workers` alto pode amplificar latência ou parecer DoS. Tente `scan.adaptive_rate_limit: true` com `target_latency_ms` realista (padrão 200); veja [USAGE.pt_BR.md](USAGE.pt_BR.md) § *Limitação de taxa adaptativa (ARL)*. `max_workers: 1` fixo continua sendo a alternativa manual.

### 3.2 Passos para corrigir

No config, defina `timeout` maior para o alvo que falha (veja [USAGE.pt_BR.md](USAGE.pt_BR.md)). Reexecute em horário de menor uso ou de um host/região mais próxima do alvo.

---

## 4. Permission denied

**O que procurar:** Reason `permission_denied`; Details com "access denied" ou "forbidden".

Verifique credenciais (usuário/senha ou token; veja [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md)). A conta do scanner deve ter **leitura** no recurso (tabelas/views do DB, caminho do share, endpoints da API). Em shares, o caminho deve ser legível pelo usuário que roda o app (ou usuário do container).

---

## 5. Erro genérico ("error")

**O que procurar:** Reason `error`; Details variados (host ausente, URL ausente, "module not found").

Causas comuns: campo obrigatório ausente (`host`, `port`, `base_url`, `share` para SMB); dependência opcional não instalada (SMB/NFS precisam de `.[shares]`; MongoDB/Redis de `.[nosql]`). Leia **Details** na planilha Scan failures; em geral indica o valor ausente ou inválido. Instale os extras opcionais se o conector exigir; corrija o config e reexecute.

---

**Índice da documentação:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). **Visão geral:** [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md).

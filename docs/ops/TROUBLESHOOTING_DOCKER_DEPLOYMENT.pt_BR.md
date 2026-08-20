# Resolução de problemas: Implantação Docker e rede do container

**English:** [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](TROUBLESHOOTING_DOCKER_DEPLOYMENT.md)

**Ver também:** [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md) (visão geral e dicas rápidas).

Este documento ajuda quando o Data Boar roda **dentro de um container Docker ou Podman** e precisa conectar a **bancos remotos**, **shares NFS/SMB** ou **APIs**. Aborda alcance de rede a partir do container, DNS e como usar shares montadas no host vs alvos NFS/SMB. Hostnames e rede rootless do Podman estão na **§ 6**. O **`HEALTHCHECK`** da imagem / `healthcheck` do Compose (`GET /health` no loopback **8088**, distroless) está na **§ 7**.

---

## 1. Bancos de dados remotos de dentro do container

**Cenário:** Config tem alvo de banco (PostgreSQL, MySQL, etc.) mas a varredura falha com **unreachable** ou connection refused.

Use **hostname ou IP** que o container consiga resolver e alcançar. **Não** use `localhost` no config para um DB que roda no **host** ou em outra máquina (dentro do container, `localhost` é o próprio container). Use o **IP do host** na bridge Docker (ex.: `172.17.0.1`) ou o **hostname** do servidor de DB. No Docker Desktop (Windows/Mac), muitas vezes dá para usar **`host.docker.internal`** como host do DB. Garanta que o servidor de DB escute em um endereço acessível pelo container (ex.: `0.0.0.0`), não só `127.0.0.1`.

**Checklist:** (1) No **host**, teste com psql/mysql. (2) A imagem publicada é **distroless** (sem `/bin/sh`, sem `nc`). `docker exec <container> nc -zv …` **falha** em `fabioleitao/data_boar`. Use um container de debug descartável na **mesma rede**, ou teste no host (`docker inspect`, `docker port`). Veja **§ 6** e **§ 7**. (3) **DNS:** Se o config usa hostname, o container precisa resolvê-lo; use `--dns` ou `--network host` (Linux) conforme necessário.

**Passos:** Defina `host` no config como IP ou hostname alcançável pelo container (`host.docker.internal` para serviços no host no Docker Desktop). Garanta que o servidor de DB permita conexões do IP do container. Se a resolução falhar, corrija o DNS do container ou use IP no config.

---

## 2. NFS ou SMB a partir do container (duas abordagens)

**Abordagem A (recomendada quando possível):** Monte o share **no host** (ex.: `/mnt/nfs-audit`). Rode o container com bind mount: `-v /mnt/nfs-audit:/data/shared`. No config, use um alvo **filesystem** com `path: /data/shared`. O app só lê arquivos nesse caminho; não precisa de cliente NFS/SMB no container. **Prós:** Sem cliente no container; sem firewall extra do container para o servidor NFS/SMB.

**Abordagem B:** Use alvo **NFS/SMB** no config (host, share, path, credenciais). A **imagem** precisa incluir o extra **shares** (bibliotecas NFS/SMB). O **container** precisa alcançar o servidor NFS (portas 2049, 111) ou SMB (445). Abra o firewall de saída do container para essas portas; use DNS se usar hostnames. **Prós:** Config autocontido. **Contras:** Rede e firewall corretos; imagem com suporte a shares.

**Quando falha:** "Missing host" / "Missing share name" → preencha host, share (SMB) e path. "unreachable" → container não alcança o servidor; verifique firewall e teste com `docker exec <container> nc -zv <server> 445` (SMB) ou `2049` (NFS). "smbprotocol not installed" → instale o extra e reconstrua a imagem. "auth_failed" → credenciais do share; veja [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](../TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md).

---

## 3. DNS de dentro do container

Se o config usa **hostnames**, o container precisa resolvê-los. Sintoma: "unreachable" ou "name or service not known" com hostname em Details. **Solução:** Rode com `--dns <ip-dns>` (ex.: 8.8.8.8) ou use **IPs** no config para teste. No Compose/Kubernetes, defina `dns` no serviço.

---

## 4. Volumes e caminho do config

O config deve estar disponível **dentro** do container. Setup típico: diretório no host `./data` com `config.yaml` → monte com `-v "$(pwd)/data:/data"` e defina `CONFIG_PATH=/data/config.yaml`. **sqlite_path** e **report.output_dir** devem ficar no volume montado (ex.: `/data/audit_results.db`, `/data/reports`) para persistência e leitura dos relatórios no host. Se o app reportar "config not found", confira `CONFIG_PATH` e o mount (`docker exec <container> cat /data/config.yaml`).

---

## 5. Resumo

| Objetivo                                | Abordagem recomendada                                                                                                                                    |
| ----------                              | ------------------------                                                                                                                                 |
| Varrer DB no host a partir do container | Use `host.docker.internal` (ou IP do host) como host do DB; garanta que o DB escute e o firewall permita o container.                                    |
| Varrer arquivos em NFS/SMB              | A) Monte o share no host, bind mount no container, alvo filesystem. B) Alvo NFS/SMB no config; imagem com `.[shares]`; rede do container até o servidor. |
| Container não resolve hostname          | Defina `--dns` ou use IP no config.                                                                                                                      |
| Config ou relatórios não encontrados    | Monte volume em `/data`; CONFIG_PATH=/data/config.yaml; sqlite_path e report.output_dir em `/data`.                                                      |
| DB no host a partir do **Podman**       | Use `host.containers.internal` (não `host.docker.internal`); rootless usa slirp4netns/pasta, não a bridge do Docker.                                     |
| Status **unhealthy** do container       | A sonda é `GET http://127.0.0.1:8088/health` **dentro** do container (`urllib` da stdlib, exec JSON). Mantenha o processo escutando na porta **8088** no container. |

---

## 6. Diferenças do Podman (rootless e rootful)

Se você roda o Data Boar com **Podman** em vez do Docker Engine, a maior parte da orientação acima ainda vale. Exemplos de pull/run: [DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md) §10 ([EN](../deploy/DEPLOY.md)).

| Tópico | Docker | Podman |
| ------ | ------ | ------ |
| Serviços do host a partir do container | `host.docker.internal` (Docker Desktop; no Linux costuma precisar de host-gateway extra) | `host.containers.internal` (Podman típico — **não** assuma `host.docker.internal`) |
| Rede | Bridge via `dockerd` | Rootless: **slirp4netns** ou **pasta**; rootful: netavark/CNI |
| Bind de porta abaixo de 1024 | Em geral precisa de root | Rootless: ajuste `net.ipv4.ip_unprivileged_port_start` ou use porta ≥ 1024 (o padrão do Data Boar **8088** serve) |
| Volumes | `-v /host/path:/container/path` | Mesma sintaxe; no rootless costuma precisar de `:Z`/`:z` (SELinux) e às vezes `--userns=keep-id` para o UID **65532** da imagem ler o bind mount |

**Correção comum:** um banco no **host** fica inacessível a partir de um container Podman **rootless** se o config ainda usa `host.docker.internal`. Defina o `host` do alvo como **`host.containers.internal`**, ou um IP que o container consiga roteiar (LAN do host / gateway em `podman inspect` — **não** `localhost`).

A imagem publicada do Data Boar é **distroless**: **não** há `/bin/sh` nem `ip`/`nc` dentro do container. Não espere que `podman exec <nome> ip route` ou `sh -c 'nc …'` funcione em `data_boar`. Depure no **host** (`podman port`, `podman inspect`) ou use um container de debug descartável na mesma rede.

Hosts de laboratório **completão** / Maestro que usam Podman seguem os mesmos padrões de hostname no config e de volumes; substitua `docker` / `docker compose` por `podman` / `podman-compose`.

---

## 7. HEALTHCHECK da imagem vs “unhealthy” (distroless)

A imagem publicada declara um **`HEALTHCHECK`** Docker (`Dockerfile`). O Compose repete a mesma sonda em `deploy/docker-compose.yml` (`healthcheck.test`). Os dois chamam **`urllib` da biblioteca padrão** — **não** `curl`, **não** um shell — porque o distroless não tem `/bin/sh`.

**O que a sonda faz:** `GET http://127.0.0.1:8088/health` **de dentro** do container. `GET /health` permanece **público** mesmo com `api.require_api_key` ligado ([USAGE.pt_BR.md](../USAGE.pt_BR.md)). Mapear uma porta no **host** (`-p 9002:8088`) **não** altera a sonda: ela continua no **8088 do loopback**.

| Origem | Intervalo | Timeout | Período inicial | Tentativas |
| ------ | --------- | ------- | --------------- | ---------- |
| `HEALTHCHECK` da imagem | 30s | 10s (timeout HTTP da sonda 8s) | 15s | 3 |
| `healthcheck` do Compose | 15s | 5s | 20s | 3 |

### Causas comuns de “unhealthy”

1. **O CMD não é o dashboard na 8088.** O `CMD` padrão é `main.py --web --port 8088`. Um override CLI de uma só varredura (`--config …` sem `--web`), `--check-extras`, ou `--port` diferente de **8088** deixa a URL da sonda sem listener. O Docker marca **unhealthy** mesmo que o processo CLI esteja fazendo trabalho útil.
1. **O processo ainda não escuta.** Respeite `start-period` / `start_period`. Bind mount lento ou criação do SQLite na primeira subida pode perder as primeiras sondas.
1. **Você esperava `docker exec … curl /health`.** Esse binário **não** está na imagem. No host: `curl http://127.0.0.1:<porta-publicada>/health` (depois do publish da porta). De outro container na mesma rede: use o **nome do serviço** e a porta **8088**.
1. **HEALTHCHECK em forma de shell num Dockerfile próprio.** `HEALTHCHECK CMD curl …` falha no distroless. Mantenha a forma exec JSON com `/usr/local/bin/python3.14` como no `Dockerfile` do repositório.

**Como confirmar:** `docker inspect --format '{{.State.Health.Status}}' <nome>` (ou `podman inspect`). Em seguida `curl` em `/health` na porta **publicada** no host. O JSON esperado inclui `"status"` (em geral `"ok"`) — veja [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md) e [deploy/DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md).

---

**Índice da documentação:** [README.md](../README.md) · [README.pt_BR.md](../README.pt_BR.md). **Visão geral:** [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md). **Deploy:** [deploy/DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md).

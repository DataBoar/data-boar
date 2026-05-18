# Implantar o Data Boar (Docker, Compose, Swarm, Kubernetes)

**English:** [DEPLOY.md](DEPLOY.md)

Você pode executar a aplicação com **Docker** (`docker run`), **Docker Compose**, **Docker Swarm** ou **Kubernetes** — escolha a opção que se adequa ao seu ambiente. Todas usam a mesma imagem; o comportamento padrão é API web e frontend na porta 8088.

## Padrão: API web e frontend

Quando você executa a imagem **sem** sobrescrever o comando (ex.: `docker run ... imagem`, Compose, Swarm ou Kubernetes sem `command`/`args`), o container inicia a **API web e o frontend**:

- **Dashboard:** `http://<host>:8088/` (status, botão **Iniciar varredura**, sessões recentes, download de relatórios).
- **Relatórios:** `http://<host>:8088/reports`
- **Configuração:** `http://<host>:8088/config`
- **Documentação da API:** `http://<host>:8088/docs`
- **Health:** `http://<host>:8088/health`

A porta **8088** é exposta. Config e dados persistentes (SQLite, relatórios) ficam em **`/data`** (monte um volume ou bind mount com `config.yaml`).

## CLI one-shot (sobrescrever)

Para rodar **uma única auditoria pela CLI** em vez da API, sobrescreva o comando do container e passe o config (e opcionalmente `--tenant` / `--technician`):

```bash
docker run --rm -v "$(pwd)/data:/data" \
  SUA_IMAGEM \
  python main.py --config /data/config.yaml --tenant "Acme" --technician "Ops"
```

Ou com `--entrypoint`:

```bash
docker run --rm -v "$(pwd)/data:/data" \
  --entrypoint python \
  SUA_IMAGEM \
  main.py --config /data/config.yaml
```

O relatório é escrito em `report.output_dir` do config (ex.: `/data`). **Não** use `--web` nessas sobrescritas.

## Imagem pré-construída no Docker Hub

Você pode executar a aplicação **sem clonar o repositório** usando a imagem publicada no Docker Hub:

- **Docker Hub:** [hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar) — **`fabioleitao/data_boar:latest`** e **`fabioleitao/data_boar:1.7.3`**

Exemplo:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```

Garanta que `/data/config.yaml` exista (ex.: copie de `deploy/config.example.yaml` no repositório). Para atualizar quando novas versões forem publicadas: `docker pull fabioleitao/data_boar:latest` e reinicie o container ou stack.

## Imagem (build a partir do código)

- **Dockerfile** na raiz do repositório. Build (marca Data Boar): `docker build -t fabioleitao/data_boar:latest .` ou tag local: `docker build -t data_boar:latest .`
- O Dockerfile usa **multi-stage build** em **`python:3.13-slim`** (`requires-python >=3.12`; CI em 3.12 e 3.13): a etapa final contém apenas bibliotecas de runtime e o código da aplicação (sem ferramentas de build), reduzindo tamanho e superfície de ataque.

## 1. Build e push da imagem

### Opção A – GitHub Container Registry (ghcr.io)

```bash
docker build -t ghcr.io/fabioleitao/data_boar:latest .
docker login ghcr.io
docker push ghcr.io/fabioleitao/data_boar:latest
```

### Opção B – Docker Hub (imagem branded Data Boar)

```bash
docker build -t fabioleitao/data_boar:latest -t fabioleitao/data_boar:1.7.3 .
docker login
docker push fabioleitao/data_boar:latest
docker push fabioleitao/data_boar:1.7.3
```

Veja também [DOCKER_SETUP.md](../DOCKER_SETUP.md).

## 2. Preparar o config

A aplicação espera **config em `/data/config.yaml`** dentro do container. Use o mesmo esquema do repositório (veja [USAGE.md](../USAGE.md) e [USAGE.pt_BR.md](../USAGE.pt_BR.md)). Mínimo para apenas API: `targets: []`, `report.output_dir: /data`, `sqlite_path: /data/audit_results.db`, `api.port: 8088`.

**Detecção de sensibilidade (ML/DL):** Configure termos de treino via `ml_patterns_file`, `dl_patterns_file` ou `sensitivity_detection.ml_terms` / `dl_terms` no config. Monte seus arquivos de termos em `/data`. Veja [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) e [SENSITIVITY_DETECTION.pt_BR.md](../SENSITIVITY_DETECTION.pt_BR.md).

Copie `deploy/config.example.yaml`, edite e use volume ou bind mount para `/data`.

### Segurança e endurecimento (opcional)

Práticas opcionais para endurecer a implantação. Veja [SECURITY.md](../../SECURITY.md). A imagem já roda como usuário não-root (`appuser`, UID 1000). Para Kubernetes, você pode adicionar securityContext, NetworkPolicy e PDB (exemplos em `deploy/kubernetes/`). **Em produção**, defina `api.require_api_key: true` e use uma chave forte via variável de ambiente (ex.: `api.api_key_from_env: "AUDIT_API_KEY"`) para não armazenar credenciais no config.

## 3. Executar como container único (docker run)

```bash
mkdir -p data
cp deploy/config.example.yaml data/config.yaml
# Edite data/config.yaml

docker build -t data_boar:latest .
docker run -d --name data-boar-audit \
  -p 8088:8088 \
  -v "$(pwd)/data:/data" \
  -e CONFIG_PATH=/data/config.yaml \
  data_boar:latest
```

Acesso: <http://localhost:8088/> (dashboard), <http://localhost:8088/docs> (API). Parar: `docker stop data-boar-audit && docker rm data-boar-audit`.

## 4. Executar com Docker Compose

Use o arquivo Compose em `deploy/` e opcionalmente um override para bind mount do config:

```bash
mkdir -p data
cp deploy/config.example.yaml data/config.yaml
cp deploy/docker-compose.override.example.yml deploy/docker-compose.override.yml

docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d
```

Logs: `docker compose -f deploy/docker-compose.yml logs -f data-boar`. Parar: `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml down`.

## 5. Docker Swarm

Use o mesmo Compose com `docker stack deploy`:

```bash
docker swarm init
# Com override para bind mount ./data
docker stack deploy -c deploy/docker-compose.yml -c deploy/docker-compose.override.yml data-boar-audit
```

Remover: `docker stack rm data-boar-audit`.

## 6. Kubernetes

Manifests em `deploy/kubernetes/`. Defina a imagem em `deploy/kubernetes/deployment.yaml`. Aplique:

```bash
kubectl apply -f deploy/kubernetes/
```

Detalhes (NodePort, LoadBalancer, Ingress, persistência) em `deploy/kubernetes/README.md`.

## 7. Usar a imagem pública (sem build local)

Em `deploy/docker-compose.yml` defina `image: fabioleitao/data_boar:latest` e remova ou comente o bloco `build:`. Prepare `/data/config.yaml` como na seção 2 e use docker run, Compose, Swarm ou Kubernetes como acima.

## 8. Docker Hub: tags suportadas e descontinuação de imagens antigas

**Por que importa:** Tags públicas continuam **puxáveis** até você removê-las no Docker Hub. Limpar tags **obsoletas** reduz o reuso casual de builds antigos (CVEs, padrões errados) e alinha a documentação ao que você realmente suporta.

1. **Inventário:** No [Docker Hub](https://hub.docker.com/r/fabioleitao/data_boar/tags), liste as tags; anote o que CI, parceiros ou docs fixam (ex.: `latest`, `1.6.5`).
1. **Política de suporte:** Em geral mantenha **`latest`** mais o **semver atual** (e opcionalmente um semver anterior para rollback). Documente o conjunto suportado aqui; mantenedores podem espelhar a matriz em **Interno e referência** em [README.md](../README.md) ou [SECURITY.md](../SECURITY.md) quando fizer sentido.
1. **Excluir no Hub:** Hub → repositório → **Tags** → exclua tags que não suporta mais. **Aviso:** quem já deu `pull` ainda tem a imagem local; a exclusão só impede *novos* pulls pelo Hub.
1. **Automação:** Ajuste CI/CD e manifests Compose/Kubernetes para não referenciar tags removidas.
1. **Comercial / IP:** Higiene de tags **não** substitui licenciamento ou repositório privado do emissor; complementa. Veja [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md) (EN) e [CODE_PROTECTION_OPERATOR_PLAYBOOK.pt_BR.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.pt_BR.md).

**English:** [DEPLOY.md §8](DEPLOY.md#8-docker-hub-supported-tags-and-retiring-old-images).

## 9. Backup e restore (dados persistentes)

Em implantações típicas, o estado fica sob **`/data`** (volume ou bind mount): **`config.yaml`**, o arquivo **SQLite** de `sqlite_path` (padrão **`/data/audit_results.db`**) e os **relatórios** em `report.output_dir` (muitas vezes `/data` ou um subdiretório). Arquivos opcionais (ex.: YAML de termos ML/DL) entram no mesmo conjunto se o `config.yaml` apontar para eles.

#### O que fazer backup

- Copiar ou gerar snapshot do **diretório inteiro** ou do volume montado em **`/data`** (ou o conteúdo do PVC no Kubernetes), preservando config, banco, relatórios e arquivos auxiliares referenciados no config.

#### Como restaurar

1. Parar o container, stack Compose, serviço Swarm ou escalar o Deployment para zero.
1. Restaurar os arquivos no mesmo caminho de montagem (`/data` dentro do container).
1. Garantir **permissões/dono** compatíveis com o usuário da imagem (**UID 1000** / `appuser`) em bind mounts em Linux.
1. Subir de novo; verificar **`GET /health`** e um scan curto ou o dashboard.

#### Notas operacionais

- Prefira **chave de API por variável de ambiente** (`api.api_key_from_env`) para que segredos não dependam só de arquivos incluídos no backup de disco — veja [SECURITY.md](../../SECURITY.md).
- Para recuperação ao longo do tempo, registre a **tag ou digest da imagem** usada (ex.: `fabioleitao/data_boar:1.7.3`) junto com o backup de dados.

**English:** [DEPLOY.md §9](DEPLOY.md#9-backup-and-restore-persistent-data).

## Resumo

| Objetivo              | Comando / passo                                                                                     |
| --------------------- | -------------------------------------------------------------------------------                     |
| Padrão (API + front)  | Executar imagem sem sobrescrever comando                                                            |
| CLI one-shot          | `docker run ... --entrypoint python IMAGE main.py --config /data/config.yaml`                       |
| Build                 | `docker build -t data_boar:latest .` ou `docker build -t fabioleitao/data_boar:latest .`            |
| Push                  | `docker tag ... fabioleitao/data_boar:latest` e `docker push ...`                                   |
| **Container único**   | `docker run -d -p 8088:8088 -v ./data:/data data_boar:latest`                                       |
| **Compose**           | `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d`           |
| **Swarm**             | `docker stack deploy -c deploy/docker-compose.yml -c deploy/docker-compose.override.yml data-boar-audit` |
| **Kubernetes**        | `kubectl apply -f deploy/kubernetes/`                                                               |
| **Backup / restore**  | Dados em `/data` (seção 9): backup do volume ou bind mount; restaurar com o mesmo layout e validar `/health` |

## Atrás de NAT, load balancer ou proxy reverso

A aplicação funciona corretamente atrás de **NAT**, **load balancer** ou **proxy reverso** (nginx, Traefik, Caddy). Se HTTPS for terminado no proxy, defina **X-Forwarded-Proto: https** nas requisições. Veja [SECURITY.md](../../SECURITY.md) para cabeçalhos de segurança HTTP. Nos exemplos de Docker e Kubernetes, a porta 8088 é exposta via bindings do container/Service, então é seguro manter o bind interno da API em `0.0.0.0` **dentro do container**, enquanto, em estações de trabalho (CLI direto), o padrão recomendado é `127.0.0.1` (loopback), com `api.host: 0.0.0.0` usado apenas quando o ambiente estiver devidamente cercado por políticas de rede, Ingress ou proxy reverso.

**Índice da documentação** (todos os tópicos, ambos os idiomas): [../README.md](../README.md) · [../README.pt_BR.md](../README.pt_BR.md). **Guia técnico:** [../TECH_GUIDE.md](../TECH_GUIDE.md) · [../TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md).

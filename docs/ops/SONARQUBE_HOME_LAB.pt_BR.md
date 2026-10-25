# SonarQube em home lab (Docker) — CI, IDE e MCP

**English:** [SONARQUBE_HOME_LAB.md](SONARQUBE_HOME_LAB.md)

Este guia ajuda a rodar o **SonarQube Server** numa segunda máquina (VM Linux ou host de containers) para:

- Apontar o **GitHub Actions** para ele (o mesmo job de `.github/workflows/ci.yml` quando `SONAR_TOKEN` e `SONAR_HOST_URL` estão definidos).
- Ligar o **Cursor / VS Code** (extensão SonarQube e/ou **MCP SonarQube**) ao mesmo servidor.

Complementa [`.cursor/rules/sonarqube_mcp_instructions.mdc`](../../.cursor/rules/sonarqube_mcp_instructions.mdc) (como o **agente** deve usar as ferramentas MCP) e [`sonar-project.properties`](../../sonar-project.properties) (o que analisamos). Para testes e lint do dia a dia, veja [TESTING.pt_BR.md](TESTING.pt_BR.md).

---

## 1. O que precisa no servidor de lab

| Recurso   | Mínimo prático            | Notas                                                         |
| -------   | --------------            | -----                                                         |
| **RAM**   | **4 GB** (SonarQube + BD) | 8 GB+ é mais confortável.                                     |
| **Disco** | **20 GB+** livres         | SSD recomendado; histórico cresce.                            |
| **CPU**   | 2 vCPU                    | Mais núcleos ajudam.                                          |
| **SO**    | Linux x86_64              | Docker ou Podman.                                             |
| **Rede**  | Acessível do seu PC       | Para IDE/MCP. Para **runners hospedados no GitHub**, veja §6. |

---

## 2. Kernel Linux (`vm.max_map_count`)

No **host** Docker:

```bash
sudo sysctl -w vm.max_map_count=524288
echo 'vm.max_map_count=524288' | sudo tee /etc/sysctl.d/99-sonarqube.conf
sudo sysctl --system
```

---

## 3. Docker Compose

Use o mesmo `docker-compose.yml` e `.env` descritos na versão em inglês: [SONARQUBE_HOME_LAB.md §3](SONARQUBE_HOME_LAB.md#3-docker-compose-sonarqube--postgresql).

Resumo: serviços `sonarqube` (imagem `sonarqube:community`, porta **9000**) e `postgres:16-alpine`, volumes nomeados, variável `SONAR_DB_PASSWORD` no `.env`.

```bash
docker compose up -d
```

Abra `http://<ip-do-servidor>:9000`, login inicial **admin/admin**, **altere a senha**.

---

## 4. Projeto e token

1. Crie projeto com **Project key** igual a `sonar.projectKey` no repositório (`data-boar`).
1. **Token de usuário** (não token de projeto): **My Account → Security → Generate Tokens** (ver regra MCP sobre tokens de usuário).
1. **Secrets no GitHub:** `SONAR_TOKEN`, `SONAR_HOST_URL` (URL base, sem barra final). Em servidor próprio **não** use `sonar.organization` (isso é SonarCloud).
1. **XML de cobertura:** o job Sonar **baixa** o artefato **`coverage-xml`** da célula Test em Python **3.13** (`pytest --cov --cov-report=xml`). `sonar.python.coverage.reportPaths=coverage.xml`. Se o job Test falhar antes do upload, o Sonar nem começa. Cobertura **0%** com o job Sonar verde costuma ser artefato ausente ou `--cov` pulado. Detalhes: [TESTING.pt_BR.md](../TESTING.pt_BR.md) *CI*.

Scripts locais:

```bash
export SONAR_HOST_URL=http://<seu-host-sonar>:9000   # hostname ou IP da LAN; não commite valores reais no repositório público
export SONAR_TOKEN=squ_xxxxxxxx
uv run python scripts/sonar_issues.py
```

---

## 5. Extensão SonarQube no Cursor/VS Code

Instale a extensão SonarSource, ligue **connected mode** com a mesma URL e token de usuário, projeto alinhado a `sonar-project.properties`.

---

## 6. GitHub Actions e rede (crítico)

Os runners **hospedados** na cloud da GitHub **não** alcançam um IP **só da sua LAN**.

Opções:

- **Expor** o SonarQube com HTTPS (proxy, Tailscale, Cloudflare Tunnel, etc.), **ou**
- Usar **runner self-hosted** na mesma rede que o SonarQube (URL interna).

Ver detalhes em [SONARQUBE_HOME_LAB.md §6](SONARQUBE_HOME_LAB.md#6-github-actions-vs-home-lab-networking-important).

---

## 7. Segurança (checklist)

- Mudar senha **admin** logo.
- Preferir **HTTPS** e firewall restrito.
- Tratar `SONAR_TOKEN` como segredo; fazer backup dos volumes se precisar do histórico.

---

## 8. MCP no Cursor

Variáveis típicas: URL base + token de usuário (iguais à extensão). Comportamento do agente: [`.cursor/rules/sonarqube_mcp_instructions.mdc`](../../.cursor/rules/sonarqube_mcp_instructions.mdc). Configure em **Cursor Settings → MCP** conforme o README do servidor MCP que instalar.

---

## 9. Ver também

- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) ([pt-BR](HOMELAB_VALIDATION.pt_BR.md)) — smoke de deploy e alvos de dados no lab.
- [TESTING.md](../TESTING.md) ([pt-BR](../TESTING.pt_BR.md))
- [sonar-project.properties](../../sonar-project.properties)
- `.github/workflows/ci.yml`

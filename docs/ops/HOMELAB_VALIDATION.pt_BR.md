# Home lab: checagens de deploy e validação de alvos (manual)

**English:** [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md)

**Objetivo:** Executar **passos concretos** numa **segunda máquina** (VM ou host de containers) para comprovar **deploy**, **smoke** e **cobertura de conectores** com dados **sintéticos** e, opcionalmente, **reais** em pequena escala—sem depender só do CI ou do portátil de desenvolvimento.

**Não é aconselhamento jurídico.** Para dados **reais** de pessoas, exija **base legal**, **minimização** e contas técnicas **só leitura**; prefira dados **sintéticos** ou **amostras públicas** quando houver dúvida.

**“Completão” multi-host (volta completa de laboratório):** Este arquivo é o **baseline** de **uma máquina** (clone, `check-all`, smoke Docker, FS sintético). Para **E2E ordenado em vários hosts**—pilha Postgres/MariaDB, arquivos comprimidos, SMB/NFS opcional, **SSHFS**, WebDAV, **filesystem sobre iSCSI** montado no SO—seguir **[LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md)** (ordem de hosts, checklist **A–M**, definição de *completão*). **PII / publicação:** não coloques linhas de montagem reais, credenciais, IPs de LAN ou caminhos de casa em docs rastreados ou issues públicas; ver [ADR 0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) e [ADR 0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md). Evidência operacional fica em `**docs/private/homelab/`** (gitignored).

**Relacionado:** [deploy/DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md) · [SONARQUBE_HOME_LAB.md](SONARQUBE_HOME_LAB.md) · [OPERATOR_IT_REQUIREMENTS.pt_BR.md](OPERATOR_IT_REQUIREMENTS.pt_BR.md) · [TESTING.pt_BR.md](../TESTING.pt_BR.md) · [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) · **Lab-op — stack mínimo (Podman + k3s):** [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) ([EN](LAB_OP_MINIMAL_CONTAINER_STACK.md)) · **LAB-NODE-01 + LMDE 7:** [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) · **Observabilidade opcional:** [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md) · **SIEM (Wazuh):** mesmo doc LAB_OP §6

---

## 0. Princípios

1. **Automatizar primeiro no repo:** `.\scripts\check-all.ps1` ou `uv run pytest -v -W error` na raiz.
2. **Lab = integração:** caminhos, volumes Docker, portas de BD, firewall.
3. **Por padrão, sintético:** arquivos `.txt` / `.csv` com padrões **falsos** (inspire-se nos testes do projeto, **não** use dados reais de terceiros).
4. **Real só com permissão:** cópias não produtivas, anonimizadas ou documentos seus.
5. **Containers Docker:** Prefira `docker run --rm` em checagens pontuais. Se mantiver um container **Data Boar** nomeado entre execuções, objetive **uma** instância principal—ou **duas** só para **A/B** explícito. Remova containers descartáveis ao fim para não confundir portas (`8088`) e volumes. Ver [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md) §7.
6. **Docker CE + Swarm já ativo:** Num **manager** Swarm (incluindo **um só nó** em homelab), `docker build` e `docker run -p …` continuam a servir para §1.3–1.5; a porta publicada liga-se ao host salvo conflito com outro serviço. Se usar **stacks** (`docker stack deploy`), traduza o `docker run` do guia para Compose com `ports:` e volume para `/data`; em rede overlay o **nome do serviço** faz DNS (como `lab-net` na §4 em inglês). Nomes de serviços e papéis dos nós só em notas privadas.

### 0.1 Acesso pela LAN a partir de outro host do lab (dashboard / API)

Para usar o **dashboard HTTP** e a **API REST** do Data Boar a partir de **outra máquina na LAN do laboratório** (navegador num segundo PC, `curl` numa VM de teste, etc.):

| Item | Detalhe |
| ---- | ------- |
| **Porta** | **TCP 8088** por padrão (igual para `uv run` nativo e Docker `-p 8088:8088`). |
| **Endereço de bind** | O processo precisa escutar em **`0.0.0.0`**, não só em **`127.0.0.1`**. Use `--web --host 0.0.0.0 --port 8088` (e `--allow-insecure-http` se não estiver usando TLS na app). Imagens Docker que já fazem bind em todas as interfaces costumam estar OK; confira com `ss -tlnp` / `curl` a partir do outro host. |
| **Firewall no host (Linux)** | Liberar **entrada** **8088/tcp** **só da sub-rede da LAN** (exemplo de padrão — ajuste o CIDR: `sudo ufw allow from 10.0.0.0/16 to any port 8088 proto tcp comment 'Data Boar lab LAN'`). Mais contexto: [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md). |
| **Roteador / UniFi (VLANs, Wi‑Fi, convidado)** | Se o cliente não estiver no mesmo segmento L2 do servidor, inclua regra **permitindo** a rede cliente a alcançar **servidor:8088** (e DNS se usar nomes). **IPs/VLAN reais** só em notas **gitignored**. |
| **WAN** | **Não** exponha **8088** na internet para testes casuais; use VPN ou túnel SSH se precisar de acesso remoto. |
| **TLS / proxy reverso** | Se nginx/Caddy ficar na frente na **443**, abra **443** até o proxy em vez de publicar **8088** cru na borda. |

**Dependências no host de lab:** `uv sync` (e **pacotes de sistema** do [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) conforme a distro) antes do §1.1; não há pacote Python extra só para “escutar na LAN”.

**Pilha de segurança no host (firewall, AppArmor, fail2ban, EDR, integridade):** controles em camadas podem bloquear portas ou gerar ruído durante runs de lab. Veja **[DATA_BOAR_LAB_SECURITY_TOOLING.pt_BR.md](DATA_BOAR_LAB_SECURITY_TOOLING.pt_BR.md)** para o que ajustar, por quê e scripts auxiliares (`scripts/lab-allow-data-boar-inbound.ps1`, `scripts/lab-allow-data-boar-inbound.sh`).

---

## 1. Checklist base (copiar)

| Passo | Ação                                                                                | Critério de sucesso                                                                                                                                  |
| ----- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.1   | `git pull`; `uv sync`                                                               | Dependências OK                                                                                                                                      |
| 1.2   | Testes completos                                                                    | Tudo verde                                                                                                                                           |
| 1.3   | `docker build -t data_boar:lab .`                                                   | Build concluído (reutilize esta tag em cada smoke de lab — não crie tag nova por execução; ver [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md) §7) |
| 1.4   | `data/config.yaml` a partir de [config.example.yaml](../deploy/config.example.yaml) | YAML válido                                                                                                                                          |
| 1.5   | `docker run` com volume `/data` e `CONFIG_PATH`                                     | Dashboard em `:8088`, `/health` OK                                                                                                                   |
| 1.6   | Scan com `targets: []`                                                              | Termina sem crash                                                                                                                                    |
| 1.7   | *(Opcional)* Abrir o dashboard em **vários** browsers no desktop                    | Páginas principais carregam; **Console** DevTools sem erros graves em fluxos centrais                                                                |

**Modo Swarm:** Se o host já for **manager** Swarm, os passos acima mantêm-se. Use outra porta se `8088` estiver ocupada por outra stack; registe conflitos no runbook privado.

**§1.7 — Motores de browser:** Cobrir **Chromium** (ex.: **Edge**, **Vivaldi**, **Chrome**) e **Gecko** (ex.: **Firefox**, **Floorp**) costuma bastar; **Safari** se demonstrar em Apple. Detalhes: [HOMELAB_VALIDATION.md §1](HOMELAB_VALIDATION.md#1-lab-baseline-checklist-copypaste) (tabela + parágrafo após Swarm). **Helium** e outros: tratar como variante Chromium se aplicável.

**VMs no portátil (Boxes / virt-manager):** Antes do Proxmox, pode correr **§1.1–1.2** e **§2** dentro de convidados **Linux**; **FreeBSD**, **Haiku** e **illumos**/OpenSolaris são **exploratórios** (Haiku/illumos não são alvos práticos; OpenSolaris legado — preferir **illumos** atual). **OS/2** (Warp, etc.) é só **museu/hobby** — nada a ver com o stack do Data Boar. Ver [HOMELAB_VALIDATION.md §1.5](HOMELAB_VALIDATION.md#15-vms-on-the-primary-laptop-gnome-boxes--virt-manager--smoke-before-proxmox); atenção à **RAM** no portátil primary (frequentemente **≤8 GB**).

---

## 2. Filesystem sintético

Crie um diretório no host, arquivos `notes.txt` / `sheet.csv` com CPF/e-mail **de teste**; monte em `/data/...`; defina alvo `type: filesystem` como em [HOMELAB_VALIDATION.md §2](HOMELAB_VALIDATION.md#2-synthetic-filesystem-target-fastest-real-connector-test).

---

## 3. SQLite como arquivo

Pequena base `.db` com tabela de texto sintético; `scan_sqlite_as_db` ou alvo database conforme [USAGE.md](../USAGE.md).

---

## 4. PostgreSQL / MySQL em Docker

Suba contentor na mesma rede Docker que a app; usuário **read-only** se possível; alvo `database` com host = nome do serviço. Detalhes: [HOMELAB_VALIDATION.md §4](HOMELAB_VALIDATION.md#4-postgresql-or-mysqlmariadb-in-docker-lab-sql).

---

## 5. NoSQL (opcional)

MongoDB / Redis com extra `nosql` em [pyproject.toml](../../pyproject.toml); dados sintéticos.

---

## 6. API REST (opcional)

Mock trivial no lab; validar conector API.

---

## 7. Arquivos compactados

`scan_compressed` + ZIP; extra `compressed` para `.7z`. Ver [HOMELAB_VALIDATION.md §7](HOMELAB_VALIDATION.md#7-compressed-archives-scan_compressed).

---

## 8. Licenciamento (opcional)

Modo `enforced` sem `.lic` deve bloquear; ver [LICENSING_SPEC.md](LICENSING_SPEC.md).

---

## 9. Vários hosts Linux (matriz opcional)

Homelab com **várias máquinas** (portátil Ubuntu/derivado com Docker, mini-PC musl, Raspberry Pi, mais tarde **hipervisor + VMs**): repetir o **mínimo** do §1 em cada “sabor” para apanhar **ARM vs x86**, **musl vs glibc**, RAM, **VM vs bare metal**. Derivados Ubuntu seguem a mesma lógica de pacotes/Docker que Ubuntu. **Swarm** no portátil não impede §1.3–1.5; atenção a portas. **PODE i**nstalar pacotes de sistema via automação sem o operador, desde que seguro e safe — se faltar `uv`/Python, o operador instala e volta a correr §1.1–1.2.

**Tabela completa (EN):** [HOMELAB_VALIDATION.md §9](HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros) — **três portáteis** em papel: **Windows+WSL** (dev), **Linux nativo** (lab), **terceiro** (muitas vezes **silício mais recente** — candidato a **paralelismo** Docker/pytest; ver linha *Secondary x86_64 laptop* na tabela EN); **WSL extra** no Windows **não** é um quarto chassis — ver [WINDOWS_WSL_MULTI_DISTRO_LAB.pt_BR.md](WINDOWS_WSL_MULTI_DISTRO_LAB.pt_BR.md). **Rig paralelo (opcional):** [§9.2 em inglês](HOMELAB_VALIDATION.md#92-parallel-testing-rig-optional--secondary-laptop-or-tower-guest). Inclui **Proxmox**, *spare desktop*, etc.; ver EN §9 e §9.1.

**Quando preparar o hardware (§9.1 + [PLANS_TODO](../plans/PLANS_TODO.md) ordem –1L):** **Agora** — nada depende da torre futura nem do Mac avariado; continue musl + ARM. **Torre principal com Proxmox** — antes de uma sessão focada de validação nesse alvo: Proxmox instalado, **≥1 VM ou LXC** Debian/Ubuntu, rede e disco prontos; depois §1+§2 **no guest** (ver [§9.1 em inglês](HOMELAB_VALIDATION.md#91-when-to-have-hardware-ready-operator-sync-with-planstodo-order-1l)). **Mac mini antigo** — só preparar quando voltar a arrancar de forma fiável.

**Simulação de cluster, Alpine / AlmaLinux e escala horizontal (§9.3 em EN):** quando a **torre + Proxmox** estiver no ar, dá para várias VMs (sabores **Alpine**, **AlmaLinux**, etc.) com **Docker/Podman** para simular **vários nós** e ensaios de **resiliência** e **réplicas** — ver [§9.3 em inglês](HOMELAB_VALIDATION.md#93-cluster-simulation-alpine--almalinux-and-when-horizontal-scale-matters) e a tabela **“quando priorizar”** no §5 de [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md).

**Não** publique no GitHub nomes reais de máquinas, IPs da LAN ou caminhos em `$HOME`—use só `**docs/private/homelab/`** (ignorado pelo git) ou notas locais; política em [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md).

---

## 10. SonarQube (opcional)

[SONARQUBE_HOME_LAB.md](SONARQUBE_HOME_LAB.md) — qualidade de código, não conectividade de dados.

---

## 11. Registar resultados

Nota datada em `**docs/private/homelab/**` (gitignored): **hostnames**, tag da imagem, alvos, pass/fail.

### 11.1 Lockfile e imagem publicada (alinhar –1L com –1 / –1b)

Quando **`uv.lock`**, **`requirements.txt`** ou **`Dockerfile`** mudam no **`main`**, mantenha **Docker Hub** e **lab** no mesmo ritmo: imagem local com **`scripts/docker-lab-build.ps1`**, **publicação** conforme **[DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md)** (semver em `pyproject.toml`, gate Scout, texto do Hub se precisar), depois **§1.3–1.6** no host de lab com **`fabioleitao/data_boar:latest`** ou o mesmo tag **semver**, para o digest do smoke bater com o que quem faz **pull** recebe. **`git` HEAD**, hash do **`uv.lock`** e **image ID** só em **`docs/private/homelab/`** — não neste arquivo.

---

## 12. Ver também

- [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md) — laboratório **multi-host** (BD + FS), opcional **SSHFS / WebDAV / iSCSI→FS**, checklist **A–M** e o que significa **“completão”** face ao baseline da §1 deste guia.
- [OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md](OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md) — **quais distros** testar (RHEL/Fedora, Arch/Manjaro, Gentoo, musl) priorizadas por relevância em produção.
- [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §5 — torre / **Alpine** / **AlmaLinux**, simulação multi-VM, **quando** priorizar **HA / escala horizontal** (vs baseline **–1L**).
- [HOMELAB_HOST_PACKAGE_INVENTORY.pt_BR.md](HOMELAB_HOST_PACKAGE_INVENTORY.pt_BR.md) — inventário de pacotes nos hosts (o repo não “vê” as suas máquinas).
- [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md) — **LAB-ROUTER-01-SE**: VLANs/firewall e SNMP local antes do servidor de monitoração.
- [HOMELAB_MOBILE_OPERATOR_TOOLS.pt_BR.md](HOMELAB_MOBILE_OPERATOR_TOOLS.pt_BR.md) — **iPhone / tablet Android** como ferramentas do operador (UniFi, GitHub, Bitwarden, SSH na LAN, smoke da UI, fotos para notas privadas).
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — sequência token-aware após o lab.
- [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md) — Priority band A.


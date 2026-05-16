# Personas de hosts LAB-OP — Ansible, completão e mapa de evidências

**English:** [LAB_OP_HOST_PERSONAS.md](LAB_OP_HOST_PERSONAS.md)

## Objetivo

Um **único mapa mental** entre:

- **Ficção de laboratório** (“servidor estilo ENT”, “laptop PRO/parceiro”, “edge só soup”, “ponte”) — **intenção de cobertura**, não SKU de produto (vocabulário para cliente: [SERVICE_TIERS_SCOPE_TEMPLATE.md](SERVICE_TIERS_SCOPE_TEMPLATE.md)).
- **Controles concretos:** playbooks Ansible, **`lab-node-01-ansible-labop-podman-apply.sh`**, **`.labop-skip-lab-node-01-podman`**, e campos do manifesto de **completão** (`**completaoEngineMode**`, **`completaoSkipEngineImport**`, **`completaoHealthUrl**`, **`completaoHardwareProfile**`).
- **Evidências:** o que registrar em **`docs/private/homelab/reports/`** e notas de sessão para não confundir host fraco com defeito do produto.

## Tabela de personas (alinhar com o inventário privado)

| Persona | Intenção | **`uv` / Python** no metal para o produto | OCI / orquestração | Ansible / scripts (típico) | Completão |
| --------- | ------ | ---------------------------------------- | ------------------- | ----------------------------- | ---------- |
| **Servidor estilo ENT** | Laptop “sala de servidores”: OCI completo, **sem** toolchain de consultor no metal | **Não** — validar Data Boar **dentro** de contêiner / `config` montado; DBs sintéticos na stack | **Podman** | **`playbooks/lab-node-01-podman.yml`** via **`scripts/lab-node-01-ansible-labop-podman-apply.sh`** — **sem** **`.labop-skip-lab-node-01-podman`** quando quiseres pacotes; **`lab-node-01-baseline.yml`** quando precisares de baseline mais largo | **`completaoEngineMode`:** **`container`** e/ou **`completaoSkipEngineImport`:** **`true`**; **`completaoHealthUrl`** para **`/health`** publicado |
| **Estação PRO / parceiro** | “Laptop de consultor”: iteração local + Swarm | **Sim** — **`uv sync`**, extras conforme [TECH_GUIDE.md](../TECH_GUIDE.md) | **Docker CE + Swarm** | **`lab-node-01-baseline.yml`**, **`deploy/lab-smoke-stack`**, compose de DB com dados **sintéticos** só nos exemplos rastreados | Smoke com import do motor no metal, salvo marcares explicitamente como só contêiner |
| **Edge / soup** | ARM/SD mínimo: **resiliência** e **data soup** como **alvo**, não fábrica de build | **Opcional** — medir **`python3 -m databoar --help`** / CLI mínimo | **Nenhum** no metal (ou NFS só leitura) | **`.labop-skip-lab-node-01-podman`**; sem papel de manager Swarm; scans dirigidos **a partir** de LAB-NODE-02/LAB-NODE-01 | **`completaoHardwareProfile`** com prefixo **`LAB-NODE-04`** (ou alias no **`sshHost`**); smoke passivo no runbook |
| **Ponte** | Entre edge e PRO: **latência** + viabilidade **HTTP/API** em máquina fraca porém online | **Leve** — smoke **`main.py --web`**, não loop completo de dev | **Podman** opcional (ou pular instalação com o marker) | **`labop-share-client-install.sh`**; **`lab-node-01-ansible-labop-podman-apply.sh`** **com** **`.labop-skip-lab-node-01-podman`** se o metal ficar fino | **`completaoHealthUrl`** + **`curl`** / browser a partir de outro host na LAN; anotar **TTFB** e roubo de CPU |

## Ansible “por papel”, não por distro imaginária

- **Família Debian** vs **Void** já está separada **dentro** do role **`lab-node-01_podman`** (ver [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md)).
- **Personas** decidem **se** corre instalação Podman (**`.labop-skip-lab-node-01-podman`** em edge/ponte quando padronizares “metal = só Python”).
- **Não** adicionar playbooks para distros que não operam; estender **`lab-node-01_podman`** (ou novo role) quando uma **nova** família aparecer no manifesto.

## DBs sintéticos e testes “completos”

- **ENT / PRO:** manter SQL/CSV e compose **sintéticos** só em **exemplos rastreados**; strings reais em **`docs/private/`** — [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md), [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.md).
- **Edge:** validar **caminhos de leitura** e **ruído** (logs, binários) que **outros** hosts montam ou exportam — não exigir Swarm no Pi como verdade do produto.

## Pacote de evidências (privado)

Por sessão, acrescentar em **`docs/private/homelab/`** (template [COMPLETAO_SESSION_TEMPLATE.pt_BR.md](../private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md) quando existir):

- Tempo de parede para **`lab-completao-orchestrate.ps1`**, Ansible **`--check`**, e **`curl`** ao **`completaoHealthUrl`**.
- **TTFB** / retentativas na ponte fraca.
- **`iostat`**, **temp do SoC**, **pressure stall** em nós estilo Pi ([LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) *Performance monitoring*).

## Links

- **Escada de arranque (agente novo / token-aware):** [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)).
- **Contratos de completão:** [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) ([pt-BR](LAB_COMPLETAO_RUNBOOK.pt_BR.md)), [LAB_COMPLETAO_FRESH_AGENT_BRIEF.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md).
- **Sudo estreito + wrappers:** [LAB_OP_PRIVILEGED_COLLECTION.md](LAB_OP_PRIVILEGED_COLLECTION.md).
- **Índice de scripts:** [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md).
- **Exemplo de manifesto (copiar para privado):** [../private.example/homelab/lab-op-hosts.manifest.example.json](../private.example/homelab/lab-op-hosts.manifest.example.json).

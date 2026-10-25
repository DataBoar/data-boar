# Lab-op: stack mínimo de contêiner — linha oficial única

**English:** [LAB_OP_MINIMAL_CONTAINER_STACK.md](LAB_OP_MINIMAL_CONTAINER_STACK.md)

**Finalidade:** Evitar **retrabalho** e **proliferação de stacks** no host **lab-op** fixando **uma** combinação mínima primeiro. **Outros** orquestradores (Nomad, outra distro Kubernetes, caminhos Compose duplicados) ficam **fora do escopo** até esta baseline estar **estável** e documentada em **`docs/private/homelab/`** (gitignored).

**Âmbito:** servidor / workstation Linux usado como **lab de integração** (SSH do operador). **Docker Desktop + Kubernetes** num **laptop Windows** de desenvolvimento é conveniência **à parte** — ver §4.

---

## 1. Combinação mínima oficial (lab-op)

| Camada                    | Escolha    | Papel                                                                                                                                                            |
| -----                     | -------    | -----                                                                                                                                                            |
| **Runtime OCI / build**   | **Podman** | Builds com viés rootless, `podman run`, opcional `podman play kube`; alinha com postura de segurança (sem daemon root obrigatório para runs locais).             |
| **Kubernetes (nó único)** | **k3s**    | Leve, um binário, **kubectl** incluído, suficiente para validar manifests estilo **`deploy/kubernetes/`** e padrões de ingress sem operar um cluster “completo”. |

**Não acrescentar** um segundo gestor de cluster no mesmo host (ex.: kind + k3s + minikube) até um caminho estar **smoke-tested** com os artefatos de deploy deste repositório.

---

## 2. Ordem de instalação concreta (Debian / Ubuntu / LMDE — usar `sudo` quando fizer sentido)

### 2.1 Podman

```bash
sudo apt-get update
sudo apt-get install -y podman
podman --version
podman info
```

Opcional (rootless por padrão para o usuário): seguir documentação **Podman** para `subuid`/`subgid` se quiser imagens totalmente rootless; para rapidez no lab, os padrões do pacote da distro costumam bastar.

### 2.2 k3s (nó único)

```bash
curl -sfL https://get.k3s.io | sh -
sudo k3s kubectl get nodes
```

Copiar kubeconfig para o seu usuário (ajustar URL do servidor se acessar a API a partir de outro host na LAN):

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$USER:" ~/.kube/config
# Se o kubectl reclamar do servidor: editar ~/.kube/config — server: https://127.0.0.1:6443
```

Instalar cliente **kubectl** standalone se preferir; o k3s inclui `k3s kubectl`.

**Firewall:** permitir **6443/tcp** (API Kubernetes) apenas a sub-redes de administração de confiança; **não** expor o k3s à Internet pública sem TLS endurecido e autenticação.

### 2.3 Smoke com este repositório

1. Clonar / atualizar **data-boar** no lab-op.
1. Build da imagem com **Podman:** `podman build -t data_boar:lab -f Dockerfile .`
1. Opcionalmente carregar no k3s: `sudo k3s ctr images import` a partir de `podman save` **ou** usar registry privado mais tarde — manter **um** fluxo de imagem documentado nas notas privadas.
1. Aplicar manifests em **`deploy/kubernetes/`** (ajustar ConfigMap/Secrets ao lab; **sem segredos no git**).

---

## 3. Política: adiar “espalhar” para outras stacks

**Enquanto** a baseline acima não estiver **verde** (build Podman + deploy k3s + Data Boar `/health`):

- **Não** normalizar **Nomad**, **Docker Swarm** nem uma **segunda** distribuição Kubernetes no lab-op.
- **Podman Desktop** no Windows é opcional e não substitui a baseline do servidor lab-op.
- Ao acrescentar uma segunda stack, abrir um **ADR** curto ou atualizar a tabela do §1 deste arquivo — evitar convenções paralelas tácitas.

---

## 4. Kubernetes do Docker Desktop (máquina de desenvolvimento Windows)

**Separado** do lab-op: ativar **Kubernetes** no **Docker Desktop** é válido para **checagem local de manifests** e prática de **kubectl**. **Não** substitui validar **`deploy/kubernetes/`** no **k3s** (ou o alvo semelhante a produção). Tratar o K8s do Desktop como **só desenvolvimento**.

---

## 5. Futuro: torre HP, Alpine / AlmaLinux e lab “cluster” simulado

**Quando a torre x86 (ex.: classe HP ML310e) + Proxmox estiver no ar**, você pode acrescentar **VMs convidado** com **sabores adequados** — por exemplo **Alpine** (pegada mínima, musl) e **AlmaLinux** (compatível com RHEL, glibc) — para ampliar a **matriz de SO** (ver [OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md](OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md)) **sem** abandonar a âncora **§1–§3**: mantenha **um** convidado “ouro” que continua rodando **Podman + k3s** como referência; use convidados extras para **smoke** específicos de distro e conectores.

**Várias VMs, cada uma com Docker Engine e/ou Podman**, podem **simular** um ambiente **estilo cluster**: vários **nós independentes**, cada um com contêineres, para exercitar **planos** que precisam de **mais de uma máquina** — por exemplo **ingress + várias réplicas** da app, **workers** separados, **isolamento de rede** entre sub-redes de “tenant”. **Escala horizontal** (mais réplicas de partes **sem estado**) importa quando o **gargalo** é CPU/RAM em um único nó ou quando é preciso **demonstrar** escalonamento e **isolamento de falha** a um stakeholder. Esse arranjo é **simulação de lab**; **não** é o mesmo que **multi-AZ** em produção ou **HA completo de Kubernetes** (quórum etcd, planos de controle redundantes), salvo se você montar essa stack de propósito.

## Quando priorizar resiliência / escala horizontal (ordem aproximada):

| Etapa                                                                                                                                                                                                                                                                                                                                                                                  | Foco                                                                                                                                                                    |
| -----                                                                                                                                                                                                                                                                                                                                                                                  | -----                                                                                                                                                                   |
| **Agora**                                                                                                                                                                                                                                                                                                                                                                              | **§1–§3** + [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) **–1L**: k3s nó único, uma réplica, `/health` verde.                                             |
| **Depois**                                                                                                                                                                                                                                                                                                                                                                             | Convidados **Alpine / AlmaLinux** no Proxmox para **cobertura de matriz**; opcional **multi-VM** Docker/Podman para ensaiar **deploy multi-nó** e esboços de **carga**. |
| **Preocupar-se com HA / escala “de verdade”** quando: **cliente ou parceiro** pedir **SLA / HA**; **testes de carga** mostrarem saturação em um nó; o **produto** tiver **filas de workers**, **sharding** ou **multi-tenant** que **exijam** N nós; a **documentação de Kubernetes** em produção exigir **Ingress + PDB + várias réplicas**; ou **DR / multi-site** entrar no escopo. |                                                                                                                                                                         |

**Ressalva:** três VMs com Docker **simulam** três **nós**; isso **não** prova automaticamente **HA do plano de controle** do Kubernetes nem segurança contra **split-brain** — diga **o que** está sendo testado (réplicas da app vs etcd).

---

## 6. Opcional adiado: Wazuh (SIEM / postura de segurança) no lab-op

**Fora da stack mínima.** Quando o lab-op (ou um **convidado Proxmox**) tiver **RAM e CPU** suficientes, vale avaliar o **[Wazuh](https://wazuh.com/)** (SIEM/XDR open source) para:

- Centralizar visibilidade de **vulnerabilidades** e relatórios de **hardening** (ex.: checagens no espírito CIS, mapeamento MITRE na UI).
- Correlacionar telemetria de **hosts** e **contêineres** com um **manager** + **agentes** (ou agentless quando aplicável).

## Sequência (não inverter sem motivo):

| Ordem | Portão                                                                                                                                    |
| ----- | ------                                                                                                                                    |
| 1     | Baseline **§1–§3** **verde** (Podman + k3s + `/health` do Data Boar no lab-op).                                                           |
| 2     | Preferir **VM ou LXC dedicado** ao **manager** Wazuh (evitar competir por RAM com o k3s no mesmo host se o limite for apertado).          |
| 3     | Registrar **lab-op** e outros **hosts do homelab** como **agentes**; afinar ruído e retenção em **`docs/private/homelab/`** (gitignored). |

**Limite de escopo:** o Wazuh **complementa** stacks de **métricas** (Prometheus, Zabbix, Netdata) e probes **manuais** (ex. logs SNMP em `docs/private.example/homelab/`); **não** substitui testes de aplicação neste repositório. Acompanhamento: [PLANS_TODO.md](../plans/PLANS_TODO.md) (LAB-OP + H2 adiado).

---

## 7. Opcional adiado: métricas + logs + Grafana (plano de observabilidade)

**Fora da stack mínima.** Para **dashboards**, **métricas centralizadas** e **logs centralizados** (ex. **Grafana** + **Prometheus** ou **InfluxDB**; **Loki** ou **Graylog** + **OpenSearch**), segue o plano sequenciado — inclui orientação de **RAM** para **ThinkPad LAB-NODE-01** vs **torre/VM**:

- **[PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)** ([EN](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md))

**Ordem:** concluir **§1–§3** deste doc primeiro; depois fases **A–E** naquele plano (escolhe **um** pilar de métricas e **um** de logs salvo se houver recursos para mais).

---

## Relacionado

- [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) — playbook completo (§9 multi-host; §9.3 simulação de cluster).
- [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) — LAB-NODE-01 + LMDE 7 passo a passo ([EN](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)).
- [deploy/DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md) — narrativa de deploy.
- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — caminhos para revisores (Corporate-Entity-C).

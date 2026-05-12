# Smoke de laboratório multi-host (pilha de BD + arquivos + rede)

**English:** [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)

**Objetivo:** Permitir uma **rodada repetível** e **amigável a colaboradores** que exercite **PostgreSQL**, **MariaDB**, amostras **comprimidas** em `tests/data/compressed` e **caminhos em LAN** (bind mounts, SMB/NFS/sshfs opcional, pastas de nuvem sincronizadas) para além do que só o CI cobre.

**Escopo:** Laboratório controlado pelo operador. **Não** exponha portas à Internet. Use apenas dados **sintéticos** do repositório e os SQL em `deploy/lab-smoke-stack` — **nunca** PII real de clientes ou família em configs compartilhadas.

---

## 1. Ordem sugerida de hosts (eficiência)

**Política:** Preferir **pelo menos duas** dimensões independentes onde importa: por exemplo dois hubs **Docker CE** para `lab-smoke-stack` (**lab-node-02 + LAB-NODE-01** chega). **LAB-NODE-03** e **LAB-NODE-04** **não** precisam de Docker ou Compose; continuam úteis para scans **CLI** por LAN (**libc** / **ARM**).

| Ordem | Host / papel                                                                                                      | Porquê                                                                                                                                                                                                                                                                        |
| ----- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1a    | **LAB-NODE-01** (Linux x86_64, Docker CE via [lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml)) | Hub de primeira classe para `deploy/lab-smoke-stack`. O mesmo playbook adiciona o operador ao grupo `**docker`** — **novo login** (ou `newgrp docker`) após o Ansible ou `docker compose` falha com **permission denied** em `docker.sock`.                                   |
| 1b    | **lab-node-02** (Zorin, Docker)                                                                                      | Segundo hub: repetir a mesma pilha Compose para o smoke de BD na LAN não depender de um único host.                                                                                                                                                                           |
| 2     | **PC Windows principal de desenvolvimento**                                                                       | `docker-lab-build.ps1` / imagem Hub + `/health` + scan contra **IP LAN do hub** nos alvos de BD; opcional montar `tests/data/compressed`. Opcional **WSL2** como segunda superfície de execução — [WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md](WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md). |
| 3     | **LAB-NODE-03** (Void **musl**)                                                                                       | Expõe surpresas de **wheels / libc** (`cryptography`, build `mysqlclient`); scan **CLI** para BD por LAN. **Sem** obrigação de Docker.                                                                                                                                        |
| 4     | **LAB-NODE-04** (ARM, pouca RAM)                                                                                         | **Por último** — lento; usar `scan.max_workers: 1`; confirmar `uv sync` / headers MariaDB conforme **HOMELAB_HOST_PACKAGE_INVENTORY.md**. **Pré-requisito:** espaço em disco. **Sem** obrigação de Docker.                                                                    |

---

## 2. Subir a pilha de BD (LAB-NODE-01 ou host hub)

Na máquina que **vai servir** as bases:

```bash
cd deploy/lab-smoke-stack
cp env.example .env
# editar .env se portas ou palavras-passe mudarem
docker compose up -d
docker compose ps
```

- **PostgreSQL** na porta de host `**55432`** (mapeia para 5432).
- **MariaDB** na porta de host `**33306`** (mapeia para 3306).
- **MongoDB (opcional):** não sobe só com `docker compose up -d`. Use **`docker compose -f docker-compose.yml -f docker-compose.mongo.yml up -d`** — publica **`27018`** por padrão. No Data Boar: **`uv sync --extra nosql`** para `driver: mongodb`.

**Firewall:** permitir TCP da LAN de laboratório só para essas portas. **Não** expor na WAN.

**Swarm:** Para um único nó, `docker compose up` basta. Para **Stack**, adaptar `ports`/`networks` e `docker stack deploy`; manter as mesmas portas publicadas para outros hosts alcançarem os BDs.

**Podman (opcional):** Os mesmos arquivos `docker-compose.yml`; usar `podman compose` no hub se você preferir rootless/OCI **sem** desinstalar o Docker CE — ver [deploy/lab-smoke-stack/README.md](../../deploy/lab-smoke-stack/README.md) (seção Podman). **k3s** continua opt-in no [lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml); converter esta pilha para manifests Kubernetes não é obrigatório para o smoke de lab.

**SCP ou cópia parcial:** Se `init/postgres` / `init/mariadb` ficarem sem permissões de leitura para “outros”, os contentores podem falhar com **Permission denied** em `/docker-entrypoint-initdb.d`. No hub: `chmod -R a+rX init/postgres init/mariadb` dentro de `deploy/lab-smoke-stack`, ou o playbook `**ops/automation/ansible/playbooks/lab-smoke-stack-init-perms.yml`** com o grupo `**[lab_smoke]**` no inventário (ver `**ops/automation/ansible/inventory.example.ini**`). **Docker CE** em Debian/Ubuntu: papel `**deploy/ansible/roles/docker`** (ADR 0009).

`**permission denied` no socket Docker:** No LAB-NODE-01, aplicar [lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml) (ou `usermod -aG docker` ao operador e **nova sessão de login**). SSH não interativo não fornece senha ao `sudo` para `docker compose`; corrigir membros de grupo em vez de depender de `sudo docker` no dia a dia.

---

## 3. Apontar o Data Boar para os BDs

1. Copiar `deploy/lab-smoke-stack/config.lab-smoke.example.yaml` para um caminho **privado** (ou nome gitignored).
2. Substituir `**HOST_LAB_DB`** por:
  - O **IPv4 LAN** do host hub (LAB-NODE-01), ou
  - `**host.docker.internal`** se o contentor do Data Boar correr **no mesmo SO** que o Docker Desktop / mesmo host com portas publicadas, ou
  - Nome DNS da **rede Docker** se serviços compartilharem o mesmo projeto Compose (avançado).
3. Correr o Data Boar (CLI ou `--web`) no host do scan; garantir **rotas e firewall** para `HOST_LAB_DB:55432` e `:33306`.

**Critério de sucesso:** sessão concluída; **findings** ou metadados de esquema para `lab_customers` / `lab_notes`; **sem** erros de ligação em `scan_failures` (ver [TROUBLESHOOTING_MATRIX.md](../TROUBLESHOOTING_MATRIX.md)).

---

## 4. Sistema de arquivos: corpus comprimido + caminhos inócuos

1. Montar **só leitura** o diretório do repositório `tests/data/compressed` (`sample1.zip`, `sample2.7z`, …) no contentor do Data Boar ou usar bind path para `uv run` nativo.
2. Ativar `file_scan.scan_compressed: true` e extensões conforme [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) **§7**.
3. Instalar `**uv sync --extra compressed`** se precisar de `**.7z**`.

**Opcional “inócuo”:** pasta paralela só com texto operacional (SKU, tickets internos) para confirmar **zero** alarmes em conteúdo limpo.

---

## 5. Compartilhamentos (SMB / NFS / sshfs / nuvem)

**Fonte da verdade:** [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) (tipos de share, YAML) e os conectores em `**connectors/`** (`smb_connector.py`, `nfs_connector.py`, …).

| Mecanismo                                      | Como o Data Boar suporta                                                                                                                                                                                                                                                                                                                                                                                     |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **SMB/CIFS**                                   | **Nativo:** `type: smb` ou `type: cifs` com `host`, `share`, `path`, credenciais — usa **Python** `smbprotocol` (instalar `**uv sync --extra shares`** / `.[shares]`). **Não** exige montagem no kernel para esse modo. **Opcional no lab:** montar o share no SO (`mount.cifs` / interface gráfica) e usar `**type: filesystem`** no ponto de montagem — mesmo pipeline de scan, outra forma de configurar. |
| **NFS**                                        | O alvo `**type: nfs`** usa um **ponto de montagem local** (`path`); o export no servidor **precisa estar** **montado pelo SO** antes (ver `nfs_connector.py` — delega ao scanner de filesystem nesse diretório). `host` / `export_path` servem para relatório. **Alternativa:** montar NFS e usar `**type: filesystem`** no mesmo caminho.                                                                   |
| **sshfs**                                      | **Sem** conector dedicado — expor a árvore como diretório local (FUSE), depois `**type: filesystem`**.                                                                                                                                                                                                                                                                                                       |
| **OneDrive / pCloud / Google Drive / Dropbox** | Usar a **pasta local sincronizada** pelo cliente (arquivos materializados). **Arquivos sob demanda** podem bloquear leitura — fixar ou hidratar antes do scan.                                                                                                                                                                                                                                               |

**Pacotes no lab (só para montagens no kernel):** Se usas **CIFS** ou **NFS** montados no SO (ou **sshfs**), instala nos hosts os pacotes cliente habituais (`cifs-utils`, `nfs-common`, `sshfs`, `fuse3` em Debian/Ubuntu — nomes variam por distro). Ansible opcional: `**ops/automation/ansible/playbooks/lab-data-boar-share-clients.yml`** (família Debian). **SMB/CIFS nativo** com `type: smb` só precisa do extra **Python** `.[shares]`, não de `mount.cifs`.

**Entre hosts:** Outras máquinas (lab-node-02, LAB-NODE-03) podem usar **TCP** para o BD no hub; **não** precisam das mesmas montagens de nuvem salvo que estejam a testar **filesystem** ou **alvos de share nativos** nesse host — aí instalam deps e config conforme a tabela, ou copiam fixtures localmente.

### 5.1 SSHFS (FUSE sobre SSH)

Quando isto funciona no teu laboratório, é um modo **válido** de expor uma **árvore remota** como path local—o Data Boar usa depois um alvo `**filesystem`** normal (não implementa SSHFS por si).

1. **Pacotes (Linux típico):** `sshfs` + FUSE (`fuse3` / `fuse` conforme a distro). Em **WSL2**, alinha FUSE/WinFsp à documentação da tua distro; falhas são **ambiente**, não bug do produto.
2. **Montagem (só ilustrativo—usa usuário/host/paths do teu lab):**

   ```bash
   mkdir -p /mnt/lab-sshfs
   sshfs USER@HOST:/caminho/remoto /mnt/lab-sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,ro
   ```

   Preferir `**-o ro**` para leitura tipo auditoria quando o remoto permitir.
3. **Config:** `type: filesystem`, `path:` por baixo do mount (ex.: `/mnt/lab-sshfs/...`). Mesmas regras que qualquer árvore local; espera **maior latência** e possíveis **handles** instáveis com Wi‑Fi fraco—`reconnect` e keep-alive ajudam.
4. **Desmontar:** `fusermount -u /mnt/lab-sshfs` (Linux) ou equivalente no SO.
5. **PII e publicação:** **Não** coloques `USER@HOST` reais, chaves, IPs de LAN ou caminhos de casa em Markdown **rastreado**, issues ou corpos de PR. Referências: [ADR 0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md), [ADR 0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md). Notas operacionais com montagens reais ficam em `**docs/private/homelab/`** (gitignored).

### 5.2 WebDAV — dois padrões de integração

| Padrão                  | Quando                                                                    | Lado Data Boar                                                                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — Conector nativo** | Queres exercitar `**webdavclient3`** / o pipeline de shares por **HTTPS** | `type: webdav`, `base_url`, credenciais conforme [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) / [USAGE.pt_BR.md](../USAGE.pt_BR.md); instalar `**.[shares]`** |
| **B — Montagem no SO**  | Queres o mesmo **caminho de código** que SMB/NFS (diretório parece local) | Montar com **davfs2**, **rclone mount**, ou similar, depois `**type: filesystem`** no ponto de montagem                                                        |

Escolhe **um** padrão por corrida de teste para falhas serem fáceis de atribuir (conector vs FUSE vs rede).

### 5.3 iSCSI / dispositivos de bloco / “LBA”

- **iSCSI:** O produto **não** tem conector iniciador iSCSI. O fluxo suportado é **só no SO**: anexar LUN → particionar/formatar se preciso → **montar filesystem** → alvo `**filesystem`** nesse mount.
- **LBA (endereçamento lógico de blocos):** Detalhe de disco/geometria **abaixo** do filesystem. **Não** entra no YAML do Data Boar; só importa o **path montado**.

### 5.4 Ordem (eficiência)

Corre os opcionais **§5.1–5.3** **depois** de **A–I** verdes. Trata **J** e **K–M** como **expansões opcionais** da mesma volta “completão”—não substituem `**check-all`** nem CI.

---

## 6. LAB-NODE-04 (ARM) — quando incluir

Usar **depois** de os caminhos x86_64 funcionarem. Libertar **espaço em disco** no Pi antes de `git fetch` / `uv sync`. Esperar tempos maiores; manter `scan.max_workers` baixo.

---

## 7. Script LAB-OP e saúde do Git

`scripts/lab-op-sync-and-collect.ps1` executa `git pull --ff-only` em cada host. Se o `**main` local divergir** de `origin/main`, o pull **falha** e **não** corre `homelab-host-report.sh` — resolver o clone (merge/rebase/reset conforme a tua política) e voltar a correr. **Disco cheio** impede `git fetch` — libertar espaço primeiro.

---

## 8. Checklist E2E completo (ordenado, passa/falha)

Usar depois da ordem de hosts da **§1**. Marcar na tua folha de laboratório.

| Passo | Ação                                                                                                                                                                | Critério de sucesso                                                                                                                                                                           |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A     | **Desbloquear git** no LAB-NODE-01, lab-node-02, LAB-NODE-03: `main` precisa permitir fast-forward a `origin/main` (ou documentar exceção).                                        | `git pull --ff-only` com sucesso.                                                                                                                                                             |
| B     | **LAB-NODE-04:** libertar espaço em disco; depois `git fetch` funciona.                                                                                                    | Sem `No space left on device` no fetch.                                                                                                                                                        |
| C     | No **LAB-NODE-01** **e** num **segundo** hub (ex.: **lab-node-02**): `deploy/lab-smoke-stack` → `docker compose up -d`; healthchecks OK **nos dois**.                          | `docker compose ps` saudável em cada um; TCP `55432` / `33306` a partir da LAN para cada IP de hub.                                                                                           |
| D     | **Povoamento** automático via `init/postgres/*.sql` e `init/mariadb/*.sql` (inclui tabelas `02_*` de ligação).                                                      | Cliente `psql`/`mysql` mostra linhas em `lab_guardians`, `lab_minors_synthetic`, `lab_phone_directory`.                                                                                      |
| E     | **PC de desenvolvimento (Windows):** Data Boar (contentor ou Win) com `config.lab-smoke.example.yaml` e IP **LAN** do hub; scan dos dois alvos de BD + FS opcional. | Sessão concluída; findings em `lab_customers` / tabelas de ligação; contadores `dob_possible_minor` se o seed de menores disparar.                                                            |
| F     | **lab-node-02:** `uv run` scan para o mesmo host:portas; dashboard opcional `:8088`.                                                                                   | Igual a E a partir de caminhos Linux.                                                                                                                                                         |
| G     | **LAB-NODE-03:** scan CLI pela LAN; confirmar wheels **musl** (PyMySQL/psycopg2).                                                                                       | Sem erros de import; scan concluído.                                                                                                                                                          |
| H     | **LAB-NODE-04:** `scan.max_workers: 1`; último na cadeia.                                                                                                                  | Conclui ou documenta timeout/OOM para o runbook.                                                                                                                                             |
| I     | **Filesystem extra:** montar `tests/data/compressed` **e** `tests/data/homelab_synthetic` só leitura; `scan_compressed: true`.                                      | Findings em arquivos compactados + texto/CSV de ligação.                                                                                                                                       |
| J     | **Compartilhamentos (opcional):** SMB/NFS/sshfs/pasta de nuvem local em alvo `filesystem` depois de montado no SO.                                                  | Igual a qualquer alvo FS — arquivos hidratados (não placeholders de nuvem).                                                                                                                    |
| K     | **Conector WebDAV (opcional):** `type: webdav` contra um servidor de lab; credenciais só em config **privada** / gitignored.                                        | Sessão concluída; listagem/download conforme [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md); sem eco de credenciais em logs que vás colar publicamente.                                          |
| L     | **SSHFS (opcional):** montagem conforme **§5.1**, depois alvo `filesystem` no mount.                                                                                | Scan concluído ou documentas timeouts/limites de latência no runbook—**sem** hostnames/IPs reais em docs rastreados.                                                                          |
| M     | **iSCSI → FS (opcional):** SO apresenta bloco, path montado, depois alvo `filesystem`.                                                                              | Comprova **SO + storage**; mesmo critério que §2—**não** é feature separada do produto.                                                                                                       |

**Bloqueios atuais?** Se os logs LAB-OP mostrarem **ramos divergentes** ou **disco cheio**, os passos **A–B** são obrigatórios antes de relatórios de host úteis ou `uv sync` fresco nessas máquinas.

**Definição — “completão”:** Esta checklist (**A–M** conforme aplicável) mais `**.\scripts\check-all.ps1`** na raiz no PC de desenvolvimento é a volta manual **completa** que o projeto menciona em conversa de operador—**não** “só pytest num PC.” Omitir hosts físicos só com **motivo** registado (tempo, hardware offline).

---

## 9. Conteúdo dos seeds SQL

| Arquivo                           | Conteúdo                                                                                                                                                                                                 |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init/*/01_lab_smoke.sql`         | `lab_customers`, `lab_notes` — caminho feliz, borderline, isco de FP, linha inócua.                                                                                                                      |
| `init/*/02_lab_smoke_linkage.sql` | `lab_guardians`, `lab_minors_synthetic` (nomes de coluna data_nascimento/idade para heurísticas de **possível menor**), `lab_phone_directory`, linhas extra para ligação por **telefone compartilhado**. |

Re-seed implica recriar volumes ou DDL manual em bases existentes — para estado limpo, `docker compose down -v` e `up -d` (destrutivo).

---

## 10. Documentos relacionados

- [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md) — **completão** (produto + hosts do lab + orquestração SSH) vs **pytest** / **check-all** só no PC de desenvolvimento.
- [WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md](WSL2_DATA_BOAR_DEV_TESTING.pt_BR.md) — segunda superfície de execução opcional no PC Windows de desenvolvimento.
- [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.md) — APIs publicas e BD somente leitura opcional (complementa o smoke LAN).
- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — playbook base.
- [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) — pacotes de sistema para conectores.
- [TROUBLESHOOTING_MATRIX.md](../TROUBLESHOOTING_MATRIX.md) — BD e rede Docker.
- [USAGE.md](../USAGE.md) — referência de `targets` e `file_scan`.


# Coleta privilegiada no LAB-OP (safe-by-default)

**English:** [LAB_OP_PRIVILEGED_COLLECTION.md](LAB_OP_PRIVILEGED_COLLECTION.md)

## Objetivo

Habilitar coleta privilegiada **controlada pelo operador** e com **guardrails** para inventário/readiness do LAB-OP — sem normalizar `sudo NOPASSWD` amplo.

## Como funciona

O script do relatório do host suporta flags opt-in:

- `bash scripts/homelab-host-report.sh` (padrão, sem sudo)
- `bash scripts/homelab-host-report.sh --privileged` (tenta `sudo -n`)
- `bash scripts/homelab-host-report.sh --privileged --deep` (cheques mais pesados, ainda best-effort)

No Windows (PC do operador), você roda em todos os hosts via manifest:

- `.\scripts\run-homelab-host-report-all.ps1`
- `.\scripts\run-homelab-host-report-all.ps1 -Privileged`
- `.\scripts\run-homelab-host-report-all.ps1 -Privileged -Deep`
- Wrapper “shorthand” (taxonomia): `.\scripts\lab-op.ps1 -Action report-all -Privileged -Deep`

Se você quer **zero prompts** (execução realmente não interativa), prefira o runner por **repo-path**:

- `.\scripts\lab-op-sync-and-collect.ps1 -SkipGitPull -Privileged -Deep`

Isso roda o report como `bash scripts/homelab-host-report.sh ...` **dentro do path do repo** listado por host no manifest (path estável para allowlist do sudoers).

## Padrão recomendado de sudoers (restrito)

Se você quiser coleta sem senha, faça de forma **cirúrgica**:

- permitir um único comando (o script de report) com argumentos fixos
- não permitir ferramentas de edição, shells genéricos ou comandos amplos

### Exemplo (template — substitua placeholders)

1) No host, crie o include do sudoers:

```bash
sudo visudo -f /etc/sudoers.d/labop-host-report
```

2) Cole (substitua `LEITAO_USER` e `REPO_PATH`):

```text
# Permite somente o host report do LAB-OP sem pedir senha.
# Substitua:
# - LEITAO_USER: seu usuário Linux (ex.: leitao)
# - REPO_PATH: path absoluto do clone do repo nesse host (evite espaços)

Cmnd_Alias LABOP_HOST_REPORT = /bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged, \
                               /usr/bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged, \
                               /bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged --deep, \
                               /usr/bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged --deep

LEITAO_USER ALL=(root) NOPASSWD: LABOP_HOST_REPORT
```

3) Valide:

```bash
sudo -l
sudo -n /bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged | head -20
```

### Path do shell no sudoers (`/bin/bash` vs `/usr/bin/bash`)

O **`sudo`** compara o **path do executável invocado literalmente**. Em alguns hosts, **`command -v bash`** devolve **`/usr/bin/bash`** (ex.: Void), enquanto você testa com **`/bin/bash`**. Se o NOPASSWD listar só um dos dois, a outra forma pede senha. **Liste os dois** no `Cmnd_Alias` (como no template acima e no role **`lab-node-01_labop_sudoers`**).

### Checklist de setup (uma vez por host)

1) Garanta que o repo exista em um path estável nesse host (exemplo):

```bash
ls -la "$HOME/Projects/dev/data-boar/scripts/homelab-host-report.sh"
```

2) Crie o include do sudoers (restrito) e valide:

```bash
sudo visudo -f /etc/sudoers.d/labop-host-report
sudo -l
sudo -n /bin/bash "$HOME/Projects/dev/data-boar/scripts/homelab-host-report.sh" --privileged --deep | head -40
```

3) Do PC Windows do operador, rode a coleta privilegiada em todos os hosts **sem prompts**:

```powershell
.\scripts\lab-op-sync-and-collect.ps1 -SkipGitPull -Privileged -Deep
```

## Ansible Podman apply (mesmo NOPASSWD estreito)

Para evitar prompt de **BECOME** ao instalar **só** Podman via `playbooks/lab-node-01-podman.yml`,
amplie o include do sudoers com comandos **fixos** para `scripts/lab-node-01-ansible-labop-podman-apply.sh`
(mesmo critério do `homelab-host-report.sh`). O role **`lab-node-01_labop_sudoers`** grava
**`LABOP_HOST_REPORT`** e **`LABOP_ANSIBLE_PODMAN`** juntos quando **`lab-node-01_labop_sudoers_enable: true`**.

Exemplo (substitua `LEITAO_USER` / `REPO_PATH`):

```text
Cmnd_Alias LABOP_ANSIBLE_PODMAN = /bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --apply, \
                                  /usr/bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --apply, \
                                  /bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --check, \
                                  /usr/bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --check

LEITAO_USER ALL=(root) NOPASSWD: LABOP_HOST_REPORT, LABOP_ANSIBLE_PODMAN
```

No host:

```bash
sudo -n /bin/bash "$HOME/Projects/dev/data-boar/scripts/lab-node-01-ansible-labop-podman-apply.sh" --check
sudo -n /bin/bash "$HOME/Projects/dev/data-boar/scripts/lab-node-01-ansible-labop-podman-apply.sh" --apply
```

No Windows (SSH **sem** TTY para senha do Ansible):

```powershell
.\scripts\lab-node-01-ansible-baseline.ps1 -SshHost lab-node-01 -Apply -SkipCheck -PodmanOnly -NoAskBecomePass
```

Exige **`ansible-playbook`** no alvo e as linhas do sudoers acima. Sob **`sudo`**, o **`secure_path`** pode esconder o **`~/.local/bin`** do operador; o script **`lab-node-01-ansible-labop-podman-apply.sh`** antecede **`~/.local/bin`** / **`~/.cargo/bin`** (via **`getent passwd`** do **`SUDO_USER`**) quando possível. Se ainda faltar o binário, instale o pacote **`ansible`** no host (ex.: Debian: **`apt install ansible`**) para colocar **`ansible-playbook`** num path de sistema.

### Ordem em `sudoers.d` vs `%wheel` (Void Linux)

Os includes em **`/etc/sudoers.d/`** são lidos pela **ordem lexicográfica do nome do arquivo**. Se existir **`wheel`** com **`%wheel ALL=(ALL:ALL) ALL`** e o teu utilizador estiver no **`wheel`**, essa regra **ampla** pode ser aplicada **depois** de um arquivo tipo **`labop-host-report`**, e o **`sudo -n`** continua a pedir senha mesmo com **`NOPASSWD`** visível no **`sudo -l`**. Renomeia o include do LAB para ordenar **depois** de **`wheel`** — ex.: **`z-labop-host-report`**. **Não** contes com o prefixo **`99-`** para ser “o último”: **dígitos ordenam antes de letras**, logo **`99-…`** fica **antes** de **`wheel`**.

### “Already up to date” no lab mas Void ainda cai em `apt` / `python3-apt` / `sshfs`

Se **`git pull --ff-only origin main`** diz **up to date** mas **`lab-node-01-ansible-labop-podman-apply.sh --check`** ainda falha no **`ansible.builtin.apt`** (ou **`labop-share-client-install.sh`** ainda tenta o pacote **`sshfs`** no Void), as **correções canónicas ainda não estão no remoto Git** que o host segue — por exemplo, alterações só no **working tree do PC de desenvolvimento** até **commit + push**. Confirma no host: **`git log -1 --oneline`** igual ao **`main`** no GitHub e volta a fazer pull.

### Maestro — ensure NFS / CIFS (`Handle-target_nfs`, `Handle-target_cifs`)

Os handlers Maestro rodam **`--check`** (padrão) ou **`--apply`** (modo **`-Deep`**):

```bash
sudo -n bash "$HOME/Projects/dev/data-boar/scripts/labop-nfs-server-ensure.sh" --check
sudo -n bash "$HOME/Projects/dev/data-boar/scripts/labop-smb-server-ensure.sh" --check
```

Os **`Cmnd_Alias`** precisam listar **`--check`** e **`--apply`**, **`/bin/bash`** e **`/usr/bin/bash`**, no caminho **canônico** do repo (não checkout efêmero com sufixo de versão). Modelo rastreado: **`docs/private.example/homelab/labop-maestro-target-sudoers.example`**. Mescla em **`/etc/sudoers.d/z-labop-host-report`** (ordena **depois** de **`wheel`** — ver acima). Valida: **`sudo visudo -cf /etc/sudoers.d/z-labop-host-report`**.

## Guardrails

- Se você não precisar disso no dia a dia, remova o arquivo do sudoers após a janela de coleta.
- Nunca use `NOPASSWD: ALL`.
- Não coloque hostnames, IPs e segredos em docs rastreadas; guarde logs brutos em `docs/private/homelab/reports/`.


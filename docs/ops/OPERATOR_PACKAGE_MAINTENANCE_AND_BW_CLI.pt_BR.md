# Manutenção de pacotes no workstation, Bitwarden CLI e Topgrade

**English:** [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md)

**Objetivo:** Fixar **hábitos concretos** (testados pelo operador) para manter **Windows**, **WSL** e **Linux** atualizados (**Debian/Ubuntu**, **Void / xbps**, outras bases) sem brigar com **gestores duplicados** e para instalar o **Bitwarden CLI** (`bw`) onde este repositório pressupõe. **Sem segredos** aqui — nada de tokens, **`BW_SESSION`** nem URLs de webhook.

**Público:** Mantenedor / operador. Alinha com [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md) (contrato do repositório) e [SECURITY.md](../../SECURITY.md).

---

## 1. Bitwarden desktop vs Bitwarden CLI (`bw`)

- Instalar o **cliente desktop** Bitwarden (por exemplo via **winget** como `Bitwarden.Bitwarden`) **não** instala o comando **`bw`**.
- O **`bw`** é **outro** componente. Instale explicitamente em **cada** ambiente onde quiser scripts **shell** ou terminal do Cursor.

### 1.1 Windows (PowerShell / cmd nativo)

- **Recomendado:** instalar com **winget** para ficar alinhado ao **Winget Auto-Update (WAU)** e ao resto da ferramenta que você atualiza com **Topgrade** no Windows:

  ```text
  winget install Bitwarden.CLI
  ```

  Confirme com **`winget search "Bitwarden CLI"`** — o **ID** pode mudar; mantenha **uma** fonte de instalação por máquina.

- Depois de instalar, **feche e reabra** o terminal (ou o Cursor) para o **`PATH`** incluir o `bw`.

- Verificação:

  ```powershell
  Get-Command bw
  bw --version
  ```

### 1.2 WSL e Linux (`PATH` à parte)

- **WSL** e **Linux** têm **`PATH` próprio**. Instalar `bw` no **Windows** **não** o disponibiliza dentro do **WSL**.

- Escolha **um** método por ambiente (exemplos — o que você já usa como padrão): **Homebrew** (`brew install bitwarden-cli`), **npm** `@bitwarden/cli`, ou pacote da **distribuição** se for mantido e confiável.

- **Debian/Ubuntu + npm:** a [documentação do CLI](https://bitwarden.com/help/cli/) avisa que, no Linux, o `npm` pode exigir o metapacote **`build-essential`** (ou equivalente da distro) antes — por exemplo `sudo apt install build-essential`. O role Ansible **`lab-node-01_bitwarden_cli`** e o script **`scripts/lab-node-01-bitwarden-cli-bootstrap.sh`** já instalam isso junto com **`nodejs`** / **`npm`**.

- Verificação:

  ```bash
  command -v bw && bw --version
  ```

### 1.2.1 Void Linux (`xbps`) — Bitwarden CLI (`bw`)

**Nao** existe pacote `bitwarden-cli` nos repositorios padrao do Void. Instale apenas **`nodejs`** com `xbps` — o **`npm`** vem **junto** no pacote Void (**nao** existe pacote separado `npm`).

```bash
sudo xbps-install -S nodejs
```

Por padrao, **`npm install -g`** tenta escrever em **`/usr/lib/node_modules`**, entao usuario normal recebe **`EACCES`**. Escolha **uma** opcao:

**A — Instalacao global com sudo (mais simples num host pessoal de lab):**

```bash
sudo npm install -g @bitwarden/cli
command -v bw && bw --version
```

**B — Prefixo no teu `$HOME` (sem `sudo npm`):**

```bash
mkdir -p ~/.local
npm config set prefix ~/.local
grep -q '\.local/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
npm install -g @bitwarden/cli
command -v bw && bw --version
```

Para outra versao do Node, `xbps-query -Rs nodejs` (ex.: `nodejs-lts`). **`bw login`** / **`bw unlock`** continuam manuais (sessao quente); **nao** colar segredos em arquivos rastreados.

**Git:** se `git pull` disser **divergent branches** depois de um **force push** no `main`, ou fazes `git pull --rebase origin main` (ou merge), ou — se **nao** precisares dos commits locais — alinhas ao remoto: `git fetch origin && git reset --hard origin/main`.

### 1.2.2 Linux (Flatpak + alias) — Bitwarden CLI (`bw`)

Se você preferir **não** usar **`npm`** na máquina, a Bitwarden documenta instalar o **desktop** via Flatpak e chamar o CLI por dentro ([ajuda do CLI — Flatpak](https://bitwarden.com/help/cli/)):

```bash
flatpak install flathub com.bitwarden.desktop
# teste pontual:
flatpak run --command=bw com.bitwarden.desktop --version
# alias no shell (ex.: ~/.bashrc):
alias bw='flatpak run --command=bw com.bitwarden.desktop'
```

Com alias, **`command -v bw`** pode mostrar `alias` — é esperado. No **baseline LAB-NODE-01**, defina **`lab-node-01_install_bitwarden_cli: false`** no inventário se o seu padrão for **só** Flatpak para o **`bw`**, para o Ansible **não** instalar também **`@bitwarden/cli`** via **`npm`**.

### 1.3 Um gestor por ferramenta (evitar duplicados)

- **Evite** instalar o mesmo binário (`bw`, `git`, `python`, …) via **winget**, **Chocolatey**, **Scoop** e **cópia manual** no **mesmo** perfil Windows. Escolha **uma** fonte principal por ferramenta e **grave uma nota privada** (por exemplo em `docs/private/`) do tipo “`bw` = winget” para upgrades previsíveis.

---

## 2. `gta` + Topgrade no Linux (sobreposição e papéis)

Muitos operadores mantêm um **script shell** (apelidado **`gta`** — “get them all”) com a sequência **pesada** de manutenção **daquela distro**, depois **Topgrade**.

Em **Debian/Ubuntu**, isso costuma ser **`dpkg` / `apt`**, **Topgrade** e um **rasto** opcional com **`needrestart`** e às vezes **bootloader / initramfs** (ver **item 2.4**).

O **Topgrade** (`~/.config/topgrade.toml` no Unix) orquestra **vários** passos (brew, cargo, flatpak, **pacotes do sistema** ligados ao **gestor nativo daquele host**, …). Em **Debian/Ubuntu**, o passo de **SO** (muitas vezes **System** no output) pode **repetir** trabalho se você **já** rodou **`apt`** no **`gta`**.

### 2.1 Porque importa (Debian / Ubuntu)

- Rodar **`apt`** completo no **`gta`** e depois deixar o Topgrade **voltar** a correr o passo de **sistema** na **mesma sessão** costuma ser **inofensivo** se a primeira passagem terminou bem, mas **perde tempo** e pode **voltar a pedir** `sudo` / **`needrestart`** quando você esperava um final silencioso.

### 2.2 Ajustes concretos — Debian / Ubuntu (escolha uma estratégia)

1. **Ritmo em dois modos (ponto de partida recomendado)**
   - **Dia pesado:** rode o **`gta`** até ao fim.
   - Depois rode o Topgrade **sem** o passo do SO **só nessa execução**, para ele ainda atualizar **brew**, **flatpak**, **cargo**, **git pulls**, etc.
   - O **flag** exato depende da sua versão do Topgrade — veja **`topgrade --help`** para **`--disable`** / **`--only`** e o nome do passo (muitas vezes **`system`** em Debian/Ubuntu).

2. **Um dono para o `apt`**
   - **Enxugue** o **`gta`** para **reparar** + **`apt update`** + **`apt -f install`** e deixe o **Topgrade** fazer o **`full-upgrade`** — **ou** o contrário: o **`gta`** é dono de **todo** o **`apt`** e o **Topgrade** **não** mexe no SO.
   - **Evite** dois “donos” sem regra clara — depois fica difícil saber qual log confiar após um upgrade ruim.

3. **Config global do Topgrade**
   - Se você **sempre** roda **`gta` antes de `topgrade`** e **nunca** confia num Topgrade **sem** `gta` para upgrade do SO, **pode** acrescentar o passo do SO a **`[misc] disable`** no **`topgrade.toml`** (para além do que já tiver, ex. **`nix`**, **`containers`**).
   - **Custo:** uma execução **`topgrade`** **isolada** **sem** `gta` **deixa** de atualizar pacotes do sistema até você rodar o **`gta`** outra vez.

4. **Execução sem interrupção**
   - Considere **`pre_sudo = true`** em **`[misc]`** para o **`sudo -v`** rodar **cedo** (comentários do próprio Topgrade no `config-reference`).

### 2.3 O `topgrade.toml` muda por máquina (ilustrativo)

- Numa workstation você **pode** ter **`disable = ["nix", "containers"]`** em **`[misc]`**; noutro Linux a lista **`disable`** pode estar **vazia** (template ainda só comentado). O **`~/.config/topgrade.toml`** é **por usuário e por host** — **não** assuma que uma cópia via `scp` se comporta igual.
- Quando você adotar uma estratégia do **item 2.2**, **documente** o motivo numa **nota gitignored** ou num **comentário** no topo do **`gta`**.

### 2.4 Vários hosts Linux — rastos do `gta` em Debian / Ubuntu

Você **pode** usar o **`gta`** em **vários** sistemas Debian/Ubuntu (por exemplo **uso diário** e **laboratório / secundário**). **Não** coloque **hostnames reais** nem identidade de LAN em docs **rastreados** — mantenha esse mapa em **`docs/private/`** (ver **[AGENTS.md](../../AGENTS.md)**).

**Núcleo comum (típico):** **`apt`** pesado **→** **`topgrade -y`** para **brew**, **cargo**, **flatpak**, **git**, etc., mesmo depois do **`apt`** ter atualizado o SO.

**Variantes de rasto (por host):**

1. **Rasto mínimo:** **`needrestart`** depois do Topgrade (ou confie nos prompts da distro) para ver **serviços / kernel** que ainda precisam de reinício.
2. **Rasto kernel / boot:** depois do Topgrade, **`update-grub2`** (ou o comando suportado pela sua distro) **→** **`update-initramfs -u`** **→** **`needrestart`**. Use quando quiser que a **mesma** janela de manutenção regenere **initramfs** e **config do bootloader** após **`apt`** instalar kernel novo — **`needrestart`** **no fim** resume o que ainda pede root ou restart de serviço.

**Blocos comentados** que às vezes você ativa só numa máquina (**`nala`**, **`deb-get`**, **`snap` / `flatpak`**, **pulls de imagens**) são **política do host**. **Registre** o motivo em notas privadas.

### 2.5 `gta` que não é Debian (Void Linux / padrão `xbps`)

Em sistemas baseados em **`xbps`** (por exemplo **Void Linux**), o **`gta`** **não** é fluxo **`apt`**. Um padrão que alguns operadores usam:

- **`xbps-install -Suy`** (ou o **equivalente atual** documentado para aquela instalação Void).
- **Ferramentas auxiliares** como **`vpm`** (**`vpm update`**, **`vpm cleanup`**) se você as usa — **confira** subcomandos na documentação oficial; nomes e flags mudam.
- **`topgrade -y`** para camadas de usuário e ecossistemas cruzados.
- **Kernels antigos:** **`vkpurge list`** e depois **`vkpurge rm all`** (ou equivalente) para **não** encher **`/boot`** após vários updates de kernel.
- **GRUB:** **`update-grub`** ou **`grub-mkconfig`** quando a imagem **precisa** regravar config após troca de kernel — habilite só quando fizer sentido.
- **`touch /forcefsck`** só quando você **quer de propósito** um **fsck** completo no **próximo root** (entenda tempo parado, **LUKS** e acesso de recuperação antes).

Um **bloco Debian `apt` comentado** no mesmo arquivo pode ser **modelo portável** entre máquinas — **não** descomente isso em **Void**. O passo de **SO** do Topgrade nesse host mapeia para **`xbps`**, não para **`apt`**.

**Shebang:** use **`#!/bin/bash`** ou **`#!/usr/bin/env bash`** — corrija erros de digitação (ex.: **`bas0`**) antes de encaixar o script em **cron** ou **launcher**.

### 2.6 Debian em ARM / SBC — Topgrade só dentro de `venv` Python

Placas **single-board** (por exemplo classe **Raspberry Pi** com **Debian** ou **Raspberry Pi OS**) costumam repetir o **mesmo bloco `apt` pesado** do `gta` de desktops. O **Topgrade** às vezes fica instalado **só** via **`pip`** num **virtualenv** do usuário (ex.: **`$HOME/.venv`**).

**Envelope típico:**

1. `source "$HOME/.venv/bin/activate"`
2. `topgrade -y`
3. `deactivate`

**Por que aparece `topgrade: command not found`:** shells que **não** ativam o venv **não** colocam **`topgrade`** no **`PATH`**. Rodar **`topgrade --config-reference`** “solto” falha da mesma forma — ative o venv antes ou instale o Topgrade num destino **global** (**pipx**, pacote da **distro**, binário de **release**, **cargo**, …).

**Endurecimento (escolha um modelo):**

- Sempre rode manutenção pelo **`gta`** (ou um wrapper) que **ativa** o venv antes do **Topgrade**.
- Prefira **`pipx install topgrade`** (ou equivalente) para o CLI cair num **bin** estável que você **já** inclui no **`PATH`**.
- Se **estender** o **`PATH`** com **`$HOME/.venv/bin`**, faça de forma **consciente** (shell de login vs **cron** vs **SSH**) para **cron** e jobs **não interativos** não “pularem” o Topgrade sem querer.

**Variante de rasto:** alguns `gta` terminam em **`update-initramfs -u`** **sem** **`needrestart`** ou refresh de **GRUB** — comum em imagens **mais leves**; mantenha a história **por host** em notas privadas.

**`touch /forcefsck`:** mesmo cuidado do **item 2.5** — só quando você **quer** forçar **fsck** no **próximo boot**.

---

## 3. Topgrade no Windows

- O Windows usa **configuração** Topgrade **à parte** (consulte **`topgrade --config-reference`** no Windows para caminhos e chaves).
- Podem existir passos **winget**, **Chocolatey**, **Scoop** — **prefira um** gestor principal por pacote (**item 1.3**).

---

## 4. Homelab e scripts do repo

- **GitHub Actions** continua com **secrets do repositório** — **não** Bitwarden em runners públicos por padrão ([OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md)).
- Scripts de **LAB-OP** e **`homelab-host-report.sh`** só **enxergam** `bw` se ele estiver no **PATH** daquele host — [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md).

---

## 5. tmux no lab-op (repositório **tmux-configs**)

Use **um** repositorio GitHub como fonte de verdade para layout e atalhos do terminal; aplique em **cada** Linux do laboratorio (Zorin/lab-node-02, Raspberry Pi, Void/LAB-NODE-03, LMDE/LAB-NODE-01, etc.):

- **Repositorio:** [github.com/FabioLeitao/tmux-configs](https://github.com/FabioLeitao/tmux-configs) — clone: `https://github.com/FabioLeitao/tmux-configs.git`.
- **Primeiro** instale o binario **`tmux`** com o gestor da distro (`apt` / `xbps-install` / baseline Ansible no LAB-NODE-01 ja inclui).
- **Depois** clone e siga o **README** daquele repo (em geral symlink `~/.tmux.conf`, TPM/plugins, tecla prefixo). Esqueleto:

  ```bash
  mkdir -p ~/Projects/dev && cd ~/Projects/dev
  git clone https://github.com/FabioLeitao/tmux-configs.git
  cd tmux-configs
  # README: aplicar config (symlink ou copia), instalar gestor de plugins se precisar, abrir nova sessao tmux e validar.
  ```

- Mantenha **um** fluxo por maquina (mesmo caminho de clone em todos os hosts, ou excecoes em notas privadas).

---

## Ver também

- [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md) — contrato `bw`, CI, testes.
- [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) — baseline ThinkPad LAB-NODE-01 + LMDE.
- [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) — captura de inventário.
- [tmux-configs](https://github.com/FabioLeitao/tmux-configs) — dotfiles tmux (secao **5** acima).

**Última revisão:** 2026-04 — fluxos do operador (winget, WAU, Topgrade, `gta`, Void **xbps**, Topgrade em **`venv`** em ARM); secao **1.2.1** (Void + `bw`) e secao **5** (**tmux-configs**); **confirme** IDs do Bitwarden CLI no site / **winget** no momento da instalação.

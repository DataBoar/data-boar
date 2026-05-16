# ThinkPad LAB-NODE-01 + LMDE 7 — preparação para desenvolvimento (Data Boar / lab)

**English (short pointer):** same content intent as this file; no separate EN twin unless needed for reviewers — use [TECH_GUIDE.md](../TECH_GUIDE.md) for package names in English context.

**Objetivo:** Deixar o **ThinkPad LAB-NODE-01** com **LMDE 7** atualizado, com uma linha de base **segura** e com os **pacotes de sistema** necessários para clonar este repositório, rodar **`uv sync`**, **`pytest`**, e **Docker CE** (baseline Ansible; Podman opcional) alinhados a [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) e [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md).

**Base:** LMDE 7 (“Gigi”) usa **Debian 13 (Trixie)** — nomes de pacotes seguem `apt` como no Debian. Ajuste se a sua imagem for mais antiga ou misturar repositórios.

**Âmbito:** laptop **do operador** (não substitui [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) nem notas em `docs/private/`).

**Reinstalação “do zero”:** segue o **§0** (Ventoy + UEFI + **Secure Boot** ligado) e o instalador gráfico do **LMDE 7**. **Quando o LAB-NODE-01 já estiver no LMDE 7 com sudo**, continua no **§1**.

## Onde está cada parte (mapa rápido)

|Seção|Conteúdo|
|---|---|
|**§0**|Instalação: **Ventoy** (USB), **UEFI**, **Secure Boot** ativo, LMDE 7 no ThinkPad **LAB-NODE-01**.|
|**§1**|Checklist antes de começar (disco, rede, backup).|
|**§2**|`apt update` / `full-upgrade`, root se necessário.|
|**§3**|Segurança: `ufw`, `unattended-upgrades`, `fwupd`, Lynis, sysctl conservador; SSH opcional.|
|**§4**|Ferramentas de dev gerais (`git`, `build-essential`, etc.).|
|**§5**|Python **3.13** (recomendado; **≥3.12** ok) + libs de sistema, **`uv`**, clone, `uv sync`, `pytest`.|
|**§6**|LAB-NODE-01: energia (**`tlp`**), **I/O NVMe**, **kernel/sysctl** (performance prudente).|
|**§7**|Docker CE (baseline Ansible) e Podman opcional.|
|**§8–§9**|Pacotes homelab/auditoria; checklist final.|
|**§10**|Links relacionados no repositório.|

**Depois disto (não é instalação de SO):** stack mínima lab-op → [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md); Grafana/Prometheus/logs → [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md).

---

## 0.x Decisão de instalação: dual boot (Windows 11 + LMDE) vs LMDE-only

**Recomendação padrão para este projeto:** manter **dual boot** (Windows 11 + LMDE) quando o LAB-NODE-01 for uma **workstation do operador**.

- **Por quê**: reduz risco operacional (firmware/BIOS tools, recovery, apps específicas de Windows), sem impedir que o LMDE seja o ambiente principal para dev/lab.
- **Como mitigar drift**: trate o Windows como **fallback** (mínimo necessário), e concentre o fluxo Data Boar no LMDE.

**Quando faz sentido LMDE-only:** quando o LAB-NODE-01 for um host dedicado de laboratório (quase “appliance”) e você quiser minimizar variação operacional. Nesse caso, registre a decisão em nota privada (custo/benefício + riscos) e mantenha backups.

### 0.x.1 Pré-flight no Windows (dual boot sem drama): BitLocker, chaves e espaço livre

**Objetivo:** antes de bootar o instalador do LMDE, deixar o Windows num estado “boring” para particionamento/UEFI/Secure Boot, reduzindo risco de travar em recovery.

- **BitLocker (recomendação prática)**:
  - Para a janela de instalação (mudança de boot/partição), prefira **desligar** ou ao menos **suspender** o BitLocker no `C:`. Isso evita cair em **BitLocker Recovery** após mudanças em UEFI/TPM/boot order.
  - **Backup da recovery key**: faça o backup no seu cofre (ex.: **Bitwarden**) *antes* de mexer no BIOS/partições. **Nunca** cole chaves em issues/PRs/arquivos rastreados no Git.
  - **Depois que o dual boot estiver estável**: você pode reconsiderar reativar BitLocker (com disciplina de **Suspend/Resume** antes de qualquer mudança de firmware/boot).
- **Desligar hibernação/fast startup** (evita NTFS “sujo” e atrito de dual boot):

```powershell
powercfg /h off
```

- **Criar espaço não alocado (recomendado: pelo Windows)**:
  - Abra **Gerenciamento de Disco** (`diskmgmt.msc`) → `C:` → **Diminuir volume…** e crie espaço **não alocado** para o LMDE.
  - Evite encolher NTFS pelo instalador Linux se o Windows conseguir fazer (menos risco).
  - **Regra prática (ordem ideal):** faça este “shrink” **antes** de bootar o Live/instalador do LMDE. Assim, quando você chegar no particionamento manual do instalador, o espaço já aparece como **Free space / Unallocated**, sem precisar redimensionar NTFS “do lado Linux”.
  - **Se você esqueceu e já está no Live:** pode voltar ao Windows com segurança para fazer o shrink.
    - Saia/cancele o instalador (não aplique mudanças).
    - Reinicie no Windows.
    - Faça o shrink em `diskmgmt.msc`.
    - Volte ao Live/instalador e continue do particionamento manual — agora o free space vai aparecer.
- **Evidências mínimas (SRE-friendly)**:
  - Foto da tela do BitLocker (estado “ligado/suspenso/desligado”).
  - Foto do `diskmgmt.msc` mostrando o **espaço não alocado**.
  - Foto do Boot Menu/UEFI mostrando USB/UEFI e Secure Boot ligado (se necessário).

#### 0.x.1.1 Passphrase LUKS (sem “errar digitando”) — workaround opcional

**Preferido (recomendação):** usar o **Bitwarden** diretamente no mesmo dispositivo em que você está digitando (desktop app/mobile) e colar via clipboard local. Isso reduz a superfície (não passa por mensageria).

**Workaround (último caso, mas prático em instalação):** enviar a passphrase por **Bitwarden Send** para você mesmo, com controles agressivos:

- **Senha forte** para abrir o Send
- **Expiração curta** (ex.: **1h**)
- **Limite de acessos** (ex.: **1 leitura**)
- **Revogar/expirar** o Send assim que terminar

**Importante:** isso ainda aumenta a superfície se você abrir o link em um app de chat (WhatsApp/Signal/etc.). Se usar mensageria, trate como “canal de conveniência”, não como local de armazenamento; prefira abrir o Send no navegador/app Bitwarden e colar localmente.

**Regra de ouro:** nunca cole a passphrase em chat/issue/arquivo versionado; não tire screenshot da passphrase.

## 0.x.2 Biometria (fingerprint / face) no Linux (opcional, estilo “Windows Hello”)

**Objetivo:** quando o hardware suportar, usar biometria para **login/unlock** e (opcionalmente) prompts de **polkit**. Para **sudo**, trate como decisão consciente (conveniência vs postura).

### 0.x.2.1 Compatibilidade (antes de prometer que “vai funcionar”)

1) Descubra o USB ID do leitor (interno ou USB):

```bash
lsusb
```

2) Confirme suporte no `libfprint`:

- `https://fprint.freedesktop.org/supported-devices.html`

> Exemplo real (comum): alguns leitores Microsoft/DP podem aparecer como `045e:00bb` e constar como suportados no `libfprint` — sempre confirme pelo seu `lsusb`.

### 0.x.2.2 Setup básico no LMDE (login/unlock)

Em Debian/LMDE o caminho típico é `fprintd` + integração PAM:

```bash
sudo apt update
sudo apt install -y fprintd libpam-fprintd
fprintd-enroll
fprintd-verify
```

Depois, habilite via PAM (tela interativa):

```bash
sudo pam-auth-update
```

### 0.x.2.3 Decisão: usar biometria para `sudo`?

- **Recomendação conservadora (padrão lab-op):** habilitar biometria para **login/unlock** e evitar mexer em `sudo` até você decidir conscientemente.
- Se você optar por biometria no `sudo`, faça isso de forma testável e documentada, mantendo um caminho de fallback (senha) e registrando a decisão em nota privada (trade-offs).

## 0. Instalação no LAB-NODE-01 — Ventoy, UEFI e **Secure Boot** ligado

**Objetivo:** preparar o USB com **Ventoy**, manter **Secure Boot ativo** no ThinkPad durante a instalação **e** depois no Linux, sem pedir que desligues o Secure Boot de forma permanente. **“Device Guard”** (e **Credential Guard**) são nomes de recursos **do Windows**; no **LMDE** não existem com esses nomes — o paralelo é **Secure Boot + TPM (se usares LUKS/TPM) + endurecimento em camadas (§3)**. Na **máquina onde geras o USB** (ex. Windows 11 com **HVCI/Device Guard**), **você pode manter** essas políticas; o **Ventoy2Disk** não exige desligá-las.

### 0.1 Versão do Ventoy (confirma no dia)

A linha de releases mudou de **`1.0.x`** para **`1.1.x`**. Em **dezembro de 2025** a release estável citada na comunidade era **v1.1.10** — **no dia da instalação** confirma em **[Ventoy — GitHub Releases](https://github.com/ventoy/Ventoy/releases)** ou **[ventoy.net — download](https://www.ventoy.net/en/download.html)**. Se o teu stick já tiver uma 1.1.x recente, **você pode atualizar o Ventoy no USB** (mesma ferramenta `Ventoy2Disk`) antes de copiar a ISO do LMDE.

### 0.2 Preparar o USB com **suporte a Secure Boot**

O suporte documental oficial: **[Ventoy — about Secure Boot (UEFI)](https://www.ventoy.net/en/doc_secure.html)** (desde **1.0.07**; opção **ligada por padrão** desde **1.0.76** no `Ventoy2Disk`).

**Windows (GUI):**

1. Extrai o ZIP do Ventoy correspondente à tua arquitetura (normalmente **x86_64**).
1. Executa **`Ventoy2Disk.exe`** como administrador.
1. Escolhe o disco USB correto (cuidado a não apontar para outro disco).
1. Em **Option → Secure Boot Support**: mantém **ativo** (as versões recentes já vêm assim).
1. Em **Option → Partition Style**: prefira **GPT** (UEFI nativo; combina com Secure Boot).
1. (Opcional) Em **Option → Partition Configuration**: mantenha o padrão, a não ser que você tenha um motivo claro (ex.: reservar espaço fixo para ISO vs dados).
1. **Install** (ou **Update** se já for um stick Ventoy).

**Recomendação prática para este projeto (para evitar “surpresas”):**

- **UEFI + Secure Boot**: use o USB em modo **UEFI** (não Legacy/CSM).
- **GPT + exFAT**: manter **GPT** e filesystem de dados **exFAT** funciona bem para copiar ISOs pelo Windows e também acessar no Linux.
- **“Mostrar todos os dispositivos”**: só use se você estiver com dúvida no enumerador do Windows; é fácil selecionar o disco errado quando o filtro é removido.

**Linux (script):**

```bash
# Dentro da pasta descompactada do Ventoy:
sudo bash Ventoy2Disk.sh -i -s /dev/sdX   # substitui sdX pelo dispositivo USB certo; -s = Secure Boot
```

1. Copia a imagem **`lmde-7-*.iso`** (oficial **Linux Mint LMDE**) para a partição de dados do Ventoy (exFAT/NTFS — a que aparece no Windows/macOS/Linux).

### 0.3 Firmware do LAB-NODE-01 antes do boot

1. Opcional mas recomendado: na **Windows** ou com **fwupd** noutro Linux, verifica se há **BIOS/UEFI** novo para **LAB-NODE-01** (melhorias TPM, UEFI e arranque).
1. Reinicia, **F1**/**Enter** (varia por geração) para **UEFI/BIOS Setup**.
1. **Boot mode:** **UEFI only** — **não** uses Legacy/CSM para esta instalação.
1. **Secure Boot:** **Enabled** (mantém **ligado**).
1. Grava e sai.

### 0.3.1 Checklist rápido do BIOS/UEFI (antes de instalar)

**Objetivo:** garantir que o LAB-NODE-01 está com o básico certo para **dual boot com fallback**, **Secure Boot ligado**, e boa compatibilidade com Linux.

- **Boot**
  - **UEFI only** (sem Legacy/CSM).
  - **Secure Boot: Enabled**.
  - **Startup / Boot order**: deixe o SSD interno como padrão; use o menu de boot só para iniciar o USB quando necessário.
- **Security**
  - **TPM 2.0**: habilitado (útil para postura e, se você escolher, integração futura com LUKS/TPM).
  - **Fingerprint / Predesktop authentication**: se você não precisa desbloquear **antes** do SO, prefira deixar **desligado** e usar o fingerprint **já no Linux** (reduz complexidade de pré-boot).
- **Config → CPU**
  - **Intel Hyper-Threading**: **On** (padrão ok).
  - **Intel Virtualization Technology**: **On** (útil para Docker/VMs; pode ficar ligado).
- **Config → Power**
  - Para instalação e testes, **Balanced** costuma ser mais previsível que “Maximum Performance”. Se você estiver caçando bugs térmicos, aí sim faz sentido forçar “Maximum Performance” temporariamente.
- **Date/Time**
  - Confirme data/hora; depois no Linux configure `timedatectl set-local-rtc 0` (recomendado em dual boot para evitar drift).

#### 0.3.2 Checklist por tela (do seu BIOS) — o que manter ligado/desligado

Esta subseção traduz “o que você viu nas fotos” em uma decisão prática para o seu objetivo: **LMDE como default**, Windows como **fallback** e **firmware updates**, e **mínimo risco de drift**.

- **Security → Security Chip (TPM 2.0 / Intel PTT)**
  - **Security Chip**: **On**.
  - **Intel PTT**: **On**.
  - **Physical Presence for Clear**: **On** (bom: evita “limpeza silenciosa” do TPM).
  - **Por quê**: o TPM ajuda postura, e pode ajudar fluxo de disco criptografado no futuro; manter “clear” como ação física reduz risco operacional.
- **Security → UEFI BIOS Update Option**
  - **Secure RollBack Prevention**: **On**.
  - **Windows UEFI Firmware Update**: **On** (faz sentido para seu dual boot “Windows só pra firmware”).
  - **Flash BIOS Updating by End-Users**: prefira **Off** se você quer reduzir superfície/erro humano; deixe **On** só se você realmente usa flashes manuais fora do Windows/ferramentas oficiais.
- **Security → Memory Protection**
  - **Execution Prevention**: **On**.
  - **Intel Total Memory Encryption**: **Off** é OK (em geral não é requisito para seu cenário; pode trazer custo/compatibilidade).
- **Security → Virtualization**
  - **Intel Virtualization Technology**: **On**.
  - **Intel VT-d Feature**: **On** (ajuda isolamento/DMA quando o kernel usa; bom para VMs e postura).
  - **Kernel DMA Protection**: **On**.
  - **Enhanced Windows Biometric Security**: não é crítico para o LMDE; pode ficar **On** se você usa Windows como fallback e não quer mexer.
  - **Por quê**: você ganha capacidade de VM/containers sem ter que voltar no BIOS; VT-d/DMA protection são bons defaults.
- **Security → I/O Port Access**
  - Para laptop de dev/lab, manter **habilitado** costuma ser a escolha prática (Wi‑Fi, Bluetooth, câmera, USB).
  - Se você quiser reduzir superfície, o maior “ganho fácil” costuma ser **desligar o que você não usa nunca** (ex.: **microfone/câmera** quando o laptop fica em bancada; Bluetooth se você não usa).
  - **Regra do projeto**: qualquer desativação aqui deve ser “consciente” (com motivo) para não virar um tipo de drift (ex.: Wi‑Fi off e depois achar que o LMDE “não tem driver”).
- **Security → Secure Boot**
  - **Secure Boot**: **On**.
  - **Secure Boot Mode**: **User Mode** (padrão OK).
  - **Allow Microsoft 3rd Party UEFI CA**: **On** (normalmente necessário para `shim`/Debian/Ubuntu-family funcionarem com Secure Boot ligado).
  - **Key Management**: **não mexer** (não “Clear keys”, não “Setup mode”), a não ser que você esteja seguindo um runbook explícito.
- **Security → ThinkShield / Presence / Passwordless power-on**
  - **ThinkShield Passwordless Power-On**: prefira **Off** (reduz complexidade de pré‑boot; biometria fica no SO).
  - **Intelligent Security → User Presence Sensing**: opcional; se o foco é previsibilidade no lab, prefira **Off**.
  - **ThinkShield secure wipe**: prefira **Off** no dia a dia e só ligue quando for usar (evita ativação acidental).
- **Config → Intel AMT**
  - Se você não usa gerenciamento remoto/vPro de forma consciente: prefira **Disabled**.
  - Se manter habilitado por algum motivo: deixe **USB key provisioning** **Off** (como nas suas telas) e trate AMT como “superfície extra” (documente o motivo).
- **Config → Thunderbolt 4**
  - **PCIe Tunneling**: se você **não** usa dock/armazenamento Thunderbolt, deixar **Off** reduz risco de DMA e costuma ser mais simples.
  - Se você usa TB dock/armazenamento e algo “não funciona” no Linux, esta é a primeira chave a revisitar (aí sim considere **On**).
- **Config → Network**
  - **UEFI IPv4/IPv6 Network Stack**: se você não usa PXE/boot por rede, prefira **Off** (menos superfície/tempo de boot).
  - **Network Boot (PXE)**: se você não usa, prefira **Disabled**.
  - **Lenovo Cloud Services**: prefira **Off** para “mínimo drift” (a menos que você tenha um motivo explícito).
  - Wake-on-LAN/dock: use só se precisar; caso contrário, **Off** é mais previsível.
- **Config → USB**
  - **Always On USB**: opcional; se você quer menos consumo/surpresas com carga, pode deixar **Off**.
- **Startup**
  - **Boot Mode**: mantenha “Quick” durante uso normal; se estiver depurando boot/firmware, mude temporariamente para um modo mais verboso/diagnóstico (quando existir).
  - **Boot Order Lock**: deixe **Off** enquanto estiver instalando/ajustando; depois você pode ligar para “travar” a ordem.

### 0.4 Primeiro arranque do Ventoy com Secure Boot

1. Liga o USB, **boot** pelo dispositivo UEFI (menu de boot do ThinkPad).
1. **Na primeira vez** por máquina, o Ventoy pode mostrar o fluxo **“Enroll Key”** ou **“Enroll Hash”** (tela azul, conforme doc oficial). Segue **uma** das vias até ao fim — em muitos ThinkPads **Enroll Hash** é o que menos atrito dá.
1. Se aparecer erro estilo **“Linpus lite”** ou recusa contínua: atualiza **Ventoy** no USB, confirma **UEFI only**, e revê a doc **Secure Boot** do Ventoy; **não** assumas que precisas desligar Secure Boot de forma permanente — primeiro tenta **regravar** o USB com release mais nova.

### 0.5 Instalar o LMDE 7 a partir do menu Ventoy

1. No menu Ventoy, escolhe a ISO **LMDE 7**.
1. No instalador: idioma, teclado, rede.
1. **Disco:** recomenda-se **criptografia LUKS** (passphrase forte; regista num **local seguro** — ex. gestor de segredos). Isto alinha com **TPM** presente no LAB-NODE-01 para arranque **posterior** conforme opções que o instalador oferecer.
1. Cria o usuário; ao fim, reinicia e **remove o USB** quando pedido.

### 0.5.1 Dual boot (Windows + LMDE) com LUKS via particionamento manual (GParted + `cryptsetup`)

**Quando usar:** se o instalador não oferecer claramente “install alongside Windows” com LUKS, ou se você quer **zero ambiguidade** controlando o particionamento.

**Pré-requisito:** o `C:` já foi reduzido no Windows e existe **Free space / Unallocated** no NVMe (ver **§0.x.1**).

**Regra de ouro:** não formatar as partições NTFS do Windows e não formatar a **EFI System Partition** existente.

1. No instalador, escolha **Manual partitioning** (não use “Automated installation / Erase disk”).
1. Clique em **Launch GParted**.
1. No disco **`/dev/nvme0n1`**, dentro do free space:
   - Crie uma partição **ext4** para **`/boot`** (1–2 GiB; label sugerido: `boot_lmde`).
   - Crie outra partição com **todo o resto** (tipo **unformatted**; label sugerido: `crypt_lmde`).
   - Clique **Apply (✓)** e confirme.
1. Ainda no Live, abra um terminal e identifique as partições recém-criadas:

```bash
lsblk -f
```

1. Formate a partição grande como **LUKS** e abra como `cryptroot` (ajuste `pX` para o número real):

```bash
sudo cryptsetup luksFormat /dev/nvme0n1pX
sudo cryptsetup open /dev/nvme0n1pX cryptroot
```

1. Escolha o filesystem **dentro** do LUKS (recomendação depende do objetivo):
   - **`ext4`**: mais simples/boring (bom se você não vai manter snapshots).
   - **`btrfs` + Snapper**: snapshots/rollback desde o dia 1 (alinha com `<lab-host-2>`).

**Opção A — ext4 (mais simples):**

```bash
sudo mkfs.ext4 -L root_lmde /dev/mapper/cryptroot
```

**Opção B — btrfs (snapshots desde o dia 1):**

```bash
sudo mkfs.btrfs -L root_lmde /dev/mapper/cryptroot
```

1. Volte ao instalador (particionamento manual) e configure mounts:
   - **EFI existente** (`/dev/nvme0n1p1`, FAT32): mount **`/boot/efi`**, **não** formatar.
   - `boot_lmde` (ext4): mount **`/boot`**, formatar.
   - `cryptroot` (ext4/btrfs em `/dev/mapper/cryptroot`): mount **`/`**, formatar.
   - Swap: opcional (swapfile depois é OK se você não usa hibernação).

#### Armadilha comum: instalador não lista `/dev/mapper/*` (dm-crypt)

Algumas versões do instalador do Mint/LMDE **não exibem** devices `dm-crypt` (ex.: **`/dev/mapper/cryptroot`**) na tela de particionamento manual. Se isso acontecer:

- **Não** selecione **`/dev/nvme0n1p6`** como `/` e marque “format btrfs/ext4” achando que está formatando “dentro do LUKS” — isso **sobrescreve o header do LUKS** e te joga num loop de reinstall.
- Sinal de que você caiu na armadilha: você “tem `cryptsetup status cryptroot` ok”, mas o instalador só oferece **`/dev/nvme0n1p6`** e nunca aparece um item `/dev/mapper/...`.

**Workaround recomendado:** use o **Plano B (§0.5.3)**: instalar primeiro em **btrfs normal** no `p6`, e só depois criptografar via **`cryptsetup reencrypt`** (padrão “Mint-like”).

### 0.5.2 Snapshots “desde o dia 1” (btrfs + Snapper) — referência `<lab-host-2>`

**Motivação:** o host `<lab-host-2>` usa **btrfs no `/`** e o **Snapper** mantém snapshots em **`/.snapshots`** (subvolume dedicado). No LMDE (Debian-family + systemd), fica ainda mais fácil automatizar via timers.

**Nota:** o instalador pode formatar/montar o `/` em btrfs sem criar subvolumes. Isso é ok para começar; depois da instalação você cria `/.snapshots` e configura o Snapper.

Depois do primeiro boot no LMDE (já instalado), rode:

```bash
sudo apt update
sudo apt install -y snapper btrfs-progs
```

Crie o subvolume de snapshots (modelo do `<lab-host-2>`) e monte no lugar certo:

```bash
sudo mkdir -p /.snapshots
sudo btrfs subvolume create /.snapshots
```

Crie a config do Snapper para o root (`/`) e habilite timers:

```bash
sudo snapper -c root create-config /
sudo systemctl enable --now snapperd
sudo systemctl enable --now snapper-timeline.timer snapper-cleanup.timer
```

Verificações rápidas:

```bash
sudo snapper list-configs
sudo snapper -c root list | head -n 30
sudo btrfs subvolume list /.snapshots | head
systemctl list-timers --all | grep -i snapper || true
```

#### 0.5.2.1 Retenção (para não “comer o disco”)

**Objetivo:** manter rollback fácil **sem** acumular snapshots indefinidamente.

**Importante:** snapshots **não** substituem **backup**. Snapshot te salva de “oops/upgrade ruim” no mesmo disco. Backup te salva de **falha do SSD**, perda/roubo, ou corrupção ampla.

O Snapper limpa snapshots automaticamente com o **`snapper-cleanup.timer`**; o que manda é a política em **`/etc/snapper/configs/root`**.

Defaults “conservadores” (bom para workstation):

- **Timeline**: mantenha, mas com limites baixos (ex.: alguns horários, poucos diários, poucos mensais).
- **Number cleanup**: mantenha um número máximo de snapshots “importantes”.

Exemplo de valores razoáveis (ajuste ao seu apetite):

- `TIMELINE_LIMIT_HOURLY="6"` (últimas 6 horas)
- `TIMELINE_LIMIT_DAILY="7"` (7 dias)
- `TIMELINE_LIMIT_WEEKLY="4"` (4 semanas)
- `TIMELINE_LIMIT_MONTHLY="3"` (3 meses)
- `TIMELINE_LIMIT_YEARLY="0"` (desligado)
- `NUMBER_LIMIT="10"` e `NUMBER_LIMIT_IMPORTANT="5"` (cap geral)

Para editar:

```bash
sudoedit /etc/snapper/configs/root
sudo systemctl restart snapperd
```

E para validar que o cleanup roda:

```bash
systemctl list-timers --all | grep -i snapper
sudo snapper -c root list | tail -n 20
```

**Dica prática:** marque snapshots realmente importantes como “important” (quando fizer uma mudança grande e estável) e deixe os de timeline serem “descartáveis”.

#### 0.5.2.2 Guardrails de “alocação vs backup” (workstation sem stress)

- **Tenha um budget mental de espaço**:
  - reserve um “piso” para o próprio sistema + dev (ex.: 30–40% do volume) e trate o resto como espaço de trabalho;
  - se o `/.snapshots` começar a crescer demais, é sinal de retenção alta *ou* dados grandes sendo versionados por snapshot.
- **Monitore uso do btrfs e do `/.snapshots`** (1 min, sem tooling extra):

```bash
sudo btrfs filesystem usage -T /
sudo du -sh /.snapshots 2>/dev/null || true
```

- **Evite snapshot de lixo volumoso**:
  - mantenha downloads/ISOs/VM images fora do root sempre que possível (ex.: outro volume/diretório que você não precisa snapshotar).
  - para cache que explode (containers), escolha conscientemente onde fica (`/var/lib/docker`, `~/.cache`, etc.). Snapshots vão capturar *mudanças* nesses diretórios.
- **Backups “de verdade” (fora do disco)**:
  - snapshots são a camada 1 (rollback rápido);
  - mantenha pelo menos 1 cópia off-host (pCloud/drive externo/NAS) do que é crítico (configs, chaves, documentos, repositórios). A política/como fazer isso fica em docs/ops separados; aqui só o lembrete.

### 0.5.3 Plano B (recomendado quando o instalador não vê `/dev/mapper`): instalar em btrfs e criptografar depois (`cryptsetup reencrypt`)

**Ideia:** completar a instalação do LMDE normalmente (root em btrfs no `p6`), **sem root**, e então transformar **o mesmo `p6`** em LUKS2 **sem destruir o btrfs**, usando `cryptsetup reencrypt`.

**Quando usar:** quando o instalador não lista `/dev/mapper/*`, mas você quer **FDE com LUKS2** + **btrfs**.

**Checkpoint de segurança antes de começar:**

- `lsblk -f` deve mostrar `p6` como **btrfs** (não `crypto_LUKS`).
- O instalador deve apontar **`/dev/nvme0n1p6` → `/`** e format **btrfs**.
- Ao terminar, **NÃO reinicie**.

**Passos (resumo):**

1. Instale LMDE com particionamento manual:
   - `p1` → `/boot/efi` (não formatar)
   - `p5` → `/boot` (ext4)
   - `p6` → `/` (btrfs)
   - GRUB em `/dev/nvme0n1`
2. Antes de criptografar, reduza o filesystem em **32 MiB** para caber o header do LUKS (em `@` se existir):
3. Rode `cryptsetup reencrypt --encrypt --type luks2 --reduce-device-size 32m /dev/nvme0n1p6`
4. Abra o LUKS, monte root/boot/efi e, em chroot:
   - configure `/etc/crypttab`
   - `update-initramfs -u`
   - `update-grub`

**Notas de troubleshooting (do mundo real):**

- **DNS falha no `chroot` (`apt update`: “Temporary failure resolving …”)**: no Live, às vezes o `chroot` não herda um `resolv.conf` funcional. Workaround rápido (dentro do `chroot`):

```bash
printf "nameserver 1.1.1.1\nnameserver 8.8.8.8\n" > /etc/resolv.conf
apt update
```

- **`update-initramfs -u` com warnings `Unknown key type PC_SUPER_LEVEL2`**: já observamos esses warnings durante este fluxo; normalmente não impedem o boot e parecem ligados a keymap/console-setup. Se o comando termina e o `initrd.img-*` é gerado, trate como **warning** (e registre como evidência).

**Nota:** este Plano B é descrito em detalhe em referências públicas (ex.: guias de Mint/LMDE btrfs+FDE). Ele evita depender do instalador “enxergar” o mapper.

#### 0.5.3.1 Pós-boot: auto-unlock “BitLocker-like” (TPM-only) com Clevis (opcional)

**Objetivo:** manter o disco protegido **se o SSD for extraído** (roubo), mas permitir boot **sem digitar** a passphrase longa no dia a dia — modelo similar a BitLocker em modo **TPM-only**.

**Trade-off:** se o atacante tiver o **laptop inteiro** e conseguir bootar “normalmente” (mesmo firmware/boot chain), o TPM pode liberar e o sistema sobe. Para elevar o bar, você precisa de **PIN pré-boot** (TPM+PIN) — este manual registra TPM-only como padrão “sem atrito”.

**Pré-requisitos:**

- Secure Boot habilitado (para manter PCR7 estável e útil).
- Repositórios Debian com **`contrib non-free non-free-firmware`** habilitados (em LMDE isso não é “multiverse”; é Debian-style).

Checar/inspecionar repositórios (sem colar dados sensíveis do seu ambiente):

```bash
grep -R --line-number -E '^(deb|deb-src)\s+' /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null
```

Instalar dependências:

```bash
sudo apt update
sudo apt install -y clevis clevis-luks clevis-tpm2 clevis-initramfs tpm2-tools
```

Sanity check do TPM + PCR (recomendação prática: usar **PCR 7**; em alguns setups o PCR 11 pode vir zerado):

```bash
sudo tpm2_getcap properties-fixed | sed -n '1,40p'
sudo tpm2_pcrread sha256:7,11
```

Fazer bind do LUKS ao TPM2 (PCR 7):

```bash
sudo clevis luks bind -d /dev/nvme0n1p6 tpm2 '{"pcr_bank":"sha256","pcr_ids":[7]}'
sudo update-initramfs -u
sudo root
```

Validar que o token/slot existe:

```bash
sudo clevis luks list -d /dev/nvme0n1p6
sudo cryptsetup luksDump /dev/nvme0n1p6 | sed -n '1,180p'
```

**Comportamento esperado no boot:** pode “pausar” por 1–2 segundos no prompt de passphrase e seguir sozinho quando o TPM liberar.

**Nota importante de privacidade:** outputs como `w`, “Last login”, IPs e hostnames são úteis para LAB-OP, mas **não devem** ir para arquivos rastreados. Se precisar registrar evidências, use `docs/private/homelab/` (gitignored).

### 0.6 Depois da instalação — Secure Boot com Debian/LMDE

O LMDE baseado em **Debian** usa normalmente **`shim`** + kernel assinado: com **Secure Boot ligado**, o sistema instalado deve **continuar a arrancar** sem desligar Secure Boot no firmware. Se **após** a instalação o firmware reclamar:

1. Confirma que não há **outro** bootloader não assinado a “saltar” à frente do `shim`.
1. Corre **`sudo dpkg-reconfigure shim-unsigned`** / pacotes **`shim-signed`** conforme a tua imagem (nomes exactos: `apt search shim` no LMDE).
1. Mantém **Secure Boot: Enabled** no UEFI; só em último caso segue notas do Debian para **MOK** (procedimento consciente, não “desligar tudo”).

### 0.6.1 Troubleshooting: “GRUB bootloader was not configured properly” no fim da instalação

**Sintoma:** ao final do instalador, aparece um aviso do tipo:

- *“WARNING: the grub bootloader was not configured properly! You need to configure it manually.”*

**Regra de ouro:** **não reinicie ainda**. Corrija **no Live** enquanto os volumes/mapeamentos estão frescos.

**Nota sobre outro alerta comum:** *“Low Disk Space … remaining”* costuma ser do **Live session** (overlay/ram/USB), não do SSD interno. Em geral é seguro **ignorar** para concluir a correção do bootloader; depois do primeiro boot no sistema instalado, esse alerta some.

#### Correção (Live → abrir LUKS → mount → chroot → `grub-install`)

1. No Live, abra um terminal.
1. Abra o LUKS e monte o sistema instalado (ajuste dispositivos se o seu layout diferir):

```bash
sudo cryptsetup open /dev/nvme0n1p6 cryptroot
sudo mkdir -p /mnt/target
sudo mount /dev/mapper/cryptroot /mnt/target

sudo mkdir -p /mnt/target/boot
sudo mount /dev/nvme0n1p5 /mnt/target/boot

sudo mkdir -p /mnt/target/boot/efi
sudo mount /dev/nvme0n1p1 /mnt/target/boot/efi

for i in /dev /dev/pts /proc /sys /run; do sudo mount --bind "$i" "/mnt/target$i"; done
sudo chroot /mnt/target /bin/bash
```

1. Dentro do `chroot`, reinstale/configure GRUB (UEFI) + `shim`:

```bash
apt update
apt install -y grub-efi-amd64 shim-signed
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=LMDE --recheck
update-grub
exit
```

1. Desmonte e feche o LUKS:

```bash
for i in /run /sys /proc /dev/pts /dev; do sudo umount -R "/mnt/target$i"; done
sudo umount -R /mnt/target/boot/efi
sudo umount -R /mnt/target/boot
sudo umount -R /mnt/target
sudo cryptsetup close cryptroot
```

1. Reinicie e remova o USB quando o instalador pedir. Confirme que o menu do GRUB lista LMDE e (idealmente) o Windows.

### 0.7 Resumo de requisitos que pediste

| Requisito | Onde fica coberto |
| --------- | ----------------- |
| USB com **Ventoy** atualizado | §0.1–0.2; confirmar versão no site oficial no dia |
| **Secure Boot** ligado na instalação | §0.2–0.5 |
| **Secure Boot** ligado na operação diária | §0.6 + §3 |
| **Device Guard** (Windows) ligado *enquanto preparas* o USB | Nota no início do §0 — no LMDE não há homônimo direto |

---

## 1. Antes de começar (checklist rápido)

| Item           | Nota                                                                                                                                        |
| ----           | ----                                                                                                                                        |
| **Instalação** | Preferir disco **criptografado** (LUKS) na instalação OEM; se já instalou sem, migrar é trabalhoso — documente a decisão em notas privadas. |
| **Rede**       | Wi‑Fi/Ethernet funcionando; **não** exponha serviços de desenvolvimento à Internet sem firewall e propósito claro.                          |
| **Backup**     | Antes de mudanças grandes no sistema, snapshot mental: **dados** em partição separada ou backup do `$HOME`.                                 |

---

## 2. Atualizar o sistema

```bash
sudo apt update
sudo apt full-upgrade -y
```

Reinicie se o kernel ou `libc` tiverem sido atualizados:

```bash
sudo root
```

Verifique versão:

```bash
cat /etc/os-release
uname -r
```

---

## 3. Linha de base de segurança (recomendado)

### 3.1 Firewall local (`ufw`)

Política mínima: negar entrada, permitir saída; liberar só o que precisar (ex.: **22/tcp** para SSH a partir da LAN).

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
# Se usar SSH a partir da rede de confiança:
sudo ufw allow from 10.0.0.0/16 to any port 22 proto tcp comment 'SSH LAN'
# Ajuste a sub-rede ao teu ambiente — ou restrinja ao IP do teu PC de trabalho.
sudo ufw enable
sudo ufw status verbose
```

**Data Boar em desenvolvimento:** se subires o dashboard em `0.0.0.0:8088` para testes na LAN, **não** abras **8088** na WAN; na LAN você pode liberar temporariamente:

`sudo ufw allow from 10.0.0.0/16 to any port 8088 proto tcp comment 'Data Boar lab LAN only'`

### 3.2 Atualizações de segurança automáticas (Debian)

```bash
sudo apt install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades
```

Confirme que está ativo (texto pode variar):

```bash
sudo unattended-upgrades --dry-run --debug 2>&1 | head -40
```

### 3.3 Firmware (ThinkPad + componentes)

```bash
sudo apt install -y fwupd
fwupdmgr refresh
fwupdmgr get-updates
# Se houver updates recomendados pela Lenovo/componentes:
sudo fwupdmgr update
```

Reinicie se o `fwupd` pedir. Isto ajuda **Wi‑Fi, TPM, BIOS/UEFI** quando há pacotes na LVFS.

#### 3.3.1 Troubleshooting: “tentei atualizar a BIOS e ela volta do boot sem mudar nada”

**Sintoma:** você inicia o fluxo de update (Windows / Lenovo / `fwupd`), o notebook reinicia, parece “fazer algo”, mas ao voltar a versão da BIOS **não mudou**.

**Objetivo deste checklist:** isolar **causa provável** sem tentar “forçar” (evitar brick) e juntar evidências mínimas para decidir o próximo passo.

**O que capturar (foto ou anotação) antes de tentar de novo:**

- **Tela Main do BIOS**: versão atual do UEFI/BIOS + data.
- **Tela Security → UEFI BIOS Update Option**: estado de opções de update/rollback.
- **Tela Security → Secure Boot**: ON/OFF + mode (User/Setup) + “Allow Microsoft 3rd Party UEFI CA”.
- **Tela Security → Security Chip (TPM)**: Security Chip / Intel PTT ON/OFF.
- **Tela Startup/Boot**: UEFI only vs Legacy/CSM, Quick/Diagnostics boot, e se há “Boot order lock”.
- **Fonte de energia**: AC conectado (muitos updates recusam sem bateria/AC).

**Regras de segurança (não pule):**

- **Não** desligue o notebook durante um update real.
- **Não** altere chaves de Secure Boot (não “Clear keys”, não “Setup mode”) só para “ver se vai” — isso costuma criar incidentes de boot.
- Se houver **BitLocker** no Windows, **suspenda temporariamente** antes de mexer em firmware (para não cair em recovery key após mudanças no TPM/boot).

**Causas comuns (na prática) e como validar:**

- **Pré‑requisitos não atendidos**: bateria mínima/AC obrigatório, temperatura alta, laptop em dock/USB‑C instável.
  - Ação: ligar no **carregador original**, remover periféricos “estranhos”, esperar resfriar.
- **Configuração bloqueando update**: opção de “flash by end users” off (ou política corporativa), rollback prevention.
  - Ação: conferir em **Security → UEFI BIOS Update Option**; documentar o estado (não “chutar”).
- **Tentativa via método errado para o modelo**: alguns ThinkPads funcionam melhor com **Lenovo Vantage (Windows)**; outros aceitam `fwupd`/LVFS.
  - Ação: tente 1 método por vez; anote resultado.
- **Secure Boot/TPM interferindo**: normalmente não impede update, mas pode disparar proteções (especialmente com BitLocker).
  - Ação: manter Secure Boot **ON** (padrão), mas garantir BitLocker suspenso no Windows durante a janela.

**Se o seu caso é ainda mais “duro” (como você descreveu no PC Windows principal de desenvolvimento):** *Vantage*, *Lenovo System Update* e o instalador baixado do site **nem chegam a mostrar progresso**, só reiniciam e voltam igual.

Neste caso, além dos itens acima, capture e valide estes pontos:

- **Security → UEFI BIOS Update Option**
  - Confirme se existe e como está a opção **“Flash BIOS Updating by End-Users”**.
    - Se estiver **Off**, isso pode impedir que alguns métodos iniciem o flash.
    - Se você quiser reduzir risco, você pode manter **Off** no dia a dia, mas precisa ficar **On** durante a janela de atualização.
  - Confirme se **“Windows UEFI Firmware Update”** está **On** (para o método Windows).
- **Security → Secure Boot**
  - Secure Boot **On** não deveria impedir update, mas **não** altere keys/mode para tentar “resolver”.
- **Startup**
  - **Boot Order Lock**: deixe **Off** durante a atualização.
  - Evite boot por dock/USB-C “instável” enquanto tenta atualizar.
- **Windows**
  - Se houver **BitLocker**: **suspenda** antes de tentar (para evitar bloqueios/recusas silenciosas por mudança de TPM/boot).
  - Garanta energia estável (AC + bateria com carga suficiente).

**Evidência no Linux (se você estiver tentando via `fwupd`):**

```bash
fwupdmgr --version
fwupdmgr get-devices
fwupdmgr get-updates
fwupdmgr update
```

Se falhar, salve o output completo (em nota privada) e rode:

```bash
journalctl -u fwupd --no-pager -n 200
```

**Nota importante (para “não esquecermos”):** você mencionou que isso está acontecendo também no **ThinkPad L-series (14-inch class)**. Este checklist é o ponto de partida; quando você trouxer as fotos do PC Windows principal de desenvolvimento, a gente compara as telas equivalentes (Main / Update Option / Secure Boot / TPM / Boot) e decide se há alguma configuração específica que está impedindo a aplicação do update.

### 3.4 SSH servidor (só se precisares)

Se **não** precisares de SSH **entrada** no LAB-NODE-01, **não** instales `openssh-server`. Se precisares:

```bash
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
```

Endureça: desative login root por password, use chave, e restrinja com `ufw` (como acima).

### 3.5 Lynis (relatório de hardening)

Útil antes de o LAB-NODE-01 entrar no **lab-op** — não substitui política nem pen-test, mas dá uma lista priorizável.

```bash
sudo apt install -y lynis
sudo lynis audit system
# Relatório em /var/log/lynis.log — rever sugestões e aplicar só o que fizer sentido para *estação de dev*
```

Tende a “reclamar” de coisas aceitáveis em laptop de desenvolvimento; usa o relatório como **checklist**, não como obrigação cega.

### 3.6 `sysctl` — rede e VM (valores **conservadores**)

Mede impacto antes de afinar agressivamente. Exemplo **seguro para desktop** com RAM razoável (ajusta ou omite linhas após testar):

```bash
sudo tee /etc/sysctl.d/99-workstation-lab-node-01.conf >/dev/null <<'EOF'
# VM — desktop com 16–32 GiB RAM típico
vm.swappiness=20
vm.vfs_cache_pressure=50
# Rede local / lab (não abre serviços — só comportamento de pilha)
net.ipv4.tcp_fastopen=1
net.core.somaxconn=4096
EOF
sudo sysctl --system
```

Se notares troca excessiva, volta `vm.swappiness` para o padrão (~60) ou remove o arquivo.

### 3.7 Pacote `auditd`, `debsecan`, `needrestart` (opcional)

```bash
sudo apt install -y debsecan needrestart
sudo debsecan --suite trixie 2>/dev/null | head -40   # ajusta o suite ao que /etc/os-release reportar
```

Depois de **upgrades** de kernel/libs, o **`needrestart`** indica o que precisa de reinício de serviço — útil para não ficares com `sshd` ou libs antigas carregadas.

**AppArmor:** o perfil padrão do Debian/LMDE costuma estar ativo; não desligue sem motivo. Para Cursor/AppArmor veja também [CURSOR_UBUNTU_APPARMOR.pt_BR.md](CURSOR_UBUNTU_APPARMOR.pt_BR.md).

---

## 4. Ferramentas de desenvolvimento gerais

```bash
sudo apt install -y \
  git curl ca-certificates \
  build-essential pkg-config \
  jq \
  tmux \
  htop \
  lsof \
  net-tools \
  dnsutils \
  openssh-client
```

### 4.1 Editor padrão do sistema (`/usr/bin/editor`) — evita prompts surpresa

Algumas ferramentas (ex.: `visudo`, `crontab -e`, `git commit` em certos fluxos) dependem do **editor padrão do sistema** (`/usr/bin/editor`). Em instalações novas, isso pode abrir `nano`/`ed` e travar teu fluxo.

**Recomendação:** escolher um editor e fixar via `update-alternatives` (não interativo).

Exemplo com **Neovim**:

```bash
sudo apt install -y neovim
sudo update-alternatives --set editor /usr/bin/nvim
```

Para checar:

```bash
readlink -f /usr/bin/editor
```

> Nota: `select-editor` é útil, mas é **interativo** (menos bom para automação). Para automação (Ansible), prefira `update-alternatives --set`.

**Cursor:** se usares **Cursor** em Debian/Ubuntu, vê também [CURSOR_UBUNTU_APPARMOR.pt_BR.md](CURSOR_UBUNTU_APPARMOR.pt_BR.md) (AppArmor / permissões).

---

## 5. Python 3.13 (recomendado) + dependências de sistema para **Data Boar**

O projeto suporta **Python ≥3.12**; **3.13** é o alvo recomendado no laptop para **paridade com a imagem Docker** publicada. Usa **`uv`** ([TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)).

### 5.1 Pacotes `apt` (alinhados ao repositório)

Confirma que **3.13** está nos repositórios: `apt-cache policy python3.13`. Se não existir (distro antiga), instala **`python3.12`** / **`python3.12-venv`** / **`python3.12-dev`** no lugar da linha abaixo.

```bash
sudo apt install -y \
  python3.13 python3.13-venv python3.13-dev \
  libpq-dev libssl-dev libffi-dev unixodbc-dev \
  zlib1g-dev
```

- **`zlib1g-dev`:** evita erros de link `-lz` ao compilar alguns wheels (ex. caminhos `mysqlclient` / similares).
- **`unixodbc-dev`:** base para **pyodbc** / drivers ODBC (SQL Server, etc.); o **driver Microsoft** para Linux é passo à parte, conforme conector.

Se fores usar **MariaDB/MySQL** com build nativo e aparecer `mariadb_config: not found`:

```bash
sudo apt install -y libmariadb-dev
```

### 5.2 `uv` (gestor de pacotes Python)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Reabra o terminal ou:
source "$HOME/.local/bin/env" 2>/dev/null || true
uv --version
```

### 5.3 Clonar e validar o projeto

```bash
cd ~/Projects   # ou o teu diretório preferido
git clone <URL-do-teu-fork-ou-origin> data-boar
cd data-boar
uv sync
uv run pytest -q --tb=no -W error
```

Se falhar por dependência opcional, vê `pyproject.toml` — exemplos:

```bash
uv pip install -e ".[nosql]"      # MongoDB/Redis
# Rich media / OCR: seguir TECH_GUIDE se precisares
```

---

## 6. ThinkPad LAB-NODE-01 — energia, I/O e kernel (opcional, reversível)

| Objetivo                 | Pacote / nota                                                                                                                              |
| --------                 | -------------                                                                                                                              |
| **Bateria / perfis**     | `sudo apt install -y tlp` e `sudo systemctl enable --now tlp` — ou usar apenas **Power Profiles** do Cinnamon se preferires menos camadas. |
| **Leituras de sensores** | `sudo apt install -y lm-sensors && sudo sensors-detect` (aceitar defaults com cuidado).                                                    |
| **Bluetooth / áudio**    | Geralmente já cobertos pelo LMDE; atualizações de firmware (§3.3) ajudam Wi‑Fi/BT.                                                         |

**Não** é obrigatório para desenvolvimento Data Boar; melhora experiência no hardware.

### 6.2 I/O em NVMe (scheduler e `fstab`)

NVMe moderno em kernel recente usa frequentemente **`none`** (multiqueue). Verifica:

```bash
for d in /sys/block/nvme*n*/queue/scheduler; do echo "$d: $(cat "$d")"; done
```

Se puderes escolher, **`none`** ou **`mq-deadline`** são típicos em NVMe; **não** forces `bfq` em NVMe sem medição.

Em **`/etc/fstab`**, para sistemas de arquivos em SSD, muitos operadores usam **`noatime`** (ou **`relatime`**, já default em muitos casos) para menos escritas metadata:

```text
# exemplo de opções numa linha de partição raiz — confirma UUID com `blkid`
UUID=XXXX  /  ext4  defaults,noatime  0 1
```

Revalida com `findmnt` e um root após editar o `fstab`.

### 6.3 Kernel — linha Debian + módulos (LAB-NODE-01)

Mantém o kernel **dos repositórios LMDE/Debian** para assinaturas alinhadas ao **Secure Boot**. Evita liquorix/random mainline **a menos que** saibas re-assinar ou aceitas gerir MOK.

Lista módulos pensados para ThinkPad (carregados ou built-in):

```bash
lsmod | egrep 'thinkpad_acpi|think_lmi|nvme|iwlwifi' || true
```

Se **Wi‑Fi** falhar após root novo, volta a §6.2/§3.3 (firmware `linux-firmware` / `fwupd`).

### 6.4 `zram` (swap comprimida — opcional)

Útil em máquinas com RAM mais justa; em 32 GiB pode ser desnecessário.

```bash
sudo apt install -y zram-tools
```

Lê **`/usr/share/doc/zram-tools/README.*`** (o nome do serviço varia entre releases Debian/LMDE — pode ser *generator* *systemd* ou script legacy). Objetivo: menos **I/O de swap em disco** em picos de compilação; se o pacote confundir ou não precisares, remove e mantém só o afinamento de **`vm.swappiness`** (§3.6).

### 6.5 Pronto para **lab-op** (SSH + inventário)

Quando o LAB-NODE-01 for host de laboratório:

1. Confirma **`openssh-server`** só se a política do lab o exigir; **`PermitRootLogin no`**, **`PasswordAuthentication no`**, chaves só.
1. Copia do repositório o manifest de exemplo **`docs/private.example/homelab/lab-op-hosts.manifest.example.json`** para **`docs/private/homelab/lab-op-hosts.manifest.json`** (gitignored) e acrescenta o LAB-NODE-01.
1. A partir do teu PC de trabalho: **`scripts/lab-op-sync-and-collect.ps1`** ou **`homelab-host-report.sh`** conforme [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md).

---

## 7. Contentores (lab — recomendado: Docker CE via baseline)

**Fonte de verdade no repositório:** [playbooks/lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml) com **`lab-node-01_install_docker_ce: true`** e plugin **Compose**. O papel **`lab-node-01_operator_supplementary_groups`** adiciona o login do operador ao grupo **`docker`** (e outros grupos padrão). **Depois do playbook:** novo login na sessão gráfica **ou** `newgrp docker` na shell **ou** SSH novo — senão `docker compose` falha com **permission denied** em `/var/run/docker.sock`.

- **Ansible (preferido):** ver [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md) e variáveis como **`lab-node-01_operator_target_user`** no inventário se correres `sudo ansible-playbook` (para não aplicar grupos ao utilizador errado).

- **Manual (não substitui o repo oficial Docker):** se precisares só de sanity sem Ansible, alinha com a doc Docker CE para Debian — **não** uses `docker.io` do Debian como substituto da baseline do projeto salvo decisão documentada.

**Podman** (rootless) continua **opt-in** no mesmo playbook (`lab-node-01_install_podman: false` por omissão). Para stack mínima lab-op com Podman/k3s, ver [LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md).

**Lab smoke multi-host:** [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md) — política prática: **dois** hubs Docker (por exemplo **lab-node-02 + LAB-NODE-01**); LAB-NODE-03 e LAB-NODE-04 **sem** obrigação de Docker.

Não corras **k3s** no LAB-NODE-01 a menos que queiras consumir RAM/CPU para testes de cluster — para desenvolvimento e `lab-smoke-stack`, **Docker CE + Compose** basta.

---

## 7.1 Automação repetível (Ansible + OpenTofu) — opcional, recomendado para “não esquecer passos”

Se você quer **repetibilidade** (reinstalar o LAB-NODE-01, padronizar baseline, ou reaplicar ajustes sem “lembrar de cabeça”), uma dupla comum é:

- **Ansible**: configurações no host (pacotes, arquivos, serviços, hardening leve).
- **OpenTofu**: infraestrutura declarativa (quando você tem APIs/provedores; útil para lab com providers suportados).

**Guardrails (sem regressão e sem segredos):**

- **Não** coloque segredos (tokens, chaves, senhas) em arquivos rastreados neste repo. Prefira:
  - variáveis de ambiente no terminal da sessão,
  - vault externo,
  - ou árvore **gitignored** (`docs/private/…`) se for só para você.
- Trate a automação como **insumo**: execute, valide, e só então torne “padrão”.

### 7.1.1 Ansible (host bootstrap)

Instalação (preferir `apt`):

```bash
sudo apt update
sudo apt install -y ansible
ansible --version
```

**Esqueleto mínimo** (recomendação: manter em um repositório separado `lab-automation/` ou em `docs/private/`):

```text
lab-automation/
  ansible/
    inventory.ini
    bootstrap-lab-node-01.yml
    group_vars/
      all.yml
```

`inventory.ini` (localhost):

```ini
[lab-node-01]
localhost ansible_connection=local
```

`bootstrap-lab-node-01.yml` (exemplo intencionalmente curto):

```yaml
---
- name: Bootstrap LAB-NODE-01 (LMDE 7)
  hosts: lab-node-01
  become: true
  tasks:
    - name: Install baseline packages
      ansible.builtin.apt:
        update_cache: true
        name:
          - git
          - curl
          - ca-certificates
          - build-essential
          - jq
          - ufw
          - unattended-upgrades
          - fwupd
        state: present

    - name: Enable UFW with safe defaults
      ansible.builtin.shell: |
        set -euo pipefail
        ufw default deny incoming
        ufw default allow outgoing
        ufw --force enable
      args:
        executable: /bin/bash
```

Execução:

```bash
cd lab-automation/ansible
ansible-playbook -i inventory.ini bootstrap-lab-node-01.yml
```

**Padrao oficial neste repo (baseline LAB-OP no LAB-NODE-01):** usar **`ops/automation/ansible/README.md`** e o playbook **`ops/automation/ansible/playbooks/lab-node-01-baseline.yml`** (roles em `ops/automation/ansible/roles/`, inclui **`tmux`** no pacote base e **`lab-node-01_bitwarden_cli`** — `bw` via `npm`, porque **nao** existe pacote `bitwarden-cli` no Debian principal). No Windows, o atalho **`scripts/lab-node-01-ansible-baseline.ps1`** gera `inventory.local.ini` com `localhost` + `ansible_connection=local` e executa o playbook **no LAB-NODE-01** por SSH. **Fluxo completo** (baseline fechado, sudo warm, `bw`, VeraCrypt): [LAB-NODE-01_BASELINE_COMPLETION.pt_BR.md](LAB-NODE-01_BASELINE_COMPLETION.pt_BR.md). **Dotfiles tmux** para todos os Linux do lab: secao **5** em [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.pt_BR.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.pt_BR.md).

**Alterações nos roles e no baseline** (por exemplo `apt-listbugs` em installs, D-Bus ou `systemctl` com Ansible, Snapper em btrfs, sincronizar o repo no LAB-NODE-01 antes de rodar o playbook) **não** são copiadas para este guia — ficam na secão **Troubleshooting** de **`ops/automation/ansible/README.md`** e no próprio código em **`ops/automation/ansible/`**. O exemplo `lab-automation/bootstrap-lab-node-01.yml` acima é só **ilustrativo**; o alvo de verdade é **`lab-node-01-baseline.yml`**.

### 7.1.2 OpenTofu (infra declarativa)

**Nota honesta:** OpenTofu vale quando você tem um provider real para o alvo (ex.: DNS/Cloud, GitHub, algum appliance com API). Para “só configurar o Linux”, Ansible costuma bastar.

Instalação:

- Primeiro tente `apt` (se existir na tua base Debian/LMDE):

```bash
sudo apt update
sudo apt install -y opentofu || true
tofu version
```

- Se não existir no `apt`, siga o método oficial de instalação do OpenTofu (binário assinado / checksum) e **documente** o caminho que você adotou em `docs/private/` para repetibilidade.

**Esqueleto mínimo**:

```text
lab-automation/
  tofu/
    versions.tf
    main.tf
    outputs.tf
```

`versions.tf` (exemplo genérico):

```hcl
terraform {
  required_version = ">= 1.6.0"
}
```

Execução (com variáveis fora do Git quando houver segredos):

```bash
cd lab-automation/tofu
tofu init
tofu plan
tofu apply
```

### 7.1.3 “Não esquecer” (checklist de validação pós-automação)

Depois de rodar automações, valide manualmente (mesma lógica do §9):

- `mokutil --sb-state` (Secure Boot ainda **enabled**)
- `ufw status verbose`
- `unattended-upgrades --dry-run --debug` (sem erro óbvio)
- `fwupdmgr get-updates` (sem falha)
- `uv sync` + `uv run pytest` no repo Data Boar

Se qualquer item “quebrar”, ajuste o playbook/tofu e reexecute — objetivo é **idempotência**.

## 9. Pacotes úteis para auditoria / homelab (opcional)

- **Lynis** — vê **§3.5** (instalação e auditoria)
- **Net-SNMP** (cliente), se fores usar [snmp-LAB-ROUTER-01-lab-probe.ps1](../../scripts/snmp-LAB-ROUTER-01-lab-probe.ps1) a partir de **outra** máquina ou WSL — no Linux nativo: `sudo apt install -y snmp` (MIBs opcionais: `snmp-mibs-downloader` pode exigir `non-free` no Debian 13; não é obrigatório para OIDs numéricos)

Inventário completo sugerido pelo projeto: [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) (script `homelab-host-report.sh`).

---

## 10. Verificação final (checklist — expandida)

- [ ] **UEFI / Secure Boot:** `mokutil --sb-state` mostra **enabled**; se usaste **Ventoy + enrolment**, confirmas que o assistente ficou concluído e não desligaste Secure Boot para “facilitar”.
- [ ] **Ventoy:** versão no stick alinhada ao release atual em [Ventoy releases](https://github.com/ventoy/Ventoy/releases) (atualiza com **`Ventoy2Disk`** no teu Windows de manutenção quando fizer sentido).
- [ ] `sudo apt update && apt list --upgradable` sem surpresas críticas pendentes há semanas.
- [ ] `ufw` ativo com regras mínimas; SSH (se existir) não aberto à Internet inteira.
- [ ] `fwupd` / firmware aplicados quando disponíveis.
- [ ] (Opcional) **`lynis audit system`** sem regressão óbvia após mudanças grandes (§3.5).
- [ ] Python: **`python3.13 --version` ≥ 3.13** (recomendado) ou **`python3.12 --version` ≥ 3.12**; `uv --version` OK.
- [ ] No clone do repo: `uv sync` sem erro; `uv run pytest` conforme o projeto.
- [ ] `config.yaml` **não** commitado (política do `.gitignore`).
- [ ] **Lab-op:** manifesto (`lab-op-hosts.manifest.json`) e SSH/chaves prontos se o LAB-NODE-01 for host de coleta (§6.5).
- [ ] **Containers:** `docker --version` e `docker compose version` (CE) ou `podman --version`; hello-world roda sem erro.
- [ ] **Swarm (se habilitado):** `docker info | grep Swarm` mostra `Active`.
- [ ] **Observabilidade CLI:** `iotop --version`, `iftop -v`, `ctop --version`, `monit --version`, `sensors` (lm-sensors).
- [ ] **Munin node:** `systemctl is-active munin-node` → `active`; plugins configurados.
- [ ] **Syslog forward (se configurado):** `journalctl -u rsyslog` sem erros de conexão.
- [ ] **Prometheus node_exporter (se instalado):** `curl -s localhost:9100/metrics | head -5`.
- [ ] **Wazuh agent (se instalado):** `/var/ossec/bin/wazuh-control status` → `wazuh-agentd running`.

---

## 11. Documentação relacionada no repositório

|Documento|Uso|
|---|---|
|[TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)|Instalação app, conectores, `uv`.|
|[HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md)|Lista de pacotes e captura de inventário.|
|[LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md](LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md)|Podman + k3s no host de lab (opcional; **Docker CE** vem da baseline Ansible).|
|[PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)|Grafana, Prometheus/Influx, Loki, Graylog — **depois** da baseline (§7 do doc acima).|
|[OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.pt_BR.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.pt_BR.md)|Atualizações no workstation, **Topgrade**, **`gta`**, **Bitwarden CLI** (`bw`).|
|[SECURITY.md](../../SECURITY.md)|API key, binding, boas práticas.|
|[PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)|Onde guardar notas **não públicas**.|

---

**Última revisão:** alinhada a Debian 13 / LMDE 7 e a `pyproject.toml` do Data Boar (**≥3.12**, **3.13** recomendado em host); confirme pacotes com `apt-cache policy python3.13` (ou `python3.12` em fallback).


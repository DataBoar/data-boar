# Cursor no Ubuntu / Zorin OS com AppArmor

**English:** [CURSOR_UBUNTU_APPARMOR.md](CURSOR_UBUNTU_APPARMOR.md)

**Público:** Operadores que usam o **Cursor** em desktops baseados em **Ubuntu** (**Zorin OS 18** ≈ base **Ubuntu 24.04 noble**) com **AppArmor** ativo (padrão nas variantes suportadas).

**Objetivo:** Instalar o Cursor, verificar se o AppArmor o afeta e aplicar correções **incrementais e seguras** quando o kernel **nega** operações.

**Fora de âmbito:** editores em **Snap** (confinamento diferente), **Cursor** em **Flatpak** (Bubblewrap), **Firejail** ou outros empacotadores **por cima** do AppArmor—trate como camadas separadas.

---

## 1. Pré-condições

1. **AppArmor** ativo (típico no Ubuntu/Zorin):

   ```bash
   systemctl is-active apparmor && sudo aa-status --enabled
   ```

1. Ferramentas úteis:

   ```bash
   sudo apt update
   sudo apt install -y apparmor-utils
   ```

---

## 2. Instalar o Cursor (`.deb` oficial Linux)

1. Baixar o **Linux** `.deb` em [cursor.com](https://cursor.com) (ou o canal licenciado que usar).
1. Instalar:

   ```bash
   sudo apt install -y ./cursor_*.deb
   # ou: sudo dpkg -i ./cursor_*.deb && sudo apt -f install
   ```

1. Confirmar o lançador:

   ```bash
   command -v cursor
   cursor --version
   ```

**Caminhos típicos** (podem mudar entre versões):

- Binário: `/usr/bin/cursor` → costuma apontar para `/usr/share/cursor/`
- Dados do usuário: `~/.config/Cursor/`, `~/.cursor/` (extensões, regras)

---

## 3. Caso padrão: sem trabalho extra no AppArmor

Em muitas instalações **.deb**, o Cursor corre **sem perfil AppArmor dedicado** (processo **unconfined** no `aa-status`). Aí o **AppArmor não bloqueia** o Cursor; concentre-se em problemas de permissões, Wayland/X11 ou GPU—not MAC.

Verificar:

```bash
sudo aa-status 2>/dev/null | grep -i cursor || true
# Se vazio: normalmente não há perfil → unconfined para efeitos de AppArmor
```

Inicie o Cursor a partir de um terminal para ver erros:

```bash
cursor --verbose 2>&1 | tee /tmp/cursor-launch.log
```

---

## 4. Quando o AppArmor *bloqueia* o Cursor

Sintomas: crash ao abrir, **terminal integrado** falhando, **Git** falhando, ou **gravar arquivos** em certas árvores—**e** o log do kernel mostra **AppArmor DENIED** para `cursor`, `cursor-sandbox` ou um Contributor-A (ex.: `node`, `bash`).

### 4.1 Recolher evidência

```bash
sudo dmesg -T | tail -80
sudo journalctl -k -b --no-pager | grep -iE 'apparmor|denied' | tail -40
```

Anote o **nome do perfil** na linha de negação (ex.: `usr.share.cursor.cursor`, `cursor`, ou nome baseado em caminho).

### 4.2 Perfis carregados

```bash
sudo aa-status
```

Se aparecer um perfil **relacionado com o Cursor** em modo **enforce** e houver **DENIED** correspondentes, avance para a §5.

---

## 5. Remediação (privilégio mínimo primeiro)

### 5.1 Atualizar o Cursor

Instale o `.deb` mais recente; o *layout* ou compatibilidade pode mudar.

### 5.2 Modo *complain* (diagnóstico temporário)

**Só se** existir um perfil que afete o Cursor. Coloca o perfil em modo que **registra** sem bloquear (Ubuntu: `aa-complain`):

```bash
sudo aa-complain /etc/apparmor.d/<nome-do-perfil>
# Teste de novo o Cursor; veja logs; depois aperte (§5.3) ou volte a enforce
sudo aa-enforce /etc/apparmor.d/<nome-do-perfil>
```

Substitua `<nome-do-perfil>` pelo arquivo em `/etc/apparmor.d/` que corresponde à negação (`ls /etc/apparmor.d/ | grep -i cursor`).

### 5.3 Sobreposições *local* (preferível a longo prazo)

Pacotes estilo Ubuntu incluem frequentemente **`#include <local/...>`** no perfil principal. Coloque regras **só** em **`/etc/apparmor.d/local/`** para upgrades do pacote **não** apagarem as suas linhas.

1. Encontrar o perfil principal:

   ```bash
   grep -ril cursor /etc/apparmor.d/ 2>/dev/null
   ```

1. Abrir o arquivo e confirmar um include do tipo:

   `#include <local/usr.bin.cursor>`

1. Criar o arquivo local (nome de exemplo—**precisa coincidir** com o include **no seu** sistema):

   ```bash
   sudo install -m 644 /dev/null /etc/apparmor.d/local/usr.bin.cursor
   sudo editor /etc/apparmor.d/local/usr.bin.cursor
   ```

1. Acrescentar permissões **mínimas**. Necessidades comuns de IDE (ajuste ao que **`dmesg`**/**`journalctl`** mostra como **DENIED**):

   - Leitura/escrita em **`@{HOME}/.config/Cursor/`** e **`@{HOME}/.cursor/`**
   - Leitura de **`@{HOME}/.ssh/`** se o Git usar chaves SSH (muitas vezes só leitura)
   - **`ix`** (*inherit execute*) para **`/usr/bin/git`**, **`/bin/bash`** ou **`/usr/bin/bash`** se o perfil exigir regras explícitas de execução

   **Não** copie perfis inteiros de terceiros; alargue só o que o kernel **negou**.

1. Recarregar:

   ```bash
   sudo apparmor_parser -r /etc/apparmor.d/<perfil-principal>
   ```

### 5.4 Perfil personalizado do zero

Uso avançado: **`aa-genprof`** / **`aa-logprof`** (ver guia Ubuntu Server — *Security — AppArmor*) a partir de registros de auditoria. Aplicações **Electron** geram muitos Contributor-As—espere várias iterações.

### 5.5 O que não fazer

- **Não** desligue o AppArmor em todo o sistema (`systemctl disable apparmor` ou `apparmor=0` no kernel) numa máquina que queira manter endurecida—perde MAC para **todas** as aplicações.
- **Não** ponha perfis em **unconfined** por conveniência sem registrar o risco.

---

## 6. Notas Zorin OS

- **Zorin OS 18** usa base **Ubuntu noble** nos pacotes centrais; o comportamento do **AppArmor** segue o deste guia como **Ubuntu 24.04**.
- **Wayland** (padrão em GNOME recente) **não** remove AppArmor; falhas continuam visíveis como **DENIED** no log do kernel se um perfil se aplicar.
- Se o **Lynis** reportar *AppArmor presente mas “MAC framework NONE”* para certos serviços, isso é **auditoria** à parte—este doc trata só da **usabilidade do Cursor** com AppArmor.

---

## 7. Ligações cruzadas

- Contexto homelab (ex. **`lab-op`** / desktop Ubuntu-family): **`docs/private/homelab/LAB_SECURITY_POSTURE.md`** §2 (UFW, Lynis, menções AppArmor)—**não** substitui este runbook.
- **Cursor + segredos / `docs/private/`:** **[PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md)**.
- **Windows / WSL** e separação de caminhos: **[WINDOWS_WSL_MULTI_DISTRO_LAB.pt_BR.md](WINDOWS_WSL_MULTI_DISTRO_LAB.pt_BR.md)**.

---

## 8. Revisão

| Data       | Nota                                              |
| ---------- | ----                                              |
| 2026-03-22 | Runbook inicial (Ubuntu / Zorin, fluxo AppArmor). |

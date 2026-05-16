# PC Windows principal de desenvolvimento — wrappers CLI rápidos (scripts `repo-*`)

**English:** [WINDOWS_FAST_CLI_WRAPPERS.md](WINDOWS_FAST_CLI_WRAPPERS.md)

## Objetivo

No **PC Windows do operador**, o assistente deve preferir **wrappers pequenos** em **`scripts/`** que chamam **ferramentas nativas rápidas** (`rg`, **`tail`** do Git, **`bat`**, **`es-find.ps1`**) antes de cair em padrões PowerShell mais lentos (`Get-ChildItem -Recurse`, varreduras sem teto). Isso reduz **toil**, **tokens** e **tempo de relógio**.

**Regra:** **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** (sempre) — folhear **`TOKEN_AWARE_SCRIPTS_HUB.md`** antes de reinventar shell.

## Scripts (este recorte)

| Script | Prefere | Fallback | Notas |
| ------ | ------- | -------- | ----- |
| **`scripts/repo-grep.ps1`** | **`rg`** (ripgrep); **`baregrep.exe`** só com **`-PreferBareGrep`** | **`Select-String`** (varredura com teto de arquivos) | Evita **`grep.exe`** “estranho” (ex.: toolchain FPC) em modo recursivo inseguro. **`-MaxOutputLines`** limita a transcrição. Também procura **`baregrep.exe`** em **`%USERPROFILE%\Downloads`** (portátil; não é winget). |
| **`scripts/repo-tail.ps1`** | **`tail.exe`** do Git (**`usr\bin`**) quando existir | **`Get-Content -Tail`** | **BareTail** é **GUI** — **não** entra na automação; se existir **`baretail.exe`** (ou erro comum **`baretai.exe`**) em **`Downloads`**, o script imprime **uma dica** para o operador lembrar do caminho rápido via Git **`tail`**. |
| **`scripts/repo-view.ps1`** | **`bat`** / **`batcat`** com pager desligado + intervalo de linhas | **`Get-Content -TotalCount`** | Resolve **`bat`** / **`batcat`** no **`PATH`**, WinGet Links, cargo ou **`Downloads`**. |

**Nome/caminho de arquivo (não conteúdo):** continuar com **`scripts/es-find.ps1`** → **`es.exe`** — ver **`EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**. Não há **`locate(1)`** no Windows; o **`es`** é o análogo rápido para **nomes/caminhos**.

## Dicas de instalação (máquina do operador)

- **Ripgrep:** `winget install BurntSushi.ripgrep.MSVC` (ou outra distribuição de **`rg`**) para o **`repo-grep.ps1`** usar o caminho rápido.
- **Git for Windows:** traz **`tail.exe`** em **`Program Files\Git\usr\bin\`** — habilita o caminho rápido do **`repo-tail.ps1`**.
- **`bat`:** costuma vir por **WinGet** ou **cargo**; o **`repo-view.ps1`** resolve **`bat`** / **`batcat`** no **`PATH`**.
- **BareGrep / BareTail (Bare Metal Software):** ferramentas **GUI** opcionais; o **`baregrep`** pode rodar por CLI (pode mostrar **splash**). Use **`-PreferBareGrep`** só quando esse trade-off for aceitável.

## Comportamento do assistente (reduzir toil)

1. **Tentar o wrapper primeiro** quando couber na tarefa (busca, tail, preview, índice de nomes).
2. **Se a ferramenta rápida faltar ou falhar:** usar o **fallback documentado** no script para o operador ainda ter **resposta** sob pressão.
3. **Avisar o operador** quando a falha parecer **ambiental** (binário ausente, **EULA**, serviço parado, instalador pedindo clique) — **uma linha curta** — para corrigir PATH, instalar **`rg`**, aceitar termos **Sysinternals**, ligar o **Everything**, etc. **Não** “esquecer” em silêncio que o wrapper existe.
4. **Adiar debug profundo** quando o fallback bastar no momento; voltar depois para corrigir flags ou edge cases do script com calma.

## Referências

- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`**
- **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**
- **ADR 0023** — Everything / **`es-find.ps1`** primeiro com fallback
- **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`**

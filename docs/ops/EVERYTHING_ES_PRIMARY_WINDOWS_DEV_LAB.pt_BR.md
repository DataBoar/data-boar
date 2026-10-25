# Voidtools Everything (`es.exe`) no PC Windows principal de desenvolvimento — busca por nome de arquivo (token-aware)

**English:** [EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md)

**Escopo:** [Voidtools Everything](https://www.voidtools.com/) indexa **nomes e caminhos** de arquivos no **Windows**. Por padrão **não** faz busca **dentro** do conteúdo dos arquivos.

---

## PC Windows principal de desenvolvimento vs lab-op (importante)

| Ambiente | Ferramenta para "achar por nome/caminho" |
| -------- | ---------------------------------------- |
| **L-series** (PC Windows principal de dev) | **`.\scripts\es-find.ps1`** → **`es.exe`** (o Everything precisa estar em execução). |
| **lab-op** (Linux via **SSH**) | **Sem** `es.exe` — usar **`find`**, **`fd`** ou **`locate`** no host, ou pistas de caminho nos reports do **`lab-op.ps1`**. |

Fluxos que citam **lab-op** e **busca de arquivos** em geral significam: orquestrar no Linux; usar **Everything** só quando o operador estiver no **Windows (PC principal de desenvolvimento)** procurando em **volumes locais** indexados (incluindo drives sincronizados como pCloud, se indexados).

---

## Instalação (uma vez por máquina Windows)

1. Instalar o **Everything** (GUI/serviço) para o índice se manter atualizado.
2. Instalar o **Everything CLI** para o `es.exe` ficar disponível, por exemplo:

   `winget install voidtools.Everything.Cli`

3. Garantir que **`es`** resolva (`Get-Command es`) ou passar **`-EsExePath`** no wrapper. O WinGet costuma colocar shim em `%LOCALAPPDATA%\Microsoft\WinGet\Links\es.exe`.

Se aparecer **Everything IPC not found**, abrir o **Everything** (aplicativo ou serviço) para o `es.exe` conseguir conectar.

---

## Wrapper preferido (repo)

Na raiz do repositório **data-boar**:

```powershell
.\scripts\es-find.ps1 -Help
.\scripts\es-find.ps1 -Query "*.md" -MaxCount 40
.\scripts\es-find.ps1 -Query "PLAN_" -Global -MaxCount 25
.\scripts\es-find.ps1 -Query "foo" -SearchRoot "D:\work" -MaxCount 30
.\scripts\es-find.ps1 -Query "bar" -ShowCommand
```

- **Escopo padrão** = **raiz deste repo** (omitir **`-Global`** para varreduras normais dentro do repo quando **Glob** ficaria pesado).
- **`-MaxCount`** limita a saída — mantém transcrições **token-aware** (padrão **50** no script).
- **`-ShowCommand`** imprime a linha exata do `es.exe` para copiar ou estender com flags **diretas** da CLI.
- **`-FallbackPowerShell`** — se o **`es.exe`** **não** estiver instalado, executa uma busca recursiva **limitada** com **`Get-ChildItem`** no mesmo escopo padrão (raiz do repo ou **`-SearchRoot`**). **Mais lenta** e com mais I/O que o Everything. **Não** combina com **`-Regex`** ou **`-Global`** (esses casos precisam da CLI real).

### pCloud (`P:`) e outras árvores de sincronização enormes

No **Windows** do operador, o **pCloud** costuma montar como **`P:`** (ver **`AGENTS.md`** / **`docs/PRIVATE_OPERATOR_NOTES.pt_BR.md`**). Pastas como **`P:\Automatic Upload\...`** podem ter **dezenas de milhares** de arquivos — **padrão** = **`es-find.ps1`** (índice do Everything / **`es.exe`**); **`Get-ChildItem`** só como **recuperação** se o **`es`** falhar (**avisar** IPC/PATH). Evitar **começar** só com **`Get-ChildItem -Recurse`** sem limite nessas raízes (lento, barulhento, péssimo custo em tokens).

**Preferir:**

```powershell
.\scripts\es-find.ps1 -SearchRoot "P:\Automatic Upload" -Query "*.jpg" -MaxCount 20
```

Use o **`-SearchRoot` mais estreito** que o operador confirmar. Notas com subpastas reais: **`docs/private/WHAT_TO_SHARE_WITH_AGENT.md`**.

---

## Fallback quando o `es.exe` não existe (assistentes)

**Ordem:**

1. **`.\scripts\es-find.ps1`** (**`es.exe`**) — **padrão** no **Windows (PC principal de desenvolvimento)** para achar arquivos por **nome/caminho** quando o índice rápido vence **Glob** em árvore **grande**; **não pular** para **`Get-ChildItem`** ad hoc quando o **`es`** devia funcionar.
2. Se **`es-find`** / **`es.exe`** falhar: **avisar o operador** em uma linha (código de saída, IPC, PATH) para instalar/corrigir o **Everything** — depois o mesmo script com **`-FallbackPowerShell`**, ou **`Glob`** do Cursor **no repo**, ou **`Get-ChildItem`** numa pasta **estreita**. **`Get-ChildItem`** é **recuperação**, não padrão equivalente.
3. **Não** usar **SemanticSearch** ou **Grep** enorme como substituto de “achar este **nome de arquivo**” — ferramenta errada e mais cara em tokens.
4. **SSH Linux (lab-op):** **`find`** / **`fd`**, não **`es`**.

---

## `es.exe` direto (avançado)

Quando o wrapper não expuser a flag necessária, rodar **`es.exe -h`** ou a mesma linha impressa por **`-ShowCommand`**, e acrescentar opções conforme a [ajuda da CLI Voidtools](https://www.voidtools.com/support/everything/command_line_interface/). Preferir passar ao assistente listas **curtas** de resultados, não milhares de caminhos.

---

## Higiene de tokens (assistentes + operador)

- Preferir **`Glob`** / **`Grep`** / **`SemanticSearch`** para trabalho **dentro** do **workspace** quando forem rápidos o bastante.
- Usar **`es-find.ps1`** quando a tarefa for **por nome/caminho**, **fora** do repo, ou **Glob** ficar enorme.
- **Nunca** colar dumps longos de caminhos reais em **commits, PRs ou docs rastreados**; usar notas **privadas** se precisar guardar evidência (**`private-pii-never-public.mdc`**).

---

## Guardrails

- **Só leitura** em relação ao Git e aos arquivos: **lista** caminhos no índice; **não** altera o repo.
- **Seguro para PC Windows principal de desenvolvimento** na árvore canônica: não é operação destrutiva — ver **[PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md)**.

---

## Taxonomia

- **Palavra-chave de sessão (chat):** **`es-find`** — ver **`.cursor/rules/session-mode-keywords.mdc`**.
- **Skill:** **`.cursor/skills/everything-es-search/SKILL.md`**
- **Regra:** **`.cursor/rules/everything-es-cli.mdc`**

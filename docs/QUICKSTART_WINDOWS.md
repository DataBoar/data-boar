# Data Boar no Windows — quickstart **sem Docker** (passo a passo)

> **Sem Docker, sem virtualização, sem complicação.** Instala direto no Windows. O demo usa **dados falsos (sintéticos)** → **nada seu sai do PC**, zero risco. Roda até em máquina modesta.
>
> Feito para quem **nunca** usou “terminal” nem “Python”. Cada passo diz o **como** e o **porquê**. Travou? [Abra uma issue](https://github.com/DataBoar/data-boar/issues/new) (foto da tela ajuda) ou fale com a gente.

**Público:** usuário final no Windows (escritório, PME, DPO sem TI profunda).
**Não é** o caminho de desenvolvedor (`git clone` + `uv` + `python main.py`) — isso fica no [QUICKSTART.md](../QUICKSTART.md) Caminho B.

---

## A regra de ouro (leia antes de tudo)

Você vai **colar comandos no Terminal** (a “telinha de comandos”). Existe uma confusão comum — evite:

- **Certo:** colar no **Terminal**, onde aparece `PS C:\Users\voce>` (ou `C:\Users\voce>`).
- **Errado:** digitar `python` primeiro, ver aparecer `>>>`, e colar os comandos **lá dentro**. Isso é o *interpretador do Python*, não o Terminal → dá erro estranho.

> **Não digite só `python` e Enter antes.** Cole os comandos **direto no Terminal.** Se aparecer `>>>`, você entrou no Python sem querer — **feche e reabra o Terminal.**

---

## Passo 0 — abra o PowerShell que já vem no Windows

Tecle **Windows** → digite **`PowerShell`** → Enter. Essa telinha de comandos **já está no Windows** — não precisa instalar nada. É **daqui** que a gente começa.

> Apareceu `PS C:\Users\voce>`? É ele. Apareceu `>>>`? Você abriu o **Python** por engano — feche (lembra a **regra de ouro** lá em cima).

---

## Passo 1 — instalar o Terminal e o Python (2 comandos, aqui no PowerShell)

Cole **um por vez**:

```powershell
winget install Microsoft.WindowsTerminal
winget install Python.Python.3.12
```

> **Por que sugerimos uma versão concreta no `winget`?**
> Só para **facilitar o primeiro dia**: instalação previsível, PATH certo, menos “deu erro estranho”.
> **Não** é “proibido usar versão nova” nem “no-GIL é ruim” — o Data Boar **suporta** Python recente e **valoriza** no-GIL (`cp314t`) nos canais nativos (pacotes com interpretador embutido).
> Prefira **winget** ou o instalador do **[python.org](https://www.python.org/downloads/windows/)** (marque **“Add python.exe to PATH”**). A **Microsoft Store** costuma bagunçar o PATH — por isso **evitamos a Store** neste guia (motivo de PATH, não de versão).
> Se você **já tem** outra versão suportada e o Passo 3 (`--demo`) sobe, **pode seguir** — não precisa desinstalar.
> **Em breve:** o instalador Windows (MSI / winget do produto — [issue #1467](https://github.com/DataBoar/data-boar/issues/1467)) **já vem com o Python embutido** (incluindo no-GIL) — aí você **não escolhe versão**.

**Agora feche o PowerShell.** Abra o **Windows Terminal** (tecle Windows → digite **`Terminal`** → Enter — agora ele existe) e **continue daqui.** O Windows Terminal copia-e-cola melhor = menos erro bobo.

*(Sem `winget`? Raro. Baixe Python em [python.org/downloads/windows](https://www.python.org/downloads/windows/) — escolha uma versão estável listada lá — e **marque “Add python.exe to PATH”**.)*

---

## Passo 2 — instalar o Data Boar

No **Terminal** (lembra: prompt `PS C:\…`, **nunca** o `>>>`), cole **uma linha por vez**:

```powershell
python -m pip install --upgrade pip
python -m pip install --user pipx
python -m pipx ensurepath
```

> **Por que `--upgrade pip` primeiro?** O “pip” é o instalador de programas do Python; atualizá-lo antes evita erros bobos na hora de instalar o pipx.

> Avisos **amarelos** (`...is not on PATH`, `A new release of pip...`) — **é normal, não é erro.** O `pipx ensurepath` + fechar-e-reabrir já resolve. **Só se assuste com vermelho que tenha a palavra `Error`.** Amarelo = tudo bem, segue em frente.

**Feche e reabra o Terminal mais uma vez.** Depois:

```powershell
pipx install data-boar
```

---

## Passo 3 — rodar o DEMO (comece sempre por aqui)

```powershell
data-boar --demo
```

O Terminal vai mostrar que **está rodando** (aparece algo como servidor em `127.0.0.1:8088`). **Isso já confirma que funcionou** no seu PC — mesmo sem abrir o navegador.

Para ver o **painel**, abra o **navegador** (Edge, Chrome ou Firefox). Na barra de endereço, digite **só isto**:

```text
http://127.0.0.1:8088
```

Digite **exatamente isso** — **sem asterisco, sem aspas.** (Aqueles `*` e `**` que às vezes aparecem em textos são só formatação de negrito — **não** fazem parte do endereço.)

O painel (**dashBOARd**) abre com uma **varredura de demonstração** (CPF/e-mail **de mentira**, nada seu).

> Abriu em inglês? Troque para o **português** no seletor de idioma na tela. **Não** precisa digitar `/pt-br` no endereço (opcional).

Para **parar**: volte no Terminal e aperte **Ctrl + C**.

> O `--demo` é o **primeiro contato:** dados **sintéticos**, roda **só na sua máquina** (loopback), **zero risco**. Serve para **validar que roda** no seu PC — **antes** de tocar em qualquer dado real.

---

## Passo 3.5 — rodar de verdade (nos seus dados) — próximo passo

O `--demo` é **auto-suficiente** (já traz a configuração pronta). Para varrer **os seus dados de verdade**, o Data Boar precisa de um **arquivo de configuração** (`config.yaml`) que **aponta para onde olhar** — qual pasta (ou banco) varrer. **Ele não adivinha: você aponta o lugar.**

Esse é um **próximo passo guiado**: [abra uma issue](https://github.com/DataBoar/data-boar/issues/new) ou fale com a gente para montar o seu `config.yaml` (pastas certas). Com ele pronto, o comando fica:

```powershell
data-boar --web --allow-insecure-http --config caminho\do\seu-config.yaml
```

> O `--allow-insecure-http` é **normal** para rodar **local** (na sua máquina, sem certificado TLS) — não use isso como desculpa para expor o painel na internet. **Comece sempre pelo `--demo`**; o modo real vem depois, **com o config**.

Mais detalhes: [USAGE.pt_BR.md](USAGE.pt_BR.md) · amostras: [deploy/samples/](../deploy/samples/).

---

## Passo 4 — criar um atalho com ícone (para quase não voltar ao terminal)

Para abrir com **2 cliques**, sem terminal:

1. Botão-direito na **Área de Trabalho** → **Novo** → **Atalho**.
2. No caminho, cole: `%USERPROFILE%\.local\bin\data-boar.exe --demo`
3. Nome: **Data Boar** → **Concluir**.
4. Botão-direito no atalho → **Propriedades** → **Alterar ícone** → aponte para o ícone do javali (quando disponível no pacote / site).

Pronto: **duplo-clique** abre o painel. *(Em breve: `data-boar --install-shortcut` pode criar isso sozinho — [issue #1127](https://github.com/DataBoar/data-boar/issues/1127). Depois, troque `--demo` por `--web --allow-insecure-http` no atalho quando tiver o config real.)*

---

## Qual Windows você tem?

Este guia é para **Windows 10 e 11** (o comum). No **11** o `winget` já vem; no **10** quase sempre também.

**Windows 7** (sem suporte há anos) é **caso especial** — o `winget` não existe lá. [Abra uma issue](https://github.com/DataBoar/data-boar/issues/new): há outro caminho, ou a máquina já pede o **MSI** (em construção, #1467).

Se o instalador **reclamar de “compilar”** algo (raro — máquina bem antiga / sem instruções modernas de CPU), avise na issue: é o caso do **MSI** / build pré-compilado. Na maioria das máquinas **roda direto. Zero Docker, zero virtualização.**

---

<details>
<summary>Alternativa Docker (só se você JÁ usa Docker)</summary>

```powershell
docker run --rm -p 8088:8088 fabioleitao/data_boar:latest demo
```

Abra `http://127.0.0.1:8088`. O caminho **pipx** acima é o **recomendado** para este público; Docker fica de reserva.

</details>

---

## Relacionado

| Doc | Para quê |
| --- | -------- |
| [QUICKSTART.md](../QUICKSTART.md) | Visão geral (Docker / uv / Caminho 0 terse) |
| [AUDIENCE_GUIDE.pt_BR.md](AUDIENCE_GUIDE.pt_BR.md) | Quem lê o quê |
| [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md) | Problemas comuns de install |
| Site institucional | Narrativa de negócio (quando publicado) — o **como rodar** fica neste guia |

---

*Feedback de campo (1º usuário non-techie): regra terminal vs REPL · porquê de sugerir versão estável · Terminal como pré-requisito · upgrade pip · `--demo` antes do `--web` · atalho. Issues [#1128](https://github.com/DataBoar/data-boar/issues/1128), [#1126](https://github.com/DataBoar/data-boar/issues/1126).*

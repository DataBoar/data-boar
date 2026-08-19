# Governance Lens — início rápido (Pro)

**English:** [GOVERNANCE_LENS_QUICKSTART.md](GOVERNANCE_LENS_QUICKSTART.md)

Guia curto para operadores: habilitar o Governance Lens, gerar relatório GRC em Markdown a partir de uma sessão SQLite existente e exportar DOCX/PDF com **pandoc** (opcional, não incluso no pacote).

**Veja também:** [USAGE.pt_BR.md](../USAGE.pt_BR.md#governance-lens-pro) · [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md#governance-lens-architecture) · [deploy/config.example.yaml](../../deploy/config.example.yaml)

## Pré-requisitos

- Sessão de varredura concluída no SQLite local (`sqlite_path` no config).
- Tier **Pro** (ou Enterprise) com `governance_lens_pro` permitido — em lab, `licensing.mode: open` + `licensing.effective_tier: pro`.
- Mapa de frameworks curado: licenciados recebem `governance_framework_map_pro.yaml` em termos comerciais. O Open Core inclui **`config/governance_framework_map_pro.example.yaml`** para lab/testes (`governance.map_file`).

O **pandoc** é ferramenta **externa opcional** para export DOCX/PDF — não é instalado nem empacotado com o Data Boar.

## 1. Habilitar no config

```yaml
licensing:
  effective_tier: pro   # só lab; produção usa arquivo de licença / JWT

governance:
  enabled: true
  tier: pro
  map_file: config/governance_framework_map_pro.example.yaml   # lab; substitua pelo mapa licenciado em produção
```

## 2. Rodar varredura ou reutilizar sessão

**Varredura nova:**

```bash
python main.py --config config.yaml
```

**Sessão existente:** liste sessões no dashboard ou no SQLite; anote o UUID `session_id`.

## 3. Gerar o relatório GRC em Markdown

```bash
python main.py --config config.yaml --governance-report ./relatorio_grc.md
```

Sessão explícita (opcional):

```bash
python main.py --config config.yaml --session <session_id> --governance-report ./relatorio_grc.md
```

Sem caminho, grava em `report.output_dir` como `Governance_Lens_<prefixo>.md`. O comando imprime o caminho absoluto no **stdout**. Sai **1** se não houver sessão; sai **2** se combinado com `--web`.

Com `governance.enabled: true`, a planilha Excel também inclui a aba **Governance View** quando os relatórios são gerados.

## 4. Exportar DOCX (pandoc)

Na raiz do repositório (caminhos relativos ao arquivo de defaults):

```bash
pandoc relatorio_grc.md --defaults config/pandoc_governance.yaml -o relatorio_grc.docx
```

Estilos Word vêm de `docs/templates/governance_reference.docx`.

## 5. Exportar PDF (pandoc + LaTeX)

```bash
pandoc relatorio_grc.md --defaults config/pandoc_governance.yaml \
  -o relatorio_grc.pdf --to=pdf -V pdf-engine=lualatex
```

Exige **LuaLaTeX** (ou outro engine que você configurar). Export PDF fica do lado do operador.

## 6. Pandoc é opcional

O Data Boar entrega Markdown **pronto para pandoc** e `config/pandoc_governance.yaml`. Instale [pandoc](https://pandoc.org/) (e LaTeX para PDF) na estação do operador ou na imagem de CI quando precisar de DOCX/PDF — o pacote Python não depende deles.

## Aviso

A saída do Governance Lens **apoia inventário técnico e narrativa GRC**; **não** constitui auditoria certificada, parecer jurídico nem atestado regulatório. Revisão humana por DPO, CISO, auditoria interna ou jurídico é obrigatória antes de uso externo.

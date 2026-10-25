# Licenciamento — Community (BSD-3) vs Pro (`pro/`) (tradução para conveniência)

**English (texto oficial):** [LICENSING.md](LICENSING.md)

O arquivo **LICENSING.md** na raiz do repositório contém o texto **oficial em inglês** sobre a fronteira de licenciamento Community vs Pro. **Para efeitos jurídicos e de licenciamento de software, somente a versão em inglês faz fé.** A tradução abaixo é apenas para facilitar a leitura em português brasileiro.

---

# Licenciamento — Community (BSD-3) vs Pro (`pro/`)

**Por que este arquivo existe.** O [LICENSE](LICENSE) na raiz é o texto oficial da **BSD 3-Clause** para a árvore open-core (Community). Em separado, os módulos comerciais do tier Pro em [`pro/`](pro/) **não** estão cobertos por essa concessão. Este documento declara essa fronteira em linguagem clara para que operadores, redistribuidores e assessoria jurídica não tratem um único arquivo de licença na raiz como aplicável a todos os caminhos do clone.

## Community (open-core)

- **Licença:** BSD 3-Clause — ver [LICENSE](LICENSE) (texto em inglês é autoritativo). Tradução de conveniência: [LICENSE.pt_BR.md](LICENSE.pt_BR.md).
- **Escopo:** Tudo neste repositório **fora** do diretório `pro/`, salvo caminho com aviso explícito próprio.

## Tier Pro (`pro/`)

- **Licença:** Proprietário / todos os direitos reservados — ver [`pro/LICENSE`](pro/LICENSE).
- **Escopo:** Todo o código-fonte sob `pro/` (incluindo cabeçalhos de copyright por arquivo que apontam de volta para `pro/LICENSE`).
- **Modelo comercial:** Os termos comerciais finais para `pro/` seguem em definição ativa (acompanhados na issue [#1576](https://github.com/DataBoar/data-boar/issues/1576) e docs de planejamento relacionados). Até a ratificação, vale o padrão em `pro/LICENSE`.

## Gate de license-key em runtime vs fronteira de copyright

O Data Boar pode restringir recursos Pro em **runtime** (chave de licença / beacon). Esse mecanismo é uma **camada de enforcement sobre** a fronteira de licenciamento descrita aqui. **Não** substitui os avisos de copyright e licença: receber ou executar um build que inclui `pro/` não amplia a concessão BSD-3 para dentro de `pro/`, e remover ou contornar o gate de runtime não cria licença de copyright para copiar, modificar ou redistribuir o código-fonte de `pro/`.

## Não-retroatividade

Este aviso e o arquivo `pro/LICENSE` documentam a fronteira pretendida daqui em diante. Eles **não** reescrevem, por si sós, o histórico de partes que já obtiveram cópia do código-fonte de `pro/` sob o empacotamento anterior do repositório, enquanto a árvore era apresentada sob um classificador BSD-3 único para o pacote inteiro. A assessoria jurídica deve avaliar distribuições anteriores com base nos fatos de cada recebimento; este arquivo não é aconselhamento jurídico.

## Contato

Dúvidas sobre licenciamento Community ou Pro: ver informações de contato em [README.md](README.md) e [SECURITY.md](SECURITY.md).

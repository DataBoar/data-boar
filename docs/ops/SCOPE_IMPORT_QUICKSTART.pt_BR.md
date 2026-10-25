# Importação de escopo — início rápido (planilha ou memória)

**English:** [SCOPE_IMPORT_QUICKSTART.md](SCOPE_IMPORT_QUICKSTART.md)

Use quando ainda **não** há exportação GLPI / CMDB — só lista de workshop, e-mail ou o que a equipe lembra. O fluxo técnico continua sendo **CSV → fragmento YAML**; colunas e tipos em [USAGE.pt_BR.md](../USAGE.pt_BR.md#scope-import-csv-fragment).

## Em uma frase

O importador de escopo transforma uma **planilha simples** (salva como **CSV UTF-8**) numa **lista YAML de `targets`** que você **cola** num arquivo de configuração real — em geral depois de copiar **[`deploy/samples/config.starter-lgpd-eval.yaml`](../../deploy/samples/config.starter-lgpd-eval.yaml)** e substituir ou mesclar o bloco `targets:`.

## Lista de entrega (autor não técnico → operador de TI)

| Etapa | Critério |
| ----- | -------- |
| Cabeçalho | Igual ao de **[`deploy/scope_import.example.csv`](../../deploy/scope_import.example.csv)** (nomes de coluna inalterados). |
| Senhas | **Sem** senhas reais nas células — só **nomes** em **`pass_from_env`** / **`user_from_env`**; o TI define as variáveis no servidor. |
| Encoding | Arquivo **CSV UTF-8** (separado por vírgula); evitar caracteres quebrados em português. |
| Fragmento | Saída do `scope_import_csv.py` **revisada** e mesclada ao `config.yaml` (não commitar se houver caminhos reais). |
| Execução | Operador roda `python main.py --config …` (ou API) com variáveis de ambiente definidas. |

## Se você está validando o produto (não vai operar a TI)

**Objetivo:** Entregar uma **lista de lugares** onde pode haver dados pessoais (pastas, bancos, compartilhamentos) para quem vai rodar o scanner. **Não** precisa entender YAML.

1. Siga os passos em **Caminho para quem não é de TI** abaixo para montar o CSV.
1. Entregue o CSV e esta página para quem executa o Data Boar; essa pessoa roda `scope_import_csv.py` e une o fragmento a um config começando por **[deploy/samples/config.starter-lgpd-eval.yaml](../../deploy/samples/config.starter-lgpd-eval.yaml)** (veja [docs/samples/README.pt_BR.md](../samples/README.pt_BR.md)).
1. **Sucesso:** fragmento `targets` revisado + `config.yaml` real com **caminhos de laboratório** e **senhas em variável de ambiente**, não na planilha.

## Caminho para quem não é de TI (Excel / LibreOffice)

Para **jurídico, DPO ou gestão de programa** que tem uma **lista de sistemas** (workshop ou memória) mas **não** um export de CMDB. Você só monta uma **tabela**; a TI roda um comando para gerar YAML.

1. Abra uma planilha nova.
1. Copie a **linha de cabeçalho** de [`deploy/scope_import.example.csv`](../../deploy/scope_import.example.csv) (a que começa com `type,`). **Não altere a ortografia do cabeçalho** — o script reconhece esses nomes de coluna.
1. Inclua **uma linha por fonte de dados** (pasta, base ou compartilhamento). Uma linha = um local onde a organização guarda arquivos ou tabelas que possam conter dados pessoais.
1. Em **`type`**, use só valores que o importador suporta hoje (ex.: `filesystem` para pasta, `postgresql` ou `mysql` para SQL, `smb` / `nfs` para compartilhamentos). Em dúvida, use `filesystem` para “uma pasta a analisar” e preencha **`path`** com o caminho que a TI confirmar.
1. **`name`** é um rótulo livre (ex.: “compartilhamento RH”) para reconhecer a linha na revisão — não é hostname técnico.
1. **Nunca** coloque senhas reais na planilha. Coloque o **nome de uma variável de ambiente** em **`pass_from_env`** (ex.: `DATA_BOAR_HR_DB_PASSWORD`) e peça à TI para definir essa variável no servidor antes das varreduras. O nome começa com `DATA_BOAR_`, `REST_API_` ou `API_`, e o YAML final precisa de `allowed_hosts` com o host daquela linha.
1. **Salvar como** → **CSV UTF-8** (vírgulas). Se só existir “CSV (delimitado por vírgulas)”, use **Excel UTF-8** ou **LibreOffice** em UTF-8 para não corromper acentos.
1. Entregue o CSV a quem executa o Data Boar (ou execute você, se tiver o repositório):
   `uv run python scripts/scope_import_csv.py caminho/para/sua.csv -o targets.fragment.yaml`
1. Abra **`targets.fragment.yaml`**. É um **fragmento** — cole a lista `targets:` num config completo. Partir de **[deploy/samples/config.starter-lgpd-eval.yaml](../../deploy/samples/config.starter-lgpd-eval.yaml)** é mais simples do que escrever YAML do zero; substitua o bloco `targets:` da amostra pela lista unida, se precisar.
1. A TI define as variáveis de ambiente para cada **`pass_from_env`** / **`user_from_env`** e sobe a aplicação com `--config` apontando para o `config.yaml` final.

## Privacidade

Trate o CSV como **inventário interno de infraestrutura** (permissões, sem repositório público). Mesma disciplina que [SECURITY.md](../../SECURITY.md) para config.

## Depois: GLPI ou outros exports

Colunas específicas de fornecedor serão mapeadas para o mesmo esquema canônico num adaptador futuro; o fluxo continua **exportação → limpeza no formato CSV → `scope_import_csv.py`**.
